import pytest

pytestmark = [
    pytest.mark.destructive_test,
]


@pytest.mark.run(order=1, before="test_changes_remove_tag")
def test_changes_add_tag(salt_call_cli, resource_group, location, tags, connection_auth):
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


@pytest.mark.run(order=1, after="test_changes_add_tag")
def test_changes_remove_tag(salt_call_cli, resource_group, location, connection_auth):
    expected = {
        "__id__": resource_group,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "location": location,
                "name": resource_group,
                "properties": {"provisioning_state": "Succeeded"},
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
        tags=None,  # Set tags to None
    )
    data = list(ret.data.values())[0]
    data["changes"]["new"].pop("id")
    data.pop("duration")
    data.pop("start_time")
    assert data == expected
