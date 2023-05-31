import pytest


@pytest.mark.run(order=1)
def test_present(salt_call_cli, resource_group, location, connection_auth):
    expected = {
        "__id__": resource_group,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "location": location,
                "name": resource_group,
                "type": "Microsoft.Resources/resourceGroups",
                "properties": {"provisioning_state": "Succeeded"},
            },
            "old": {},
        },
        "comment": f"Resource group {resource_group} has been created.",
        "name": resource_group,
        "result": True,
    }
    # ret = resource.resource_group_present(resource_group, location, connection_auth=connection_auth)
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_resource.resource_group_present",
        name=resource_group,
        location=location,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data["changes"]["new"].pop("id")
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=1, after="test_present", before="test_absent")
def test_changes(salt_call_cli, resource_group, location, tags, connection_auth):
    expected = {
        "__id__": resource_group,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "location": location,
                "name": resource_group,
                "properties": {"provisioning_state": "Succeeded"},
                "tags": tags,
                "type": "Microsoft.Resources/resourceGroups",
            },
            "old": {},
        },
        "comment": f"Resource group {resource_group} has been created.",
        "name": resource_group,
        "result": True,
    }

    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_resource.resource_group_present",
        name=resource_group,
        location=location,
        connection_auth=connection_auth,
        tags=tags,
    )
    data = list(ret.data.values())[0]
    data["changes"]["new"].pop("id")
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=-1)
def test_absent(salt_call_cli, resource_group, location, tags, connection_auth):
    expected = {
        "__id__": resource_group,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {},
            "old": {
                "location": location,
                "name": resource_group,
                "properties": {"provisioning_state": "Succeeded"},
                "tags": tags,
                "type": "Microsoft.Resources/resourceGroups",
            },
        },
        "comment": f"Resource group {resource_group} has been deleted.",
        "name": resource_group,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_resource.resource_group_absent",
        name=resource_group,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    expected["changes"]["old"]["id"] = data["changes"]["old"]["id"]
    assert data == expected
