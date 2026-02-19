"""Character schemas."""
from pydantic import BaseModel, Field


class CharacterCreate(BaseModel):
    """Create character."""
    name: str = Field(..., min_length=1)
    description: str = ""


class CharacterUpdate(BaseModel):
    """Update character."""
    name: str | None = Field(None, min_length=1)
    description: str | None = None


class CharacterRead(BaseModel):
    """Character read."""
    id: str
    name: str
    description: str
