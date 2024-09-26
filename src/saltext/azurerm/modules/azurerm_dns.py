"""
Azure Resource Manager DNS Execution Module

.. versionadded:: 3000

:maintainer: <devops@eitr.tech>
:maturity: new
:platform: linux
:configuration:
    This module requires Azure Resource Manager credentials to be passed as keyword arguments
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

import saltext.azurerm.utils.azurerm

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.dns.models  # pylint: disable=unused-import
    import azure.mgmt.privatedns.models  # pylint: disable=unused-import
    from azure.core.exceptions import HttpResponseError
    from azure.core.exceptions import ResourceNotFoundError
    from azure.core.exceptions import SerializationError

    HAS_LIBS = True
except ImportError:
    pass

__virtualname__ = "azurerm_dns"

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


def record_set_create_or_update(
    name, zone_name, resource_group, record_type, zone_type="Public", **kwargs
):
    """
    .. versionadded:: 3000

    Creates or updates a record set within a DNS zone.

    :param name: The name of the record set, relative to the name of the zone.

    :param zone_name: The name of the DNS zone (without a terminating dot).

    :param resource_group: The name of the resource group.

    :param record_type:
        The type of DNS record in this record set. Record sets of type SOA can be
        updated but not created (they are created when the DNS zone is created).
        Possible values include: 'A', 'AAAA', 'CAA', 'CNAME', 'MX', 'NS', 'PTR', 'SOA', 'SRV', 'TXT'

    :param zone_type: The type of DNS zone (set default to Public)

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_dns.record_set_create_or_update myhost myzone testgroup A
            arecords='[{ipv4_address: 10.0.0.1}]' ttl=300

    """

    client = "dns"
    if zone_type.lower() == "private":
        client = "privatedns"

    dnsconn = saltext.azurerm.utils.azurerm.get_client(client, **kwargs)

    try:
        record_set_model = saltext.azurerm.utils.azurerm.create_object_model(
            "dns", "RecordSet", **kwargs
        )
    except TypeError as exc:
        result = {"error": f"The object model could not be built. ({str(exc)})"}
        return result

    try:
        if zone_type.lower() == "private":
            record_set = dnsconn.record_sets.create_or_update(
                relative_record_set_name=name,
                private_zone_name=zone_name,
                resource_group_name=resource_group,
                record_type=record_type,
                parameters=record_set_model,
                if_match=kwargs.get("if_match"),
                if_none_match=kwargs.get("if_none_match"),
            )
        else:
            record_set = dnsconn.record_sets.create_or_update(
                relative_record_set_name=name,
                zone_name=zone_name,
                resource_group_name=resource_group,
                record_type=record_type,
                parameters=record_set_model,
                if_match=kwargs.get("if_match"),
                if_none_match=kwargs.get("if_none_match"),
            )
        result = record_set.as_dict()
    except (HttpResponseError, ResourceNotFoundError) as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("dns", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {"error": f"The object model could not be parsed. ({str(exc)})"}

    return result


def record_set_delete(name, zone_name, resource_group, record_type, zone_type="Public", **kwargs):
    """
    .. versionadded:: 3000

    Deletes a record set from a DNS zone. This operation cannot be undone.

    :param name: The name of the record set, relative to the name of the zone.

    :param zone_name: The name of the DNS zone (without a terminating dot).

    :param resource_group: The name of the resource group.

    :param record_type:
        The type of DNS record in this record set. Record sets of type SOA cannot be
        deleted (they are deleted when the DNS zone is deleted).
        Possible values include: 'A', 'AAAA', 'CAA', 'CNAME', 'MX', 'NS', 'PTR', 'SOA', 'SRV', 'TXT'

    :param zone_type: The type of DNS zone (set default to Public)

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_dns.record_set_delete myhost myzone testgroup A

    """
    result = False

    client = "dns"
    if zone_type.lower() == "private":
        client = "privatedns"

    dnsconn = saltext.azurerm.utils.azurerm.get_client(client, **kwargs)
    try:
        if zone_type.lower() == "private":
            dnsconn.record_sets.delete(
                relative_record_set_name=name,
                private_zone_name=zone_name,
                resource_group_name=resource_group,
                record_type=record_type,
                if_match=kwargs.get("if_match"),
            )
        else:
            dnsconn.record_sets.delete(
                relative_record_set_name=name,
                zone_name=zone_name,
                resource_group_name=resource_group,
                record_type=record_type,
                if_match=kwargs.get("if_match"),
            )
        result = True
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("dns", str(exc), **kwargs)

    return result


def record_set_get(name, zone_name, resource_group, record_type, zone_type="Public", **kwargs):
    """
    .. versionadded:: 3000

    Get a dictionary representing a record set's properties.

    :param name: The name of the record set, relative to the name of the zone.

    :param zone_name: The name of the DNS zone (without a terminating dot).

    :param resource_group: The name of the resource group.

    :param record_type:
        The type of DNS record in this record set.
        Possible values include: 'A', 'AAAA', 'CAA', 'CNAME', 'MX', 'NS', 'PTR', 'SOA', 'SRV', 'TXT'

    :param zone_type: The type of DNS zone (set default to Public)

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_dns.record_set_get '@' myzone testgroup SOA

    """

    client = "dns"
    if zone_type.lower() == "private":
        client = "privatedns"

    dnsconn = saltext.azurerm.utils.azurerm.get_client(client, **kwargs)
    try:
        if zone_type.lower() == "private":
            record_set = dnsconn.record_sets.get(
                relative_record_set_name=name,
                private_zone_name=zone_name,
                resource_group_name=resource_group,
                record_type=record_type,
            )
        else:
            record_set = dnsconn.record_sets.get(
                relative_record_set_name=name,
                zone_name=zone_name,
                resource_group_name=resource_group,
                record_type=record_type,
            )
        result = record_set.as_dict()
    except (ResourceNotFoundError, HttpResponseError) as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error(client, str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def record_sets_list_by_type(
    zone_name,
    resource_group,
    record_type,
    top=None,
    recordsetnamesuffix=None,
    zone_type="Public",
    **kwargs,
):
    """
    .. versionadded:: 3000

    Lists the record sets of a specified type in a DNS zone.

    :param zone_name: The name of the DNS zone (without a terminating dot).

    :param resource_group: The name of the resource group.

    :param record_type:
        The type of record sets to enumerate.
        Possible values include: 'A', 'AAAA', 'CAA', 'CNAME', 'MX', 'NS', 'PTR', 'SOA', 'SRV', 'TXT'

    :param top:
        The maximum number of record sets to return. If not specified,
        returns up to 100 record sets.

    :param recordsetnamesuffix:
        The suffix label of the record set name that has
        to be used to filter the record set enumerations.

    :param zone_type: The type of DNS zone (set default to Public)

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_dns.record_sets_list_by_type myzone testgroup SOA

    """
    result = {}

    client = "dns"
    if zone_type.lower() == "private":
        client = "privatedns"

    dnsconn = saltext.azurerm.utils.azurerm.get_client(client, **kwargs)
    try:
        if zone_type.lower() == "private":
            record_sets = saltext.azurerm.utils.azurerm.paged_object_to_list(
                dnsconn.record_sets.list_by_type(
                    private_zone_name=zone_name,
                    resource_group_name=resource_group,
                    record_type=record_type,
                    top=top,
                    recordsetnamesuffix=recordsetnamesuffix,
                )
            )
        else:
            record_sets = saltext.azurerm.utils.azurerm.paged_object_to_list(
                dnsconn.record_sets.list_by_type(
                    zone_name=zone_name,
                    resource_group_name=resource_group,
                    record_type=record_type,
                    top=top,
                    recordsetnamesuffix=recordsetnamesuffix,
                )
            )
        for record_set in record_sets:
            result[record_set["name"]] = record_set
    except (ResourceNotFoundError, HttpResponseError) as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("dns", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def record_sets_list_by_dns_zone(
    zone_name, resource_group, top=None, recordsetnamesuffix=None, zone_type="Public", **kwargs
):
    """
    .. versionadded:: 3000

    Lists all record sets in a DNS zone.

    :param zone_name: The name of the DNS zone (without a terminating dot).

    :param resource_group: The name of the resource group.

    :param top:
        The maximum number of record sets to return. If not specified,
        returns up to 100 record sets.

    :param recordsetnamesuffix:
        The suffix label of the record set name that has
        to be used to filter the record set enumerations.

    :param zone_type: The type of DNS zone (set default to Public)

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_dns.record_sets_list_by_dns_zone myzone testgroup

    """
    result = {}

    client = "dns"
    if zone_type.lower() == "private":
        client = "privatedns"

    dnsconn = saltext.azurerm.utils.azurerm.get_client(client, **kwargs)
    try:
        if zone_type.lower() == "private":
            record_sets = saltext.azurerm.utils.azurerm.paged_object_to_list(
                dnsconn.record_sets.list(
                    private_zone_name=zone_name,
                    resource_group_name=resource_group,
                    top=top,
                    recordsetnamesuffix=recordsetnamesuffix,
                )
            )
        else:
            record_sets = saltext.azurerm.utils.azurerm.paged_object_to_list(
                dnsconn.record_sets.list_by_dns_zone(
                    zone_name=zone_name,
                    resource_group_name=resource_group,
                    top=top,
                    recordsetnamesuffix=recordsetnamesuffix,
                )
            )

        for record_set in record_sets:
            result[record_set["name"]] = record_set
    except (ResourceNotFoundError, HttpResponseError) as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("dns", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def zone_create_or_update(name, resource_group, zone_type="Public", **kwargs):
    """
    .. versionadded:: 3000

    Creates or updates a DNS zone. Does not modify DNS records within the zone.

    :param name: The name of the DNS zone to create (without a terminating dot).

    :param resource_group: The name of the resource group.

    :param zone_type: The type of DNS zone (set default to Public)

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_dns.zone_create_or_update myzone testgroup

    """
    # DNS zones are global objects
    kwargs["location"] = "global"

    client = "dns"
    obj = "Zone"
    if zone_type.lower() == "private":
        client = "privatedns"
        obj = "PrivateZone"

    dnsconn = saltext.azurerm.utils.azurerm.get_client(client, **kwargs)

    # Convert list of ID strings to list of dictionaries with id key.
    if isinstance(kwargs.get("registration_virtual_networks"), list):
        kwargs["registration_virtual_networks"] = [
            {"id": vnet} for vnet in kwargs["registration_virtual_networks"]
        ]

    if isinstance(kwargs.get("resolution_virtual_networks"), list):
        kwargs["resolution_virtual_networks"] = [
            {"id": vnet} for vnet in kwargs["resolution_virtual_networks"]
        ]

    try:
        zone_model = saltext.azurerm.utils.azurerm.create_object_model(client, obj, **kwargs)
    except TypeError as exc:
        result = {"error": f"The object model could not be built. ({str(exc)})"}
        return result

    try:
        if zone_type.lower() == "private":
            zone = dnsconn.private_zones.begin_create_or_update(
                private_zone_name=name,
                resource_group_name=resource_group,
                parameters=zone_model,
                if_match=kwargs.get("if_match"),
                if_none_match=kwargs.get("if_none_match"),
                polling=True,
            )
            zone.wait()
            zone_result = zone.result()
            result = zone_result.as_dict()
        else:
            zone = dnsconn.zones.create_or_update(
                zone_name=name,
                resource_group_name=resource_group,
                parameters=zone_model,
                if_match=kwargs.get("if_match"),
                if_none_match=kwargs.get("if_none_match"),
            )
            result = zone.as_dict()
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("dns", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {"error": f"The object model could not be parsed. ({str(exc)})"}

    return result


def zone_delete(name, resource_group, zone_type="Public", **kwargs):
    """
    .. versionadded:: 3000

    Delete a DNS zone within a resource group.

    :param name: The name of the DNS zone to delete.

    :param resource_group: The name of the resource group.

    :param zone_type: The type of DNS zone (set default to Public)

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_dns.zone_delete myzone testgroup

    """
    result = False

    client = "dns"
    if zone_type.lower() == "private":
        client = "privatedns"

    dnsconn = saltext.azurerm.utils.azurerm.get_client(client, **kwargs)
    try:
        if zone_type.lower() == "private":
            zone = dnsconn.private_zones.begin_delete(
                private_zone_name=name,
                resource_group_name=resource_group,
                if_match=kwargs.get("if_match"),
                polling=True,
            )
        else:
            zone = dnsconn.zones.begin_delete(
                zone_name=name,
                resource_group_name=resource_group,
                if_match=kwargs.get("if_match"),
            )
        zone.wait()
        result = True
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("dns", str(exc), **kwargs)

    return result


def zone_get(name, resource_group, zone_type="Public", **kwargs):
    """
    .. versionadded:: 3000

    Get a dictionary representing a DNS zone's properties, but not the
    record sets within the zone.

    :param name: The DNS zone to get.

    :param resource_group: The name of the resource group.

    :param zone_type: The type of DNS zone (set default to Public)

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_dns.zone_get myzone testgroup

    """
    client = "dns"
    if zone_type.lower() == "private":
        client = "privatedns"

    dnsconn = saltext.azurerm.utils.azurerm.get_client(client, **kwargs)
    try:
        if zone_type.lower() == "private":
            zone = dnsconn.private_zones.get(
                private_zone_name=name, resource_group_name=resource_group
            )
            result = zone.as_dict()
        else:
            zone = dnsconn.zones.get(zone_name=name, resource_group_name=resource_group)
            result = zone.as_dict()

    except (ResourceNotFoundError, HttpResponseError) as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("dns", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def zones_list_by_resource_group(resource_group, zone_type="Public", top=None, **kwargs):
    """
    .. versionadded:: 3000

    Lists the DNS zones in a resource group.

    :param resource_group: The name of the resource group.

    :param zone_type: The type of DNS zone (set default to Public)

    :param top:
        The maximum number of DNS zones to return. If not specified,
        returns up to 100 zones.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_dns.zones_list_by_resource_group testgroup

    """
    result = {}

    client = "dns"
    if zone_type.lower() == "private":
        client = "privatedns"

    dnsconn = saltext.azurerm.utils.azurerm.get_client(client, **kwargs)
    try:
        if zone_type.lower() == "private":
            zones = saltext.azurerm.utils.azurerm.paged_object_to_list(
                dnsconn.private_zones.list_by_resource_group(
                    resource_group_name=resource_group, top=top
                )
            )
        else:
            zones = saltext.azurerm.utils.azurerm.paged_object_to_list(
                dnsconn.zones.list_by_resource_group(resource_group_name=resource_group, top=top)
            )

        for zone in zones:
            result[zone["name"]] = zone
    except (ResourceNotFoundError, HttpResponseError) as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("dns", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def zones_list(top=None, zone_type="Public", **kwargs):
    """
    .. versionadded:: 3000

    Lists the DNS zones in all resource groups in a subscription.

    :param top:
        The maximum number of DNS zones to return. If not specified,
        eturns up to 100 zones.

    :param zone_type: The type of DNS zone (set default to Public)

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_dns.zones_list

    """
    result = {}

    client = "dns"
    if zone_type.lower() == "private":
        client = "privatedns"

    dnsconn = saltext.azurerm.utils.azurerm.get_client(client, **kwargs)
    try:
        if zone_type.lower() == "private":
            zones = saltext.azurerm.utils.azurerm.paged_object_to_list(
                dnsconn.private_zones.list(top=top)
            )
        else:
            zones = saltext.azurerm.utils.azurerm.paged_object_to_list(dnsconn.zones.list(top=top))

        for zone in zones:
            result[zone["name"]] = zone
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("dns", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
