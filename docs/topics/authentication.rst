======================
Authentication Systems
======================

This system has migrated from the older version management library (msrestazure) to 
using the systems supported through azure identity.

Azure Identity Authentication
=============================
The `azure identity library <https://docs.microsoft.com/en-us/python/api/azure-identity/azure.identity?view=azure-python>`_
offers many different credentials to generate.

Using azure identity, ServicePrincipalCredentials was replaced with ClientSecretCredential.
UserPassCredentials was replaced with UsernamePasswordCredential.
Lastly, MSIAuthentication was replaced with DefaultAzureCredential.
