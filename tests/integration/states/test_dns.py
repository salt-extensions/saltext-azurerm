import pytest


@pytest.mark.run(order=3)
def test_zone_present(salt_call_cli, zone, resource_group, connection_auth):
    expected = {
        "__id__": zone,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "name": zone,
                "tags": None,
                "resource_group": resource_group,
                "registration_virtual_networks": None,
                "resolution_virtual_networks": None,
                "zone_type": "Public",
            },
            "old": {},
        },
        "comment": f"DNS zone {zone} has been created.",
        "name": zone,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_dns.zone_present",
        name=zone,
        resource_group=resource_group,
        connection_auth=connection_auth,
    )

    data = list(ret.data.values())[0]
    data["changes"]["new"].pop("etag")
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=3, after="test_zone_present", before="test_zone_absent")
def test_zone_changes(salt_call_cli, zone, resource_group, tags, connection_auth):
    expected = {
        "__id__": zone,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "tags": {"new": tags},
        },
        "comment": f"DNS zone {zone} has been created.",
        "name": zone,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_dns.zone_present",
        name=zone,
        resource_group=resource_group,
        tags=tags,
        connection_auth=connection_auth,
    )

    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=-3)
def test_zone_absent(salt_call_cli, zone, resource_group, connection_auth):
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": zone,
            },
        },
        "comment": f"DNS zone {zone} has been deleted.",
        "name": zone,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_dns.zone_absent",
        name=zone,
        resource_group=resource_group,
        connection_auth=connection_auth,
    )

    data = list(ret.data.values())[0]
    assert data["changes"]["new"] == expected["changes"]["new"]
    assert data["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert data["result"] == expected["result"]
