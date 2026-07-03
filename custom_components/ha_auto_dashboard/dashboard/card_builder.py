"""Builds individual Lovelace card dicts from graph nodes.

Favors Mushroom (custom:mushroom-*) and Bubble Card (custom:bubble-card)
for entity/section chrome, and native `map`/`history-graph`/`logbook`
cards plus `custom:mini-graph-card` for anything with real history to
show. Kept deliberately dumb: each function takes plain data and returns
a plain dict matching the Lovelace card schema, so the factory/compiler
can be tested without any Home Assistant runtime.

These are HACS-distributed frontend resources, not built into HA core;
the generated dashboards assume Mushroom, Bubble Card and mini-graph-card
are already installed as Lovelace resources.
"""
from __future__ import annotations

from ..const import LOCATION_DOMAINS, MUSHROOM_DOMAIN_CARDS, MUSHROOM_GENERIC_CARD
from ..models import AreaNode, DeviceNode, EntityNode, RegistryGraph


def visible_entities(entities: list[EntityNode]) -> list[EntityNode]:
    """Filter out disabled/hidden entities, which have no state to show."""
    return [entity for entity in entities if not entity.disabled and not entity.hidden]


def visible_entity_ids(entities: list[EntityNode]) -> list[str]:
    return [entity.entity_id for entity in visible_entities(entities)]


def is_graphable(entity: EntityNode) -> bool:
    """True for numeric sensors worth trending on a history graph."""
    return entity.domain == "sensor" and bool(entity.unit_of_measurement)


def mushroom_card(entity: EntityNode) -> dict:
    """A domain-appropriate Mushroom card, or the generic one as a fallback."""
    card_type = MUSHROOM_DOMAIN_CARDS.get(entity.domain, MUSHROOM_GENERIC_CARD)
    return {"type": card_type, "entity": entity.entity_id}


def mini_graph_card(entity: EntityNode, *, hours_to_show: int = 24) -> dict:
    """A `custom:mini-graph-card` trend line for a numeric sensor."""
    return {
        "type": "custom:mini-graph-card",
        "name": entity.name,
        "entities": [entity.entity_id],
        "hours_to_show": hours_to_show,
        "points_per_hour": 2,
        "line_width": 2,
        "show": {"labels": True, "points": False},
    }


def entity_card(entity: EntityNode) -> dict:
    """Route a single entity to its best card: graph, Mushroom, or generic."""
    if is_graphable(entity):
        return mini_graph_card(entity)
    return mushroom_card(entity)


def grid(cards: list[dict], *, columns: int = 2) -> dict:
    """A responsive `type: grid` layout wrapping the given cards."""
    return {"type": "grid", "columns": columns, "square": False, "cards": cards}


def vertical_stack(cards: list[dict]) -> dict:
    return {"type": "vertical-stack", "cards": cards}


def bubble_separator(name: str, icon: str | None = None) -> dict:
    """A `custom:bubble-card` section header."""
    card: dict = {"type": "custom:bubble-card", "card_type": "separator", "name": name}
    if icon:
        card["icon"] = icon
    return card


def bubble_button(entity_id: str, *, name: str | None = None, icon: str | None = None) -> dict:
    """A `custom:bubble-card` button, good for a quick-actions row."""
    card: dict = {"type": "custom:bubble-card", "card_type": "button", "entity": entity_id}
    if name:
        card["name"] = name
    if icon:
        card["icon"] = icon
    return card


def mushroom_chips_card(chips: list[dict]) -> dict:
    return {"type": "custom:mushroom-chips-card", "chips": chips}


def entity_chip(entity_id: str, *, icon: str | None = None) -> dict:
    chip: dict = {"type": "entity", "entity": entity_id}
    if icon:
        chip["icon"] = icon
    return chip


def area_card(area: AreaNode) -> dict:
    """The built-in `area` card: HA renders the area's controls/sensors for us."""
    return {"type": "area", "area": area.area_id}


def map_card(entity_ids: list[str], *, title: str | None = None) -> dict:
    card: dict = {"type": "map", "entities": [{"entity": eid} for eid in entity_ids]}
    if title:
        card["title"] = title
    return card


def history_graph_card(title: str, entity_ids: list[str]) -> dict | None:
    if not entity_ids:
        return None
    return {"type": "history-graph", "title": title, "entities": entity_ids}


def logbook_card(entity_ids: list[str], *, hours_to_show: int = 24) -> dict | None:
    if not entity_ids:
        return None
    return {"type": "logbook", "entities": entity_ids, "hours_to_show": hours_to_show}


def picture_glance_card(camera_entity_id: str, extra_entity_ids: list[str] | None = None) -> dict:
    card: dict = {"type": "picture-glance", "camera_image": camera_entity_id, "entities": extra_entity_ids or []}
    return card


def entities_card(title: str, entity_ids: list[str]) -> dict | None:
    """Plain `entities` card fallback for cases a richer card doesn't fit."""
    if not entity_ids:
        return None
    return {"type": "entities", "title": title, "entities": entity_ids}


def device_card(device: DeviceNode, graph: RegistryGraph) -> dict | None:
    entities = visible_entities([graph.entities[eid] for eid in device.entity_ids if eid in graph.entities])
    if not entities:
        return None
    cards = [entity_card(entity) for entity in entities]
    return vertical_stack([bubble_separator(device.name), grid(cards)])


def markdown_card(content: str) -> dict:
    return {"type": "markdown", "content": content}
