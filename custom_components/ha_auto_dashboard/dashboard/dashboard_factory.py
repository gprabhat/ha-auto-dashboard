"""Assembles Lovelace view/card structures for each dashboard from the graph."""
from __future__ import annotations

from ..const import CATEGORY_HOMELAB, CATEGORY_NETWORK, CATEGORY_SECURITY, CATEGORY_UPDATES
from ..models import RegistryGraph
from .card_builder import area_card, device_card, entities_card, markdown_card, picture_entity_card


def _category_entity_ids(graph: RegistryGraph, category: str) -> list[str]:
    return [
        entity_id
        for entity_id in graph.categories.get(category, [])
        if (entity := graph.entities.get(entity_id)) and not entity.disabled and not entity.hidden
    ]


def _area_entity_ids(graph: RegistryGraph, area_id: str) -> list[str]:
    return [
        entity_id
        for entity_id in graph.areas[area_id].entity_ids
        if (entity := graph.entities.get(entity_id)) and not entity.disabled and not entity.hidden
    ]


def build_home_view(graph: RegistryGraph) -> dict:
    cards = [area_card(area) for area in sorted(graph.areas.values(), key=lambda a: a.name)]
    return {
        "title": "Home",
        "path": "home",
        "icon": "mdi:home",
        "cards": cards or [markdown_card("No areas discovered yet.")],
    }


def build_rooms_views(graph: RegistryGraph) -> list[dict]:
    views = []
    for area in sorted(graph.areas.values(), key=lambda a: a.name):
        card = entities_card(area.name, _area_entity_ids(graph, area.area_id))
        views.append(
            {
                "title": area.name,
                "path": area.area_id,
                "icon": area.icon or "mdi:sofa",
                "cards": [card] if card else [markdown_card("No entities in this area yet.")],
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
    orphan_ids = [eid for eid in _category_entity_ids(graph, CATEGORY_HOMELAB) if eid not in device_entity_ids]
    if orphan_card := entities_card("Other", orphan_ids):
        cards.append(orphan_card)

    return {
        "title": "Homelab",
        "path": "homelab",
        "icon": "mdi:server",
        "cards": cards or [markdown_card("No homelab entities discovered yet.")],
    }


def build_security_view(graph: RegistryGraph) -> dict:
    entity_ids = _category_entity_ids(graph, CATEGORY_SECURITY)
    camera_ids = [eid for eid in entity_ids if eid.startswith("camera.")]
    other_ids = [eid for eid in entity_ids if not eid.startswith("camera.")]

    cards = [picture_entity_card(eid) for eid in camera_ids]
    if other_card := entities_card("Security", other_ids):
        cards.append(other_card)

    return {
        "title": "Security",
        "path": "security",
        "icon": "mdi:shield-home",
        "cards": cards or [markdown_card("No security entities discovered yet.")],
    }


def build_monitoring_view(graph: RegistryGraph) -> dict:
    card = entities_card("Network", _category_entity_ids(graph, CATEGORY_NETWORK))
    return {
        "title": "Monitoring",
        "path": "monitoring",
        "icon": "mdi:chart-line",
        "cards": [card] if card else [markdown_card("No monitoring entities discovered yet.")],
    }


def build_admin_view(graph: RegistryGraph) -> dict:
    card = entities_card("Updates", _category_entity_ids(graph, CATEGORY_UPDATES))
    return {
        "title": "Admin",
        "path": "admin",
        "icon": "mdi:cog",
        "cards": [card] if card else [markdown_card("No update entities discovered yet.")],
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

    cards = [
        card
        for area in sorted(cloud_areas, key=lambda a: a.name)
        if (card := entities_card(area.name, _area_entity_ids(graph, area.area_id)))
    ]
    if not cards:
        return None

    return {"title": "Cloud", "path": "cloud", "icon": "mdi:cloud", "cards": cards}
