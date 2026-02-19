"""Locations API (name-unique resource)."""
from app.api.base_resource import NameResourceRouter
from app.models.schemas import LocationCreate, LocationUpdate, LocationRead
from shared.events import EventType


class LocationsRouter(NameResourceRouter[LocationCreate, LocationUpdate, LocationRead]):
    label = "Location"
    prefix = "/locations"
    path_id_param = "location_id"
    create_schema = LocationCreate
    update_schema = LocationUpdate
    read_schema = LocationRead
    event_create = EventType.LOCATION_CREATE
    event_update = EventType.LOCATION_UPDATE
    entity_name = "Location"


_router = LocationsRouter()
router = _router.router
