"""
Azure Resource Manager (ARM) Compute Image Execution Module

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
    from azure.core.exceptions import SerializationError
    from azure.mgmt.core.tools import is_valid_resource_id

    HAS_LIBS = True
except ImportError:
    pass

__func_alias__ = {"list_": "list"}

log = logging.getLogger(__name__)


def create_or_update(
    name,
    resource_group,
    source_vm=None,
    source_vm_group=None,
    os_disk=None,
    data_disks=None,
    zone_resilient=False,
    hyper_vgeneration=None,
    **kwargs,
):
    """
    .. versionadded:: 2.1.0

    Create or update an image.

    :param name: The image to create.

    :param resource_group: The resource group name assigned to the image.

    :param source_vm: The name of the virtual machine from which the image is created. This parameter or a valid
        os_disk is required.

    :param source_vm_group: The name of the resource group containing the source virtual machine.
        This defaults to the same resource group specified for the resultant image.

    :param os_disk: The resource ID of an operating system disk to use for the image.

    :param data_disks: The resource ID or list of resource IDs associated with data disks to add to
        the image.

    :param zone_resilient: Specifies whether an image is zone resilient or not. Zone resilient images
        can be created only in regions that provide Zone Redundant Storage (ZRS).

    :param hyper_vgeneration: Gets the HyperVGenerationType of the VirtualMachine created from the image. Possible
        values include: "V1" and "V2".

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute_image.create_or_update testimage testgroup

    """
    if "location" not in kwargs:
        rg_props = __salt__["azurerm_resource.resource_group_get"](resource_group, **kwargs)

        if "error" in rg_props:
            log.error("Unable to determine location from resource group specified.")
            return {"error": "Unable to determine location from resource group specified."}
        kwargs["location"] = rg_props["location"]

    result = {}
    compconn = saltext.azurerm.utils.azurerm.get_client("compute", **kwargs)

    if source_vm:
        # Use VM name to link to the IDs of existing VMs.
        vm_instance = __salt__["azurerm_compute_virtual_machine.get"](
            name=source_vm,
            resource_group=(source_vm_group or resource_group),
            log_level="info",
            **kwargs,
        )

        if "error" in vm_instance:
            errmsg = "The source virtual machine could not be found."
            log.error(errmsg)
            result = {"error": errmsg}
            return result

        source_vm = {"id": str(vm_instance["id"])}

    spmodel = None
    if os_disk:
        if is_valid_resource_id(os_disk):
            os_disk = {"id": os_disk}
        else:
            errmsg = "The os_disk parameter is not a valid resource ID string."
            log.error(errmsg)
            result = {"error": errmsg}
            return result

        if data_disks:
            if isinstance(data_disks, list):
                data_disks = [{"id": dd} for dd in data_disks]
            elif isinstance(data_disks, str):
                data_disks = [{"id": data_disks}]
            else:
                errmsg = "The data_disk parameter is a single resource ID string or a list of resource IDs."
                log.error(errmsg)
                result = {"error": errmsg}
                return result

        try:
            spmodel = saltext.azurerm.utils.azurerm.create_object_model(
                "compute",
                "ImageStorageProfile",
                os_disk=os_disk,
                data_disks=data_disks,
                zone_resilient=zone_resilient,
                **kwargs,
            )
        except TypeError as exc:
            result = {"error": f"The object model could not be built. ({str(exc)})"}
            return result

    try:
        imagemodel = saltext.azurerm.utils.azurerm.create_object_model(
            "compute",
            "Image",
            source_virtual_machine=source_vm,
            storage_profile=spmodel,
            hyper_vgeneration=hyper_vgeneration,
            **kwargs,
        )
    except TypeError as exc:
        result = {"error": f"The object model could not be built. ({str(exc)})"}
        return result

    try:
        image = compconn.images.begin_create_or_update(
            resource_group_name=resource_group, image_name=name, parameters=imagemodel
        )

        image.wait()
        result = image.result().as_dict()
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {"error": f"The object model could not be parsed. ({str(exc)})"}

    return result


def delete(name, resource_group, **kwargs):
    """
    .. versionadded:: 2.1.0

    Delete an image.

    :param name: The image to delete.

    :param resource_group: The resource group name assigned to the image.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute_image.delete testimage testgroup

    """
    result = False
    compconn = saltext.azurerm.utils.azurerm.get_client("compute", **kwargs)

    try:
        image = compconn.images.begin_delete(resource_group_name=resource_group, image_name=name)
        image.wait()
        result = True
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def get(name, resource_group, **kwargs):
    """
    .. versionadded:: 2.1.0

    Get properties of the specified image.

    :param name: The name of the image to query.

    :param resource_group: The resource group name assigned to the image.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute_image.get testimage testgroup

    """
    result = {}
    compconn = saltext.azurerm.utils.azurerm.get_client("compute", **kwargs)

    try:
        image = compconn.images.get(resource_group_name=resource_group, image_name=name)
        result = image.as_dict()
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def list_(resource_group=None, **kwargs):
    """
    .. versionadded:: 2.1.0

    Gets the list of Images in the subscription.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute_image.list

    """
    result = {}
    compconn = saltext.azurerm.utils.azurerm.get_client("compute", **kwargs)

    try:
        if resource_group:
            images = saltext.azurerm.utils.azurerm.paged_object_to_list(
                compconn.images.list_by_resource_group(resource_group_name=resource_group)
            )
        else:
            images = saltext.azurerm.utils.azurerm.paged_object_to_list(compconn.images.list())

        for image in images:
            result[image["name"]] = image
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
