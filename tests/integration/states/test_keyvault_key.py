import random
import string

import pytest

pytestmark = [
    pytest.mark.destructive_test,
]


@pytest.fixture(scope="session")
def key():
    yield "key-salt-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=4)
def test_present(salt_call_cli, key, keyvault, connection_auth):
    key_type = "RSA"
    vault_url = f"https://{keyvault}.vault.azure.net"
    expected = {
        "__id__": key,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "name": key,
                "key_type": key_type,
                "key_operations": [
                    "encrypt",
                    "decrypt",
                    "sign",
                    "verify",
                    "wrapKey",
                    "unwrapKey",
                ],
                "properties": {
                    "enabled": False,
                    "expires_on": None,
                    "managed": None,
                    "name": key,
                    "not_before": None,
                    "recovery_level": "Purgeable",
                    "tags": None,
                    "vault_url": vault_url,
                },
            },
            "old": {},
        },
        "comment": f"Key {key} has been created.",
        "name": key,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_keyvault_key.present",
        name=key,
        key_type=key_type,
        vault_url=vault_url,
        enabled=False,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data["changes"]["new"].pop("id")
    data["changes"]["new"]["properties"].pop("id")
    data["changes"]["new"]["properties"].pop("updated_on")
    data["changes"]["new"]["properties"].pop("created_on")
    data["changes"]["new"]["properties"].pop("version")
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=4, after="test_present", before="test_absent")
def test_changes(salt_call_cli, key, keyvault, connection_auth):
    key_type = "RSA"
    vault_url = f"https://{keyvault}.vault.azure.net/"
    expected = {
        "__id__": key,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {"enabled": {"new": True, "old": False}},
        "comment": f"Key {key} has been updated.",
        "name": key,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_keyvault_key.present",
        name=key,
        key_type=key_type,
        vault_url=vault_url,
        enabled=True,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=-4)
def test_absent(salt_call_cli, key, keyvault, connection_auth):
    vault_url = f"https://{keyvault}.vault.azure.net/"
    expected = {
        "changes": {"new": {}, "old": {"name": key}},
        "comment": f"Key {key} has been deleted.",
        "name": key,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_keyvault_key.absent",
        name=key,
        vault_url=vault_url,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    assert data["changes"]["new"] == expected["changes"]["new"]
    assert data["changes"]["old"]["name"] == expected["changes"]["old"]["name"]
    assert data["result"] == expected["result"]
