"""Scene schemas."""
from pydantic import BaseModel, Field


class SceneCreate(BaseModel):
    """Create scene."""
    title: str = Field(..., min_length=1)
    description: str = ""
    location_id: str = Field(..., min_length=1)
    character_ids: list[str] = Field(default_factory=list)


class SceneUpdate(BaseModel):
    """Update scene."""
    title: str | None = Field(None, min_length=1)
    description: str | None = None
    location_id: str | None = None
    character_ids: list[str] | None = None


class SceneRead(BaseModel):
    """Scene read."""
    id: str
    title: str
    description: str
    location_id: str
    character_ids: list[str]
