import pytest

pytestmark = [
    pytest.mark.destructive_test,
]


@pytest.mark.run(order=3)
# Creates a public IP address with a "Standard" SKU for Bastion Host tests and another one with a "Basic" SKU
# for the virtual network gateway tests
def test_present(salt_call_cli, public_ip_addr, public_ip_addr2, resource_group, connection_auth):
    idle_timeout = 10
    standard_expected = {
        "__id__": public_ip_addr,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "name": public_ip_addr,
                "dns_settings": None,
                "sku": {"name": "Standard"},
                "public_ip_allocation_method": "Static",
                "public_ip_address_version": "IPv4",
                "idle_timeout_in_minutes": idle_timeout,
                "tags": None,
            },
            "old": {},
        },
        "comment": f"Public IP address {public_ip_addr} has been created.",
        "name": public_ip_addr,
        "result": True,
    }

    basic_expected = {
        "__id__": public_ip_addr2,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "name": public_ip_addr2,
                "dns_settings": None,
                "sku": {"name": "Basic"},
                "public_ip_allocation_method": "Dynamic",
                "public_ip_address_version": "IPv4",
                "idle_timeout_in_minutes": idle_timeout,
                "tags": None,
            },
            "old": {},
        },
        "comment": f"Public IP address {public_ip_addr2} has been created.",
        "name": public_ip_addr2,
        "result": True,
    }

    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.public_ip_address_present",
        name=public_ip_addr,
        resource_group=resource_group,
        public_ip_allocation_method="Static",
        public_ip_address_version="IPv4",
        sku="Standard",
        idle_timeout_in_minutes=idle_timeout,
        connection_auth=connection_auth,
    )

    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == standard_expected

    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.public_ip_address_present",
        name=public_ip_addr2,
        resource_group=resource_group,
        sku="Basic",
        public_ip_allocation_method="Dynamic",
        public_ip_address_version="IPv4",
        idle_timeout_in_minutes=idle_timeout,
        connection_auth=connection_auth,
    )

    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == basic_expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
def test_changes(salt_call_cli, public_ip_addr, resource_group, tags, connection_auth):
    idle_timeout = 10
    new_timeout = 4
    expected = {
        "__id__": public_ip_addr,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "idle_timeout_in_minutes": {"new": new_timeout, "old": idle_timeout},
            "tags": {"new": tags},
            "sku": {"old": {"tier": "Regional"}},
        },
        "comment": f"Public IP address {public_ip_addr} has been created.",
        "name": public_ip_addr,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.public_ip_address_present",
        name=public_ip_addr,
        resource_group=resource_group,
        sku="Standard",
        public_ip_allocation_method="Static",
        idle_timeout_in_minutes=new_timeout,
        tags=tags,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=-3)
def test_absent(salt_call_cli, public_ip_addr, resource_group, connection_auth):
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": public_ip_addr,
            },
        },
        "comment": f"Public IP address {public_ip_addr} has been deleted.",
        "name": public_ip_addr,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.public_ip_address_absent",
        name=public_ip_addr,
        resource_group=resource_group,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    assert data["changes"]["new"] == expected["changes"]["new"]
    assert data["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert data["result"] == expected["result"]


@pytest.mark.run(order=-3)
def test_absent_second_ip(salt_call_cli, public_ip_addr2, resource_group, connection_auth):
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": public_ip_addr2,
            },
        },
        "comment": f"Public IP address {public_ip_addr2} has been deleted.",
        "name": public_ip_addr2,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.public_ip_address_absent",
        name=public_ip_addr2,
        resource_group=resource_group,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    assert data["changes"]["new"] == expected["changes"]["new"]
    assert data["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert data["result"] == expected["result"]
