import random
import pytest
import asyncio
from typing import Tuple
import config
import logging

from resources.resource import post_resource, disable_and_delete_resource
from resources.workspace import get_workspace_auth_details
from resources import strings as resource_strings
from helpers import get_admin_token


LOGGER = logging.getLogger(__name__)
pytestmark = pytest.mark.asyncio


def pytest_addoption(parser):
    parser.addoption("--verify", action="store", default="true")


@pytest.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()


@pytest.fixture(scope="session")
def verify(pytestconfig):
    if pytestconfig.getoption("verify").lower() == "true":
        return True
    elif pytestconfig.getoption("verify").lower() == "false":
        return False


async def create_or_get_test_workspace(
        auth_type: str,
        verify: bool,
        template_name: str = resource_strings.BASE_WORKSPACE,
        pre_created_workspace_id: str = "",
        client_id: str = "",
        client_secret: str = "") -> Tuple[str, str]:
    if pre_created_workspace_id != "":
        return f"/workspaces/{pre_created_workspace_id}", pre_created_workspace_id

    LOGGER.info(f"Creating workspace {template_name}")

    description = " ".join([x.capitalize() for x in template_name.split("-")[2:]])
    payload = {
        "templateName": template_name,
        "properties": {
            "display_name": f"E2E {description} workspace ({auth_type} AAD)",
            "description": f"{template_name} test workspace for E2E tests",
            "auth_type": auth_type,
            "address_space_size": "small"
        }
    }
    if config.TEST_WORKSPACE_APP_PLAN != "":
        payload["properties"]["app_service_plan_sku"] = config.TEST_WORKSPACE_APP_PLAN

    if auth_type == "Manual":
        payload["properties"]["client_id"] = client_id
        payload["properties"]["client_secret"] = client_secret

    admin_token = await get_admin_token(verify=verify)
    # TODO: Temp fix to solve creation of workspaces - https://github.com/microsoft/AzureTRE/issues/2986
    await asyncio.sleep(random.uniform(1, 9))
    workspace_path, workspace_id = await post_resource(payload, resource_strings.API_WORKSPACES, access_token=admin_token, verify=verify)

    LOGGER.info(f"Workspace {workspace_id} {template_name} created")
    return workspace_path, workspace_id


async def create_or_get_test_workpace_service(workspace_path, workspace_owner_token, pre_created_workspace_service_id, verify):
    if pre_created_workspace_service_id != "":
        workspace_service_id = pre_created_workspace_service_id
        workspace_service_path = f"{workspace_path}/{resource_strings.API_WORKSPACE_SERVICES}/{workspace_service_id}"
        return workspace_service_path, workspace_service_id

    # create a guac service
    service_payload = {
        "templateName": resource_strings.GUACAMOLE_SERVICE,
        "properties": {
            "display_name": "Workspace service test",
            "description": ""
        }
    }

    workspace_service_path, workspace_service_id = await post_resource(
        payload=service_payload,
        endpoint=f'/api{workspace_path}/{resource_strings.API_WORKSPACE_SERVICES}',
        access_token=workspace_owner_token,
        verify=verify)

    return workspace_service_path, workspace_service_id


async def clean_up_test_workspace(pre_created_workspace_id: str, workspace_path: str, verify: bool):
    # Only delete the workspace if it wasn't pre-created
    if pre_created_workspace_id == "":
        LOGGER.info(f"Deleting workspace {pre_created_workspace_id}")
        admin_token = await get_admin_token(verify=verify)
        await disable_and_delete_resource(f'/api{workspace_path}', admin_token, verify)


async def clean_up_test_workspace_service(pre_created_workspace_service_id: str, workspace_service_path: str, verify: bool):
    if pre_created_workspace_service_id == "":
        LOGGER.info(f"Deleting workspace service {pre_created_workspace_service_id}")
        admin_token = await get_admin_token(verify=verify)
        await disable_and_delete_resource(f'/api{workspace_service_path}', admin_token, verify)


# Session scope isn't in effect with python-xdist: https://github.com/microsoft/AzureTRE/issues/2868
@pytest.fixture(scope="session")
async def setup_test_workspace(verify) -> Tuple[str, str, str]:
    pre_created_workspace_id = config.TEST_WORKSPACE_ID
    # Set up
    workspace_path, workspace_id = await create_or_get_test_workspace(
        auth_type="Manual", verify=verify, pre_created_workspace_id=pre_created_workspace_id, client_id=config.TEST_WORKSPACE_APP_ID, client_secret=config.TEST_WORKSPACE_APP_SECRET)

    admin_token = await get_admin_token(verify=verify)
    workspace_owner_token, _ = await get_workspace_auth_details(admin_token=admin_token, workspace_id=workspace_id, verify=verify)
    yield workspace_path, workspace_id, workspace_owner_token

    # Tear-down
    clean_up_test_workspace(pre_created_workspace_id=pre_created_workspace_id, workspace_path=workspace_path, verify=verify)


# Session scope isn't in effect with python-xdist: https://github.com/microsoft/AzureTRE/issues/2868
@pytest.fixture(scope="session")
async def setup_test_workspace_and_workspace_service(verify, setup_test_workspace):
    # Set up
    workspace_path, workspace_id, workspace_owner_token = setup_test_workspace

    pre_created_workspace_service_id = config.TEST_WORKSPACE_SERVICE_ID
    workspace_service_path, workspace_service_id = await create_or_get_test_workpace_service(
        workspace_path,
        workspace_owner_token=workspace_owner_token,
        pre_created_workspace_service_id=pre_created_workspace_service_id,
        verify=verify)

    yield workspace_path, workspace_id, workspace_service_path, workspace_service_id, workspace_owner_token

    clean_up_test_workspace_service(pre_created_workspace_service_id=pre_created_workspace_service_id, workspace_service_path=workspace_service_path, verify=verify)


# Session scope isn't in effect with python-xdist: https://github.com/microsoft/AzureTRE/issues/2868
@pytest.fixture(scope="session")
async def setup_test_aad_workspace(verify) -> Tuple[str, str, str]:
    pre_created_workspace_id = config.TEST_AAD_WORKSPACE_ID
    # Set up
    workspace_path, workspace_id = await create_or_get_test_workspace(auth_type="Automatic", verify=verify, pre_created_workspace_id=pre_created_workspace_id)

    admin_token = await get_admin_token(verify=verify)
    workspace_owner_token, _ = await get_workspace_auth_details(admin_token=admin_token, workspace_id=workspace_id, verify=verify)
    yield workspace_path, workspace_id, workspace_owner_token

    # Tear-down
    clean_up_test_workspace(pre_created_workspace_id=pre_created_workspace_id, workspace_path=workspace_path, verify=verify)


# Session scope isn't in effect with python-xdist: https://github.com/microsoft/AzureTRE/issues/2868
@pytest.fixture(scope="session")
async def setup_test_airlock_import_review_workspace_and_workspace_service(verify) -> Tuple[str, str, str, str, str]:
    pre_created_workspace_id = config.TEST_AIRLOCK_IMPORT_REVIEW_WORKSPACE_ID
    # Set up
    workspace_path, workspace_id = await create_or_get_test_workspace(auth_type="Automatic", verify=verify, template_name=resource_strings.AIRLOCK_IMPORT_REVIEW_WORKSPACE, pre_created_workspace_id=pre_created_workspace_id)

    admin_token = await get_admin_token(verify=verify)
    workspace_owner_token, _ = await get_workspace_auth_details(admin_token=admin_token, workspace_id=workspace_id, verify=verify)
    pre_created_workspace_service_id = config.TEST_AIRLOCK_IMPORT_REVIEW_WORKSPACE_SERVICE_ID

    workspace_service_path, workspace_service_id = await create_or_get_test_workpace_service(
        workspace_path,
        workspace_owner_token=workspace_owner_token,
        pre_created_workspace_service_id=pre_created_workspace_service_id,
        verify=verify)

    workspace_owner_token, _ = await get_workspace_auth_details(admin_token=admin_token, workspace_id=workspace_id, verify=verify)
    yield workspace_path, workspace_id, workspace_service_path, workspace_service_id, workspace_owner_token

    # Tear-down
    clean_up_test_workspace_service(pre_created_workspace_service_id=pre_created_workspace_service_id, workspace_service_path=workspace_service_path, verify=verify)
    clean_up_test_workspace(pre_created_workspace_id=pre_created_workspace_id, workspace_path=workspace_path, verify=verify)
