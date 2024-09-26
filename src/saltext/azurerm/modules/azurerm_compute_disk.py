"""
Azure Resource Manager (ARM) Compute Disk Execution Module

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


def get(name, resource_group, **kwargs):
    """
    .. versionadded:: 2.1.0

    Gets information about a disk.

    :param name: The disk to query.

    :param resource_group: The resource group name assigned to the disk.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute_disk.get test_name test_group

    """
    result = {}
    compconn = saltext.azurerm.utils.azurerm.get_client("compute", **kwargs)

    try:
        disk = compconn.disks.get(resource_group_name=resource_group, disk_name=name)
        result = disk.as_dict()
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def delete(name, resource_group, **kwargs):
    """
    .. versionadded:: 2.1.0

    Delete a disk.

    :param name: The disk to delete.

    :param resource_group: The resource group name assigned to the disk.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute_disk.delete test_name test_group

    """
    result = False
    compconn = saltext.azurerm.utils.azurerm.get_client("compute", **kwargs)

    try:
        # pylint: disable=unused-variable
        disk = compconn.disks.begin_delete(resource_group_name=resource_group, disk_name=name)
        result = True
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def list_(resource_group=None, **kwargs):
    """
    .. versionadded:: 2.1.0

    Lists all the disks under a subscription.

    :param resource_group: The name of the resource group to limit the results.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute_disk.list

    """
    result = {}
    compconn = saltext.azurerm.utils.azurerm.get_client("compute", **kwargs)

    try:
        if resource_group:
            disks = saltext.azurerm.utils.azurerm.paged_object_to_list(
                compconn.disks.list_by_resource_group(resource_group_name=resource_group)
            )
        else:
            disks = saltext.azurerm.utils.azurerm.paged_object_to_list(compconn.disks.list())

        for disk in disks:
            result[disk["name"]] = disk
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def grant_access(name, resource_group, access, duration, **kwargs):
    """
    .. versionadded:: 2.1.0

    Grants access to a disk.

    :param name: The name of the disk to grant access to.

    :param resource_group: The resource group name assigned to the disk.

    :param access: Possible values include: 'None', 'Read', 'Write'.

    :param duration: Time duration in seconds until the SAS access expires.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute_disk.grant_access test_name test_group

    """
    result = False
    compconn = saltext.azurerm.utils.azurerm.get_client("compute", **kwargs)

    try:
        disk = compconn.disks.begin_grant_access(
            resource_group_name=resource_group,
            disk_name=name,
            access=access,
            duration_in_seconds=duration,
        )
        disk.wait()
        result = True
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def revoke_access(name, resource_group, **kwargs):
    """
    .. versionadded:: 2.1.0

    Revokes access to a disk.

    :param name: The name of the disk to revoke access to.

    :param resource_group: The resource group name assigned to the disk.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute_disk.revoke_access test_name test_group

    """
    result = False
    compconn = saltext.azurerm.utils.azurerm.get_client("compute", **kwargs)

    try:
        disk = compconn.disks.begin_revoke_access(
            resource_group_name=resource_group, disk_name=name
        )
        disk.wait()
        result = True
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("compute", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
