import random
import string

import pytest

pytestmark = [
    pytest.mark.destructive_test,
]


@pytest.fixture(scope="session")
def secret():
    yield "secret-salt-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.mark.run(order=4)
def test_present(salt_call_cli, secret, keyvault, connection_auth):
    expected = {
        "__id__": secret,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "name": secret,
                "properties": {
                    "content_type": None,
                    "enabled": True,
                    "expires_on": None,
                    "key_id": None,
                    "name": secret,
                    "not_before": None,
                    "recovery_level": "Purgeable",
                    "tags": None,
                    "vault_url": f"https://{keyvault}.vault.azure.net",
                },
                "value": "REDACTED",
            },
            "old": {},
        },
        "comment": f"Secret {secret} has been created.",
        "name": secret,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_keyvault_secret.present",
        name=secret,
        value="supersecret",
        vault_url=f"https://{keyvault}.vault.azure.net/",
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data["changes"]["new"].pop("id")
    data["changes"]["new"]["properties"].pop("created_on")
    data["changes"]["new"]["properties"].pop("updated_on")
    data["changes"]["new"]["properties"].pop("id")
    data["changes"]["new"]["properties"].pop("version")
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=4, after="test_present", before="test_absent")
def test_changes(salt_call_cli, secret, keyvault, tags, connection_auth):
    expected = {
        "__id__": secret,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "tags": {
                "new": tags,
            },
            "content_type": {"new": "text/plain", "old": None},
        },
        "comment": f"Secret {secret} has been updated.",
        "name": secret,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_keyvault_secret.present",
        name=secret,
        value="supersecret",
        vault_url=f"https://{keyvault}.vault.azure.net/",
        content_type="text/plain",
        tags=tags,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=-4)
def test_absent(salt_call_cli, secret, keyvault, tags, connection_auth):
    expected = {
        "__id__": secret,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {},
            "old": {
                "name": secret,
                "properties": {
                    "name": secret,
                    "content_type": "text/plain",
                    "enabled": True,
                    "expires_on": None,
                    "not_before": None,
                    "key_id": None,
                    "recovery_level": "Purgeable",
                    "vault_url": f"https://{keyvault}.vault.azure.net",
                    "tags": tags,
                },
                "value": "supersecret",
            },
        },
        "comment": f"Secret {secret} has been deleted.",
        "name": secret,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_keyvault_secret.absent",
        name=secret,
        vault_url=f"https://{keyvault}.vault.azure.net/",
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data["changes"]["old"].pop("id")
    data["changes"]["old"]["properties"].pop("created_on")
    data["changes"]["old"]["properties"].pop("updated_on")
    data["changes"]["old"]["properties"].pop("id")
    data["changes"]["old"]["properties"].pop("version")
    data.pop("duration")
    data.pop("start_time")
    assert data == expected
