"""Builds individual Lovelace card dicts from graph nodes.

Favors Mushroom (custom:mushroom-*) and Bubble Card (custom:bubble-card)
for entity/section chrome, and native `map`/`history-graph`/`logbook`
cards plus `custom:mini-graph-card` for anything with real history to
show. `CardTheme` is the entry point the factory actually uses: it picks
Mushroom/Bubble Card/mini-graph-card when the resources module confirms
they're registered, and falls back to native HA cards (`tile`, `light`,
`thermostat`, `heading`, `button`, `sensor` with an inline graph, ...)
otherwise, so a dashboard never ships a card that renders as "custom
element doesn't exist".

Kept deliberately dumb: each function takes plain data and returns a
plain dict matching the Lovelace card schema, so the factory/compiler
can be tested without any Home Assistant runtime.
"""
from __future__ import annotations

from ..const import (
    MUSHROOM_DOMAIN_CARDS,
    MUSHROOM_GENERIC_CARD,
    NATIVE_DOMAIN_CARDS,
    NATIVE_GENERIC_CARD,
    NATIVE_TILE_FEATURES,
)
from ..models import AreaNode, DeviceNode, EntityNode, RegistryGraph
from .resources import ALL_PRESENT, FrontendResources


def visible_entities(entities: list[EntityNode]) -> list[EntityNode]:
    """Filter out disabled/hidden entities, which have no state to show."""
    return [entity for entity in entities if not entity.disabled and not entity.hidden]


def visible_entity_ids(entities: list[EntityNode]) -> list[str]:
    return [entity.entity_id for entity in visible_entities(entities)]


def is_graphable(entity: EntityNode) -> bool:
    """True for numeric sensors worth trending on a history graph."""
    return entity.domain == "sensor" and bool(entity.unit_of_measurement)


def mushroom_card(entity: EntityNode) -> dict:
    card_type = MUSHROOM_DOMAIN_CARDS.get(entity.domain, MUSHROOM_GENERIC_CARD)
    return {"type": card_type, "entity": entity.entity_id}


def native_entity_card(entity: EntityNode) -> dict:
    card_type = NATIVE_DOMAIN_CARDS.get(entity.domain, NATIVE_GENERIC_CARD)
    card: dict = {"type": card_type, "entity": entity.entity_id}
    if card_type == "tile":
        features = NATIVE_TILE_FEATURES.get(entity.domain)
        if features:
            card["features"] = features
    return card


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


def native_graph_card(entity: EntityNode, *, hours_to_show: int = 24) -> dict:
    """Native `sensor` card fallback: still renders an inline trend line."""
    return {
        "type": "sensor",
        "entity": entity.entity_id,
        "name": entity.name,
        "graph": "line",
        "hours_to_show": hours_to_show,
    }


def grid(cards: list[dict], *, columns: int | None = None, title: str | None = None) -> dict:
    """A responsive `type: grid` layout wrapping the given cards, with an
    optional native section heading (the `grid` card's own `title`, not a
    separate header card - one less card to render, and it works whether
    or not Bubble Card is installed).

    Column count scales with content instead of a fixed number, capped
    at 4 so rows stay readable on a wide dashboard. Pass a smaller
    `columns` explicitly to make a group of cards (e.g. simple toggles)
    render noticeably bigger than the rest.
    """
    if columns is None:
        columns = max(1, min(4, len(cards)))
    card: dict = {"type": "grid", "columns": columns, "square": False, "cards": cards}
    if title:
        card["title"] = title
    return card


def bubble_separator(name: str, icon: str | None = None) -> dict:
    """A `custom:bubble-card` section header."""
    card: dict = {"type": "custom:bubble-card", "card_type": "separator", "name": name}
    if icon:
        card["icon"] = icon
    return card


def native_heading_card(name: str, icon: str | None = None) -> dict:
    """Native `heading` card fallback for a section header."""
    card: dict = {"type": "heading", "heading": name}
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


def native_button_card(entity_id: str, *, name: str | None = None, icon: str | None = None) -> dict:
    card: dict = {"type": "button", "entity": entity_id}
    if name:
        card["name"] = name
    if icon:
        card["icon"] = icon
    return card


def mushroom_title_card(title: str, subtitle: str | None = None) -> dict:
    card: dict = {"type": "custom:mushroom-title-card", "title": title}
    if subtitle:
        card["subtitle"] = subtitle
    return card


def mushroom_chips_card(chips: list[dict]) -> dict | None:
    if not chips:
        return None
    return {"type": "custom:mushroom-chips-card", "chips": chips}


def entity_chip(entity_id: str, *, icon: str | None = None) -> dict:
    chip: dict = {"type": "entity", "entity": entity_id}
    if icon:
        chip["icon"] = icon
    return chip


def weather_chip(entity_id: str) -> dict:
    return {"type": "weather", "entity": entity_id, "show_conditions": True, "show_temperature": True}


def toggle_entities_chip(entity_ids: list[str], *, icon: str, icon_color: str, service: str) -> dict | None:
    """A chip that toggles a whole group of entities in one tap (e.g. all lights)."""
    if not entity_ids:
        return None
    return {
        "type": "template",
        "icon": icon,
        "icon_color": icon_color,
        "tap_action": {
            "action": "call-service",
            "service": service,
            "service_data": {"entity_id": entity_ids},
        },
    }


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


def picture_glance_card(camera_entity_id: str, extra_entity_ids: list[str] | None = None, *, title: str | None = None) -> dict:
    card: dict = {"type": "picture-glance", "camera_image": camera_entity_id, "entities": extra_entity_ids or []}
    if title:
        card["title"] = title
    return card


def entities_card(title: str, entity_ids: list[str]) -> dict | None:
    """Plain `entities` card fallback for cases a richer card doesn't fit."""
    if not entity_ids:
        return None
    return {"type": "entities", "title": title, "entities": entity_ids}


def markdown_card(content: str) -> dict:
    return {"type": "markdown", "content": content}


class CardTheme:
    """Picks concrete card types for entities/sections based on which
    optional frontend resources are actually installed.
    """

    def __init__(self, resources: FrontendResources | None = None) -> None:
        self.resources = resources or ALL_PRESENT

    def entity(self, entity: EntityNode) -> dict:
        if is_graphable(entity):
            return self.graph(entity)
        if self.resources.mushroom:
            return mushroom_card(entity)
        return native_entity_card(entity)

    def graph(self, entity: EntityNode, *, hours_to_show: int = 24) -> dict:
        if self.resources.mini_graph_card:
            return mini_graph_card(entity, hours_to_show=hours_to_show)
        return native_graph_card(entity, hours_to_show=hours_to_show)

    def separator(self, name: str, icon: str | None = None) -> dict:
        if self.resources.bubble_card:
            return bubble_separator(name, icon)
        return native_heading_card(name, icon)

    def button(self, entity_id: str, *, name: str | None = None, icon: str | None = None) -> dict:
        if self.resources.bubble_card:
            return bubble_button(entity_id, name=name, icon=icon)
        return native_button_card(entity_id, name=name, icon=icon)

    def device(self, device: DeviceNode, graph: RegistryGraph) -> dict | None:
        entities = visible_entities([graph.entities[eid] for eid in device.entity_ids if eid in graph.entities])
        if not entities:
            return None
        return grid([self.entity(entity) for entity in entities], title=device.name)
