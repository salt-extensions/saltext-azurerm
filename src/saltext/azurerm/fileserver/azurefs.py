"""
The backend for serving files from the Azure blob storage service.

.. versionadded:: 2015.8.0

To enable, add ``azurefs`` to the `fileserver_backend` option in the
Master config file.

.. code-block:: yaml

    fileserver_backend:
      - azurefs

Starting in Salt 2018.3.0, this fileserver requires the standalone Azure
Storage SDK for Python. Theoretically any version >= v0.20.0 should work, but
it was developed against the v0.33.0 version.

Each storage container will be mapped to an environment. By default, containers
will be mapped to the ``base`` environment. You can override this behavior with
the ``saltenv`` configuration option. You can have an unlimited number of
storage containers, and can have a storage container serve multiple
environments, or have multiple storage containers mapped to the same
environment. Normal first-found rules apply, and storage containers are
searched in the order they are defined.

You must have either an account_key or a sas_token defined for each container,
if it is private. If you use a sas_token, it must have READ and LIST
permissions.

.. code-block:: yaml

    azurefs:
      - account_name: my_storage
        account_key: 'YOUR_ACCOUNT_KEY'
        container_name: my_container
      - account_name: my_storage
        sas_token: 'YOUR_SAS_TOKEN'
        container_name: my_dev_container
        saltenv: dev
      - account_name: my_storage
        container_name: my_public_container

.. note::

    Do not include the leading ? for sas_token if generated from the web
"""

import base64
import logging
import os
import shutil

import salt.fileserver  # pylint: disable=import-error
import salt.utils.files  # pylint: disable=import-error
import salt.utils.gzip_util  # pylint: disable=import-error
import salt.utils.hashutils  # pylint: disable=import-error
import salt.utils.json  # pylint: disable=import-error
import salt.utils.path  # pylint: disable=import-error
import salt.utils.stringutils  # pylint: disable=import-error

try:
    from azure.storage.blob import BlobServiceClient

    HAS_AZURE = True
except (ImportError, AttributeError):
    HAS_AZURE = False


__virtualname__ = "azurefs"

log = logging.getLogger()


def __virtual__():
    """
    Only load if defined in fileserver_backend and azure.storage is present
    """
    if __virtualname__ not in __opts__["fileserver_backend"]:
        return False

    if not HAS_AZURE:
        return False

    if "azurefs" not in __opts__:
        return False

    if not _validate_config():
        return False

    return True


def find_file(path, saltenv="base", **kwargs):  # pylint: disable=W0613
    """
    Search the environment for the relative path
    """
    fnd = {"path": "", "rel": ""}
    for container in __opts__.get("azurefs", []):
        if container.get("saltenv", "base") != saltenv:
            continue
        full = os.path.join(_get_container_path(container), path)
        if os.path.isfile(full) and not salt.fileserver.is_file_ignored(__opts__, path):
            fnd["path"] = full
            fnd["rel"] = path
            try:
                # Converting the stat result to a list, the elements of the
                # list correspond to the following stat_result params:
                # 0 => st_mode=33188
                # 1 => st_ino=10227377
                # 2 => st_dev=65026
                # 3 => st_nlink=1
                # 4 => st_uid=1000
                # 5 => st_gid=1000
                # 6 => st_size=1056233
                # 7 => st_atime=1468284229
                # 8 => st_mtime=1456338235
                # 9 => st_ctime=1456338235
                fnd["stat"] = list(os.stat(full))
            except Exception:  # pylint: disable=broad-except
                pass
            return fnd
    return fnd


def envs():
    """
    Each container configuration can have an environment setting, or defaults
    to base
    """
    saltenvs = []
    for container in __opts__.get("azurefs", []):
        saltenvs.append(container.get("saltenv", "base"))
    # Remove duplicates
    return list(set(saltenvs))


def serve_file(load, fnd):
    """
    Return a chunk from a file based on the data received
    """
    ret = {"data": "", "dest": ""}
    required_load_keys = {"path", "loc", "saltenv"}
    if not all(x in load for x in required_load_keys):
        log.debug(
            "Not all of the required keys present in payload. Missing: %s",
            ", ".join(required_load_keys.difference(load)),
        )
        return ret
    if not fnd["path"]:
        return ret
    ret["dest"] = fnd["rel"]
    gzip = load.get("gzip", None)
    fpath = os.path.normpath(fnd["path"])
    with salt.utils.files.fopen(fpath, "rb") as fp_:
        fp_.seek(load["loc"])
        data = fp_.read(__opts__["file_buffer_size"])
        if data and not salt.utils.files.is_binary(fpath):
            data = data.decode(__salt_system_encoding__)
        if gzip and data:
            data = salt.utils.gzip_util.compress(data, gzip)
            ret["gzip"] = gzip
        ret["data"] = data
    return ret


def update():
    """
    Update caches of the storage containers.

    Compares the md5 of the files on disk to the md5 of the blobs in the
    container, and only updates if necessary.

    Also processes deletions by walking the container caches and comparing
    with the list of blobs in the container
    """
    for container in __opts__["azurefs"]:
        path = _get_container_path(container)
        try:
            if not os.path.exists(path):
                os.makedirs(path)
            elif not os.path.isdir(path):
                shutil.rmtree(path)
                os.makedirs(path)
        except Exception:  # pylint: disable=broad-except
            log.exception("Error occurred creating cache directory for azurefs")
            continue
        container_client = _get_container_client(container)
        try:
            blob_list = container_client.list_blobs()
        except Exception:  # pylint: disable=broad-except
            log.exception("Error occurred fetching blob list for azurefs")
            continue

        # Walk the cache directory searching for deletions
        blob_names = [blob.name for blob in blob_list]
        blob_set = set(blob_names)
        for root, dirs, files in salt.utils.path.os_walk(path):
            for file_name in files:
                fname = os.path.join(root, file_name)
                relpath = os.path.relpath(fname, path)
                if relpath not in blob_set:
                    salt.fileserver.wait_lock(fname + ".lk", fname)
                    try:
                        os.unlink(fname)
                    except Exception:  # pylint: disable=broad-except
                        pass
            if not dirs and not files:
                shutil.rmtree(root)
        for blob in blob_list:
            fname = os.path.join(path, blob.name)
            need_update = False
            if os.path.exists(fname):
                # File exists, check the hashes
                source_md5 = blob.properties.content_settings.content_md5
                local_md5 = base64.b64encode(
                    salt.utils.hashutils.get_hash(fname, "md5").decode("hex")
                )
                if local_md5 != source_md5:
                    need_update = True
            else:
                need_update = True

            if need_update:
                if not os.path.exists(os.path.dirname(fname)):
                    os.makedirs(os.path.dirname(fname))
                # Lock writes
                lk_fn = fname + ".lk"
                salt.fileserver.wait_lock(lk_fn, fname)
                with salt.utils.files.fopen(lk_fn, "w"):
                    pass

                try:
                    _download_blob_to_file(container_client, blob.name, fname)
                except Exception as exc:  # pylint: disable=broad-except
                    log.exception("Error occurred fetching blob from azurefs: %s", exc)
                    continue

                # Unlock writes
                try:
                    os.unlink(lk_fn)
                except Exception:  # pylint: disable=broad-except
                    pass

        # Write out file list
        container_list = path + ".list"
        lk_fn = container_list + ".lk"
        salt.fileserver.wait_lock(lk_fn, container_list)
        with salt.utils.files.fopen(lk_fn, "w"):
            pass
        with salt.utils.files.fopen(container_list, "w") as fp_:
            salt.utils.json.dump(blob_names, fp_)
        try:
            os.unlink(lk_fn)
        except Exception:  # pylint: disable=broad-except
            pass
        try:
            hash_cachedir = os.path.join(__opts__["cachedir"], "azurefs", "hashes")
            shutil.rmtree(hash_cachedir)
        except Exception:  # pylint: disable=broad-except
            pass


def file_hash(load, fnd):
    """
    Return a file hash based on the hash type set in the master config
    """
    if not all(x in load for x in ("path", "saltenv")):
        return "", None
    ret = {"hash_type": __opts__["hash_type"]}
    relpath = fnd["rel"]
    path = fnd["path"]
    hash_cachedir = os.path.join(__opts__["cachedir"], "azurefs", "hashes")
    hashdest = salt.utils.path.join(
        hash_cachedir,
        load["saltenv"],
        "{}.hash.{}".format(  # pylint: disable=consider-using-f-string
            relpath, __opts__["hash_type"]
        ),
    )
    if not os.path.isfile(hashdest):
        if not os.path.exists(os.path.dirname(hashdest)):
            os.makedirs(os.path.dirname(hashdest))
        ret["hsum"] = salt.utils.hashutils.get_hash(path, __opts__["hash_type"])
        with salt.utils.files.fopen(hashdest, "w+") as fp_:
            fp_.write(salt.utils.stringutils.to_str(ret["hsum"]))
        return ret
    else:
        with salt.utils.files.fopen(hashdest, "rb") as fp_:
            ret["hsum"] = salt.utils.stringutils.to_unicode(fp_.read())
        return ret


def file_list(load):
    """
    Return a list of all files in a specified environment
    """
    ret = set()
    try:
        for container in __opts__["azurefs"]:
            if container.get("saltenv", "base") != load["saltenv"]:
                continue
            container_list = _get_container_path(container) + ".list"
            lk_file = container_list + ".lk"
            salt.fileserver.wait_lock(lk_file, container_list, 5)
            if not os.path.exists(container_list):
                continue
            with salt.utils.files.fopen(container_list, "r") as fp_:
                ret.update(set(salt.utils.json.load(fp_)))
    except Exception:  # pylint: disable=broad-except
        log.error(
            "azurefs: an error ocurred retrieving file lists. "
            "It should be resolved next time the fileserver "
            "updates. Please do not manually modify the azurefs "
            "cache directory."
        )
    return list(ret)


def dir_list(load):
    """
    Return a list of all directories in a specified environment
    """
    ret = set()
    files = file_list(load)
    for file_path in files:
        dirname = file_path
        while dirname:
            dirname = os.path.dirname(dirname)
            if dirname:
                ret.add(dirname)
    return list(ret)


def _get_container_path(container):
    """
    Get the cache path for the container in question

    Cache paths are generate by combining the account name, container name,
    and saltenv, separated by underscores
    """
    root = os.path.join(__opts__["cachedir"], "azurefs")
    container_dir = "{}_{}_{}".format(  # pylint: disable=consider-using-f-string
        container.get("account_name", ""),
        container.get("container_name", ""),
        container.get("saltenv", "base"),
    )
    return os.path.join(root, container_dir)


def _get_container_client(container):
    """
    Get the azure container client for the container in question

    Try account_key, sas_token, and no auth in that order
    """
    try:
        account_name = container["account_name"]
        account_url = f"https://{account_name}.blob.core.windows.net"
        if "account_key" in container:
            account_key = container["account_key"]
            connect_str = (
                f"DefaultEndpointsProtocol=https;AccountName={account_name};"
                f"AccountKey={account_key};EndpointSuffix=core.windows.net"
            )
            blob_service_client = BlobServiceClient.from_connection_string(connect_str)
        elif "sas_token" in container:
            sas_token = container["sas_token"]
            blob_service_client = BlobServiceClient(account_url, credential=sas_token)
        else:
            blob_service_client = BlobServiceClient(account_url)

        container_client = blob_service_client.get_container_client(container["container_name"])
        return container_client
    except Exception as exc:  # pylint: disable=broad-except
        log.exception("An error occured while creating the container client: %s", exc)


def _download_blob_to_file(container_client, blob_name, fname):
    """
    Downloads a blob from Azure Blob Storage and saves it to the specified file name and path.
    """
    try:
        with open(file=fname, mode="wb") as local_file:
            download_stream = container_client.download_blob(blob_name)
            local_file.write(download_stream.readall())
    except Exception as exc:  # pylint: disable=broad-except
        log.exception("An error occured while downloading the blob: %s", exc)


def _validate_config():
    """
    Validate azurefs config, return False if it doesn't validate
    """
    if not isinstance(__opts__["azurefs"], list):
        log.error("azurefs configuration is not formed as a list, skipping azurefs")
        return False
    for container in __opts__["azurefs"]:
        if not isinstance(container, dict):
            log.error(
                "One or more entries in the azurefs configuration list are "
                "not formed as a dict. Skipping azurefs: %s",
                container,
            )
            return False
        if "account_name" not in container or "container_name" not in container:
            log.error(
                "An azurefs container configuration is missing either an "
                "account_name or a container_name: %s",
                container,
            )
            return False
    return True
