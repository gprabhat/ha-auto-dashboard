"""Assembles Lovelace view/card structures for each dashboard from the graph."""
from __future__ import annotations

from ..const import (
    CATEGORY_HOMELAB,
    CATEGORY_NETWORK,
    CATEGORY_SECURITY,
    CATEGORY_UPDATES,
    LOCATION_DOMAINS,
)
from ..models import RegistryGraph
from .card_builder import (
    area_card,
    bubble_separator,
    device_card,
    entity_card,
    grid,
    history_graph_card,
    is_graphable,
    logbook_card,
    map_card,
    markdown_card,
    mini_graph_card,
    picture_glance_card,
    vertical_stack,
    visible_entities,
)


def _category_entities(graph: RegistryGraph, category: str) -> list:
    return visible_entities(
        [graph.entities[eid] for eid in graph.categories.get(category, []) if eid in graph.entities]
    )


def _area_entities(graph: RegistryGraph, area_id: str) -> list:
    return visible_entities(
        [graph.entities[eid] for eid in graph.areas[area_id].entity_ids if eid in graph.entities]
    )


def build_home_view(graph: RegistryGraph) -> dict:
    cards: list[dict] = []

    location_ids = [
        entity.entity_id
        for entity in visible_entities(graph.entities.values())
        if entity.domain in LOCATION_DOMAINS
    ]
    if location_ids:
        cards.append(map_card(location_ids, title="Family & Devices"))

    areas = sorted(graph.areas.values(), key=lambda a: a.name)
    if areas:
        cards.append(bubble_separator("Rooms", icon="mdi:floor-plan"))
        cards.append(grid([area_card(area) for area in areas], columns=2))

    highlight_ids = [
        entity.entity_id
        for entity in _category_entities(graph, CATEGORY_SECURITY) + _category_entities(graph, CATEGORY_UPDATES)
    ]
    if card := logbook_card(highlight_ids):
        cards.append(bubble_separator("Recent Activity", icon="mdi:history"))
        cards.append(card)

    return {
        "title": "Home",
        "path": "home",
        "icon": "mdi:home",
        "cards": cards or [markdown_card("No areas discovered yet.")],
    }


def build_rooms_views(graph: RegistryGraph) -> list[dict]:
    views = []
    for area in sorted(graph.areas.values(), key=lambda a: a.name):
        entities = _area_entities(graph, area.area_id)
        if entities:
            cards = [
                bubble_separator(area.name, icon=area.icon or "mdi:sofa"),
                grid([entity_card(entity) for entity in entities], columns=2),
            ]
        else:
            cards = [markdown_card("No entities in this area yet.")]
        views.append(
            {
                "title": area.name,
                "path": area.area_id,
                "icon": area.icon or "mdi:sofa",
                "cards": cards,
            }
        )
    if not views:
        views = [{"title": "Rooms", "path": "rooms", "cards": [markdown_card("No areas discovered yet.")]}]
    return views


def build_homelab_view(graph: RegistryGraph) -> dict:
    devices = sorted(
        (d for d in graph.devices.values() if d.category == CATEGORY_HOMELAB and not d.disabled),
        key=lambda d: d.name,
    )
    cards = [card for device in devices if (card := device_card(device, graph))]

    device_entity_ids = {eid for device in devices for eid in device.entity_ids}
    orphans = [e for e in _category_entities(graph, CATEGORY_HOMELAB) if e.entity_id not in device_entity_ids]
    if orphans:
        cards.append(vertical_stack([bubble_separator("Other"), grid([entity_card(e) for e in orphans])]))

    return {
        "title": "Homelab",
        "path": "homelab",
        "icon": "mdi:server",
        "cards": cards or [markdown_card("No homelab entities discovered yet.")],
    }


def build_security_view(graph: RegistryGraph) -> dict:
    entities = _category_entities(graph, CATEGORY_SECURITY)
    cameras = [e for e in entities if e.domain == "camera"]
    others = [e for e in entities if e.domain != "camera"]

    camera_device_ids = {camera.device_id for camera in cameras if camera.device_id}

    cards: list[dict] = []
    for camera in cameras:
        sibling_ids = [
            e.entity_id
            for e in others
            if camera.device_id and e.device_id == camera.device_id
        ]
        cards.append(picture_glance_card(camera.entity_id, sibling_ids))

    other_only = [e for e in others if e.device_id not in camera_device_ids]
    if other_only:
        cards.append(grid([entity_card(e) for e in other_only], columns=2))

    if card := logbook_card([e.entity_id for e in entities]):
        cards.append(bubble_separator("Recent Events", icon="mdi:history"))
        cards.append(card)

    return {
        "title": "Security",
        "path": "security",
        "icon": "mdi:shield-home",
        "cards": cards or [markdown_card("No security entities discovered yet.")],
    }


def build_monitoring_view(graph: RegistryGraph) -> dict:
    entities = _category_entities(graph, CATEGORY_NETWORK)
    graphable = [e for e in entities if is_graphable(e)]
    other = [e for e in entities if not is_graphable(e)]

    cards: list[dict] = []
    if trend_card := history_graph_card("Network Trends", [e.entity_id for e in graphable]):
        cards.append(trend_card)
    if graphable:
        cards.append(grid([mini_graph_card(e) for e in graphable], columns=2))
    if other:
        cards.append(grid([entity_card(e) for e in other], columns=2))

    return {
        "title": "Monitoring",
        "path": "monitoring",
        "icon": "mdi:chart-line",
        "cards": cards or [markdown_card("No monitoring entities discovered yet.")],
    }


def build_admin_view(graph: RegistryGraph) -> dict:
    entities = _category_entities(graph, CATEGORY_UPDATES)
    cards: list[dict] = []
    if entities:
        cards.append(grid([entity_card(e) for e in entities], columns=2))
    if card := logbook_card([e.entity_id for e in entities]):
        cards.append(bubble_separator("Update History", icon="mdi:history"))
        cards.append(card)

    return {
        "title": "Admin",
        "path": "admin",
        "icon": "mdi:cog",
        "cards": cards or [markdown_card("No update entities discovered yet.")],
    }


def build_cloud_view(graph: RegistryGraph) -> dict | None:
    """Only produced when an area looks cloud-related; there's no dedicated
    "cloud" category, so this piggybacks on area naming (e.g. "Cloud Server").
    """
    cloud_areas = [
        area for area in graph.areas.values() if "cloud" in area.name.lower() or "cloud" in area.area_id.lower()
    ]
    if not cloud_areas:
        return None

    cards: list[dict] = []
    for area in sorted(cloud_areas, key=lambda a: a.name):
        entities = _area_entities(graph, area.area_id)
        if entities:
            cards.append(bubble_separator(area.name, icon="mdi:cloud"))
            cards.append(grid([entity_card(e) for e in entities], columns=2))

    if not cards:
        return None

    return {"title": "Cloud", "path": "cloud", "icon": "mdi:cloud", "cards": cards}
