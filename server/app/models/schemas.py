"""Pydantic schemas for API."""
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


class SearchResult(BaseModel):
    """Search result item."""
    type: str  # location, character, scene, concept
    id: str
    name: str
    snippet: str = ""


class LLMAnswerRequest(BaseModel):
    """Request for LLM answer (stub)."""
    question: str = Field(..., min_length=1)
    role: str | None = None  # character id or "narrator"


class LLMAnswerResponse(BaseModel):
    """LLM answer (stub)."""
    answer: str
    role: str | None = None
