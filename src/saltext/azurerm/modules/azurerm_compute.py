"""
Azure Resource Manager Compute Execution Module

.. versionadded:: 2019.2.0

:maintainer: <devops@eitr.tech>
:maturity: new
:platform: linux

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

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.compute.models  # pylint: disable=unused-import

    HAS_LIBS = True
except ImportError:
    pass

__virtualname__ = "azurerm_compute"

log = logging.getLogger(__name__)


def __virtual__():
    if not HAS_LIBS:
        return (
            False,
            "The following dependencies are required to use the Azure Resource Manager modules: "
            "Microsoft Azure SDK for Python >= 2.0rc6, "
            "MS REST Azure (msrestazure) >= 0.4",
        )

    return __virtualname__


def availability_set_create_or_update(
    name, resource_group, **kwargs
):  # pylint: disable=invalid-name
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_availability_set.py)
    and will be deprecated in the future.**

    Create or update an availability set.

    :param name: The availability set to create.

    :param resource_group: The resource group name assigned to the
        availability set.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute.availability_set_create_or_update testset testgroup

    """
    return __salt__["azurerm_compute_availability_set.create_or_update"](
        name=name, resource_group=resource_group, **kwargs
    )


def availability_set_delete(name, resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_availability_set.py)
    and will be deprecated in the future.**

    Delete an availability set.

    :param name: The availability set to delete.

    :param resource_group: The resource group name assigned to the
        availability set.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute.availability_set_delete testset testgroup

    """
    return __salt__["azurerm_compute_availability_set.delete"](
        name=name, resource_group=resource_group, **kwargs
    )


def availability_set_get(name, resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_availability_set.py)
    and will be deprecated in the future.**

    Get a dictionary representing an availability set's properties.

    :param name: The availability set to get.

    :param resource_group: The resource group name assigned to the
        availability set.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute.availability_set_get testset testgroup

    """
    return __salt__["azurerm_compute_availability_set.get"](
        name=name, resource_group=resource_group, **kwargs
    )


def availability_sets_list(resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_availability_set.py)
    and will be deprecated in the future.**

    List all availability sets within a resource group.

    :param resource_group: The resource group name to list availability
        sets within.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute.availability_sets_list testgroup

    """
    return __salt__["azurerm_compute_availability_set.list"](
        resource_group=resource_group, **kwargs
    )


def availability_sets_list_available_sizes(name, resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_availability_set.py)
    and will be deprecated in the future.**

    List all available virtual machine sizes that can be used to
    to create a new virtual machine in an existing availability set.

    :param name: The availability set name to list available
        virtual machine sizes within.

    :param resource_group: The resource group name to list available
        availability set sizes within.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute.availability_sets_list_available_sizes testset testgroup

    """
    return __salt__["azurerm_compute_availability_set.list_available_sizes"](
        name=name, resource_group=resource_group, **kwargs
    )


def virtual_machine_capture(
    name, destination_name, resource_group, prefix="capture-", overwrite=False, **kwargs
):
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_virtual_machine.py)
    and will be deprecated in the future.**

    Captures the VM by copying virtual hard disks of the VM and outputs
    a template that can be used to create similar VMs.

    :param name: The name of the virtual machine.

    :param destination_name: The destination container name.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    :param prefix: (Default: 'capture-') The captured virtual hard disk's name prefix.

    :param overwrite: (Default: False) Overwrite the destination disk in case of conflict.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute.virtual_machine_capture testvm testcontainer testgroup

    """
    return __salt__["azurerm_compute_virtual_machine.capture"](
        name=name,
        destination_name=destination_name,
        resource_group=resource_group,
        prefix=prefix,
        overwrite=overwrite,
        **kwargs,
    )


def virtual_machine_get(name, resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_virtual_machine.py)
    and will be deprecated in the future.**

    Retrieves information about the model view or the instance view of a
    virtual machine.

    :param name: The name of the virtual machine.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute.virtual_machine_get testvm testgroup

    """
    return __salt__["azurerm_compute_virtual_machine.get"](
        name=name, resource_group=resource_group, **kwargs
    )


def virtual_machine_convert_to_managed_disks(name, resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_virtual_machine.py)
    and will be deprecated in the future.**

    Converts virtual machine disks from blob-based to managed disks. Virtual
    machine must be stop-deallocated before invoking this operation.

    :param name: The name of the virtual machine to convert.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute.virtual_machine_convert_to_managed_disks testvm testgroup

    """
    return __salt__["azurerm_compute_virtual_machine.convert_to_managed_disks"](
        name=name, resource_group=resource_group, **kwargs
    )


def virtual_machine_deallocate(name, resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_virtual_machine.py)
    and will be deprecated in the future.**

    Power off a virtual machine and deallocate compute resources.

    :param name: The name of the virtual machine to deallocate.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute.virtual_machine_deallocate testvm testgroup

    """
    return __salt__["azurerm_compute_virtual_machine.deallocate"](
        name=name, resource_group=resource_group, **kwargs
    )


def virtual_machine_generalize(name, resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_virtual_machine.py)
    and will be deprecated in the future.**

    Set the state of a virtual machine to 'generalized'.

    :param name: The name of the virtual machine.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute.virtual_machine_generalize testvm testgroup

    """
    return __salt__["azurerm_compute_virtual_machine.generalize"](
        name=name, resource_group=resource_group, **kwargs
    )


def virtual_machines_list(resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_virtual_machine.py)
    and will be deprecated in the future.**

    List all virtual machines within a resource group.

    :param resource_group: The resource group name to list virtual
        machines within.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute.virtual_machines_list testgroup

    """
    return __salt__["azurerm_compute_virtual_machine.list"](resource_group=resource_group, **kwargs)


def virtual_machines_list_all(**kwargs):
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_virtual_machine.py)
    and will be deprecated in the future.**

    List all virtual machines within a subscription.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute.virtual_machines_list_all

    """
    return __salt__["azurerm_compute_virtual_machine.list_all"](**kwargs)


def virtual_machines_list_available_sizes(
    name, resource_group, **kwargs
):  # pylint: disable=invalid-name
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_virtual_machine.py)
    and will be deprecated in the future.**

    Lists all available virtual machine sizes to which the specified virtual
    machine can be resized.

    :param name: The name of the virtual machine.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute.virtual_machines_list_available_sizes testvm testgroup

    """
    return __salt__["azurerm_compute_virtual_machine.list_available_sizes"](
        name=name, resource_group=resource_group, **kwargs
    )


def virtual_machine_power_off(name, resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_virtual_machine.py)
    and will be deprecated in the future.**

    Power off (stop) a virtual machine.

    :param name: The name of the virtual machine to stop.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute.virtual_machine_power_off testvm testgroup

    """
    return __salt__["azurerm_compute_virtual_machine.power_off"](
        name=name, resource_group=resource_group, **kwargs
    )


def virtual_machine_restart(name, resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_virtual_machine.py)
    and will be deprecated in the future.**

    Restart a virtual machine.

    :param name: The name of the virtual machine to restart.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute.virtual_machine_restart testvm testgroup

    """
    return __salt__["azurerm_compute_virtual_machine.restart"](
        name=name, resource_group=resource_group, **kwargs
    )


def virtual_machine_start(name, resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_virtual_machine.py)
    and will be deprecated in the future.**

    Power on (start) a virtual machine.

    :param name: The name of the virtual machine to start.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute.virtual_machine_start testvm testgroup

    """
    return __salt__["azurerm_compute_virtual_machine.start"](
        name=name, resource_group=resource_group, **kwargs
    )


def virtual_machine_redeploy(name, resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_virtual_machine.py)
    and will be deprecated in the future.**

    Redeploy a virtual machine.

    :param name: The name of the virtual machine to redeploy.

    :param resource_group: The resource group name assigned to the
        virtual machine.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_compute.virtual_machine_redeploy testvm testgroup

    """
    return __salt__["azurerm_compute_virtual_machine.redeploy"](
        name=name, resource_group=resource_group, **kwargs
    )
