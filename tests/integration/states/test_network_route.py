import pytest

pytestmark = [
    pytest.mark.destructive_test,
]


@pytest.mark.run(order=3)
def test_table_present(salt_call_cli, route_table, resource_group, connection_auth):
    expected = {
        "__id__": route_table,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "name": route_table,
                "routes": None,
                "disable_bgp_route_propagation": None,
                "tags": None,
            },
            "old": {},
        },
        "comment": f"Route table {route_table} has been created.",
        "name": route_table,
        "result": True,
    }

    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.route_table_present",
        name=route_table,
        resource_group=resource_group,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=3, after="test_table_present", before="test_present")
def test_table_changes(salt_call_cli, route_table, resource_group, tags, connection_auth):
    new_routes = [
        {
            "name": "test_route1",
            "address_prefix": "0.0.0.0/0",
            "next_hop_type": "internet",
        }
    ]

    expected = {
        "__id__": route_table,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {"routes": {"new": new_routes, "old": []}, "tags": {"new": tags}},
        "comment": f"Route table {route_table} has been created.",
        "name": route_table,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.route_table_present",
        name=route_table,
        resource_group=resource_group,
        routes=new_routes,
        tags=tags,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=3, after="test_table_changes", before="test_changes")
def test_present(salt_call_cli, route, route_table, resource_group, connection_auth):
    next_hop_type = "vnetlocal"
    addr_prefix = "192.168.0.0/16"
    expected = {
        "__id__": route,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "name": route,
                "address_prefix": addr_prefix,
                "next_hop_ip_address": None,
                "next_hop_type": "vnetlocal",
            },
            "old": {},
        },
        "comment": f"Route {route} has been created.",
        "name": route,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.route_present",
        name=route,
        route_table=route_table,
        resource_group=resource_group,
        address_prefix=addr_prefix,
        next_hop_type=next_hop_type,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
def test_changes(salt_call_cli, route, route_table, resource_group, connection_auth):
    next_hop_type = "vnetlocal"
    addr_prefix = "192.168.0.0/16"
    changed_addr_prefix = "192.168.0.0/24"
    expected = {
        "__id__": route,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {"address_prefix": {"new": changed_addr_prefix, "old": addr_prefix}},
        "comment": f"Route {route} has been created.",
        "name": route,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.route_present",
        name=route,
        route_table=route_table,
        resource_group=resource_group,
        address_prefix=changed_addr_prefix,
        next_hop_type=next_hop_type,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=3, after="test_table_changes", before="test_table_absent")
def test_absent(salt_call_cli, route, route_table, resource_group, connection_auth):
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": route,
            },
        },
        "comment": f"Route {route} has been deleted.",
        "name": route,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.route_absent",
        name=route,
        route_table=route_table,
        resource_group=resource_group,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    assert data["changes"]["new"] == expected["changes"]["new"]
    assert data["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert data["result"] == expected["result"]


@pytest.mark.run(order=-3)
def test_table_absent(salt_call_cli, route_table, resource_group, connection_auth):
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": route_table,
            },
        },
        "comment": f"Route table {route_table} has been deleted.",
        "name": route_table,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.route_table_absent",
        name=route_table,
        resource_group=resource_group,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    assert data["changes"]["new"] == expected["changes"]["new"]
    assert data["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert data["result"] == expected["result"]
