import pytest

pytestmark = [
    pytest.mark.destructive_test,
]


@pytest.mark.run(order=3)
def test_present(salt_call_cli, vnet, resource_group, location, connection_auth):
    vnet_addr_prefixes = ["10.0.0.0/16"]
    expected = {
        "__id__": vnet,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "name": vnet,
                "address_space": {"address_prefixes": vnet_addr_prefixes},
                "dhcp_options": {"dns_servers": None},
                "enable_ddos_protection": False,
                "enable_vm_protection": False,
                "resource_group": resource_group,
                "tags": None,
            },
            "old": {},
        },
        "comment": f"Virtual network {vnet} has been created.",
        "name": vnet,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.virtual_network_present",
        name=vnet,
        resource_group=resource_group,
        address_prefixes=vnet_addr_prefixes,
        location=location,
        connection_auth=connection_auth,
    )

    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=3, after="test_present", before="test_subnet_present")
def test_changes(salt_call_cli, vnet, resource_group, connection_auth):
    vnet_addr_prefixes = ["10.0.0.0/16"]
    changed_vnet_addr_prefixes = ["10.0.0.0/16", "192.168.0.0/16", "128.0.0.0/16"]
    expected = {
        "__id__": vnet,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "address_space": {
                "address_prefixes": {
                    "new": changed_vnet_addr_prefixes,
                    "old": vnet_addr_prefixes,
                }
            },
            "enable_vm_protection": {"new": None, "old": None},
        },
        "comment": f"Virtual network {vnet} has been created.",
        "name": vnet,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.virtual_network_present",
        name=vnet,
        resource_group=resource_group,
        address_prefixes=changed_vnet_addr_prefixes,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


# Tests the creation of a subnet with service endpoints, a GatewaySubnet, and a AzureBastionSubnet (all are necessary
# for other tests)
@pytest.mark.run(order=3, after="test_changes", before="test_subnet_changes")
def test_subnet_present(salt_call_cli, subnet, vnet, resource_group, connection_auth):
    subnet_addr_prefix = "10.0.0.0/16"
    gateway_snet_addr_prefix = "192.168.0.0/16"
    bastion_snet_addr_prefix = "128.0.0.0/16"
    snet_expected = {
        "__id__": subnet,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "name": subnet,
                "address_prefix": subnet_addr_prefix,
                "network_security_group": None,
                "route_table": None,
            },
            "old": {},
        },
        "comment": f"Subnet {subnet} has been created.",
        "name": subnet,
        "result": True,
    }

    gateway_expected = {
        "__id__": "GatewaySubnet",
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "name": "GatewaySubnet",
                "address_prefix": gateway_snet_addr_prefix,
                "network_security_group": None,
                "route_table": None,
            },
            "old": {},
        },
        "comment": "Subnet GatewaySubnet has been created.",
        "name": "GatewaySubnet",
        "result": True,
    }

    bastion_expected = {
        "__id__": "AzureBastionSubnet",
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "name": "AzureBastionSubnet",
                "address_prefix": bastion_snet_addr_prefix,
                "network_security_group": None,
                "route_table": None,
            },
            "old": {},
        },
        "comment": "Subnet AzureBastionSubnet has been created.",
        "name": "AzureBastionSubnet",
        "result": True,
    }

    # Tests creation of a regular subnet with a service_endpoint
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.subnet_present",
        name=subnet,
        virtual_network=vnet,
        resource_group=resource_group,
        address_prefix=subnet_addr_prefix,
        # Service endpoints used for testing PostgreSQL virtual network rules
        service_endpoints=["Microsoft.Sql"],
        connection_auth=connection_auth,
    )

    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == snet_expected

    # Tests creation of a GatewaySubnet used by a virtual network gateway
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.subnet_present",
        name="GatewaySubnet",
        virtual_network=vnet,
        resource_group=resource_group,
        address_prefix=gateway_snet_addr_prefix,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == gateway_expected

    # Tests creation of an AzureBastionSubnet used by a Bastion Host
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.subnet_present",
        name="AzureBastionSubnet",
        virtual_network=vnet,
        resource_group=resource_group,
        address_prefix=bastion_snet_addr_prefix,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == bastion_expected


@pytest.mark.run(order=3, after="test_subnet_present", before="test_subnet_absent")
def test_subnet_changes(salt_call_cli, subnet, vnet, resource_group, connection_auth):
    subnet_addr_prefix = "10.0.0.0/16"
    changed_subnet_addr_prefix = "10.0.0.0/24"
    expected = {
        "__id__": subnet,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "address_prefix": {
                "new": changed_subnet_addr_prefix,
                "old": subnet_addr_prefix,
            }
        },
        "comment": f"Subnet {subnet} has been created.",
        "name": subnet,
        "result": True,
    }

    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.subnet_present",
        name=subnet,
        virtual_network=vnet,
        resource_group=resource_group,
        address_prefix=changed_subnet_addr_prefix,
        # Service endpoints used for testing PostgreSQL virtual network rules
        service_endpoints=["Microsoft.Sql"],
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=-3, before="test_absent")
def test_subnet_absent(salt_call_cli, subnet, vnet, resource_group, connection_auth):
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": subnet,
            },
        },
        "comment": f"Subnet {subnet} has been deleted.",
        "name": subnet,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.subnet_absent",
        name=subnet,
        virtual_network=vnet,
        resource_group=resource_group,
        connection_auth=connection_auth,
    )

    data = list(ret.data.values())[0]
    assert data["changes"]["new"] == expected["changes"]["new"]
    assert data["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert data["result"] == expected["result"]


@pytest.mark.run(order=-3)
def test_absent(salt_call_cli, vnet, resource_group, connection_auth):
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": vnet,
            },
        },
        "comment": f"Virtual network {vnet} has been deleted.",
        "name": vnet,
        "result": True,
    }

    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.virtual_network_absent",
        name=vnet,
        resource_group=resource_group,
        connection_auth=connection_auth,
    )

    data = list(ret.data.values())[0]
    assert data["changes"]["new"] == expected["changes"]["new"]
    assert data["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert data["result"] == expected["result"]
