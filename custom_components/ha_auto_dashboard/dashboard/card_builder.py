"""Builds individual Lovelace card dicts from graph nodes.

Kept deliberately dumb: each function takes plain data and returns a plain
dict matching the Lovelace card schema, so the factory/compiler can be
tested without any Home Assistant runtime.
"""
from __future__ import annotations

from ..models import AreaNode, DeviceNode, EntityNode, RegistryGraph


def visible_entity_ids(entities: list[EntityNode]) -> list[str]:
    """Filter out disabled/hidden entities, which have no state to show."""
    return [entity.entity_id for entity in entities if not entity.disabled and not entity.hidden]


def area_card(area: AreaNode) -> dict:
    """A built-in `area` card: HA renders the area's controls/sensors for us."""
    return {"type": "area", "area": area.area_id}


def entities_card(title: str, entity_ids: list[str]) -> dict | None:
    """An `entities` card, or None if there's nothing to show (card would be empty)."""
    if not entity_ids:
        return None
    return {"type": "entities", "title": title, "entities": entity_ids}


def device_card(device: DeviceNode, graph: RegistryGraph) -> dict | None:
    entities = [graph.entities[eid] for eid in device.entity_ids if eid in graph.entities]
    return entities_card(device.name, visible_entity_ids(entities))


def picture_entity_card(entity_id: str) -> dict:
    return {"type": "picture-entity", "entity": entity_id}


def markdown_card(content: str) -> dict:
    return {"type": "markdown", "content": content}
