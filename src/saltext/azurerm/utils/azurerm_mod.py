"""
Salt util module
"""
import logging

log = logging.getLogger(__name__)

__virtualname__ = "azurerm"


def __virtual__():
    # To force a module not to load return something like:
    #   return (False, "The azurerm util module is not implemented yet")
    return __virtualname__
