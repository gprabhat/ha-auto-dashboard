"""Builds the full RegistryGraph from the individual registry managers."""
from __future__ import annotations

from homeassistant.core import HomeAssistant

from ..const import CATEGORY_OTHER
from ..models import RegistryGraph
from .area_manager import collect_areas
from .classifier import classify_device, classify_entity
from .device_manager import collect_devices
from .entity_manager import collect_entities


async def async_build_graph(
    hass: HomeAssistant,
    *,
    excluded_areas: set[str] | None = None,
    excluded_entities: set[str] | None = None,
) -> RegistryGraph:
    """Discover areas/devices/entities and assemble the classified graph.

    Registry reads are synchronous but fast (in-memory dict lookups), so
    this only needs to be a coroutine for the sake of coordinator scheduling.

    `excluded_areas`/`excluded_entities` drop the matching nodes before
    linking/classification; excluding an area cascades to the devices and
    entities that live in it.
    """
    graph = RegistryGraph()

    graph.areas = collect_areas(hass)
    graph.devices = collect_devices(hass)
    graph.entities = collect_entities(hass, graph.devices)

    if excluded_areas:
        graph.areas = {aid: a for aid, a in graph.areas.items() if aid not in excluded_areas}
        graph.devices = {
            did: d for did, d in graph.devices.items() if d.area_id not in excluded_areas
        }
        graph.entities = {
            eid: e for eid, e in graph.entities.items() if e.area_id not in excluded_areas
        }
    if excluded_entities:
        graph.entities = {
            eid: e for eid, e in graph.entities.items() if eid not in excluded_entities
        }

    # Link entities onto their owning device and area.
    for entity in graph.entities.values():
        if entity.device_id and entity.device_id in graph.devices:
            graph.devices[entity.device_id].entity_ids.append(entity.entity_id)
        if entity.area_id and entity.area_id in graph.areas:
            graph.areas[entity.area_id].entity_ids.append(entity.entity_id)

    for device in graph.devices.values():
        if device.area_id and device.area_id in graph.areas:
            graph.areas[device.area_id].device_ids.append(device.device_id)

    # Classify entities, then devices (which considers their entities).
    categories: dict[str, list[str]] = {}
    for entity in graph.entities.values():
        entity.category = classify_entity(entity)
        categories.setdefault(entity.category, []).append(entity.entity_id)

    for device in graph.devices.values():
        device_entities = [
            graph.entities[eid]
            for eid in device.entity_ids
            if eid in graph.entities
        ]
        device.category = classify_device(device, device_entities)

    other_ids = categories.pop(CATEGORY_OTHER, [])
    graph.categories = {name: sorted(ids) for name, ids in categories.items()}
    graph.categories[CATEGORY_OTHER] = sorted(other_ids)

    return graph
