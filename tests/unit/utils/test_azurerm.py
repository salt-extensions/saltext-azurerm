import os
from unittest.mock import MagicMock
from unittest.mock import patch

import pytest
from azure.mgmt.resource.resources import ResourceManagementClient

import saltext.azurerm.utils.azurerm

try:
    from salt._logging.impl import SaltLoggingClass
    from salt.exceptions import SaltInvocationError
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
            # pylint: disable=import-outside-toplevel
            from azure.core.credentials import AccessToken

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

    with (
        patch.object(SaltLoggingClass, "info", mock_info),
        patch.object(SaltLoggingClass, "error", mock_error),
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
    old = [
        {"name": "group1", "location": "eastus"},
        {"name": "group2", "location": "eastus"},
    ]
    new = [
        {"name": "group1", "location": "eastus"},
        {"name": "group2", "location": "eastus"},
    ]
    ret = saltext.azurerm.utils.azurerm.compare_list_of_dicts(old, new)
    assert not ret

    # case difference
    new[0]["location"] = "EastUS"
    ret = saltext.azurerm.utils.azurerm.compare_list_of_dicts(old, new)
    assert not ret

    # not equal
    new[0]["location"] = "westus"
    ret = saltext.azurerm.utils.azurerm.compare_list_of_dicts(old, new)
    expected = {
        "changes": {
            "old": old,
            "new": new,
        }
    }
    assert ret == expected

    # missing name key
    new[0].pop("name")
    ret = saltext.azurerm.utils.azurerm.compare_list_of_dicts(old, new)
    expected = {"comment": 'configuration dictionaries must contain the "name" key!'}
    assert ret == expected


def test__determine_auth():
    # test cloud environment starts with http
    mock_credentials = MagicMock()
    mock_get_cloud_from_metadata_endpoint = MagicMock(return_value="cloud_from_metadata")
    with (
        patch("saltext.azurerm.utils.azurerm.DefaultAzureCredential", mock_credentials),
        patch(
            "saltext.azurerm.utils.azurerm.get_cloud_from_metadata_endpoint",
            mock_get_cloud_from_metadata_endpoint,
        ),
    ):
        (
            _,
            subscription_id,
            cloud_env,
        ) = saltext.azurerm.utils.azurerm._determine_auth(  # pylint: disable=protected-access
            subscription_id="54321",
            cloud_environment="http://random.com",
        )
        assert subscription_id == "54321"
        assert mock_credentials.call_args.kwargs["authority"] == "http://random.com"
        mock_get_cloud_from_metadata_endpoint.assert_called_once_with("http://random.com")
        assert cloud_env == "cloud_from_metadata"

    # test valid cloud name
    mock_credentials.reset_mock()
    with patch("saltext.azurerm.utils.azurerm.DefaultAzureCredential", mock_credentials):
        (
            _,
            subscription_id,
            cloud_env,
        ) = saltext.azurerm.utils.azurerm._determine_auth(  # pylint: disable=protected-access
            subscription_id="54321",
            cloud_environment="AZURE_GOVERNMENT",
        )
        assert subscription_id == "54321"
        assert cloud_env.name == "AzureUSGovernment"
        assert mock_credentials.call_args.kwargs["authority"] == "login.microsoftonline.us"

    # test no subscription id provided error
    with pytest.raises(SaltInvocationError):
        saltext.azurerm.utils.azurerm._determine_auth(  # pylint: disable=protected-access
            username="usertest", password="passtest"
        )


def test_get_identity_credentials():
    kwargs = {
        "tenant": "test_tenant_id",
        "client_id": "test_client_id",
        "secret": "test_secret",
    }

    mock_credential = MagicMock()
    mock_os_environ = {}

    with (
        patch("saltext.azurerm.utils.azurerm.DefaultAzureCredential", mock_credential),
        patch.object(os, "environ", mock_os_environ),
    ):
        saltext.azurerm.utils.azurerm.get_identity_credentials(**kwargs)

        assert mock_credential.call_args.kwargs["authority"] == "login.microsoftonline.com"
        assert mock_os_environ["AZURE_TENANT_ID"] == "test_tenant_id"
        assert mock_os_environ["AZURE_CLIENT_ID"] == "test_client_id"
        assert mock_os_environ["AZURE_CLIENT_SECRET"] == "test_secret"

        kwargs["cloud_environment"] = "http://random.com"
        saltext.azurerm.utils.azurerm.get_identity_credentials(**kwargs)
        assert mock_credential.call_args.kwargs["authority"] == "http://random.com"

        kwargs["cloud_environment"] = "AZURE_GOVERNMENT"
        saltext.azurerm.utils.azurerm.get_identity_credentials(**kwargs)
        assert mock_credential.call_args.kwargs["authority"] == "login.microsoftonline.us"

        kwargs["cloud_environment"] = "THIS_CLOUD_IS_FAKE"
        saltext.azurerm.utils.azurerm.get_identity_credentials(**kwargs)
        assert mock_credential.call_args.kwargs["authority"] == "login.microsoftonline.com"
