import time

import pytest

pytestmark = [
    pytest.mark.destructive_test,
]


@pytest.mark.run(order=3)
def test_present(
    salt_call_cli,
    resource_group,
    location,
    keyvault,
    first_subscription,
    tenant_id,
    object_id,
    connection_auth,
):
    subscription_id = first_subscription
    sku = "standard"
    access_policies = [
        {
            "tenant_id": tenant_id,
            "object_id": object_id,
            "permissions": {
                "keys": [
                    "Get",
                    "List",
                    "Update",
                    "Create",
                    "Import",
                    "Delete",
                    "Recover",
                    "Backup",
                    "Restore",
                    "UnwrapKey",
                    "WrapKey",
                    "Verify",
                    "Sign",
                    "Encrypt",
                    "Decrypt",
                ],
                "secrets": [
                    "Get",
                    "List",
                    "Set",
                    "Delete",
                    "Recover",
                    "Backup",
                    "Restore",
                ],
            },
        }
    ]
    expected = {
        "__id__": keyvault,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {
                "id": f"/subscriptions/{subscription_id}/resourceGroups/"
                + f"{resource_group}/providers/Microsoft.KeyVault/vaults/{keyvault}",
                "location": location,
                "name": keyvault,
                "properties": {
                    "access_policies": access_policies,
                    "enable_rbac_authorization": False,
                    "enable_soft_delete": False,
                    "enabled_for_deployment": False,
                    "provisioning_state": "Succeeded",
                    "public_network_access": "Enabled",
                    "tenant_id": tenant_id,
                    "sku": {"name": sku, "family": "A"},
                    "soft_delete_retention_in_days": 90,
                    "vault_uri": f"https://{keyvault}.vault.azure.net/",
                },
                "type": "Microsoft.KeyVault/vaults",
                "tags": {},
            },
            "old": {},
        },
        "comment": f"Key Vault {keyvault} has been created.",
        "name": keyvault,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_keyvault_vault.present",
        name=keyvault,
        resource_group=resource_group,
        location=location,
        tenant_id=tenant_id,
        sku=sku,
        access_policies=access_policies,
        enable_soft_delete=False,
        connection_auth=connection_auth,
    )

    # sleep because access policies need some time to take effect
    time.sleep(5)
    data = list(ret.data.values())[0]
    data["changes"]["new"].pop("system_data")
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=3, after="test_present", before="test_absent")
def test_changes(
    salt_call_cli,
    resource_group,
    location,
    tags,
    keyvault,
    tenant_id,
    object_id,
    connection_auth,
):
    sku = "standard"
    access_policies = [
        {
            "tenant_id": tenant_id,
            "object_id": object_id,
            "permissions": {
                "keys": [
                    "Get",
                    "List",
                    "Update",
                    "Create",
                    "Import",
                    "Delete",
                    "Recover",
                    "Backup",
                    "Restore",
                    "UnwrapKey",
                    "WrapKey",
                    "Verify",
                    "Sign",
                    "Encrypt",
                    "Decrypt",
                ],
                "secrets": [
                    "Get",
                    "List",
                    "Set",
                    "Delete",
                    "Recover",
                    "Backup",
                    "Restore",
                ],
            },
        }
    ]
    expected = {
        "__id__": keyvault,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "tags": {
                "new": tags,
            },
        },
        "comment": f"Key Vault {keyvault} has been updated.",
        "name": keyvault,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_keyvault_vault.present",
        name=keyvault,
        resource_group=resource_group,
        location=location,
        tenant_id=tenant_id,
        sku=sku,
        access_policies=access_policies,
        enable_soft_delete=False,
        tags=tags,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data.pop("duration")
    data.pop("start_time")
    assert data == expected


@pytest.mark.run(order=-3)
def test_absent(
    salt_call_cli,
    resource_group,
    location,
    tags,
    keyvault,
    first_subscription,
    tenant_id,
    object_id,
    connection_auth,
):
    subscription_id = first_subscription
    access_policies = [
        {
            "tenant_id": tenant_id,
            "object_id": object_id,
            "permissions": {
                "keys": [
                    "Get",
                    "List",
                    "Update",
                    "Create",
                    "Import",
                    "Delete",
                    "Recover",
                    "Backup",
                    "Restore",
                    "UnwrapKey",
                    "WrapKey",
                    "Verify",
                    "Sign",
                    "Encrypt",
                    "Decrypt",
                ],
                "secrets": [
                    "Get",
                    "List",
                    "Set",
                    "Delete",
                    "Recover",
                    "Backup",
                    "Restore",
                ],
            },
        }
    ]
    expected = {
        "__id__": keyvault,
        "__run_num__": 0,
        "__sls__": None,
        "changes": {
            "new": {},
            "old": {
                "id": f"/subscriptions/{subscription_id}/resourceGroups/"
                + f"{resource_group}/providers/Microsoft.KeyVault/vaults/{keyvault}",
                "location": location,
                "name": keyvault,
                "properties": {
                    "access_policies": access_policies,
                    "enable_soft_delete": False,
                    "enabled_for_deployment": False,
                    "enable_rbac_authorization": False,
                    "provisioning_state": "Succeeded",
                    "public_network_access": "Enabled",
                    "sku": {"family": "A", "name": "standard"},
                    "soft_delete_retention_in_days": 90,
                    "tenant_id": f"{tenant_id}",
                    "vault_uri": f"https://{keyvault}.vault.azure.net/",
                },
                "tags": tags,
                "type": "Microsoft.KeyVault/vaults",
            },
        },
        "comment": f"Key Vault {keyvault} has been deleted.",
        "name": keyvault,
        "result": True,
    }
    ret = salt_call_cli.run(
        "--local",
        "state.single",
        "azurerm_keyvault_vault.absent",
        name=keyvault,
        resource_group=resource_group,
        connection_auth=connection_auth,
    )
    data = list(ret.data.values())[0]
    data["changes"]["old"].pop("system_data")
    data.pop("duration")
    data.pop("start_time")
    assert data == expected
