"""Search schemas."""
from pydantic import BaseModel


class SearchResult(BaseModel):
    """Search result item."""
    type: str  # location, character, scene, concept
    id: str
    name: str
    snippet: str = ""
