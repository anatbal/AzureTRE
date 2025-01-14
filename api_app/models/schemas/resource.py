from typing import Optional
from pydantic import BaseModel


class ResourcePatch(BaseModel):
    isEnabled: Optional[bool]
    properties: Optional[dict]
    templateVersion: Optional[str]

    class Config:
        schema_extra = {
            "example": {
                "isEnabled": False,
                "templateVersion": "1.0.1",
                "properties": {
                    "display_name": "the display name",
                    "description": "a description",
                    "other_fields": "other properties defined by the resource template"
                }
            }
        }
