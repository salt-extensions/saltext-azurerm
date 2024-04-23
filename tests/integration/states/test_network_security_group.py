import random
import string

import pytest

pytestmark = [
    pytest.mark.destructive_test,
]


@pytest.fixture(scope="session")
def nsg():
    yield "nsg-salt-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def rule():
    yield "nsg-rule-salt-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=3)
def test_present(salt_call_cli, nsg, resource_group, connection_auth):
    expected = {
        "__id__": nsg,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "name": nsg,
                "security_rules": None,
                "resource_group": resource_group,
                "tags": None,
            },
            "old": {},
        },
        "comment": f"Network security group {nsg} has been created.",
        "name": nsg,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.network_security_group_present",
        name=nsg,
        resource_group=resource_group,
        connection_auth=connection_auth,
    )

    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
def test_changes(salt_call_cli, nsg, resource_group, tags, connection_auth):
    expected = {
        "__id__": nsg,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {"tags": {"new": tags}},
        "comment": f"Network security group {nsg} has been created.",
        "name": nsg,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.network_security_group_present",
        name=nsg,
        resource_group=resource_group,
        tags=tags,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=3, after="test_changes", before="test_rule_changes")
def test_rule_present(salt_call_cli, nsg, resource_group, rule, connection_auth):
    expected = {
        "__id__": rule,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "name": rule,
                "priority": 100,
                "protocol": "tcp",
                "access": "allow",
                "direction": "outbound",
                "description": None,
                "source_address_prefix": "virtualnetwork",
                "source_address_prefixes": None,
                "destination_address_prefix": "internet",
                "destination_port_range": "*",
                "destination_port_ranges": None,
                "destination_address_prefixes": None,
                "source_port_range": "*",
                "source_port_ranges": None,
            },
            "old": {},
        },
        "comment": f"Security rule {rule} has been created.",
        "name": rule,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.security_rule_present",
        name=rule,
        security_group=nsg,
        resource_group=resource_group,
        priority=100,
        access="allow",
        protocol="tcp",
        direction="outbound",
        source_address_prefix="virtualnetwork",
        destination_address_prefix="internet",
        source_port_range="*",
        destination_port_range="*",
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=3, after="test_rule_present", before="test_rule_absent")
def test_rule_changes(salt_call_cli, nsg, resource_group, rule, connection_auth):
    expected = {
        "__id__": rule,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {"priority": {"new": 101, "old": 100}},
        "comment": f"Security rule {rule} has been created.",
        "name": rule,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.security_rule_present",
        name=rule,
        security_group=nsg,
        resource_group=resource_group,
        priority=101,
        access="allow",
        protocol="tcp",
        direction="outbound",
        source_address_prefix="virtualnetwork",
        destination_address_prefix="internet",
        source_port_range="*",
        destination_port_range="*",
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=-3, after="test_rule_changes", before="test_absent")
def test_rule_absent(salt_call_cli, nsg, resource_group, rule, connection_auth):
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": rule,
            },
        },
        "comment": f"Security rule {rule} has been deleted.",
        "name": rule,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.security_rule_absent",
        name=rule,
        security_group=nsg,
        resource_group=resource_group,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    assert data["changes"]["new"] == expected["changes"]["new"]
    assert data["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert data["result"] == expected["result"]


@pytest.mark.run(order=-3, after="test_rule_absent")
def test_absent(salt_call_cli, nsg, resource_group, connection_auth):
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": nsg,
            },
        },
        "comment": f"Network security group {nsg} has been deleted.",
        "name": nsg,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_network.network_security_group_absent",
        name=nsg,
        resource_group=resource_group,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    assert data["changes"]["new"] == expected["changes"]["new"]
    assert data["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert data["result"] == expected["result"]
