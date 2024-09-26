"""
Azure Resource Manager (ARM) Compute Virtual Machine Extension Operations Execution Module

.. versionadded:: 2.1.0

:maintainer: <devops@eitr.tech>
:configuration: This module requires Azure Resource Manager credentials to be passed as keyword arguments
    to every function in order to work properly.

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

import saltext.azurerm.utils.azurerm

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.compute.models  # pylint: disable=unused-import
    from azure.core.exceptions import HttpResponseError

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


def create_or_update(
    name,
    vm_name,
    resource_group,
    location,
    publisher,
    extension_type,
    version,
    settings,
    auto_upgrade_minor_version=None,
    **kwargs,
):
    """
    .. versionadded:: 2.1.0

    The operation to create or update the extension.

    :param name: The name of the virtual machine extension.

    :param vm_name: The name of the virtual machine where the extension should be created or updated.

    :param resource_group: The name of the resource group.

    :param location: Resource location.

    :param publisher: The publisher of the extension.

    :param extension_type: Specifies the type of the extension; an example is "CustomScriptExtension".

    :param version: Specifies the version of the script handler.

    :param settings: A dictionary representing the public settings for the extension. This dictionary will be
        utilized as JSON by the SDK operation.

    :param auto_upgrade_minor_version: A boolean value indicating whether the extension should use a newer minor version
        if one is available at deployment time. Once deployed, however, the extension will not upgrade minor versions
        unless redeployed, even with this property set to True.

    :param tags: A dictionary of strings can be passed as tag metadata to the virtual machine extension object.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute_virtual_machine_extension.create_or_update test_name test_vm test_group
        test_loc test_publisher test_type test_version test_settings

    """
    result = {}
    compconn = saltext.azurerm.utils.azurerm.get_client("compute", **kwargs)

    try:
        paramsmodel = saltext.azurerm.utils.azurerm.create_object_model(
            "compute",
            "VirtualMachineExtension",
            location=location,
            settings=settings,
            publisher=publisher,
            type_properties_type=extension_type,
            type_handler_version=version,
            auto_upgrade_minor_version=auto_upgrade_minor_version,
            **kwargs,
        )
    except TypeError as exc:
        result = {"error": f"The object model could not be built. ({str(exc)})"}
        return result

    try:
        extension = compconn.virtual_machine_extensions.begin_create_or_update(
            vm_extension_name=name,
            vm_name=vm_name,
            resource_group_name=resource_group,
            extension_parameters=paramsmodel,
        )

        extension.wait()
        result = extension.result().as_dict()
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def delete(name, vm_name, resource_group, **kwargs):
    """
    .. versionadded:: 2.1.0

    The operation to delete the extension.

    :param name: The name of the virtual machine extension.

    :param vm_name: The name of the virtual machine where the extension should be deleted.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute_virtual_machine_extension.delete test_name test_vm test_group

    """
    result = False
    compconn = saltext.azurerm.utils.azurerm.get_client("compute", **kwargs)

    try:
        extension = compconn.virtual_machine_extensions.begin_delete(
            vm_extension_name=name, vm_name=vm_name, resource_group_name=resource_group
        )

        extension.wait()
        result = True
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def get(name, vm_name, resource_group, **kwargs):
    """
    .. versionadded:: 2.1.0

    The operation to get the extension.

    :param name: The name of the virtual machine extension.

    :param vm_name: The name of the virtual machine containing the extension.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute_virtual_machine_extension.get test_name test_vm test_group

    """
    result = {}
    compconn = saltext.azurerm.utils.azurerm.get_client("compute", **kwargs)

    try:
        extension = compconn.virtual_machine_extensions.get(
            vm_extension_name=name, vm_name=vm_name, resource_group_name=resource_group
        )

        result = extension.as_dict()
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def list_(vm_name, resource_group, **kwargs):
    """
    .. versionadded:: 2.1.0

    The operation to get all extensions of a Virtual Machine.

    :param vm_name: The name of the virtual machine containing the extension.

    :param resource_group: The name of the resource group.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute_virtual_machine_extension.list test_vm test_group

    """
    result = {}
    compconn = saltext.azurerm.utils.azurerm.get_client("compute", **kwargs)

    try:
        extensions = compconn.virtual_machine_extensions.list(
            vm_name=vm_name, resource_group_name=resource_group
        )

        extensions_as_list = extensions.as_dict().get("value", {})
        for extension in extensions_as_list:
            result[extension["name"]] = extension
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
