import pytest

pytestmark = [
    pytest.mark.destructive_test,
]


@pytest.mark.run(order=4)
def test_present(
    salt_call_cli, network_interface, subnet, vnet, resource_group, ip_config, connection_auth
):
    expected = {
        "__id__": network_interface,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "dns_settings": None,
                "name": network_interface,
                "ip_configurations": [
                    {
                        "name": ip_config,
                    }
                ],
                "mac_address": None,
                "enable_accelerated_networking": None,
                "enable_ip_forwarding": None,
                "network_security_group": None,
                "tags": None,
                "primary": None,
                "virtual_machine": None,
            },
            "old": {},
        },
        "comment": f"Network interface {network_interface} has been created.",
        "name": network_interface,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.network_interface_present",
        name=network_interface,
        subnet=subnet,
        virtual_network=vnet,
        resource_group=resource_group,
        ip_configurations=[{"name": ip_config}],
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data["changes"]["new"]["ip_configurations"][0].pop("subnet")
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=4, after="test_present", before="test_absent")
def test_changes(
    salt_call_cli, network_interface, subnet, vnet, resource_group, ip_config, tags, connection_auth
):
    expected = {
        "__id__": network_interface,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {"tags": {"new": tags}},
        "comment": f"Network interface {network_interface} has been created.",
        "name": network_interface,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.network_interface_present",
        name=network_interface,
        subnet=subnet,
        virtual_network=vnet,
        resource_group=resource_group,
        ip_configurations=[{"name": ip_config}],
        tags=tags,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=-4)
def test_absent(salt_call_cli, network_interface, resource_group, connection_auth):
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": network_interface,
            },
        },
        "comment": f"Network interface {network_interface} has been deleted.",
        "name": network_interface,
        "result": True,
    }

    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.network_interface_absent",
        name=network_interface,
        resource_group=resource_group,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    assert data["changes"]["new"] == expected["changes"]["new"]
    assert data["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert data["result"] == expected["result"]
