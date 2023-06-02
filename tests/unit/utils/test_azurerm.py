from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
import saltext.azurerm.utils.azurerm
from azure.mgmt.resource.resources import ResourceManagementClient

try:
    from salt._logging.impl import SaltLoggingClass
    from salt.exceptions import SaltSystemExit
except ImportError:
    pass


@pytest.fixture()
def credentials():
    class FakeCredential:
        """
        FakeCredential class swiped from the SDK
        """

        def get_token(self, *scopes, **kwargs):  # pylint: disable=unused-argument
            from azure.core.credentials import (  # pylint: disable=import-outside-toplevel
                AccessToken,
            )

            return AccessToken("fake_token", 2527537086)

        def close(self):
            pass

    return FakeCredential()


@pytest.fixture()
def subscription_id():
    return "e6df6af5-9a24-46ff-8527-b55c3788a6dd"


@pytest.fixture()
def cloud_env():
    cloud_env = MagicMock()
    cloud_env.endpoints.resource_manager = "http://localhost/someurl"
    return cloud_env


@pytest.fixture()
def mock_determine_auth(credentials, subscription_id, cloud_env):
    return MagicMock(return_value=(credentials, subscription_id, cloud_env))


def test_log_cloud_error():
    client = "foo"
    message = "bar"

    mock_error = MagicMock()
    mock_info = MagicMock()

    with patch.object(SaltLoggingClass, "info", mock_info), patch.object(
        SaltLoggingClass, "error", mock_error
    ):
        saltext.azurerm.utils.azurerm.log_cloud_error(client, message)
        mock_error.assert_called_once_with(
            "An Azure Resource Manager %s ResourceNotFoundError has occurred: %s", "Foo", "bar"
        )
        saltext.azurerm.utils.azurerm.log_cloud_error(client, message, azurerm_log_level="info")
        mock_info.assert_called_once_with(
            "An Azure Resource Manager %s ResourceNotFoundError has occurred: %s", "Foo", "bar"
        )


@pytest.mark.parametrize(
    "client_type,client_object",
    [
        ("compute", "ComputeManagement"),
        ("authorization", "AuthorizationManagement"),
        ("dns", "DnsManagement"),
        ("storage", "StorageManagement"),
        ("managementlock", "ManagementLock"),
        ("monitor", "MonitorManagement"),
        ("network", "NetworkManagement"),
        ("policy", "Policy"),
        ("privatedns", "PrivateDnsManagement"),
        ("resource", "ResourceManagement"),
        ("subscription", "Subscription"),
        ("web", "WebSiteManagement"),
        ("NOT_THERE", "not_used"),
    ],
)
def test_get_client(client_type, client_object, mock_determine_auth):
    if client_type == "NOT_THERE":
        with pytest.raises(SaltSystemExit):
            saltext.azurerm.utils.azurerm.get_client(client_type)
    else:
        with patch("saltext.azurerm.utils.azurerm._determine_auth", mock_determine_auth):
            client = saltext.azurerm.utils.azurerm.get_client(client_type)
            assert f"{client_object}Client" in str(client)


def test_paged_object_to_list():
    models = ResourceManagementClient.models()

    def _r_groups():
        rg_list = [
            models.ResourceGroup(
                location="eastus",
            ),
            models.ResourceGroup(
                location="westus",
            ),
        ]
        yield from rg_list

    paged_object = _r_groups()

    paged_return = saltext.azurerm.utils.azurerm.paged_object_to_list(paged_object)

    assert isinstance(paged_return, list)
    assert paged_return == [
        {"location": "eastus"},
        {"location": "westus"},
    ]


def test_create_object_model():
    obj = saltext.azurerm.utils.azurerm.create_object_model(
        "network",
        "VirtualNetwork",
    )
    assert "VirtualNetwork" in str(obj.__class__)
    assert obj.as_dict() == {"enable_ddos_protection": False, "enable_vm_protection": False}


def test_compare_list_of_dicts():
    # equal
    old1 = [
        {"name": "group1", "location": "eastus", "type": "ResourceGroup"},
        {"name": "group2", "location": "eastus"},
    ]
    new1 = [
        {"name": "group1", "location": "eastus"},
        {"name": "group2", "location": "eastus"},
    ]

    # not equal
    old2 = [
        {"name": "group1", "location": "eastus"},
        {"name": "group2", "location": "eastus"},
    ]
    new2 = [
        {"name": "group1", "location": "westus"},
        {"name": "group2", "location": "eastus"},
    ]

    # missing name key
    old3 = [
        {"name": "group1", "location": "eastus"},
        {"name": "group2", "location": "eastus"},
    ]
    new3 = [
        {"name": "group1", "location": "eastus"},
        {"location": "eastus"},
    ]

    ret = saltext.azurerm.utils.azurerm.compare_list_of_dicts(old1, new1)
    assert not ret

    ret = saltext.azurerm.utils.azurerm.compare_list_of_dicts(old2, new2)
    expected = {
        "changes": {
            "old": old2,
            "new": new2,
        }
    }
    assert ret == expected

    ret = saltext.azurerm.utils.azurerm.compare_list_of_dicts(old3, new3)
    expected = {"comment": 'configuration dictionaries must contain the "name" key!'}
    assert ret == expected


def test_determine_auth():
    assert False
