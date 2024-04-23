import pytest

pytestmark = [
    pytest.mark.destructive_test,
]


@pytest.mark.run(order=4)
def test_present(salt_call_cli, availability_set, resource_group, connection_auth):
    expected = {
        "__id__": availability_set,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "name": availability_set,
                "sku": {"name": "Classic"},
                "platform_fault_domain_count": None,
                "platform_update_domain_count": None,
                "tags": None,
                "virtual_machines": None,
            },
            "old": {},
        },
        "comment": f"Availability set {availability_set} has been created.",
        "name": availability_set,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_compute_availability_set.present",
        name=availability_set,
        resource_group=resource_group,
        sku="classic",
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=4, after="test_present", before="test_absent")
def test_changes(salt_call_cli, availability_set, resource_group, tags, connection_auth):
    expected = {
        "__id__": availability_set,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {"tags": {"new": tags}},
        "comment": f"Availability set {availability_set} has been created.",
        "name": availability_set,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_compute_availability_set.present",
        name=availability_set,
        resource_group=resource_group,
        tags=tags,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=-4)
def test_absent(salt_call_cli, availability_set, resource_group, connection_auth):
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": availability_set,
            },
        },
        "comment": f"Availability set {availability_set} has been deleted.",
        "name": availability_set,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_compute_availability_set.absent",
        name=availability_set,
        resource_group=resource_group,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    assert data["changes"]["new"] == expected["changes"]["new"]
    assert data["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert data["result"] == expected["result"]
