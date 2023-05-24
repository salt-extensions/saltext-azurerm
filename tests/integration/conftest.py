import random
import string

import pytest
from azure.identity import DefaultAzureCredential
from azure.mgmt.subscription import SubscriptionClient


@pytest.fixture(scope="package")
def master(master):
    with master.started():
        yield master


@pytest.fixture(scope="package")
def minion(minion):
    with minion.started():
        yield minion


@pytest.fixture
def salt_run_cli(master):
    return master.get_salt_run_cli()


@pytest.fixture
def salt_cli(master):
    return master.get_salt_cli()


@pytest.fixture
def salt_call_cli(minion):
    return minion.salt_call_cli()


@pytest.fixture(scope="session")
def location():
    yield "eastus"


@pytest.fixture(scope="session")
def tags():
    yield {
        "Organization": "Everest",
        "Owner": "Elmer Fudd Gantry",
    }


@pytest.fixture(scope="session")
def resource_group():
    yield "rg-salt-inttest-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(20)
    )


@pytest.fixture(scope="session")
def virt_mach():
    yield "vm-salt-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(5)
    )


@pytest.fixture(scope="session")
def storage_account():
    yield "stsalt" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(16)
    )


@pytest.fixture(scope="session")
def storage_container():
    yield "container-salt-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(32)
    )


@pytest.fixture(scope="session")
def vnet():
    yield "vnet-salt-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def vnet2():
    yield "vnet-salt2-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def subnet():
    yield "snet-salt-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def public_ip_addr():
    yield "pip-salt-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def public_ip_addr2():
    yield "pip-salt-2-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def route_table():
    yield "rt-table-salt-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def route():
    yield "rt-salt-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def load_balancer():
    yield "lb-salt-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def zone():
    yield "zone.salt." + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def availability_set():
    yield "avail-salt-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def network_interface():
    yield "nic-salt-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def ip_config():
    yield "ip-config-salt-" + "".join(
        random.choice(string.ascii_lowercase + string.digits) for _ in range(8)
    )


@pytest.fixture(scope="session")
def first_subscription():
    # Create an instance of DefaultAzureCredential to authenticate
    credential = DefaultAzureCredential()

    # Create a SubscriptionClient using the credential
    subscription_client = SubscriptionClient(credential)

    # Retrieve the list of subscriptions
    subscription_list = list(subscription_client.subscriptions.list())

    # Extract the subscription IDs and names
    subscriptions = [sub.subscription_id for sub in subscription_list]
    subscription = subscriptions[0]

    return subscription


@pytest.fixture(scope="session")
def connection_auth(first_subscription):
    yield {"subscription_id": first_subscription}
