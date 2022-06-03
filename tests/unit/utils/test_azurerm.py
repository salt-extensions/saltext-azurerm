import pytest
import saltext.azurerm.utils.azurerm_mod as azurerm_util


@pytest.fixture
def configure_loader_modules():
    module_globals = {
        "__salt__": {"this_does_not_exist.please_replace_it": lambda: True},
    }
    return {
        azurerm_util: module_globals,
    }


def test_replace_this_this_with_something_meaningful():
    assert "this_does_not_exist.please_replace_it" in azurerm_util.__salt__
    assert azurerm_util.__salt__["this_does_not_exist.please_replace_it"]() is True
