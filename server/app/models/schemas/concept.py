"""Concept schemas."""
from pydantic import BaseModel, Field


class ConceptCreate(BaseModel):
    """Create concept."""
    name: str = Field(..., min_length=1)
    description: str = ""


class ConceptUpdate(BaseModel):
    """Update concept."""
    name: str | None = Field(None, min_length=1)
    description: str | None = None


class ConceptRead(BaseModel):
    """Concept read."""
    id: str
    name: str
    description: str
