"""
Azure Resource Manager Resource Execution Module

.. versionadded:: 2019.2.0

:maintainer: <devops@eitr.tech>
:maturity: new
:platform: linux

:configuration: This module requires Azure Resource Manager credentials to be passed as keyword arguments
    to every function in order to work properly.

    Required provider parameters:

    if using username and password:
      * ``subscription_id``
      * ``username``
      * ``password``

    if using a service principal:
      * ``subscription_id``
      * ``tenant``
      * ``client_id``
      * ``secret``

    Optional provider parameters:

**cloud_environment**: Used to point the cloud driver to different API endpoints, such as Azure GovCloud.
    Possible values:
      * ``AZURE_PUBLIC_CLOUD`` (default)
      * ``AZURE_CHINA_CLOUD``
      * ``AZURE_US_GOV_CLOUD``
      * ``AZURE_GERMAN_CLOUD``

"""

# Python libs
import logging
from json.decoder import JSONDecodeError

import salt.utils.files  # pylint: disable=import-error
import salt.utils.json  # pylint: disable=import-error

import saltext.azurerm.utils.azurerm

# Azure libs
HAS_LIBS = False
try:
    import azure.mgmt.resource.resources.models  # pylint: disable=unused-import
    from azure.core.exceptions import HttpResponseError
    from azure.core.exceptions import ResourceNotFoundError
    from azure.core.exceptions import SerializationError

    HAS_LIBS = True
except ImportError:
    pass

__virtualname__ = "azurerm_resource"

log = logging.getLogger(__name__)


def __virtual__():
    if not HAS_LIBS:
        return (
            False,
            "The following dependencies are required to use the Azure Resource Manager modules: "
            "Microsoft Azure SDK for Python >= 2.0rc6, "
            "MS REST Azure (msrestazure) >= 0.4",
        )

    return __virtualname__


def resource_groups_list(**kwargs):
    """
    .. versionadded:: 2019.2.0

    List all resource groups within a subscription.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.resource_groups_list

    """
    result = {}
    resconn = saltext.azurerm.utils.azurerm.get_client("resource", **kwargs)
    try:
        groups = saltext.azurerm.utils.azurerm.paged_object_to_list(resconn.resource_groups.list())

        for group in groups:
            result[group["name"]] = group
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def resource_group_check_existence(name, **kwargs):
    """
    .. versionadded:: 2019.2.0

    Check for the existence of a named resource group in the current subscription.

    :param name: The resource group name to check.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.resource_group_check_existence testgroup

    """
    result = False
    resconn = saltext.azurerm.utils.azurerm.get_client("resource", **kwargs)
    try:
        result = resconn.resource_groups.check_existence(name)

    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)

    return result


def resource_group_get(name, **kwargs):
    """
    .. versionadded:: 2019.2.0

    Get a dictionary representing a resource group's properties.

    :param name: The resource group name to get.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.resource_group_get testgroup

    """
    result = {}
    resconn = saltext.azurerm.utils.azurerm.get_client("resource", **kwargs)
    try:
        group = resconn.resource_groups.get(name)
        result = group.as_dict()

    except (ResourceNotFoundError, HttpResponseError) as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def resource_group_create_or_update(name, location, **kwargs):  # pylint: disable=invalid-name
    """
    .. versionadded:: 2019.2.0

    Create or update a resource group in a given location.

    :param name: The name of the resource group to create or update.

    :param location: The location of the resource group. This value
        is not able to be updated once the resource group is created.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.resource_group_create_or_update testgroup westus

    """
    result = {}
    resconn = saltext.azurerm.utils.azurerm.get_client("resource", **kwargs)
    resource_group_params = {
        "location": location,
        "managed_by": kwargs.get("managed_by"),
        "tags": kwargs.get("tags"),
    }
    try:
        group = resconn.resource_groups.create_or_update(name, resource_group_params)
        result = group.as_dict()
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def resource_group_delete(name, **kwargs):
    """
    .. versionadded:: 2019.2.0

    Delete a resource group from the subscription.

    :param name: The resource group name to delete.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.resource_group_delete testgroup

    """
    result = False
    resconn = saltext.azurerm.utils.azurerm.get_client("resource", **kwargs)
    try:
        group = resconn.resource_groups.begin_delete(name, polling=True)
        group.wait()
        result = True
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)

    return result


def deployment_operation_get(operation, deployment, resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    Get a deployment operation within a deployment.

    :param operation: The operation ID of the operation within the deployment.

    :param deployment: The name of the deployment containing the operation.

    :param resource_group: The resource group name assigned to the
        deployment.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.deployment_operation_get XXXXX testdeploy testgroup

    """
    resconn = saltext.azurerm.utils.azurerm.get_client("resource", **kwargs)
    try:
        operation = resconn.deployment_operations.get(
            resource_group_name=resource_group,
            deployment_name=deployment,
            operation_id=operation,
        )

        result = operation.as_dict()
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def deployment_operations_list(name, resource_group, result_limit=10, **kwargs):
    """
    .. versionadded:: 2019.2.0

    List all deployment operations within a deployment.

    :param name: The name of the deployment to query.

    :param resource_group: The resource group name assigned to the
        deployment.

    :param result_limit: (Default: 10) The limit on the list of deployment
        operations.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.deployment_operations_list testdeploy testgroup

    """
    result = {}
    resconn = saltext.azurerm.utils.azurerm.get_client("resource", **kwargs)
    try:
        operations = saltext.azurerm.utils.azurerm.paged_object_to_list(
            resconn.deployment_operations.list(
                resource_group_name=resource_group,
                deployment_name=name,
                top=result_limit,
            )
        )

        for oper in operations:
            result[oper["operation_id"]] = oper
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def deployment_delete(name, resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    Delete a deployment.

    :param name: The name of the deployment to delete.

    :param resource_group: The resource group name assigned to the
        deployment.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.deployment_delete testdeploy testgroup

    """
    result = False
    resconn = saltext.azurerm.utils.azurerm.get_client("resource", **kwargs)
    try:
        deploy = resconn.deployments.delete(
            deployment_name=name, resource_group_name=resource_group
        )
        deploy.wait()
        result = True
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)

    return result


def deployment_check_existence(name, resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    Check the existence of a deployment.

    :param name: The name of the deployment to query.

    :param resource_group: The resource group name assigned to the
        deployment.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.deployment_check_existence testdeploy testgroup

    """
    result = False
    resconn = saltext.azurerm.utils.azurerm.get_client("resource", **kwargs)
    try:
        result = resconn.deployments.check_existence(
            deployment_name=name, resource_group_name=resource_group
        )
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)

    return result


def deployment_create_or_update(
    name,
    resource_group,
    deploy_mode="incremental",
    debug_setting="none",
    deploy_params=None,
    parameters_link=None,
    deploy_template=None,
    template_link=None,
    **kwargs,
):
    """
    .. versionadded:: 2019.2.0

    Deploys resources to a resource group.

    :param name: The name of the deployment to create or update.

    :param resource_group: The resource group name assigned to the
        deployment.

    :param deploy_mode: The mode that is used to deploy resources. This value can be either
        'incremental' or 'complete'. In Incremental mode, resources are deployed without deleting
        existing resources that are not included in the template. In Complete mode, resources
        are deployed and existing resources in the resource group that are not included in
        the template are deleted. Be careful when using Complete mode as you may
        unintentionally delete resources.

    :param debug_setting: The debug setting of the deployment. The permitted values are 'none',
        'requestContent', 'responseContent', or 'requestContent,responseContent'. By logging
        information about the request or response, you could potentially expose sensitive data
        that is retrieved through the deployment operations.

    :param deploy_params: JSON string containing name and value pairs that define the deployment
        parameters for the template. You use this element when you want to provide the parameter
        values directly in the request rather than link to an existing parameter file. Use either
        the parameters_link property or the deploy_params property, but not both.

    :param parameters_link: The URI of a parameters file. You use this element to link to an existing
        parameters file. Use either the parameters_link property or the deploy_params property, but not both.

    :param deploy_template: JSON string of template content. You use this element when you want to pass
        the template syntax directly in the request rather than link to an existing template. Use either
        the template_link property or the deploy_template property, but not both.

    :param template_link: The URI of the template. Use either the template_link property or the
        deploy_template property, but not both.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.deployment_create_or_update testdeploy testgroup

    """
    resconn = saltext.azurerm.utils.azurerm.get_client("resource", **kwargs)

    prop_kwargs = {"mode": deploy_mode}
    if isinstance(debug_setting, dict):
        prop_kwargs["debug_setting"] = debug_setting
    else:
        prop_kwargs["debug_setting"] = {"detail_level": debug_setting}

    if deploy_params is not None:
        prop_kwargs["parameters"] = deploy_params
    else:
        param_uri = None
        if isinstance(parameters_link, dict) and parameters_link.get("uri"):
            param_uri = parameters_link["uri"]
        elif isinstance(parameters_link, dict):
            log.error("Error - URI is missing.")
        else:
            param_uri = parameters_link

        # look for salt:// uri in parameters_link
        # and use cp.get_file_str to get JSON file content
        # as Python dict and pass in prop_kwargs["parameters"]
        if param_uri:
            if salt.utils.url.validate(param_uri, ["salt"]):
                file_str = __salt__["cp.get_file_str"](param_uri) or "{}"
                file_dict = salt.utils.json.loads(file_str)
                if isinstance(file_dict, dict):
                    prop_kwargs["parameters"] = file_dict
            elif salt.utils.url.validate(param_uri, ["http", "https"]):
                prop_kwargs["parameters_link"] = {"uri": param_uri}
            else:
                with salt.utils.files.fopen(param_uri, "r") as param_file:
                    file_str = param_file.read()
                    try:
                        file_dict = salt.utils.json.loads(file_str)
                        if isinstance(file_dict, dict):
                            prop_kwargs["parameters"] = file_dict
                    except (JSONDecodeError, TypeError) as exc:
                        log.error(exc)
    if deploy_template is not None:
        prop_kwargs["template"] = deploy_template
    else:
        template_uri = None
        if isinstance(template_link, dict) and template_link.get("uri"):
            template_uri = template_link["uri"]
        elif isinstance(template_link, dict):
            log.error("Error - URI is missing.")
        else:
            template_uri = template_link

        # look for salt:// uri in template_link
        # and use cp.get_file_str to get JSON file content
        # as Python dict and pass in prop_kwargs["template"]
        if template_uri:
            if salt.utils.url.validate(template_link, ["salt"]):
                file_str = __salt__["cp.get_file_str"](template_link) or "{}"
                file_dict = salt.utils.json.loads(file_str)
                if isinstance(file_dict, dict):
                    prop_kwargs["template"] = file_dict
            elif salt.utils.url.validate(template_link, ["http", "https"]):
                prop_kwargs["template_link"] = {"uri": template_uri}
            else:
                with salt.utils.files.fopen(template_link, "r") as template_file:
                    file_str = template_file.read()
                    try:
                        file_dict = salt.utils.json.loads(file_str)
                        if isinstance(file_dict, dict):
                            prop_kwargs["template"] = file_dict
                    except (JSONDecodeError, TypeError) as exc:
                        log.error(exc)

    deploy_kwargs = kwargs.copy()
    deploy_kwargs.update(prop_kwargs)

    try:
        deploy_model = saltext.azurerm.utils.azurerm.create_object_model(
            "resource.resources", "DeploymentProperties", **deploy_kwargs
        )
    except TypeError as exc:
        result = {"error": f"The object model could not be built. ({str(exc)})"}
        return result

    try:
        validate = deployment_validate(
            name=name,
            resource_group=resource_group,
            deploy_mode=deploy_kwargs.get("mode"),
            debug_setting=deploy_kwargs.get("debug_setting"),
            deploy_params=deploy_kwargs.get("parameters"),
            parameters_link=deploy_kwargs.get("parameters_link"),
            deploy_template=deploy_kwargs.get("template"),
            template_link=deploy_kwargs.get("template_link"),
            **kwargs,
        )
        if "error" in validate:
            result = validate
        else:
            deploy = resconn.deployments.begin_create_or_update(
                deployment_name=name,
                resource_group_name=resource_group,
                parameters={"properties": deploy_model},
            )
            deploy.wait()
            deploy_result = deploy.result()
            result = deploy_result.as_dict()
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {"error": f"The object model could not be parsed. ({str(exc)})"}

    return result


def deployment_get(name, resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    Get details about a specific deployment.

    :param name: The name of the deployment to query.

    :param resource_group: The resource group name assigned to the
        deployment.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.deployment_get testdeploy testgroup

    """
    resconn = saltext.azurerm.utils.azurerm.get_client("resource", **kwargs)
    try:
        deploy = resconn.deployments.get(deployment_name=name, resource_group_name=resource_group)
        result = deploy.as_dict()
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def deployment_cancel(name, resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    Cancel a deployment if in 'Accepted' or 'Running' state.

    :param name: The name of the deployment to cancel.

    :param resource_group: The resource group name assigned to the
        deployment.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.deployment_cancel testdeploy testgroup

    """
    resconn = saltext.azurerm.utils.azurerm.get_client("resource", **kwargs)
    try:
        resconn.deployments.cancel(deployment_name=name, resource_group_name=resource_group)
        result = {"result": True}
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc), "result": False}

    return result


def deployment_validate(
    name,
    resource_group,
    deploy_mode=None,
    debug_setting=None,
    deploy_params=None,
    parameters_link=None,
    deploy_template=None,
    template_link=None,
    **kwargs,
):
    """
    .. versionadded:: 2019.2.0

    Validates whether the specified template is syntactically correct
    and will be accepted by Azure Resource Manager.

    :param name: The name of the deployment to validate.

    :param resource_group: The resource group name assigned to the
        deployment.

    :param deploy_mode: The mode that is used to deploy resources. This value can be either
        'incremental' or 'complete'. In Incremental mode, resources are deployed without deleting
        existing resources that are not included in the template. In Complete mode, resources
        are deployed and existing resources in the resource group that are not included in
        the template are deleted. Be careful when using Complete mode as you may
        unintentionally delete resources.

    :param debug_setting: The debug setting of the deployment. The permitted values are 'none',
        'requestContent', 'responseContent', or 'requestContent,responseContent'. By logging
        information about the request or response, you could potentially expose sensitive data
        that is retrieved through the deployment operations.

    :param deploy_params: JSON string containing name and value pairs that define the deployment
        parameters for the template. You use this element when you want to provide the parameter
        values directly in the request rather than link to an existing parameter file. Use either
        the parameters_link property or the deploy_params property, but not both.

    :param parameters_link: The URI of a parameters file. You use this element to link to an existing
        parameters file. Use either the parameters_link property or the deploy_params property, but not both.

    :param deploy_template: JSON string of template content. You use this element when you want to pass
        the template syntax directly in the request rather than link to an existing template. Use either
        the template_link property or the deploy_template property, but not both.

    :param template_link: The URI of the template. Use either the template_link property or the
        deploy_template property, but not both.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.deployment_validate testdeploy testgroup

    """
    resconn = saltext.azurerm.utils.azurerm.get_client("resource", **kwargs)

    prop_kwargs = {"mode": deploy_mode}
    if isinstance(debug_setting, dict):
        prop_kwargs["debug_setting"] = debug_setting
    else:
        prop_kwargs["debug_setting"] = {"detail_level": debug_setting}

    if deploy_params is not None:
        prop_kwargs["parameters"] = deploy_params
    else:
        if isinstance(parameters_link, dict):
            prop_kwargs["parameters_link"] = parameters_link
        else:
            prop_kwargs["parameters_link"] = {"uri": parameters_link}

    if deploy_template:
        prop_kwargs["template"] = deploy_template
    else:
        if isinstance(template_link, dict):
            prop_kwargs["template_link"] = template_link
        else:
            prop_kwargs["template_link"] = {"uri": template_link}

    deploy_kwargs = kwargs.copy()
    deploy_kwargs.update(prop_kwargs)

    try:
        deploy_model = saltext.azurerm.utils.azurerm.create_object_model(
            "resource.resources", "DeploymentProperties", **deploy_kwargs
        )
    except TypeError as exc:
        result = {"error": f"The object model could not be built. ({str(exc)})"}
        return result

    try:
        local_validation = deploy_model.validate()
        if local_validation:
            raise local_validation[0]

        deploy = resconn.deployments.begin_validate(
            deployment_name=name,
            resource_group_name=resource_group,
            parameters={"properties": deploy_model},
        )
        deploy.wait()
        deploy_result = deploy.result()
        result = deploy_result.as_dict()
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {"error": f"The object model could not be parsed. ({str(exc)})"}

    return result


def deployment_export_template(name, resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    Exports the template used for the specified deployment.

    :param name: The name of the deployment to query.

    :param resource_group: The resource group name assigned to the
        deployment.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.deployment_export_template testdeploy testgroup

    """
    resconn = saltext.azurerm.utils.azurerm.get_client("resource", **kwargs)
    try:
        deploy = resconn.deployments.export_template(
            deployment_name=name, resource_group_name=resource_group
        )
        result = deploy.as_dict()
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def deployments_list(resource_group, **kwargs):
    """
    .. versionadded:: 2019.2.0

    List all deployments within a resource group.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.deployments_list testgroup

    """
    result = {}
    resconn = saltext.azurerm.utils.azurerm.get_client("resource", **kwargs)
    try:
        deployments = saltext.azurerm.utils.azurerm.paged_object_to_list(
            resconn.deployments.list_by_resource_group(resource_group_name=resource_group)
        )

        for deploy in deployments:
            result[deploy["name"]] = deploy
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def subscriptions_list_locations(subscription_id=None, **kwargs):
    """
    .. versionadded:: 2019.2.0

    List all locations for a subscription.

    :param subscription_id: The ID of the subscription to query.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.subscriptions_list_locations XXXXXXXX

    """
    result = {}

    if not subscription_id:
        subscription_id = kwargs.get("subscription_id")
    elif not kwargs.get("subscription_id"):
        kwargs["subscription_id"] = subscription_id

    subconn = saltext.azurerm.utils.azurerm.get_client("subscription", **kwargs)
    try:
        locations = saltext.azurerm.utils.azurerm.paged_object_to_list(
            subconn.subscriptions.list_locations(subscription_id=kwargs["subscription_id"])
        )

        for loc in locations:
            result[loc["name"]] = loc
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def subscription_get(subscription_id=None, **kwargs):
    """
    .. versionadded:: 2019.2.0

    Get details about a subscription.

    :param subscription_id: The ID of the subscription to query.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.subscription_get XXXXXXXX

    """
    result = {}

    if not subscription_id:
        subscription_id = kwargs.get("subscription_id")
    elif not kwargs.get("subscription_id"):
        kwargs["subscription_id"] = subscription_id

    subconn = saltext.azurerm.utils.azurerm.get_client("subscription", **kwargs)
    try:
        subscription = subconn.subscriptions.get(subscription_id=kwargs.get("subscription_id"))

        result = subscription.as_dict()
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def subscriptions_list(**kwargs):
    """
    .. versionadded:: 2019.2.0

    List all subscriptions for a tenant.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.subscriptions_list

    """
    result = {}
    subconn = saltext.azurerm.utils.azurerm.get_client("subscription", **kwargs)
    try:
        subs = saltext.azurerm.utils.azurerm.paged_object_to_list(subconn.subscriptions.list())

        for sub in subs:
            result[sub["subscription_id"]] = sub
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def tenants_list(**kwargs):
    """
    .. versionadded:: 2019.2.0

    List all tenants for your account.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.tenants_list

    """
    result = {}
    subconn = saltext.azurerm.utils.azurerm.get_client("subscription", **kwargs)
    try:
        tenants = saltext.azurerm.utils.azurerm.paged_object_to_list(subconn.tenants.list())

        for tenant in tenants:
            result[tenant["tenant_id"]] = tenant
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def policy_assignment_delete(name, scope, **kwargs):
    """
    .. versionadded:: 2019.2.0

    Delete a policy assignment.

    :param name: The name of the policy assignment to delete.

    :param scope: The scope of the policy assignment.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.policy_assignment_delete testassign \
        /subscriptions/bc75htn-a0fhsi-349b-56gh-4fghti-f84852

    """
    result = False
    polconn = saltext.azurerm.utils.azurerm.get_client("policy", **kwargs)
    try:
        # pylint: disable=unused-variable
        policy = polconn.policy_assignments.delete(policy_assignment_name=name, scope=scope)
        result = True
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)

    return result


def policy_assignment_create(name, scope, definition_name, **kwargs):
    """
    .. versionadded:: 2019.2.0

    Create a policy assignment.

    :param name: The name of the policy assignment to create.

    :param scope: The scope of the policy assignment.

    :param definition_name: The name of the policy definition to assign.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.policy_assignment_create testassign \
        /subscriptions/bc75htn-a0fhsi-349b-56gh-4fghti-f84852 testpolicy

    """
    polconn = saltext.azurerm.utils.azurerm.get_client("policy", **kwargs)

    # "get" doesn't work for built-in policies per https://github.com/Azure/azure-cli/issues/692
    # Uncomment this section when the ticket above is resolved.
    #  BEGIN
    # definition = policy_definition_get(
    #     name=definition_name,
    #     **kwargs
    # )
    #  END

    # Delete this section when the ticket above is resolved.
    #  BEGIN
    definition_list = policy_definitions_list(**kwargs)
    definition = definition_list.get(
        definition_name,
        {"error": f'The policy definition named "{definition_name}" could not be found.'},
    )
    #  END

    if "error" not in definition:
        definition_id = str(definition["id"])

        prop_kwargs = {"policy_definition_id": definition_id}

        policy_kwargs = kwargs.copy()
        policy_kwargs.update(prop_kwargs)

        try:
            policy_model = saltext.azurerm.utils.azurerm.create_object_model(
                "resource.policy", "PolicyAssignment", **policy_kwargs
            )
        except TypeError as exc:
            result = {"error": f"The object model could not be built. ({str(exc)})"}
            return result

        try:
            policy = polconn.policy_assignments.create(
                scope=scope, policy_assignment_name=name, parameters=policy_model
            )
            result = policy.as_dict()
        except HttpResponseError as exc:
            saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
            result = {"error": str(exc)}
        except SerializationError as exc:
            result = {"error": f"The object model could not be parsed. ({str(exc)})"}
    else:
        result = {"error": f'The policy definition named "{definition_name}" could not be found.'}

    return result


def policy_assignment_get(name, scope, **kwargs):
    """
    .. versionadded:: 2019.2.0

    Get details about a specific policy assignment.

    :param name: The name of the policy assignment to query.

    :param scope: The scope of the policy assignment.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.policy_assignment_get testassign \
        /subscriptions/bc75htn-a0fhsi-349b-56gh-4fghti-f84852

    """
    polconn = saltext.azurerm.utils.azurerm.get_client("policy", **kwargs)
    try:
        policy = polconn.policy_assignments.get(policy_assignment_name=name, scope=scope)
        result = policy.as_dict()
    except (ResourceNotFoundError, HttpResponseError) as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def policy_assignments_list_for_resource_group(
    resource_group, **kwargs
):  # pylint: disable=invalid-name
    """
    .. versionadded:: 2019.2.0

    List all policy assignments for a resource group.

    :param resource_group: The resource group name to list policy assignments within.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.policy_assignments_list_for_resource_group testgroup

    """
    result = {}
    polconn = saltext.azurerm.utils.azurerm.get_client("policy", **kwargs)
    try:
        policy_assign = saltext.azurerm.utils.azurerm.paged_object_to_list(
            polconn.policy_assignments.list_for_resource_group(
                resource_group_name=resource_group, filter=kwargs.get("filter")
            )
        )

        for assign in policy_assign:
            result[assign["name"]] = assign
    except (ResourceNotFoundError, HttpResponseError) as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def policy_assignments_list(**kwargs):
    """
    .. versionadded:: 2019.2.0

    List all policy assignments for a subscription.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.policy_assignments_list

    """
    result = {}
    polconn = saltext.azurerm.utils.azurerm.get_client("policy", **kwargs)
    try:
        policy_assign = saltext.azurerm.utils.azurerm.paged_object_to_list(
            polconn.policy_assignments.list()
        )

        for assign in policy_assign:
            result[assign["name"]] = assign
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def policy_definition_create_or_update(name, policy_rule, **kwargs):  # pylint: disable=invalid-name
    """
    .. versionadded:: 2019.2.0

    Create or update a policy definition.

    :param name: The name of the policy definition to create or update.

    :param policy_rule: A dictionary defining the
        `policy rule <https://learn.microsoft.com/en-us/azure/governance/policy/concepts/definition-structure-policy-rule>`_.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.policy_definition_create_or_update testpolicy '{...rule definition..}'

    """
    if not isinstance(policy_rule, dict):
        result = {"error": "The policy rule must be a dictionary!"}
        return result

    polconn = saltext.azurerm.utils.azurerm.get_client("policy", **kwargs)

    # Convert OrderedDict to dict
    prop_kwargs = {"policy_rule": salt.utils.json.loads(salt.utils.json.dumps(policy_rule))}

    policy_kwargs = kwargs.copy()
    policy_kwargs.update(prop_kwargs)

    try:
        policy_model = saltext.azurerm.utils.azurerm.create_object_model(
            "resource.policy", "PolicyDefinition", **policy_kwargs
        )
    except TypeError as exc:
        result = {"error": f"The object model could not be built. ({str(exc)})"}
        return result

    try:
        policy = polconn.policy_definitions.create_or_update(
            policy_definition_name=name, parameters=policy_model
        )
        result = policy.as_dict()
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}
    except SerializationError as exc:
        result = {"error": f"The object model could not be parsed. ({str(exc)})"}

    return result


def policy_definition_delete(name, **kwargs):
    """
    .. versionadded:: 2019.2.0

    Delete a policy definition.

    :param name: The name of the policy definition to delete.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.policy_definition_delete testpolicy

    """
    result = False
    polconn = saltext.azurerm.utils.azurerm.get_client("policy", **kwargs)
    try:
        # pylint: disable=unused-variable
        policy = polconn.policy_definitions.delete(policy_definition_name=name)
        result = True
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)

    return result


def policy_definition_get(name, **kwargs):
    """
    .. versionadded:: 2019.2.0

    Get details about a specific policy definition.

    :param name: The name of the policy definition to query.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.policy_definition_get testpolicy

    """
    polconn = saltext.azurerm.utils.azurerm.get_client("policy", **kwargs)
    try:
        policy_def = polconn.policy_definitions.get(policy_definition_name=name)
        result = policy_def.as_dict()
    except (ResourceNotFoundError, HttpResponseError) as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result


def policy_definitions_list(hide_builtin=False, **kwargs):
    """
    .. versionadded:: 2019.2.0

    List all policy definitions for a subscription.

    :param hide_builtin: Boolean which will filter out BuiltIn policy definitions from the result.

    CLI Example:

    .. code-block:: bash

        salt-call azurerm_resource.policy_definitions_list

    """
    result = {}
    polconn = saltext.azurerm.utils.azurerm.get_client("policy", **kwargs)
    try:
        policy_defs = saltext.azurerm.utils.azurerm.paged_object_to_list(
            polconn.policy_definitions.list()
        )

        for policy in policy_defs:
            if not (hide_builtin and policy["policy_type"] == "BuiltIn"):
                result[policy["name"]] = policy
    except HttpResponseError as exc:
        saltext.azurerm.utils.azurerm.log_cloud_error("resource", str(exc), **kwargs)
        result = {"error": str(exc)}

    return result
