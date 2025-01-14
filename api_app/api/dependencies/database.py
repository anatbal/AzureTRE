import logging
from typing import Callable, Type

from azure.cosmos.aio import CosmosClient
from azure.mgmt.cosmosdb.aio import CosmosDBManagementClient
from fastapi import Depends, FastAPI, HTTPException
from fastapi import Request, status
from core import config
from db.errors import UnableToAccessDatabase
from db.repositories.base import BaseRepository
from resources import strings
from azure.identity.aio import (
    DefaultAzureCredential as DefaultAzureCredentialASync,
    ManagedIdentityCredential as ManagedIdentityCredentialASync,
    ChainedTokenCredential as ChainedTokenCredentialASync,
)
from azure.core.credentials import TokenCredential


async def get_credential_async() -> TokenCredential:
    """
    Context manager which yields the default credentials.
    """
    managed_identity = config.MANAGED_IDENTITY_CLIENT_ID
    credential = (
        ChainedTokenCredentialASync(
            ManagedIdentityCredentialASync(client_id=managed_identity)
        )
        if managed_identity
        else DefaultAzureCredentialASync()
    )
    return credential


async def connect_to_db() -> CosmosClient:
    logging.debug(f"Connecting to {config.STATE_STORE_ENDPOINT}")

    try:
        database_credentials = await get_credential_async()
        primary_master_key = await get_store_key(database_credentials)

        if config.STATE_STORE_SSL_VERIFY:
            cosmos_client = CosmosClient(url=config.STATE_STORE_ENDPOINT, credential=primary_master_key)
        else:
            # ignore TLS (setup is a pain) when using local Cosmos emulator.
            cosmos_client = CosmosClient(config.STATE_STORE_ENDPOINT, primary_master_key, connection_verify=False)
        logging.debug("Connection established")
        return cosmos_client
    except Exception:
        logging.exception("Connection to state store could not be established.")


async def get_store_key(credential) -> str:
    if config.STATE_STORE_KEY:
        primary_master_key = config.STATE_STORE_KEY
    else:
        async with CosmosDBManagementClient(credential, subscription_id=config.SUBSCRIPTION_ID) as cosmosdb_mng_client:
            database_keys = await cosmosdb_mng_client.database_accounts.list_keys(resource_group_name=config.RESOURCE_GROUP_NAME, account_name=config.COSMOSDB_ACCOUNT_NAME)
            primary_master_key = database_keys.primary_master_key
            return primary_master_key


async def get_db_client(app: FastAPI) -> CosmosClient:
    if not app.state.cosmos_client:
        app.state.cosmos_client = await connect_to_db()
    return app.state.cosmos_client


async def get_db_client_from_request(request: Request) -> CosmosClient:
    return await get_db_client(request.app)


def get_repository(repo_type: Type[BaseRepository]) -> Callable[[CosmosClient], BaseRepository]:
    async def _get_repo(client: CosmosClient = Depends(get_db_client_from_request)) -> BaseRepository:
        try:
            return await repo_type.create(client)
        except UnableToAccessDatabase:
            logging.exception(strings.STATE_STORE_ENDPOINT_NOT_RESPONDING)
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=strings.STATE_STORE_ENDPOINT_NOT_RESPONDING)

    return _get_repo
