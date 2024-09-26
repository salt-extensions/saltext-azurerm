"""
Azure Resource Manager (ARM) Key Vault Secret State Module

.. versionadded:: 2.1.0

:maintainer: <devops@eitr.tech>
:configuration: This module requires Azure Resource Manager credentials to be passed as a dictionary of
    keyword arguments to the ``connection_auth`` parameter in order to work properly. Since the authentication
    parameters are sensitive, it's recommended to pass them to the states via Pillar.

    Required provider parameters:

    if using username and password:
      * ``subscription_id``
      * ``username``
      * ``password``

    if using a service principal:
      * ``subscription_id``
      * ``tenant``
      * ``client_id``
      * ``secret``

    if using managed identity:
      * ``subscription_id``

    Optional provider parameters:

    **cloud_environment**: Used to point the cloud driver to different API endpoints, such as Azure GovCloud.

      Possible values:
        * ``AZURE_PUBLIC_CLOUD`` (default)
        * ``AZURE_CHINA_CLOUD``
        * ``AZURE_US_GOV_CLOUD``
        * ``AZURE_GERMAN_CLOUD``

"""

# Python libs
import logging

import salt.utils.dictdiffer  # pylint: disable=import-error

log = logging.getLogger(__name__)


def present(
    name,
    value,
    vault_url,
    content_type=None,
    enabled=None,
    expires_on=None,
    not_before=None,
    tags=None,
    version=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2.1.0

    Ensure the specified secret exists within the given key vault. Requires secrets/set permission. Secret properties
    can be specified as keyword arguments.

    :param name: The name of the secret. Secret names can only contain alphanumeric characters and dashes.

    :param value: The value of the secret.

    :param vault_url: The URL of the vault that the client will access.

    :param content_type: An arbitrary string indicating the type of the secret.

    :param enabled: Whether the secret is enabled for use.

    :param expires_on: When the secret will expire, in UTC. This parameter should be a string representation
        of a Datetime object in ISO-8601 format.

    :param not_before: The time before which the secret cannot be used, in UTC. This parameter should be a
        string representation of a Datetime object in ISO-8601 format.

    :param tags: A dictionary of strings can be passed as tag metadata to the secret.

    :param version: The version of the secret. By default, a new version of the secret will not be created if the name
        is already in use UNLESS the value of the secret is changed. Secret properties will be updated on the latest
        version unless otherwise specified with this parameter.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure secret exists:
            azurerm_keyvault_secret.present:
                - name: secretname
                - value: supersecret
                - content_type: "text/plain"
                - vault_url: "https://myvault.vault.azure.net/"
                - tags:
                    contact_name: Elmer Fudd Gantry

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}
    action = "create"

    if not isinstance(connection_auth, dict):
        ret["comment"] = (
            "Connection information must be specified via acct or connection_auth dictionary!"
        )
        return ret

    secret = __salt__["azurerm_keyvault_secret.get_secret"](
        name=name,
        vault_url=vault_url,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" not in secret:
        action = "update"
        if value != secret.get("value"):
            ret["changes"]["value"] = {
                "old": "REDACTED_OLD_VALUE",
                "new": "REDACTED_NEW_VALUE",
            }

        if tags:
            tag_changes = salt.utils.dictdiffer.deep_diff(
                secret.get("properties", {}).get("tags", {}) or {}, tags or {}
            )
            if tag_changes:
                ret["changes"]["tags"] = tag_changes

        if content_type:
            if (
                content_type.lower()
                != (secret.get("properties", {}).get("content_type", "") or "").lower()
            ):
                ret["changes"]["content_type"] = {
                    "old": secret.get("properties", {}).get("content_type"),
                    "new": content_type,
                }

        if enabled is not None:
            if enabled != secret.get("properties", {}).get("enabled"):
                ret["changes"]["enabled"] = {
                    "old": secret.get("properties", {}).get("enabled"),
                    "new": enabled,
                }

        if expires_on:
            if expires_on != secret.get("properties", {}).get("expires_on"):
                ret["changes"]["expires_on"] = {
                    "old": secret.get("properties", {}).get("expires_on"),
                    "new": expires_on,
                }

        if not_before:
            if not_before != secret.get("properties", {}).get("not_before"):
                ret["changes"]["not_before"] = {
                    "old": secret.get("properties", {}).get("not_before"),
                    "new": not_before,
                }

        if not ret["changes"]:
            ret["result"] = True
            ret["comment"] = f"Secret {name} is already present."
            return ret

        if __opts__["test"]:
            ret["result"] = None
            ret["comment"] = f"Secret {name} would be updated."
            return ret

    if __opts__["test"]:
        ret["comment"] = f"Secret {name} would be created."
        ret["result"] = None
        return ret

    secret_kwargs = kwargs.copy()
    secret_kwargs.update(connection_auth)

    if action == "create" or (action == "update" and ret["changes"].get("value")):
        secret = __salt__["azurerm_keyvault_secret.set_secret"](
            name=name,
            value=value,
            vault_url=vault_url,
            content_type=content_type,
            enabled=enabled,
            expires_on=expires_on,
            not_before=not_before,
            tags=tags,
            **secret_kwargs,
        )
    else:
        secret = __salt__["azurerm_keyvault_secret.update_secret_properties"](
            name=name,
            vault_url=vault_url,
            version=version,
            content_type=content_type,
            enabled=enabled,
            expires_on=expires_on,
            not_before=not_before,
            tags=tags,
            **secret_kwargs,
        )

    if action == "create":
        ret["changes"] = {"old": {}, "new": secret}
        if ret["changes"]["new"].get("value"):
            ret["changes"]["new"]["value"] = "REDACTED"

    if "error" not in secret:
        ret["result"] = True
        ret["comment"] = f"Secret {name} has been {action}d."
        return ret

    ret["comment"] = (
        "Failed to {} Secret {}! ({})".format(  # pylint: disable=consider-using-f-string
            action, name, secret.get("error")
        )
    )
    if not ret["result"]:
        ret["changes"] = {}
    return ret


def absent(name, vault_url, purge=False, wait=False, connection_auth=None):
    """
    .. versionadded:: 2.1.0

    Ensure the specified secret does not exist within the given key vault.

    :param name: The name of the secret to delete.

    :param vault_url: The URL of the vault that the client will access.

    :param purge: Permanently deletes a deleted secret. Possible only in vaults with soft-delete enabled. Performs an
        irreversible deletion of the specified secret, without possibility for recovery. The operation is not available
        if the ``recovery_level`` does not specify 'Purgeable'.

    :param wait: When this method returns, Key Vault has begun deleting the secret. Deletion may take several seconds in
        a vault with soft-delete enabled. Setting this parameter to ``True`` enables you to wait for deletion to
        complete.

    :param connection_auth: A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure secret is absent:
            azurerm_keyvault_secret.absent:
                - name: secretname
                - vault_url: "https://myvault.vault.azure.net/"

    """
    ret = {"name": name, "result": False, "comment": "", "changes": {}}
    action = "delete"
    deleted = False

    if not isinstance(connection_auth, dict):
        ret["comment"] = (
            "Connection information must be specified via acct or connection_auth dictionary!"
        )
        return ret

    secret = __salt__["azurerm_keyvault_secret.get_secret"](
        name=name,
        vault_url=vault_url,
        azurerm_log_level="info",
        **connection_auth,
    )

    if "error" in secret:
        action = "purge"
        if purge:
            secret = __salt__["azurerm_keyvault_secret.get_deleted_secret"](
                name=name,
                vault_url=vault_url,
                azurerm_log_level="info",
                **connection_auth,
            )
        if "error" in secret:
            ret["result"] = True
            ret["comment"] = f"Secret {name} was not found."
            return ret

    if __opts__["test"]:
        ret["comment"] = f"Secret {name} would be {action}d."
        ret["result"] = None
        ret["changes"] = {
            "old": secret,
            "new": {},
        }
        return ret

    if action == "delete":
        deleted = __salt__["azurerm_keyvault_secret.delete_secret"](
            name=name, vault_url=vault_url, wait=wait, **connection_auth
        )

    if purge:
        action = "purge"
        deleted = __salt__["azurerm_keyvault_secret.purge_deleted_secret"](
            name=name, vault_url=vault_url, **connection_auth
        )

    if deleted:
        ret["result"] = True
        ret["comment"] = f"Secret {name} has been {action}d."
        ret["changes"] = {"old": secret, "new": {}}
        return ret

    ret["comment"] = f"Failed to {action} Secret {name}!"
    return ret
