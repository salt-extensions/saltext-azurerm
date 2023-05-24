import pytest


@pytest.mark.run(order=3)
def test_present(salt_call_cli, vnet, resource_group, location, connection_auth):
    vnet_addr_prefixes = ["10.0.0.0/16"]
    expected = {
        "changes": {
            "new": {
                "name": vnet,
                "address_space": {"address_prefixes": vnet_addr_prefixes},
                "dhcp_options": {"dns_servers": []},
                "location": location,
                "enable_ddos_protection": False,
                # "enable_vm_protection": False, # Not usable until next version bump
                "subnets": [],
                "virtual_network_peerings": [],
                "type": "Microsoft.Network/virtualNetworks",
                "provisioning_state": "Succeeded",
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
    ret["changes"]["new"].pop("id")
    ret["changes"]["new"].pop("etag")
    ret["changes"]["new"].pop("resource_guid")
    assert ret == expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
def test_changes(salt_call_cli, vnet, resource_group, connection_auth):
    vnet_addr_prefixes = ["10.0.0.0/16"]
    changed_vnet_addr_prefixes = ["10.0.0.0/16", "192.168.0.0/16", "128.0.0.0/16"]
    expected = {
        "changes": {
            "address_space": {
                "address_prefixes": {
                    "new": changed_vnet_addr_prefixes,
                    "old": vnet_addr_prefixes,
                }
            }
        },
        "comment": f"Virtual network {vnet} has been updated.",
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

    assert ret == expected


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

    assert ret["changes"]["new"] == expected["changes"]["new"]
    assert ret["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert ret["result"] == expected["result"]
