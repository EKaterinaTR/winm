"""Tests for Pydantic schemas."""
from app.models.schemas import (
    LocationCreate,
    LocationRead,
    SceneCreate,
    SearchResult,
    LLMAnswerRequest,
    LLMAnswerResponse,
)


def test_location_create():
    m = LocationCreate(name="Tavern", description="A tavern")
    assert m.name == "Tavern"
    assert m.description == "A tavern"


def test_location_read():
    m = LocationRead(id="loc-1", name="Tavern", description="")
    assert m.id == "loc-1"


def test_scene_create():
    m = SceneCreate(title="Meet", description="", location_id="loc-1", character_ids=["c1"])
    assert m.title == "Meet"
    assert m.character_ids == ["c1"]


def test_search_result():
    m = SearchResult(type="Location", id="loc-1", name="Tavern", snippet="A place")
    assert m.type == "Location"


def test_llm_answer_request():
    m = LLMAnswerRequest(question="What?", role="narrator")
    assert m.question == "What?"
    assert m.role == "narrator"


def test_llm_answer_response():
    m = LLMAnswerResponse(answer="Stub", role="narrator")
    assert m.answer == "Stub"
