"""
Azure Resource Manager Compute State Module

.. versionadded:: 2019.2.0

:maintainer: <devops@eitr.tech>
:maturity: new
:platform: linux

:configuration: This module requires Azure Resource Manager credentials to be passed as a dictionary of
    keyword arguments to the ``connection_auth`` parameter in order to work properly. Since the authentication
    parameters are sensitive, it's recommended to pass them to the states via pillar.

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

    **cloud_environment**:
      Used to point the cloud driver to different API endpoints, such as Azure GovCloud. Possible values:
        * ``AZURE_PUBLIC_CLOUD`` (default)
        * ``AZURE_CHINA_CLOUD``
        * ``AZURE_US_GOV_CLOUD``
        * ``AZURE_GERMAN_CLOUD``

    Example Pillar for Azure Resource Manager authentication:

    .. code-block:: yaml

        azurerm:
            user_pass_auth:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                username: fletch
                password: 123pass
            mysubscription:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                tenant: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                client_id: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                secret: XXXXXXXXXXXXXXXXXXXXXXXX
                cloud_environment: AZURE_PUBLIC_CLOUD

    Example states using Azure Resource Manager authentication:

    .. code-block:: jinja

        {% set profile = salt['pillar.get']('azurerm:mysubscription') %}
        Ensure availability set exists:
            azurerm_compute.availability_set_present:
                - name: my_avail_set
                - resource_group: my_rg
                - virtual_machines:
                    - my_vm1
                    - my_vm2
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}

        Ensure availability set is absent:
            azurerm_compute.availability_set_absent:
                - name: other_avail_set
                - resource_group: my_rg
                - connection_auth: {{ profile }}

"""

# Python libs
import logging

__virtualname__ = "azurerm_compute"

log = logging.getLogger(__name__)


def __virtual__():
    """
    Only make this state available if the azurerm_compute module is available.
    """
    if "azurerm_compute.availability_set_create_or_update" in __salt__:
        return __virtualname__
    return (False, "azurerm module could not be loaded")


def availability_set_present(
    name,
    resource_group,
    tags=None,
    platform_update_domain_count=None,
    platform_fault_domain_count=None,
    virtual_machines=None,
    sku=None,
    connection_auth=None,
    **kwargs,
):
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_availability_set.py)
    and will be deprecated in the future.**

    Ensure an availability set exists.

    :param name:
        Name of the availability set.

    :param resource_group:
        The resource group assigned to the availability set.

    :param tags:
        A dictionary of strings can be passed as tag metadata to the availability set object.

    :param platform_update_domain_count:
        An optional parameter which indicates groups of virtual machines and underlying physical hardware that can be
        rebooted at the same time.

    :param platform_fault_domain_count:
        An optional parameter which defines the group of virtual machines that share a common power source and network
        switch.

    :param virtual_machines:
        A list of names of existing virtual machines to be included in the availability set.

    :param sku:
        The availability set SKU, which specifies whether the availability set is managed or not. Possible values are
        'Aligned' or 'Classic'. An 'Aligned' availability set is managed, 'Classic' is not.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.

    Example usage:

    .. code-block:: yaml

        Ensure availability set exists:
            azurerm_compute.availability_set_present:
                - name: aset1
                - resource_group: group1
                - platform_update_domain_count: 5
                - platform_fault_domain_count: 3
                - sku: aligned
                - tags:
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}
                - require:
                  - azurerm_resource: Ensure resource group exists

    """
    return __states__["azurerm_compute_availability_set.present"](
        name=name,
        resource_group=resource_group,
        tags=tags,
        platform_update_domain_count=platform_update_domain_count,
        platform_fault_domain_count=platform_fault_domain_count,
        virtual_machines=virtual_machines,
        sku=sku,
        connection_auth=connection_auth,
        **kwargs,
    )


def availability_set_absent(name, resource_group, connection_auth=None):
    """
    .. versionadded:: 2019.2.0

    **WARNING: This function has been moved to another file (azurerm_compute_availability_set.py)
    and will be deprecated in the future.**

    Ensure an availability set does not exist in a resource group.

    :param name:
        Name of the availability set.

    :param resource_group:
        Name of the resource group containing the availability set.

    :param connection_auth:
        A dict with subscription and authentication parameters to be used in connecting to the
        Azure Resource Manager API.
    """
    return __states__["azurerm_compute_availability_set.absent"](
        name=name,
        resource_group=resource_group,
        connection_auth=connection_auth,
    )
