"""
Azure Resource Manager Cloud Module
===================================

.. versionadded:: 2016.11.0

.. versionchanged:: 2019.2.0

The Azure Resource Manager cloud module is used to control access to Microsoft Azure Resource Manager

:configuration:
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

    if using Managed Service Identity authentication:
      * ``subscription_id``

    Optional provider parameters:

    **cloud_environment**:
      Used to point the cloud driver to different API endpoints, such as Azure GovCloud. Possible values:
        * ``AZURE_PUBLIC_CLOUD`` (default)
        * ``AZURE_CHINA_CLOUD``
        * ``AZURE_US_GOV_CLOUD``
        * ``AZURE_GERMAN_CLOUD``
        * HTTP base URL for a custom endpoint, such as Azure Stack.
          The ``/metadata/endpoints`` path will be added to the URL.

    **userdata** and **userdata_file**:
      Azure Resource Manager uses a separate VirtualMachineExtension object to pass userdata scripts to the virtual
      machine. Arbitrary shell commands can be passed via the ``userdata`` parameter, or via a file local to the Salt
      Cloud system using the ``userdata_file`` parameter. Note that the local file is not treated as a script by the
      extension, so "one-liners" probably work best. If greater functionality is desired, a web-hosted script file can
      be specified via ``userdata_file: https://raw.githubusercontent.com/account/repo/master/azure-script.py``, which
      will be executed on the system after VM creation. For Windows systems, script files ending in ``.ps1`` will be
      executed with ``powershell.exe``. The ``userdata`` parameter takes precedence over the ``userdata_file`` parameter
      when creating the custom script extension.

      Not to be confused with **`user_data <https://learn.microsoft.com/en-us/azure/virtual-machines/user-data>`_**, which
      only holds static content.

    **win_installer**:
      This parameter, which holds the local path to the Salt Minion installer package, is used to determine if the
      virtual machine type will be "Windows". Only set this parameter on profiles which install Windows operating
      systems.

    **user_data**:
      .. versionadded:: 4.2.0

      Plain string representing `user data <https://learn.microsoft.com/en-us/azure/virtual-machines/user-data>`_.
      It should not be base64 encoded, as that will be done by Salt.

    **custom_data**:
      .. versionadded:: 4.2.0

      Older version of ``user_data``. See `custom data <https://learn.microsoft.com/en-us/azure/virtual-machines/custom-data>`_.
      It should not be base64 encoded, as that will be done by Salt.

    **identity_type**:
      .. versionadded:: 4.2.0

      The `type of identity <https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/how-managed-identities-work-vm>`__ used for the virtual machine.
      The type ``SystemAssigned, UserAssigned`` includes both an implicitly created identity and a set of user assigned identities.
      If left undefined will remove any identities from the virtual machine.
      Known values are: ``SystemAssigned``, ``UserAssigned``, ``SystemAssigned, UserAssigned``, and undefined.

    **user_assigned_identities**:
      .. versionadded:: 4.2.0

      The list of `user identities <https://learn.microsoft.com/en-us/entra/identity/managed-identities-azure-resources/how-managed-identities-work-vm>`__ associated with the Virtual Machine. Requires **identity_type** to be
      either ``SystemAssigned, UserAssigned`` or ``UserAssigned``.

      Value is a a map of Managed Identity ID to dict of ``principal_id`` and ``client_id``.

      Example:

      .. code-block:: yaml

          user_assigned_identities:
            "/subscriptions/[redacted]/resourcegroups/[redacted]/providers/Microsoft.ManagedIdentity/userAssignedIdentities/[redacted]":
                client_id: "[redacted]"
                principal_id: "[redacted]"

    **public_ip_sku**:
      .. versionadded:: 4.3.0

      SKU of a public IP address.

      Defaults to ``Basic``, possible options are ``Standard`` or ``Basic``. Basic SKU will be deprecated soon. See more <https://azure.microsoft.com/en-us/updates?id=upgrade-to-standard-sku-public-ip-addresses-in-azure-by-30-september-2025-basic-sku-will-be-retired>.

    **public_ip_allocation_method**:
      .. versionadded:: 4.3.0

      Defaults to ``Dynamic``, possible options are ``Static`` and ``Dynamic``.

      If **public_ip_sku** is ``Standard`` then this must be ``Static``.

Example ``/etc/salt/cloud.providers`` or
``/etc/salt/cloud.providers.d/azure.conf`` configuration:

.. code-block:: yaml

    my-azure-config with username and password:
      driver: azurerm
      subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
      username: larry
      password: 123pass

    Or my-azure-config with service principal:
      driver: azurerm
      subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
      tenant: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
      client_id: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
      secret: XXXXXXXXXXXXXXXXXXXXXXXX
      cloud_environment: AZURE_US_GOV_CLOUD

    azure-config-with-cleanup-options:
      drive: azurerm
      subscription_id: "[redacted]"
      cleanup_disks: True
      cleanup_vhds: True
      cleanup_osdisks: True
      cleanup_datadisks: True
      cleanup_interfaces: True
      cleanup_public_ips: True

The Service Principal can be created with the new `Azure CLI <https://github.com/Azure/azure-cli>`_ with:

.. code-block:: shell

      az ad sp create-for-rbac -n "http://<yourappname>" --role <role> --scopes <scope>

For example, this creates a service principal with 'owner' role for the whole subscription:

.. code-block:: shell

      az ad sp create-for-rbac \
          -n "http://mysaltapp" \
          --role owner \
          --scopes /subscriptions/3287abc8-f98a-c678-3bde-326766fd3617

**Note:** review the details of Service Principals. Owner role is more than you normally need, and you can restrict
scope to a resource group or individual resources.

Example ``/etc/salt/cloud.profiles`` or
``/etc/salt/cloud.profiles.d/azure.conf`` configuration:

.. code-block:: yaml

    my-vm-profile:
      provider: my-azure-config
      image: "[redacted]"
      resource_group: super-duper
      location: brazilsouth
      size: Standard_A4_v2
      network: awesome
      subnet: opossum
      allocate_public_ip: True
      public_ip_sku: "Standard"
      public_ip_allocation_method: "Static"
      identity_type: "UserAssigned"
      user_assigned_identities:
        "/subscriptions/[redacted]/resourcegroups/[redacted]/providers/Microsoft.ManagedIdentity/userAssignedIdentities/[redacted]":
          client_id: "[redacted]"
          principal_id: "[redacted]"
      custom_data: '{ "some":"json" }'
      user_data: 'Or even just a text file'
      tags:
        awesome: opossum

"""

import base64
import importlib
import logging
import os.path
import pprint
import string
from multiprocessing import cpu_count
from multiprocessing.pool import ThreadPool

import salt.cache
import salt.utils.cloud
import salt.utils.files
import salt.utils.stringutils
import salt.utils.yaml
import salt.version
from salt import config
from salt.exceptions import SaltCloudConfigError
from salt.exceptions import SaltCloudExecutionFailure
from salt.exceptions import SaltCloudExecutionTimeout
from salt.exceptions import SaltCloudSystemExit

import saltext.azurerm.utils.azurerm

HAS_LIBS = False
try:
    import azure.mgmt.compute.models as compute_models
    import azure.mgmt.network.models as network_models
    from azure.core.exceptions import HttpResponseError
    from azure.storage.blob import BlobServiceClient
    from azure.storage.blob import ContainerClient

    HAS_LIBS = True
except ImportError:
    pass

try:
    __salt__  # pylint: disable=used-before-assignment
except NameError:
    import salt.loader

    __opts__ = salt.config.minion_config("/etc/salt/minion")
    __utils__ = salt.loader.utils(__opts__)
    __salt__ = salt.loader.minion_mods(__opts__, utils=__utils__)


__virtualname__ = "azurerm"

log = logging.getLogger(__name__)


def __virtual__():
    """
    Check for Azure configurations.
    """
    if get_configured_provider() is False:
        return False

    if get_dependencies() is False:
        return (
            False,
            "The following dependencies are required to use the Azure Resource Manager driver: "
            "Microsoft Azure SDK for Python >= 2.0rc6, "
            "Microsoft Azure Storage SDK for Python >= 0.32, "
            "MS REST Azure (msrestazure) >= 0.4",
        )

    return __virtualname__


def _get_active_provider_name():
    """
    Get active provider name.
    """
    try:
        return __active_provider_name__.value()
    except AttributeError:
        return __active_provider_name__


def get_api_versions(call=None, kwargs=None):  # pylint: disable=unused-argument
    """
    Get a resource type api versions
    """
    if kwargs is None:
        kwargs = {}

    if "resource_provider" not in kwargs:
        raise SaltCloudSystemExit("A resource_provider must be specified")

    if "resource_type" not in kwargs:
        raise SaltCloudSystemExit("A resource_type must be specified")

    api_versions = []

    try:
        resconn = get_conn(client_type="resource")
        provider_query = resconn.providers.get(
            resource_provider_namespace=kwargs["resource_provider"]
        )

        for resource in provider_query.resource_types:
            if str(resource.resource_type) == kwargs["resource_type"]:
                resource_dict = resource.as_dict()
                api_versions = resource_dict["api_versions"]
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", exc.message)

    return api_versions


def get_resource_by_id(resource_id, api_version, extract_value=None):
    """
    Get an Azure Resource Manager resource by id
    """
    ret = {}

    try:
        resconn = get_conn(client_type="resource")
        resource_query = resconn.resources.get_by_id(
            resource_id=resource_id, api_version=api_version
        )
        resource_dict = resource_query.as_dict()
        if extract_value is not None:
            ret = resource_dict[extract_value]
        else:
            ret = resource_dict
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", exc.message)
        ret = {"Error": exc.message}

    return ret


def get_configured_provider():
    """
    Return the first configured provider instance.
    """
    key_combos = [
        ("subscription_id", "tenant", "client_id", "secret"),
        ("subscription_id", "username", "password"),
        ("subscription_id",),
    ]

    for combo in key_combos:
        provider = config.is_provider_configured(
            __opts__,
            _get_active_provider_name() or __virtualname__,
            combo,
            log_message=False,
        )

        if provider:
            return provider

    return provider


def get_dependencies():
    """
    Warn if dependencies aren't met.
    """
    return config.check_driver_dependencies(__virtualname__, {"azurerm": HAS_LIBS})


def get_conn(client_type):
    """
    Return a connection object for a client type.
    """
    conn_kwargs = get_conn_dict()
    client = saltext.azurerm.utils.azurerm.get_client(client_type=client_type, **conn_kwargs)

    return client


def get_conn_dict():
    """
    Return a connection auth dictionary.
    """
    conn_kwargs = {}

    conn_kwargs["subscription_id"] = salt.utils.stringutils.to_str(
        config.get_cloud_config_value(
            "subscription_id", get_configured_provider(), __opts__, search_global=False
        )
    )

    cloud_env = config.get_cloud_config_value(
        "cloud_environment", get_configured_provider(), __opts__, search_global=False
    )

    if cloud_env is not None:
        conn_kwargs["cloud_environment"] = cloud_env

    tenant = config.get_cloud_config_value(
        "tenant", get_configured_provider(), __opts__, search_global=False
    )

    if tenant is not None:
        client_id = config.get_cloud_config_value(
            "client_id", get_configured_provider(), __opts__, search_global=False
        )
        secret = config.get_cloud_config_value(
            "secret", get_configured_provider(), __opts__, search_global=False
        )
        conn_kwargs.update({"client_id": client_id, "secret": secret, "tenant": tenant})

    username = config.get_cloud_config_value(
        "username", get_configured_provider(), __opts__, search_global=False
    )

    if username:
        password = config.get_cloud_config_value(
            "password", get_configured_provider(), __opts__, search_global=False
        )
        conn_kwargs.update({"username": username, "password": password})

    return conn_kwargs


def get_location(call=None, kwargs=None):  # pylint: disable=unused-argument
    """
    Return the location that is configured for this provider
    """
    if not kwargs:
        kwargs = {}
    vm_dict = get_configured_provider()
    vm_dict.update(kwargs)
    return config.get_cloud_config_value("location", vm_dict, __opts__, search_global=False)


def avail_locations(call=None):
    """
    Return a dict of all available regions.
    """
    if call == "action":
        raise SaltCloudSystemExit(
            "The avail_locations function must be called with "
            "-f or --function, or with the --list-locations option"
        )

    ret = {}
    ret["locations"] = []

    try:
        resconn = get_conn(client_type="resource")
        provider_query = resconn.providers.get(resource_provider_namespace="Microsoft.Compute")
        locations = []
        for resource in provider_query.resource_types:
            if str(resource.resource_type) == "virtualMachines":
                resource_dict = resource.as_dict()
                locations = resource_dict["locations"]
        for location in locations:
            lowercase = location.lower().replace(" ", "")
            ret["locations"].append(lowercase)
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", exc.message)
        ret = {"Error": exc.message}

    return ret


def avail_images(call=None):
    """
    Return a dict of all available images on the provider
    """
    if call == "action":
        raise SaltCloudSystemExit(
            "The avail_images function must be called with "
            "-f or --function, or with the --list-images option"
        )
    compconn = get_conn(client_type="compute")
    region = get_location()
    publishers = []
    ret = {}

    def _get_publisher_images(publisher):
        """
        Get all images from a specific publisher
        """
        data = {}
        try:
            offers = compconn.virtual_machine_images.list_offers(
                location=region,
                publisher_name=publisher,
            )
            for offer_obj in offers:
                offer = offer_obj.as_dict()
                skus = compconn.virtual_machine_images.list_skus(
                    location=region,
                    publisher_name=publisher,
                    offer=offer["name"],
                )
                for sku_obj in skus:
                    sku = sku_obj.as_dict()
                    results = compconn.virtual_machine_images.list(
                        location=region,
                        publisher_name=publisher,
                        offer=offer["name"],
                        skus=sku["name"],
                    )
                    for version_obj in results:
                        version = version_obj.as_dict()
                        name = "|".join(
                            (
                                publisher,
                                offer["name"],
                                sku["name"],
                                version["name"],
                            )
                        )
                        data[name] = {
                            "publisher": publisher,
                            "offer": offer["name"],
                            "sku": sku["name"],
                            "version": version["name"],
                        }
        except HttpResponseError as exc:
            saltext.azurerm.utils.azurerm.log_cloud_error("compute", exc.message)
            data = {publisher: exc.message}

        return data

    try:
        publishers_query = compconn.virtual_machine_images.list_publishers(location=region)
        for publisher_obj in publishers_query:
            publisher = publisher_obj.as_dict()
            publishers.append(publisher["name"])
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("compute", exc.message)

    pool = ThreadPool(cpu_count() * 6)
    results = pool.map_async(_get_publisher_images, publishers)
    results.wait()

    ret = {k: v for result in results.get() for k, v in result.items()}

    return ret


def avail_sizes(call=None):
    """
    Return a list of sizes available from the provider
    """
    if call == "action":
        raise SaltCloudSystemExit(
            "The avail_sizes function must be called with "
            "-f or --function, or with the --list-sizes option"
        )

    compconn = get_conn(client_type="compute")

    ret = {}
    location = get_location()

    try:
        sizes = compconn.virtual_machine_sizes.list(location=location)
        for size_obj in sizes:
            size = size_obj.as_dict()
            ret[size["name"]] = size
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("compute", exc.message)
        ret = {"Error": exc.message}

    return ret


def list_nodes(call=None):
    """
    List VMs on this Azure account
    """
    if call == "action":
        raise SaltCloudSystemExit("The list_nodes function must be called with -f or --function.")

    ret = {}

    nodes = list_nodes_full()
    for node in nodes:  # pylint: disable=consider-using-dict-items
        ret[node] = {"name": node}
        for prop in ("id", "image", "size", "state", "private_ips", "public_ips"):
            ret[node][prop] = nodes[node].get(prop)
    return ret


def _get_node_info(node, netapi_version):
    """
    Get node info.
    """
    node_ret = {}
    node["id"] = node["vm_id"]
    node["size"] = node["hardware_profile"]["vm_size"]
    node["state"] = node["provisioning_state"]
    node["public_ips"] = []
    node["private_ips"] = []
    node_ret[node["name"]] = node
    try:
        image_ref = node["storage_profile"]["image_reference"]
        node["image"] = "|".join(
            [
                image_ref["publisher"],
                image_ref["offer"],
                image_ref["sku"],
                image_ref["version"],
            ]
        )
    except (TypeError, KeyError):
        try:
            node["image"] = node["storage_profile"]["os_disk"]["image"]["uri"]
        except (TypeError, KeyError):
            node["image"] = node.get("storage_profile", {}).get("image_reference", {}).get("id")
    try:
        netifaces = node["network_profile"]["network_interfaces"]
        for index, netiface in enumerate(netifaces):
            netiface_name = get_resource_by_id(netiface["id"], netapi_version, "name")
            netiface, pubips, privips = _get_network_interface(
                netiface_name, node["resource_group"]
            )
            node["network_profile"]["network_interfaces"][index].update(netiface)
            node["public_ips"].extend(pubips)
            node["private_ips"].extend(privips)
    except Exception:  # pylint: disable=broad-except
        pass

    node_ret[node["name"]] = node

    return node_ret


def get_node_full(name, resource_group_name, call=None):
    """
    Get single VM on the subscription and resource group with full information
    """
    if call == "action":
        raise SaltCloudSystemExit(
            "The get_node_full function must be called with -f or --function."
        )

    netapi_versions = get_api_versions(
        kwargs={
            "resource_provider": "Microsoft.Network",
            "resource_type": "networkInterfaces",
        }
    )
    netapi_version = netapi_versions[0]
    compconn = get_conn(client_type="compute")

    node_query = compconn.virtual_machines.get(
        resource_group_name=resource_group_name, vm_name=name
    )
    node = node_query.as_dict()
    node["resource_group"] = resource_group_name

    return _get_node_info(node, netapi_version)


def list_nodes_full(call=None):
    """
    List all VMs on the subscription with full information
    """
    if call == "action":
        raise SaltCloudSystemExit(
            "The list_nodes_full function must be called with -f or --function."
        )

    netapi_versions = get_api_versions(
        kwargs={
            "resource_provider": "Microsoft.Network",
            "resource_type": "networkInterfaces",
        }
    )
    netapi_version = netapi_versions[0]
    compconn = get_conn(client_type="compute")

    ret = {}

    def _get_node_info_with_version(node):
        return _get_node_info(node, netapi_version)

    for group in list_resource_groups():
        nodes = []
        nodes_query = compconn.virtual_machines.list(resource_group_name=group)
        for node_obj in nodes_query:
            node = node_obj.as_dict()
            node["resource_group"] = group
            nodes.append(node)

        pool = ThreadPool(cpu_count() * 6)
        results = pool.map_async(_get_node_info_with_version, nodes)
        results.wait()

        group_ret = {k: v for result in results.get() for k, v in result.items()}
        ret.update(group_ret)

    return ret


def list_resource_groups(call=None):
    """
    List resource groups associated with the subscription
    """
    if call == "action":
        raise SaltCloudSystemExit(
            "The list_hosted_services function must be called with -f or --function"
        )
    conn_kwargs = get_conn_dict()
    ret = __salt__["azurerm_resource.resource_groups_list"](**conn_kwargs)
    return ret


def show_instance(name, call=None):
    """
    Show the details from Azure Resource Manager concerning an instance
    """
    if call != "action":
        raise SaltCloudSystemExit("The show_instance action must be called with -a or --action.")
    try:
        node = list_nodes_full("function")[name]
    except KeyError:
        log.debug("Failed to get data for node '%s'", name)
        node = {}

    __utils__["cloud.cache_node"](node, _get_active_provider_name(), __opts__)

    return node


def show_instance_in_resource_group(name, resource_group_name, call=None):
    """
    Show the details from Azure Resource Manager concerning an instance in specific resource group
    """
    if call != "action":
        raise SaltCloudSystemExit(
            "The show_instance_in_resource_group action must be called with -a or --action."
        )
    try:
        node = get_node_full(name, resource_group_name, "function")[name]
    except KeyError:
        log.debug("Failed to get data for node '%s'", name)
        node = {}

    __utils__["cloud.cache_node"](node, _get_active_provider_name(), __opts__)

    return node


def delete_interface(call=None, kwargs=None):  # pylint: disable=unused-argument
    """
    Delete a network interface.
    """
    if kwargs is None:
        kwargs = {}

    if kwargs.get("resource_group") is None:
        kwargs["resource_group"] = config.get_cloud_config_value(
            "resource_group", {}, __opts__, search_global=True
        )
    conn_kwargs = get_conn_dict()
    ips = []
    iface = __salt__["azurerm_network.network_interface_get"](
        resource_group=kwargs["resource_group"], name=kwargs["iface_name"], **conn_kwargs
    )
    iface_name = iface["name"]
    for ip_ in iface["ip_configurations"]:
        ips.append(ip_["name"])

    __salt__["azurerm_network.network_interface_delete"](
        resource_group=kwargs["resource_group"], name=kwargs["iface_name"], **conn_kwargs
    )

    for ip_ in ips:
        __salt__["azurerm_network.public_ip_address_delete"](
            resource_group=kwargs["resource_group"], name=ip_, **conn_kwargs
        )

    return {iface_name: ips}


def _get_public_ip(name, resource_group):
    """
    Get the public ip address details by name.
    """
    conn_kwargs = get_conn_dict()
    ret = __salt__["azurerm_network.public_ip_address_get"](
        name=name, resource_group=resource_group, **conn_kwargs
    )
    return ret


def _get_network_interface(name, resource_group):
    """
    Get a network interface.
    """
    public_ips = []
    private_ips = []
    netapi_versions = get_api_versions(
        kwargs={
            "resource_provider": "Microsoft.Network",
            "resource_type": "publicIPAddresses",
        }
    )
    netapi_version = netapi_versions[0]

    conn_kwargs = get_conn_dict()
    netiface = __salt__["azurerm_network.network_interface_get"](
        name=name, resource_group=resource_group, **conn_kwargs
    )

    for index, ip_config in enumerate(netiface["ip_configurations"]):
        if ip_config.get("private_ip_address") is not None:
            private_ips.append(ip_config["private_ip_address"])
        if "id" in ip_config.get("public_ip_address", {}):
            public_ip_name = get_resource_by_id(
                ip_config["public_ip_address"]["id"], netapi_version, "name"
            )
            public_ip = _get_public_ip(public_ip_name, resource_group)
            if public_ip.get("ip_address"):
                public_ips.append(public_ip["ip_address"])
                netiface["ip_configurations"][index]["public_ip_address"].update(public_ip)

    return netiface, public_ips, private_ips


def create_network_interface(call=None, kwargs=None):
    """
    Create a network interface.
    """
    if call != "action":
        raise SaltCloudSystemExit(
            "The create_network_interface action must be called with -a or --action."
        )

    # pylint: disable=invalid-name
    IPAllocationMethod = getattr(network_models, "IPAllocationMethod")
    # pylint: disable=invalid-name
    PublicIPAddress = getattr(network_models, "PublicIPAddress")
    # pylint: disable=invalid-name
    PublicIPAddressSku = getattr(network_models, "PublicIPAddressSku")

    if not isinstance(kwargs, dict):
        kwargs = {}

    vm_ = kwargs
    conn_kwargs = get_conn_dict()

    # Set values for various parameters if they are not provided
    if kwargs.get("location") is None:
        kwargs["location"] = get_location()

    if kwargs.get("network") is None:
        kwargs["network"] = config.get_cloud_config_value(
            "network", vm_, __opts__, search_global=False
        )

    if kwargs.get("subnet") is None:
        kwargs["subnet"] = config.get_cloud_config_value(
            "subnet", vm_, __opts__, search_global=False
        )

    if kwargs.get("network_resource_group") is None:
        kwargs["network_resource_group"] = config.get_cloud_config_value(
            "resource_group", vm_, __opts__, search_global=False
        )

    if kwargs.get("iface_name") is None:
        kwargs["iface_name"] = "{}-iface0".format(  # pylint: disable=consider-using-f-string
            vm_["name"]
        )

    # Handle IP configuration based on provided parameters
    ip_kwargs = {}
    ip_configurations = None

    if "load_balancer_backend_address_pools" in kwargs:
        ip_kwargs["load_balancer_backend_address_pools"] = kwargs[
            "load_balancer_backend_address_pools"
        ]
    if "private_ip_address" in kwargs.keys():
        ip_kwargs["private_ip_address"] = kwargs["private_ip_address"]
        ip_kwargs["private_ip_allocation_method"] = IPAllocationMethod.static
    else:
        ip_kwargs["private_ip_allocation_method"] = IPAllocationMethod.dynamic

    if kwargs.get("allocate_public_ip") is True:
        pub_ip_name = "{}-ip".format(  # pylint: disable=consider-using-f-string
            kwargs["iface_name"]
        )
        pub_ip_data = __salt__["azurerm_network.public_ip_address_create_or_update"](
            name=pub_ip_name,
            resource_group=kwargs["resource_group"],
            sku=PublicIPAddressSku(name=kwargs.get("public_ip_sku", "Basic")),
            public_ip_allocation_method=kwargs.get(
                "public_ip_allocation_method", IPAllocationMethod.dynamic
            ),
            **conn_kwargs,
        )

        ip_kwargs["public_ip_address"] = PublicIPAddress(
            id=str(pub_ip_data["id"]),
        )
        ip_kwargs["name"] = pub_ip_name
        ip_configurations = [ip_kwargs]
    else:
        priv_ip_name = "{}-ip".format(  # pylint: disable=consider-using-f-string
            kwargs["iface_name"]
        )
        ip_kwargs["name"] = priv_ip_name
        ip_configurations = [ip_kwargs]
    # pylint: disable=unused-variable
    netiface = __salt__["azurerm_network.network_interface_create_or_update"](
        name=kwargs["iface_name"],
        ip_configurations=ip_configurations,
        subnet=kwargs["subnet"],
        virtual_network=kwargs["network"],
        resource_group=kwargs["resource_group"],
        **conn_kwargs,
    )

    return _get_network_interface(kwargs["iface_name"], kwargs["resource_group"])


def request_instance(vm_, kwargs=None):  # pylint: disable=unused-argument
    """
    Request a VM from Azure.
    """
    compconn = get_conn(client_type="compute")

    # pylint: disable=invalid-name
    CachingTypes = getattr(compute_models, "CachingTypes")
    # pylint: disable=invalid-name
    DataDisk = getattr(compute_models, "DataDisk")
    # pylint: disable=invalid-name
    DiskCreateOptionTypes = getattr(compute_models, "DiskCreateOptionTypes")
    # pylint: disable=invalid-name
    HardwareProfile = getattr(compute_models, "HardwareProfile")
    # pylint: disable=invalid-name
    ImageReference = getattr(compute_models, "ImageReference")
    # pylint: disable=invalid-name
    LinuxConfiguration = getattr(compute_models, "LinuxConfiguration")
    # pylint: disable=invalid-name
    SshConfiguration = getattr(compute_models, "SshConfiguration")
    # pylint: disable=invalid-name
    SshPublicKey = getattr(compute_models, "SshPublicKey")
    # pylint: disable=invalid-name
    NetworkInterfaceReference = getattr(compute_models, "NetworkInterfaceReference")
    # pylint: disable=invalid-name
    NetworkProfile = getattr(compute_models, "NetworkProfile")
    # pylint: disable=invalid-name
    OSDisk = getattr(compute_models, "OSDisk")
    # pylint: disable=invalid-name
    OSProfile = getattr(compute_models, "OSProfile")
    # pylint: disable=invalid-name
    StorageProfile = getattr(compute_models, "StorageProfile")
    # pylint: disable=invalid-name
    VirtualHardDisk = getattr(compute_models, "VirtualHardDisk")
    # pylint: disable=invalid-name
    VirtualMachine = getattr(compute_models, "VirtualMachine")
    # pylint: disable=invalid-name
    VirtualMachineIdentity = getattr(compute_models, "VirtualMachineIdentity")

    subscription_id = config.get_cloud_config_value(
        "subscription_id", get_configured_provider(), __opts__, search_global=False
    )

    if vm_.get("driver") is None:
        vm_["driver"] = "azurerm"

    if vm_.get("location") is None:
        vm_["location"] = get_location()

    if vm_.get("resource_group") is None:
        vm_["resource_group"] = config.get_cloud_config_value(
            "resource_group", vm_, __opts__, search_global=True
        )

    if vm_.get("name") is None:
        vm_["name"] = config.get_cloud_config_value("name", vm_, __opts__, search_global=True)

    # pylint: disable=unused-variable
    iface_data, public_ips, private_ips = create_network_interface(call="action", kwargs=vm_)
    vm_["iface_id"] = iface_data["id"]

    disk_name = "{}-vol0".format(vm_["name"])  # pylint: disable=consider-using-f-string

    vm_username = config.get_cloud_config_value(
        "ssh_username",
        vm_,
        __opts__,
        search_global=True,
        default=config.get_cloud_config_value("win_username", vm_, __opts__, search_global=True),
    )

    ssh_publickeyfile_contents = None
    ssh_publickeyfile = config.get_cloud_config_value(
        "ssh_publickeyfile", vm_, __opts__, search_global=False, default=None
    )
    if ssh_publickeyfile is not None:
        try:
            with salt.utils.files.fopen(ssh_publickeyfile, "r") as spkc_:
                ssh_publickeyfile_contents = spkc_.read()
        except Exception as exc:  # pylint: disable=broad-except
            raise SaltCloudConfigError(  # pylint: disable=raise-missing-from
                f"Failed to read ssh publickey file '{ssh_publickeyfile}': {exc.args[-1]}"
            )

    disable_password_authentication = config.get_cloud_config_value(
        "disable_password_authentication",
        vm_,
        __opts__,
        search_global=False,
        default=False,
    )

    os_kwargs = {}
    win_installer = config.get_cloud_config_value(
        "win_installer", vm_, __opts__, search_global=True
    )
    if not win_installer and ssh_publickeyfile_contents is not None:
        sshpublickey = SshPublicKey(
            key_data=ssh_publickeyfile_contents,
            path=f"/home/{vm_username}/.ssh/authorized_keys",
        )
        sshconfiguration = SshConfiguration(
            public_keys=[sshpublickey],
        )
        linuxconfiguration = LinuxConfiguration(
            disable_password_authentication=disable_password_authentication,
            ssh=sshconfiguration,
        )
        os_kwargs["linux_configuration"] = linuxconfiguration
        vm_password = None
    else:
        vm_password = salt.utils.stringutils.to_str(
            config.get_cloud_config_value(
                "ssh_password",
                vm_,
                __opts__,
                search_global=True,
                default=config.get_cloud_config_value(
                    "win_password", vm_, __opts__, search_global=True
                ),
            )
        )

    if win_installer or (vm_password is not None and not disable_password_authentication):
        if not isinstance(vm_password, str):
            raise SaltCloudSystemExit("The admin password must be a string.")
        if len(vm_password) < 8 or len(vm_password) > 123:
            raise SaltCloudSystemExit("The admin password must be between 8-123 characters long.")
        complexity = 0
        if any(char.isdigit() for char in vm_password):
            complexity += 1
        if any(char.isupper() for char in vm_password):
            complexity += 1
        if any(char.islower() for char in vm_password):
            complexity += 1
        if any(char in string.punctuation for char in vm_password):
            complexity += 1
        if complexity < 3:
            raise SaltCloudSystemExit(
                "The admin password must contain at least 3 of the following types: "
                "upper, lower, digits, special characters"
            )
        os_kwargs["admin_password"] = vm_password

    availability_set = config.get_cloud_config_value(
        "availability_set", vm_, __opts__, search_global=False, default=None
    )
    if availability_set is not None and isinstance(availability_set, str):
        availability_set = {
            "id": "/subscriptions/{}/resourceGroups/{}/providers/Microsoft.Compute/availabilitySets/{}".format(  # pylint: disable=consider-using-f-string
                subscription_id, vm_["resource_group"], availability_set
            )
        }
    else:
        availability_set = None

    cloud_env = _get_cloud_environment()

    storage_endpoint_suffix = cloud_env.suffixes.storage_endpoint

    if isinstance(vm_.get("volumes"), str):
        volumes = salt.utils.yaml.safe_load(vm_["volumes"])
    else:
        volumes = vm_.get("volumes")

    data_disks = None
    if isinstance(volumes, list):
        data_disks = []
    else:
        volumes = []

    lun = 0
    luns = []
    for volume in volumes:
        if isinstance(volume, str):
            volume = {"name": volume}

        volume.setdefault(
            "name",
            volume.get(
                "name",
                volume.get(
                    "name",
                    "{}-datadisk{}".format(  # pylint: disable=consider-using-f-string
                        vm_["name"], str(lun)
                    ),
                ),
            ),
        )

        volume.setdefault(
            "disk_size_gb",
            volume.get("logical_disk_size_in_gb", volume.get("size", 100)),
        )
        # Old kwarg was host_caching, new name is caching
        volume.setdefault("caching", volume.get("host_caching", "ReadOnly"))
        while lun in luns:
            lun += 1
            if lun > 15:
                log.error("Maximum lun count has been reached")
                break
        volume.setdefault("lun", lun)
        lun += 1
        # The default vhd is {vm_name}-datadisk{lun}.vhd
        if "media_link" in volume:
            volume["vhd"] = VirtualHardDisk(uri=volume["media_link"])
            del volume["media_link"]
        elif volume.get("vhd") == "unmanaged":
            volume["vhd"] = VirtualHardDisk(
                uri="https://{}.blob.{}/vhds/{}-datadisk{}.vhd".format(  # pylint: disable=consider-using-f-string
                    vm_["storage_account"],
                    storage_endpoint_suffix,
                    vm_["name"],
                    volume["lun"],
                ),
            )
        elif "vhd" in volume:
            volume["vhd"] = VirtualHardDisk(uri=volume["vhd"])

        if "image" in volume:
            volume["create_option"] = "from_image"
        elif "attach" in volume:
            volume["create_option"] = "attach"
        else:
            volume["create_option"] = "empty"
        data_disks.append(DataDisk(**volume))

    img_ref = None
    if vm_["image"].startswith("http") or vm_.get("vhd") == "unmanaged":
        if vm_["image"].startswith("http"):
            source_image = VirtualHardDisk(uri=vm_["image"])
        else:
            source_image = None
            if "|" in vm_["image"]:
                img_pub, img_off, img_sku, img_ver = vm_["image"].split("|")
                img_ref = ImageReference(
                    publisher=img_pub,
                    offer=img_off,
                    sku=img_sku,
                    version=img_ver,
                )
            elif vm_["image"].startswith("/subscriptions"):
                img_ref = ImageReference(id=vm_["image"])
        if win_installer:
            os_type = "Windows"
        else:
            os_type = "Linux"
        os_disk = OSDisk(
            caching=CachingTypes.none,
            create_option=DiskCreateOptionTypes.from_image,
            name=disk_name,
            vhd=VirtualHardDisk(
                uri="https://{}.blob.{}/vhds/{}.vhd".format(  # pylint: disable=consider-using-f-string
                    vm_["storage_account"],
                    storage_endpoint_suffix,
                    disk_name,
                ),
            ),
            os_type=os_type,
            image=source_image,
            disk_size_gb=vm_.get("os_disk_size_gb"),
        )
    else:
        source_image = None
        os_type = None
        os_disk = OSDisk(
            create_option=DiskCreateOptionTypes.from_image,
            disk_size_gb=vm_.get("os_disk_size_gb"),
        )
        if "|" in vm_["image"]:
            img_pub, img_off, img_sku, img_ver = vm_["image"].split("|")
            img_ref = ImageReference(
                publisher=img_pub,
                offer=img_off,
                sku=img_sku,
                version=img_ver,
            )
        elif vm_["image"].startswith("/subscriptions"):
            img_ref = ImageReference(id=vm_["image"])

    userdata_file = config.get_cloud_config_value(
        "userdata_file", vm_, __opts__, search_global=False, default=None
    )
    userdata = config.get_cloud_config_value(
        "userdata", vm_, __opts__, search_global=False, default=None
    )
    userdata_template = config.get_cloud_config_value(
        "userdata_template", vm_, __opts__, search_global=False, default=None
    )

    if userdata_file:
        if os.path.exists(userdata_file):
            with salt.utils.files.fopen(userdata_file, "r") as fh_:
                userdata = fh_.read()

    if userdata and userdata_template:
        userdata_sendkeys = config.get_cloud_config_value(
            "userdata_sendkeys", vm_, __opts__, search_global=False, default=None
        )
        if userdata_sendkeys:
            vm_["priv_key"], vm_["pub_key"] = salt.utils.cloud.gen_keys(
                config.get_cloud_config_value("keysize", vm_, __opts__)
            )

            key_id = vm_.get("name")
            if "append_domain" in vm_:
                key_id = ".".join([key_id, vm_["append_domain"]])

            salt.utils.cloud.accept_key(__opts__["pki_dir"], vm_["pub_key"], key_id)

        userdata = salt.utils.cloud.userdata_template(__opts__, vm_, userdata)

    custom_extension = None
    if userdata is not None or userdata_file is not None:
        try:
            if win_installer:
                publisher = "Microsoft.Compute"
                virtual_machine_extension_type = "CustomScriptExtension"
                type_handler_version = "1.8"
                if userdata_file and userdata_file.endswith(".ps1"):
                    command_prefix = "powershell -ExecutionPolicy Unrestricted -File "
                else:
                    command_prefix = ""
            else:
                publisher = "Microsoft.Azure.Extensions"
                virtual_machine_extension_type = "CustomScript"
                type_handler_version = "2.0"
                command_prefix = ""

            settings = {}
            if userdata:
                settings["commandToExecute"] = userdata
            elif userdata_file.startswith("http"):
                settings["fileUris"] = [userdata_file]
                settings["commandToExecute"] = (
                    command_prefix + "./" + userdata_file[userdata_file.rfind("/") + 1 :]
                )

            custom_extension = {
                "resource_group": vm_["resource_group"],
                "virtual_machine_name": vm_["name"],
                "extension_name": vm_["name"] + "_custom_userdata_script",
                "location": vm_["location"],
                "publisher": publisher,
                "virtual_machine_extension_type": virtual_machine_extension_type,
                "type_handler_version": type_handler_version,
                "auto_upgrade_minor_version": True,
                "settings": settings,
                "protected_settings": None,
            }
        except Exception as exc:  # pylint: disable=broad-except
            log.exception("Failed to encode userdata: %s", exc)

    identity_type = config.get_cloud_config_value(
        "identity_type", vm_, __opts__, search_global=False, default="None"
    )
    user_assigned_identities = config.get_cloud_config_value(
        "user_assigned_identities", vm_, __opts__, search_global=False, default=None
    )
    custom_data = config.get_cloud_config_value(
        "custom_data", vm_, __opts__, search_global=False, default=""
    )
    user_data = config.get_cloud_config_value(
        "user_data", vm_, __opts__, search_global=False, default=""
    )

    params = VirtualMachine(
        location=vm_["location"],
        plan=None,
        user_data=base64.b64encode(user_data.encode("ascii")).decode("ascii"),
        hardware_profile=HardwareProfile(
            vm_size=vm_["size"].lower(),
        ),
        storage_profile=StorageProfile(
            os_disk=os_disk,
            data_disks=data_disks,
            image_reference=img_ref,
        ),
        os_profile=OSProfile(
            admin_username=vm_username,
            computer_name=vm_["name"],
            custom_data=base64.b64encode(custom_data.encode("ascii")).decode("ascii"),
            **os_kwargs,
        ),
        network_profile=NetworkProfile(
            network_interfaces=[NetworkInterfaceReference(id=vm_["iface_id"])],
        ),
        identity=VirtualMachineIdentity(
            type=identity_type,
            user_assigned_identities=user_assigned_identities,
        ),
        availability_set=availability_set,
        tags=config.get_cloud_config_value(
            "tags", vm_, __opts__, search_global=False, default=None
        ),
    )

    salt.utils.cloud.fire_event(
        "event",
        "requesting instance",
        "salt/cloud/{}/requesting".format(vm_["name"]),  # pylint: disable=consider-using-f-string
        args=__utils__["cloud.filter_event"](
            "requesting", vm_, ["name", "profile", "provider", "driver"]
        ),
        sock_dir=__opts__["sock_dir"],
        transport=__opts__["transport"],
    )

    try:
        vm_create = compconn.virtual_machines.begin_create_or_update(
            resource_group_name=vm_["resource_group"],
            vm_name=vm_["name"],
            parameters=params,
            polling=True,
        )
        vm_create.wait()
        vm_result = vm_create.result()
        vm_result = vm_result.as_dict()
        if custom_extension:
            create_or_update_vmextension(kwargs=custom_extension)
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("compute", exc.message)
        vm_result = {}

    return vm_result


def create(vm_):
    """
    Create a single VM from a data dict.
    """
    try:
        if (
            vm_["profile"]
            and config.is_profile_configured(
                __opts__,
                _get_active_provider_name() or "azurerm",
                vm_["profile"],
                vm_=vm_,
            )
            is False
        ):
            return False
    except AttributeError:
        pass

    if vm_.get("bootstrap_interface") is None:
        vm_["bootstrap_interface"] = "public"

    if vm_.get("resource_group") is None:
        vm_["resource_group"] = config.get_cloud_config_value(
            "resource_group", vm_, __opts__, search_global=True
        )

    salt.utils.cloud.fire_event(
        "event",
        "starting create",
        "salt/cloud/{}/creating".format(vm_["name"]),  # pylint: disable=consider-using-f-string
        args=__utils__["cloud.filter_event"](
            "creating", vm_, ["name", "profile", "provider", "driver"]
        ),
        sock_dir=__opts__["sock_dir"],
        transport=__opts__["transport"],
    )
    __utils__["cloud.cachedir_index_add"](vm_["name"], vm_["profile"], "azurerm", vm_["driver"])
    if not vm_.get("location"):
        vm_["location"] = get_location(kwargs=vm_)

    log.info(
        "Creating Cloud VM %s in %s for resource group %s",
        vm_["name"],
        vm_["location"],
        vm_["resource_group"],
    )

    vm_request = request_instance(vm_=vm_)

    if not vm_request or "error" in vm_request:
        err_message = (
            "Error creating VM {}! ({})".format(  # pylint: disable=consider-using-f-string
                vm_["name"], str(vm_request)
            )
        )
        log.error(err_message)
        raise SaltCloudSystemExit(err_message)

    def _query_node_data(name, resource_group_name, bootstrap_interface):
        """
        Query node data.
        """
        data = show_instance_in_resource_group(name, resource_group_name, call="action")
        if not data:
            return False
        ip_address = None
        if bootstrap_interface == "public":
            ip_address = data["public_ips"][0]
        if bootstrap_interface == "private":
            ip_address = data["private_ips"][0]
        if ip_address is None:
            return False
        return ip_address

    try:
        data = salt.utils.cloud.wait_for_ip(
            _query_node_data,
            update_args=(
                vm_["name"],
                vm_["resource_group"],
                vm_["bootstrap_interface"],
            ),
            timeout=config.get_cloud_config_value(
                "wait_for_ip_timeout", vm_, __opts__, default=10 * 60
            ),
            interval=config.get_cloud_config_value(
                "wait_for_ip_interval", vm_, __opts__, default=10
            ),
            interval_multiplier=config.get_cloud_config_value(
                "wait_for_ip_interval_multiplier", vm_, __opts__, default=1
            ),
        )
    except (
        SaltCloudExecutionTimeout,
        SaltCloudExecutionFailure,
        SaltCloudSystemExit,
    ) as exc:
        try:
            log.warning(exc)
        finally:
            raise SaltCloudSystemExit(str(exc))  # pylint: disable=raise-missing-from

    vm_["ssh_host"] = data
    if not vm_.get("ssh_username"):
        vm_["ssh_username"] = config.get_cloud_config_value("ssh_username", vm_, __opts__)
    vm_["password"] = config.get_cloud_config_value("ssh_password", vm_, __opts__)
    ret = __utils__["cloud.bootstrap"](vm_, __opts__)

    data = show_instance_in_resource_group(vm_["name"], vm_["resource_group"], call="action")
    log.info("Created Cloud VM '%s'", vm_["name"])
    log.debug("'%s' VM creation details:\n%s", vm_["name"], pprint.pformat(data))

    ret.update(data)

    salt.utils.cloud.fire_event(
        "event",
        "created instance",
        "salt/cloud/{}/created".format(vm_["name"]),  # pylint: disable=consider-using-f-string
        args=__utils__["cloud.filter_event"](
            "created", vm_, ["name", "profile", "provider", "driver"]
        ),
        sock_dir=__opts__["sock_dir"],
        transport=__opts__["transport"],
    )

    return ret


def destroy(name, call=None, kwargs=None):
    """
    Destroy a VM.

    CLI Examples:

    .. code-block:: bash

        salt-cloud -d myminion
        salt-cloud -a destroy myminion service_name=myservice
    """
    if kwargs is None:
        kwargs = {}

    if call == "function":
        raise SaltCloudSystemExit(
            "The destroy action must be called with -d, --destroy, -a or --action."
        )

    conn_kwargs = get_conn_dict()

    node_data = show_instance(name, call="action")
    if node_data["storage_profile"]["os_disk"].get("managed_disk"):
        vhd = node_data["storage_profile"]["os_disk"]["managed_disk"]["id"]
    else:
        vhd = node_data["storage_profile"]["os_disk"]["vhd"]["uri"]

    ret = {name: {}}
    log.debug("Deleting VM")
    result = __salt__["azurerm_compute_virtual_machine.delete"](  # pylint: disable=unused-variable
        name=name, resource_group=node_data["resource_group"], **conn_kwargs
    )
    if not result:
        log.error("VM deletion failed. Stopping further execution.")
        return ret

    if __opts__.get("update_cachedir", False) is True:
        __utils__["cloud.delete_minion_cachedir"](
            name, _get_active_provider_name().split(":")[0], __opts__
        )

    cleanup_disks = config.get_cloud_config_value(
        "cleanup_disks",
        get_configured_provider(),
        __opts__,
        search_global=False,
        default=False,
    )

    if cleanup_disks:
        cleanup_vhds = kwargs.get(
            "delete_vhd",
            config.get_cloud_config_value(
                "cleanup_vhds",
                get_configured_provider(),
                __opts__,
                search_global=False,
                default=False,
            ),
        )

        if cleanup_vhds:
            log.debug("Deleting vhd")

            comps = vhd.split("/")
            container = comps[-2]
            blob = comps[-1]

            ret[name]["delete_disk"] = {
                "delete_disks": cleanup_disks,
                "delete_vhd": cleanup_vhds,
                "container": container,
                "blob": blob,
            }

            if vhd.startswith("http"):
                ret[name]["data"] = delete_blob(
                    kwargs={"container": container, "blob": blob}, call="function"
                )
            else:
                ret[name]["data"] = delete_managed_disk(
                    kwargs={
                        "resource_group": node_data["resource_group"],
                        "container": container,
                        "blob": blob,
                    },
                    call="function",
                )

        cleanup_data_disks = kwargs.get(
            "delete_data_disks",
            config.get_cloud_config_value(
                "cleanup_data_disks",
                get_configured_provider(),
                __opts__,
                search_global=False,
                default=False,
            ),
        )

        if cleanup_data_disks:
            log.debug("Deleting data_disks")
            ret[name]["data_disks"] = {}

            for disk in node_data["storage_profile"]["data_disks"]:
                datavhd = disk.get("managed_disk", {}).get("id") or disk.get("vhd", {}).get("uri")
                comps = datavhd.split("/")
                container = comps[-2]
                blob = comps[-1]

                ret[name]["data_disks"][disk["name"]] = {
                    "delete_disks": cleanup_disks,
                    "delete_vhd": cleanup_vhds,
                    "container": container,
                    "blob": blob,
                }

                if datavhd.startswith("http"):
                    ret[name]["data"] = delete_blob(
                        kwargs={"container": container, "blob": blob}, call="function"
                    )
                else:
                    ret[name]["data"] = delete_managed_disk(
                        kwargs={
                            "resource_group": node_data["resource_group"],
                            "container": container,
                            "blob": blob,
                        },
                        call="function",
                    )

    cleanup_interfaces = config.get_cloud_config_value(
        "cleanup_interfaces",
        get_configured_provider(),
        __opts__,
        search_global=False,
        default=False,
    )

    if cleanup_interfaces:
        ret[name]["cleanup_network"] = {
            "cleanup_interfaces": cleanup_interfaces,
            "resource_group": node_data["resource_group"],
            "data": [],
        }

        ifaces = node_data["network_profile"]["network_interfaces"]
        for iface in ifaces:
            resource_group = iface["id"].split("/")[4]
            ret[name]["cleanup_network"]["data"].append(
                delete_interface(
                    kwargs={
                        "resource_group": resource_group,
                        "iface_name": iface["name"],
                    },
                    call="function",
                )
            )

    return ret


def list_storage_accounts(call=None):
    """
    List storage accounts within the subscription.
    """
    if call == "action":
        raise SaltCloudSystemExit(
            "The list_storage_accounts function must be called with -f or --function"
        )

    storconn = get_conn(client_type="storage")

    ret = {}
    try:
        accounts_query = storconn.storage_accounts.list()
        accounts = saltext.azurerm.utils.azurerm.paged_object_to_list(accounts_query)
        for account in accounts:
            ret[account["name"]] = account
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("storage", exc.message)
        ret = {"Error": exc.message}

    return ret


def _get_cloud_environment():
    """
    Get the cloud environment object.
    """
    cloud_environment = config.get_cloud_config_value(
        "cloud_environment", get_configured_provider(), __opts__, search_global=False
    )
    try:
        cloud_env_module = importlib.import_module("msrestazure.azure_cloud")
        cloud_env = getattr(cloud_env_module, cloud_environment or "AZURE_PUBLIC_CLOUD")
    except (AttributeError, ImportError):
        raise SaltCloudSystemExit(  # pylint: disable=raise-missing-from
            f"The azure {cloud_environment} cloud environment is not available."
        )

    return cloud_env


def _get_block_blob_service(kwargs=None):
    """
    Get the block blob storage service.
    """
    resource_group = kwargs.get("resource_group") or config.get_cloud_config_value(
        "resource_group", get_configured_provider(), __opts__, search_global=False
    )
    storage_account = kwargs.get("storage_account") or config.get_cloud_config_value(
        "storage_account", get_configured_provider(), __opts__, search_global=False
    )
    storage_key = kwargs.get("storage_key") or config.get_cloud_config_value(
        "storage_key", get_configured_provider(), __opts__, search_global=False
    )

    if not resource_group:
        raise SaltCloudSystemExit("A resource group must be specified")

    if not storage_account:
        raise SaltCloudSystemExit("A storage account must be specified")

    if not storage_key:
        storconn = get_conn(client_type="storage")
        storage_keys = storconn.storage_accounts.list_keys(resource_group, storage_account)
        storage_keys = {v.key_name: v.value for v in storage_keys.keys}
        storage_key = next(iter(storage_keys.values()))

    return BlobServiceClient(
        account_url=storage_account,
        credential=storage_key,
    )


def _get_container_client(kwargs=None):
    """
    Get the storage container client.
    """
    resource_group = kwargs.get("resource_group") or config.get_cloud_config_value(
        "resource_group", get_configured_provider(), __opts__, search_global=False
    )
    storage_account = kwargs.get("storage_account") or config.get_cloud_config_value(
        "storage_account", get_configured_provider(), __opts__, search_global=False
    )
    container_name = kwargs.get("container_name") or config.get_cloud_config_value(
        "container_name", get_configured_provider(), __opts__, search_global=False
    )
    storage_key = kwargs.get("storage_key") or config.get_cloud_config_value(
        "storage_key", get_configured_provider(), __opts__, search_global=False
    )

    if not resource_group:
        raise SaltCloudSystemExit("A resource group must be specified")

    if not storage_account:
        raise SaltCloudSystemExit("A storage account must be specified")

    if not storage_key:
        storconn = get_conn(client_type="storage")
        storage_keys = storconn.storage_accounts.list_keys(resource_group, storage_account)
        storage_keys = {v.key_name: v.value for v in storage_keys.keys}
        storage_key = next(iter(storage_keys.values()))

    return ContainerClient(
        account_url=storage_account,
        container_name=container_name,
        credential=storage_key,
    )


def list_blobs(call=None, kwargs=None):  # pylint: disable=unused-argument
    """
    List blobs.
    """
    if kwargs is None:
        kwargs = {}

    if "container" not in kwargs:
        raise SaltCloudSystemExit("A container must be specified")

    storageservice = _get_container_client(kwargs)

    ret = {}
    try:
        for blob in storageservice.list_blobs(kwargs["container"]):
            ret[blob.name] = {
                "blob_type": blob.properties.blob_type,
                "last_modified": blob.properties.last_modified.isoformat(),
                "server_encrypted": blob.properties.server_encrypted,
            }
    except Exception as exc:  # pylint: disable=broad-except
        log.warning(str(exc))

    return ret


def delete_blob(call=None, kwargs=None):  # pylint: disable=unused-argument
    """
    Delete a blob from a container.
    """
    if kwargs is None:
        kwargs = {}

    if "container" not in kwargs:
        raise SaltCloudSystemExit("A container must be specified")

    if "blob" not in kwargs:
        raise SaltCloudSystemExit("A blob must be specified")

    storageservice = _get_container_client(kwargs)

    storageservice.delete_blob(kwargs["container"], kwargs["blob"])
    return True


def delete_managed_disk(call=None, kwargs=None):  # pylint: disable=unused-argument
    """
    Delete a managed disk from a resource group.
    """
    conn_kwargs = get_conn_dict()

    ret = __salt__["azurerm_compute_disk.delete"](
        name=kwargs["blob"], resource_group=kwargs["resource_group"], **conn_kwargs
    )

    return ret


def list_virtual_networks(call=None):
    """
    List virtual networks.
    """
    if call == "action":
        raise SaltCloudSystemExit("The avail_sizes function must be called with -f or --function")

    conn_kwargs = get_conn_dict()

    networks = __salt__["azurerm_network.virtual_networks_list_all"](**conn_kwargs)

    return networks


def list_subnets(call=None, kwargs=None):
    """
    List subnets in a virtual network.
    """
    if kwargs is None:
        kwargs = {}

    if call == "action":
        raise SaltCloudSystemExit("The avail_sizes function must be called with -f or --function")

    resource_group = kwargs.get("resource_group") or config.get_cloud_config_value(
        "resource_group", get_configured_provider(), __opts__, search_global=False
    )

    if not resource_group and "group" in kwargs and "resource_group" not in kwargs:
        resource_group = kwargs["group"]

    if not resource_group:
        raise SaltCloudSystemExit("A resource group must be specified")

    if kwargs.get("network") is None:
        kwargs["network"] = config.get_cloud_config_value(
            "network", get_configured_provider(), __opts__, search_global=False
        )

    if "network" not in kwargs or kwargs["network"] is None:
        raise SaltCloudSystemExit('A virtual network name must be specified as "network"')

    conn_kwargs = get_conn_dict()

    subnets = __salt__["azurerm_network.subnets_list"](
        resource_group=resource_group, virtual_network=kwargs["network"], **conn_kwargs
    )

    return subnets


def create_or_update_vmextension(call=None, kwargs=None):  # pylint: disable=unused-argument
    """
    .. versionadded:: 2019.2.0

    Create or update a VM extension object "inside" of a VM object.

    required kwargs:
      .. code-block:: yaml

        extension_name: myvmextension
        virtual_machine_name: myvm
        settings: {"commandToExecute": "hostname"}

    optional kwargs:
      .. code-block:: yaml

        resource_group: < inferred from cloud configs >
        location: < inferred from cloud configs >
        publisher: < default: Microsoft.Azure.Extensions >
        virtual_machine_extension_type: < default: CustomScript >
        type_handler_version: < default: 2.0 >
        auto_upgrade_minor_version: < default: True >
        protected_settings: < default: None >
    """
    if kwargs is None:
        kwargs = {}

    if "extension_name" not in kwargs:
        raise SaltCloudSystemExit("An extension name must be specified")

    if "virtual_machine_name" not in kwargs:
        raise SaltCloudSystemExit("A virtual machine name must be specified")

    resource_group = kwargs.get("resource_group") or config.get_cloud_config_value(
        "resource_group", get_configured_provider(), __opts__, search_global=False
    )

    if not resource_group:
        raise SaltCloudSystemExit("A resource group must be specified")

    location = kwargs.get("location") or get_location()

    if not location:
        raise SaltCloudSystemExit("A location must be specified")

    publisher = kwargs.get("publisher", "Microsoft.Azure.Extensions")
    virtual_machine_extension_type = kwargs.get("virtual_machine_extension_type", "CustomScript")
    type_handler_version = kwargs.get("type_handler_version", "2.0")
    auto_upgrade_minor_version = kwargs.get("auto_upgrade_minor_version", True)
    settings = kwargs.get("settings", {})
    protected_settings = kwargs.get("protected_settings")

    if not isinstance(settings, dict):
        raise SaltCloudSystemExit("VM extension settings are not valid")
    if "commandToExecute" not in settings and "script" not in settings:
        raise SaltCloudSystemExit(
            "VM extension settings are not valid. Either commandToExecute or script"
            " must be specified."
        )

    conn_kwargs = get_conn_dict()

    log.info("Creating VM extension %s", kwargs["extension_name"])
    ret = __salt__["azurerm_compute_virtual_machine_extension.create_or_update"](
        name=kwargs["extension_name"],
        vm_name=kwargs["virtual_machine_name"],
        resource_group=resource_group,
        location=location,
        publisher=publisher,
        extension_type=virtual_machine_extension_type,
        version=type_handler_version,
        settings=settings,
        auto_upgrade_minor_version=auto_upgrade_minor_version,
        protected_settings=protected_settings,
        **conn_kwargs,
    )

    return ret


def stop(name, call=None):
    """
    .. versionadded:: 2019.2.0

    Stop (deallocate) a VM

    CLI Examples:

    .. code-block:: bash

         salt-cloud -a stop myminion
    """
    if call == "function":
        raise SaltCloudSystemExit("The stop action must be called with -a or --action.")

    conn_kwargs = get_conn_dict()

    resource_group = config.get_cloud_config_value(
        "resource_group", get_configured_provider(), __opts__, search_global=False
    )

    ret = False
    if not resource_group:
        groups = list_resource_groups()
        for group in groups:
            ret = __salt__["azurerm_compute_virtual_machine.deallocate"](
                name=name, resource_group=group, **conn_kwargs
            )
            if ret:
                break
            if "error" in ret and "was not found" in ret["error"]:
                continue

        if not ret or "error" in ret:
            ret = {"error": f"Unable to find virtual machine with name: {name}"}
    else:
        ret = __salt__["azurerm_compute_virtual_machine.deallocate"](
            name=name, resource_group=resource_group, **conn_kwargs
        )

    return ret


def start(name, call=None):
    """
    .. versionadded:: 2019.2.0

    Start a VM

    CLI Examples:

    .. code-block:: bash

         salt-cloud -a start myminion
    """
    if call == "function":
        raise SaltCloudSystemExit("The start action must be called with -a or --action.")

    conn_kwargs = get_conn_dict()

    resource_group = config.get_cloud_config_value(
        "resource_group", get_configured_provider(), __opts__, search_global=False
    )

    ret = False
    if not resource_group:
        groups = list_resource_groups()
        for group in groups:
            ret = __salt__["azurerm_compute_virtual_machine.start"](
                name=name, resource_group=group, **conn_kwargs
            )
            if ret:
                break
            if "error" in ret and "was not found" in ret["error"]:
                continue

        if not ret or "error" in ret:
            ret = {"error": f"Unable to find virtual machine with name: {name}"}
    else:
        ret = __salt__["azurerm_compute_virtual_machine.start"](
            name=name, resource_group=resource_group, **conn_kwargs
        )

    return ret
