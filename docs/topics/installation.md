# Installation

Generally, extensions need to be installed into the same Python
environment Salt uses.

:::{tab} State
```yaml
Install Salt Azurerm extension:
  pip.installed:
    - name: saltext-azurerm
```
:::

:::{tab} Onedir installation
```bash
salt-pip install saltext-azurerm
```
:::

:::{tab} Regular installation
```bash
pip install saltext-azurerm
```

Salt itself is expected to be provided by the environment. If it
should be pip-managed as well, request the `salt` extra:

```bash
pip install 'saltext-azurerm[salt]'
```
:::

:::{hint}
Saltexts are not distributed automatically via the fileserver like
custom modules, they need to be installed on each node you want them
to be available on.
:::
