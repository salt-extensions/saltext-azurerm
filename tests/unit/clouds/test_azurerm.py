import pytest
import saltext.azurerm.clouds.azurerm_mod as azurerm_cloud


@pytest.fixture
def configure_loader_modules():
    module_globals = {
        "__salt__": {"this_does_not_exist.please_replace_it": lambda: True},
    }
    return {
        azurerm_cloud: module_globals,
    }


def test_replace_this_this_with_something_meaningful():
    assert "this_does_not_exist.please_replace_it" in azurerm_cloud.__salt__
    assert azurerm_cloud.__salt__["this_does_not_exist.please_replace_it"]() is True
