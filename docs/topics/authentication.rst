======================
Authentication Systems
======================

This system has migrated from the older version management library (``msrestazure``) to
using the systems supported through ``azure-identity``.

Azure Identity Authentication
=============================
The `azure identity library <https://docs.microsoft.com/en-us/python/api/azure-
identity/azure.identity?view=azure-python>`_ offers many different credentials to
generate for Azure SDK Clients. The different login mechanisms that are supported by this
code include ``ClientSecretCredential``, ``UsernamePasswordCredential``, and
``DefaultAzureCredential``, respectively. Based on the different parameters provided in
either the function call or the testing (``.sls``) file, the user can decide which
authentication mechanisms to activate.

ClientSecretCredential
======================
The ``ClientSecretCredential`` authenticates a service principal using a client secret.
This credential was updated from msrestazure's ``ServicePrincipalCredentials``,
maintaining the same functionality but allowing the code to be more adaptable to updated
dependencies. It is the first authentication option in the code, requiring the ``client
ID``, ``client secret``, ``tenant ID``, and ``subscription ID``. This type of
authentication is ideal for controlling which resources can be accessed and level of
access. The ``client secret`` is `generated <https://docs.microsoft.com/en-us/azure/active-
directory/develop/quickstart-register-app#add-credentials>`_ for App Registration.
This information is provided to salt through pillar in the ``test.sls`` file:

.. code-block:: yaml

        azurerm:
            mysubscription:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                tenant: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                client_id: ABCDEFAB-1234-ABCD-1234-ABCDEFABCDEF
                secret: XXXXXXXXXXXXXXXXXXXXXXXX
                cloud_environment: AZURE_PUBLIC_CLOUD

When the actual state block is called, the pillar is referenced:

.. code-block:: jinja

        {% set profile = salt['pillar.get']('azurerm:mysubscription') %}
        Ensure resource group exists:
            azurerm_resource.resource_group_present:
                - name: my_rg
                - location: westus
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}

UsernamePasswordCredential
==========================
The ``UsernamePasswordCredential`` authenticates a user using work and school accounts'
usernames and passwords (Microsoft accounts are not supported). This credential was
updated from msrestazure's ``UserPassCredentials``, also maintaining functionality while
being compatible with updated dependencies. This is the second authentication option in
the code and requires a ``username``, ``password``, and ``subscription ID``. This type of authentication
is not as recommended as the other types because it is not as secure or compatible with
other functionalities (such as multi-factor authentication and consent prompting). This
information can be provided to Salt through the testing file, similar to the example
above, but with changed variables. This information is also passed through Salt by pillar
in the ``test.sls`` file:

.. code-block:: yaml

        azurerm:
            user_pass_auth:
                subscription_id: 3287abc8-f98a-c678-3bde-326766fd3617
                username: fletch
                password: 123pass

Similarly, the pillar is referenced:

.. code-block:: jinja

        {% set profile = salt['pillar.get']('azurerm:user_path_auth') %}
        Ensure resource group exists:
            azurerm_resource.resource_group_present:
                - name: my_rg
                - location: westus
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}



DefaultAzureCredential
======================
The ``DefaultAzureCredential`` authenticates  when no other specifications are provided.
This credential was updated from msrestazure's ``MSIAuthentication``, so it now allows
the user to get the access tokens rather than just setting them. This type of
authentication is the last and default authentication option. Based on different
situations, DefaultAzureCredential automatically goes through multiple different
mechanisms and detects the best fit authentication method:

#. Environment: Authenticates using `environment variables <https://docs.microsoft.com/en-us/python/api/azure-
   identity/azure.identity.environmentcredential?view=azure-python>`_.
#. Managed Identity: Authenticates with managed identity if the application is deployed to an Azure host.
#. VS Code: Authenticates as the VS Code Azure Account Extension user if signed in.
#. Azure CLI: Authenticates as the Azure CLI user if signed in (via ``az login`` command)
#. Azure PowerShell: Authenticates as the Azure PowerShell user if signed in (via ``Connect-AzAccount`` command)
#. Interactive Browser: Authenticates a user via default browser

To implement, no pillar is needed, as it authenticates without those extra parameters and
only the subscription id in the ``test.sls`` file:

.. code-block:: jinja

        {% set profile = {"subscription_id" : "3287abc8-f98a-c678-3bde-326766fd3617"} %}
        Ensure resource group exists:
            azurerm_resource.resource_group_present:
                - name: my_rg
                - location: westus
                - tags:
                    how_awesome: very
                    contact_name: Elmer Fudd Gantry
                - connection_auth: {{ profile }}


Because of its flexibility, ``DefaultAzureCredential`` is the preferred method of
authentication.
