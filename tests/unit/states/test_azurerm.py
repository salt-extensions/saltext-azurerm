import pytest
import salt.modules.test as testmod
import saltext.azurerm.modules.azurerm_mod as azurerm_module
import saltext.azurerm.states.azurerm_mod as azurerm_state


@pytest.fixture
def configure_loader_modules():
    return {
        azurerm_module: {
            "__salt__": {
                "test.echo": testmod.echo,
            },
        },
        azurerm_state: {
            "__salt__": {
                "azurerm.example_function": azurerm_module.example_function,
            },
        },
    }


def test_replace_this_this_with_something_meaningful():
    echo_str = "Echoed!"
    expected = {
        "name": echo_str,
        "changes": {},
        "result": True,
        "comment": f"The 'azurerm.example_function' returned: '{echo_str}'",
    }
    assert azurerm_state.exampled(echo_str) == expected
