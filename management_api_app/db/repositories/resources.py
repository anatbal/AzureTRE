from azure.cosmos import CosmosClient
from jsonschema import validate
from pydantic import UUID4

from core import config
from db.errors import EntityDoesNotExist
from db.repositories.base import BaseRepository
from db.repositories.resource_templates import ResourceTemplateRepository
from models.domain.resource import ResourceType, Resource, Status


class ResourceRepository(BaseRepository):
    def __init__(self, client: CosmosClient):
        super().__init__(client, config.STATE_STORE_RESOURCES_CONTAINER)

    @staticmethod
    def _active_resources_query():
        return f'SELECT * FROM c WHERE c.deployment.status != "{Status.Deleted}"'

    def _active_resources_by_type_query(self, resource_type: ResourceType):
        return self._active_resources_query() + f' AND c.resourceType = "{resource_type}"'

    def _active_resources_by_id_query(self, resource_id: str):
        return self._active_resources_query() + f' AND c.id = "{resource_id}"'

    def _active_resources_by_type_and_id_query(self, resource_id: str, resource_type: ResourceType):
        return self._active_resources_by_type_query(resource_type) + f' AND c.id = "{resource_id}"'

    @staticmethod
    def _validate_resource_parameters(resource_input, resource_template):
        validate(instance=resource_input["properties"], schema=resource_template)

    def _get_enriched_template(self, template_name: str, resource_type: ResourceType):
        template_repo = ResourceTemplateRepository(self._client)
        template = template_repo.get_current_template(template_name, resource_type)
        return template_repo.enrich_template(template)

    def get_resource_dict_by_id(self, resource_id: UUID4) -> dict:
        query = self._active_resources_by_id_query(str(resource_id))
        resources = self.query(query=query)
        if not resources:
            raise EntityDoesNotExist
        return resources[0]

    def get_resource_dict_by_type_and_id(self, resource_id: str, resource_type: ResourceType) -> dict:
        query = self._active_resources_by_type_and_id_query(resource_id, resource_type)
        resources = self.query(query=query)
        if not resources:
            raise EntityDoesNotExist
        return resources[0]

    def validate_input_against_template(self, template_name: str, resource_input, resource_type: ResourceType) -> str:
        try:
            template = self._get_enriched_template(template_name, resource_type)
            template_version = template["version"]
        except EntityDoesNotExist:
            raise ValueError(f'The template for "{template_name}" does not exist')

        self._validate_resource_parameters(resource_input.dict(), template)

        return template_version

    def mark_resource_as_deleting(self, resource: Resource) -> Status:
        current_deletion_status = resource.deployment.status

        resource.deployment.status = Status.Deleting
        self.update_item(resource)

        return current_deletion_status

    def restore_previous_deletion_state(self, resource: Resource, previous_deletion_status: Status):
        resource.deployment.status = previous_deletion_status
        self.update_item(resource)