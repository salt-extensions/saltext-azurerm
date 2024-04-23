import random
import string

import pytest

pytestmark = [
    pytest.mark.destructive_test,
]


@pytest.fixture(scope="session")
def password():
    yield "#PASS" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(16)
    ) + "!"


@pytest.mark.run(order=5)
def test_present(salt_call_cli, virt_mach, resource_group, vnet, subnet, password, connection_auth):
    vm_size = "Standard_B4ms"
    windows_image = "MicrosoftWindowsServer|WindowsServer|2019-Datacenter|latest"

    image_info = windows_image.split("|")
    expected = {
        "changes": {
            "new": {
                "name": virt_mach,
                "hardware_profile": {"vm_size": vm_size},
                "storage_profile": {
                    "image_reference": {
                        "publisher": image_info[0],
                        "offer": image_info[1],
                        "sku": image_info[2],
                        "version": image_info[3],
                    },
                    "os_disk": {"disk_size_gb": 128},
                },
            },
            "old": {},
        },
        "comment": f"Virtual machine {virt_mach} has been created.",
        "name": virt_mach,
        "result": True,
    }

    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_compute_virtual_machine.present",
        name=virt_mach,
        resource_group=resource_group,
        vm_size=vm_size,
        image=windows_image,
        os_disk_size_gb=128,
        virtual_network=vnet,
        subnet=subnet,
        admin_password=password,
        connection_auth=connection_auth,
    )

    data = list(ret.data.values())[0]
    data["changes"]["new"]["storage_profile"]["image_reference"].pop("exact_version")
    assert data["changes"]["new"]["name"] == expected["changes"]["new"]["name"]
    assert (
        data["changes"]["new"]["hardware_profile"] == expected["changes"]["new"]["hardware_profile"]
    )
    assert (
        data["changes"]["new"]["storage_profile"]["image_reference"]
        == expected["changes"]["new"]["storage_profile"]["image_reference"]
    )
    assert (
        data["changes"]["new"]["storage_profile"]["os_disk"]["disk_size_gb"]
        == expected["changes"]["new"]["storage_profile"]["os_disk"]["disk_size_gb"]
    )


@pytest.mark.run(order=5, after="test_present", before="test_absent")
def test_changes(
    salt_call_cli, virt_mach, resource_group, vnet, subnet, password, tags, connection_auth
):
    vm_size = "Standard_B4ms"
    windows_image = "MicrosoftWindowsServer|WindowsServer|2019-Datacenter|latest"

    expected = {
        "__id__": virt_mach,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {"admin_password": {"new": "REDACTED"}, "tags": {"new": tags}},
        "comment": f"Virtual machine {virt_mach} has been updated.",
        "name": virt_mach,
        "result": True,
    }

    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_compute_virtual_machine.present",
        name=virt_mach,
        resource_group=resource_group,
        vm_size=vm_size,
        image=windows_image,
        os_disk_size_gb=128,
        virtual_network=vnet,
        subnet=subnet,
        admin_password=password,
        tags=tags,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=-5)
def test_absent(salt_call_cli, virt_mach, resource_group, connection_auth):
    expected = {
        "changes": {
            "new": {},
            "old": {
                "name": virt_mach,
            },
        },
        "comment": f"Virtual machine {virt_mach} has been deleted.",
        "name": virt_mach,
        "result": True,
    }

    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_compute_virtual_machine.absent",
        name=virt_mach,
        resource_group=resource_group,
        cleanup_osdisks=True,
        cleanup_datadisks=True,
        cleanup_interfaces=True,
        cleanup_public_ips=True,
        connection_auth=connection_auth,
    )

    data = list(ret.data.values())[0]
    assert data["changes"]["new"] == expected["changes"]["new"]
    assert data["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert data["result"] == expected["result"]
