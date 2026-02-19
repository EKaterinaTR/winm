"""Location schemas."""
from pydantic import BaseModel, Field


class LocationCreate(BaseModel):
    """Create location."""
    name: str = Field(..., min_length=1)
    description: str = ""


class LocationUpdate(BaseModel):
    """Update location."""
    name: str | None = Field(None, min_length=1)
    description: str | None = None


class LocationRead(BaseModel):
    """Location read."""
    id: str
    name: str
    description: str
