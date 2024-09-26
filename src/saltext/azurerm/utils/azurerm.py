"""
Azure Resource Manager Utilities

.. versionadded:: 2019.2.0

:maintainer: <devops@eitr.tech>
:maturity: new
:depends:
    * `azure <https://pypi.python.org/pypi/azure>`_ >= 5.0.0
    * `azure-common <https://pypi.python.org/pypi/azure-common>`_ >= 1.1.28
    * `azure-mgmt <https://pypi.python.org/pypi/azure-mgmt>`_ >= 5.0.0
    * `azure-mgmt-compute <https://pypi.python.org/pypi/azure-mgmt-compute>`_ >= 27.1.0
    * `azure-mgmt-network <https://pypi.python.org/pypi/azure-mgmt-network>`_ >= 20.0.0
    * `azure-mgmt-resource <https://pypi.python.org/pypi/azure-mgmt-resource>`_ >= 21.1.0
    * `azure-mgmt-storage <https://pypi.python.org/pypi/azure-mgmt-storage>`_ >= 20.0.0
    * `azure-mgmt-web <https://pypi.python.org/pypi/azure-mgmt-web>`_ >= 6.1.0
    * `azure-storage <https://pypi.python.org/pypi/azure-storage>`_ >= 0.37.0
    * `msrestazure <https://pypi.python.org/pypi/msrestazure>`_ >= 0.6.4
:platform: linux

"""

import importlib
import logging
import os
import sys
from operator import itemgetter

import salt.config  # pylint: disable=import-error
import salt.loader  # pylint: disable=import-error
import salt.utils.stringutils  # pylint: disable=import-error
import salt.version  # pylint: disable=import-error
from salt.exceptions import SaltInvocationError  # pylint: disable=import-error
from salt.exceptions import SaltSystemExit  # pylint: disable=import-error

try:
    from azure.core.exceptions import ClientAuthenticationError
    from azure.core.pipeline.policies import UserAgentPolicy
    from azure.identity import AzureAuthorityHosts
    from azure.identity import DefaultAzureCredential
    from azure.identity import KnownAuthorities
    from msrestazure.azure_cloud import MetadataEndpointError
    from msrestazure.azure_cloud import get_cloud_from_metadata_endpoint

    HAS_AZURE = True
except ImportError:
    HAS_AZURE = False

__opts__ = salt.config.minion_config("/etc/salt/minion")
__salt__ = salt.loader.minion_mods(__opts__)

log = logging.getLogger(__name__)


def __virtual__():
    if not HAS_AZURE:
        return False
    else:
        return True


def _determine_auth(**kwargs):
    """
    Acquire Azure Resource Manager Credentials
    """
    mrest_cloud_name = {
        "AZURE_CHINA": "AZURE_CHINA_CLOUD",
        "AZURE_GOVERNMENT": "AZURE_US_GOV_CLOUD",
        "AZURE_GERMANY": "AZURE_GERMAN_CLOUD",
    }
    if "profile" in kwargs:
        azure_credentials = __salt__["config.option"](kwargs["profile"])
        kwargs.update(azure_credentials)

    try:
        if kwargs.get("cloud_environment", "").startswith("http"):
            cloud_env = get_cloud_from_metadata_endpoint(kwargs["cloud_environment"])
            authority = kwargs["cloud_environment"]
        else:
            cloud_env_module = importlib.import_module("msrestazure.azure_cloud")

            # Map the new cloud_environment name to the corresponding old msrest name
            old_cloud_env_name = mrest_cloud_name.get(
                kwargs.get("cloud_environment", "AZURE_PUBLIC_CLOUD"), "AZURE_PUBLIC_CLOUD"
            )

            # Retrieve the cloud environment based on the old msrest name
            cloud_env = getattr(cloud_env_module, old_cloud_env_name)

            authority = getattr(
                AzureAuthorityHosts, kwargs.get("cloud_environment", "AZURE_PUBLIC_CLOUD")
            )
    except (AttributeError, ImportError, MetadataEndpointError):
        raise SaltSystemExit(  # pylint: disable=raise-missing-from
            f"The Azure cloud environment {kwargs['cloud_environment']} is not available."
        )

    try:
        if "client_id" in kwargs and "tenant" in kwargs and "secret" in kwargs:
            credentials = get_identity_credentials(**kwargs)
        else:
            kwargs.pop("client_id", None)
            credentials = DefaultAzureCredential(authority=authority, **kwargs)
    except ClientAuthenticationError:
        raise SaltInvocationError(  # pylint: disable=raise-missing-from
            "Unable to determine credentials. "
            "A subscription_id with username and password, "
            "or client_id, secret, and tenant or a profile with the "
            "required parameters populated"
        )

    try:
        subscription_id = salt.utils.stringutils.to_str(kwargs["subscription_id"])
    except KeyError:
        raise SaltInvocationError(  # pylint: disable=raise-missing-from
            "A subscription_id must be specified"
        )

    return credentials, subscription_id, cloud_env


def get_client(client_type, **kwargs):
    """
    Dynamically load the selected client and return a management client object
    """
    client_map = {
        "compute": "ComputeManagement",
        "authorization": "AuthorizationManagement",
        "dns": "DnsManagement",
        "keyvault": "KeyVaultManagement",
        "storage": "StorageManagement",
        "managementlock": "ManagementLock",
        "monitor": "MonitorManagement",
        "network": "NetworkManagement",
        "policy": "Policy",
        "privatedns": "PrivateDnsManagement",
        "resource": "ResourceManagement",
        "subscription": "Subscription",
        "web": "WebSiteManagement",
    }

    if client_type not in client_map:
        raise SaltSystemExit(
            msg=f"The Azure Resource Manager client_type {client_type} specified can not be found."
        )

    map_value = client_map[client_type]

    if client_type in ["policy", "subscription"]:
        module_name = "resource"
    elif client_type in ["managementlock"]:
        module_name = "resource.locks"
    else:
        module_name = client_type

    try:
        client_module = importlib.import_module("azure.mgmt." + module_name)
        Client = getattr(client_module, f"{map_value}Client")  # pylint: disable=invalid-name
    except ImportError:
        raise SaltSystemExit(  # pylint: disable=raise-missing-from
            f"The azure {client_type} client is not available."
        )
    credentials, subscription_id, cloud_env = _determine_auth(**kwargs)

    user_agent = UserAgentPolicy(f"Salt/{salt.version.__version__}")
    if client_type == "subscription":
        client = Client(
            credential=credentials,
            base_url=cloud_env.endpoints.resource_manager,
            user_agent_policy=user_agent,
        )
    else:
        client = Client(
            credential=credentials,
            subscription_id=subscription_id,
            base_url=cloud_env.endpoints.resource_manager,
            user_agent_policy=user_agent,
        )
    return client


def log_cloud_error(client, message, **kwargs):
    """
    Log an azurerm cloud error exception
    """
    try:
        cloud_logger = getattr(log, kwargs.get("azurerm_log_level"))
    except (AttributeError, TypeError):
        cloud_logger = getattr(log, "error")

    cloud_logger(
        "An Azure Resource Manager %s ResourceNotFoundError has occurred: %s",
        client.capitalize(),
        message,
    )


def paged_object_to_list(paged_object):
    """
    Extract all pages within a paged object as a list of dictionaries
    """
    paged_return = []
    while True:
        try:
            page = next(paged_object)
            paged_return.append(page.as_dict())
        except StopIteration:
            break

    return paged_return


def create_object_model(module_name, object_name, **kwargs):
    """
    Assemble an object from incoming parameters.
    """
    object_kwargs = {}

    try:
        model_module = importlib.import_module(f"azure.mgmt.{module_name}.models")
        # pylint: disable=invalid-name
        Model = getattr(model_module, object_name)
    except ImportError:
        raise sys.exit(  # pylint: disable=raise-missing-from
            f"The {object_name} model in the {module_name} Azure module is not available."
        )

    if "_attribute_map" in dir(Model):
        for attr, items in Model._attribute_map.items():  # pylint: disable=protected-access
            param = kwargs.get(attr)
            if param is not None:
                if items["type"][0].isupper() and isinstance(param, dict):
                    object_kwargs[attr] = create_object_model(module_name, items["type"], **param)
                elif items["type"][0] == "{" and isinstance(param, dict):
                    object_kwargs[attr] = param
                elif items["type"][0] == "[" and isinstance(param, list):
                    obj_list = []
                    for list_item in param:
                        if items["type"][1].isupper() and isinstance(list_item, dict):
                            obj_list.append(
                                create_object_model(
                                    module_name,
                                    items["type"][
                                        items["type"].index("[") + 1 : items["type"].rindex("]")
                                    ],
                                    **list_item,
                                )
                            )
                        elif items["type"][1] == "{" and isinstance(list_item, dict):
                            obj_list.append(list_item)
                        elif not items["type"][1].isupper() and items["type"][1] != "{":
                            obj_list.append(list_item)
                    object_kwargs[attr] = obj_list
                else:
                    object_kwargs[attr] = param

    # wrap calls to this function to catch TypeError exceptions
    return Model(**object_kwargs)


def compare_list_of_dicts(old, new, convert_id_to_name=None):
    """
    Compare lists of dictionaries representing Azure objects. Only keys found in the "new" dictionaries are compared to
    the "old" dictionaries, since getting Azure objects from the API returns some read-only data which should not be
    used in the comparison. A list of parameter names can be passed in order to compare a bare object name to a full
    Azure ID path for brevity. If string types are found in values, comparison is case insensitive. Return comment
    should be used to trigger exit from the calling function.
    """
    ret = {}

    if not convert_id_to_name:
        convert_id_to_name = []

    if not isinstance(new, list):
        ret["comment"] = "must be provided as a list of dictionaries!"
        return ret

    if len(new) != len(old):
        ret["changes"] = {"old": old, "new": new}
        return ret

    try:
        local_configs, remote_configs = (
            sorted(config, key=itemgetter("name")) for config in (new, old)
        )
    except TypeError:
        ret["comment"] = "configurations must be provided as a list of dictionaries!"
        return ret
    except KeyError:
        ret["comment"] = 'configuration dictionaries must contain the "name" key!'
        return ret

    for idx, val in enumerate(local_configs):
        for key in val:
            local_val = val[key]
            if key in convert_id_to_name:
                remote_val = remote_configs[idx].get(key, {}).get("id", "").split("/")[-1]
            else:
                remote_val = remote_configs[idx].get(key)
                if isinstance(local_val, str):
                    local_val = local_val.lower()
                if isinstance(remote_val, str):
                    remote_val = remote_val.lower()
            if local_val != remote_val:
                ret["changes"] = {"old": remote_configs, "new": local_configs}
                return ret

    return ret


def get_identity_credentials(**kwargs):
    """
    Acquire Azure RM Credentials from the identity provider (not for mgmt)

    This is accessible on the hub so clients out in the code can use it. Non-management clients
    can't be consolidated neatly here.

    We basically set environment variables based upon incoming parameters and then pass off to
    the DefaultAzureCredential object to correctly parse those environment variables. See the
    `Microsoft Docs on EnvironmentCredential <https://aka.ms/azsdk-python-identity-default-cred-ref>`_
    for more information.
    """
    kwarg_map = {
        "tenant": "AZURE_TENANT_ID",
        "client_id": "AZURE_CLIENT_ID",
        "secret": "AZURE_CLIENT_SECRET",
        "client_certificate_path": "AZURE_CLIENT_CERTIFICATE_PATH",
        "username": "AZURE_USERNAME",
        "password": "AZURE_PASSWORD",
    }
    for keyword, value in kwarg_map.items():
        if kwargs.get(keyword):
            os.environ[value] = kwargs[keyword]
    try:
        if kwargs.get("cloud_environment") and kwargs.get("cloud_environment").startswith("http"):
            authority = kwargs["cloud_environment"]
        else:
            authority = getattr(
                KnownAuthorities, kwargs.get("cloud_environment", "AZURE_PUBLIC_CLOUD")
            )
        log.debug("AUTHORITY: %s", authority)

    except AttributeError as exc:
        log.error('Unknown authority presented for "cloud_environment": %s', exc)
        authority = KnownAuthorities.AZURE_PUBLIC_CLOUD

    try:
        credential = DefaultAzureCredential(authority=authority)
    except ClientAuthenticationError:
        raise SaltInvocationError(  # pylint: disable=raise-missing-from
            "Unable to determine credentials. "
        )

    return credential
