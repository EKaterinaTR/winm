"""Characters API (name-unique resource)."""
from app.api.base_resource import NameResourceRouter
from app.models.schemas import CharacterCreate, CharacterUpdate, CharacterRead
from shared.events import EventType


class CharactersRouter(NameResourceRouter[CharacterCreate, CharacterUpdate, CharacterRead]):
    label = "Character"
    prefix = "/characters"
    path_id_param = "character_id"
    create_schema = CharacterCreate
    update_schema = CharacterUpdate
    read_schema = CharacterRead
    event_create = EventType.CHARACTER_CREATE
    event_update = EventType.CHARACTER_UPDATE
    entity_name = "Character"


_router = CharactersRouter()
router = _router.router
