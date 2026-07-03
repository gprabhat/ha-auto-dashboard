"""Assembles Lovelace view/card structures for each dashboard from the graph."""
from __future__ import annotations

from ..const import (
    CATEGORY_HOMELAB,
    CATEGORY_NETWORK,
    CATEGORY_SECURITY,
    CATEGORY_UPDATES,
    LOCATION_DOMAINS,
)
from ..models import EntityNode, RegistryGraph
from .card_builder import (
    CardTheme,
    area_card,
    grid,
    history_graph_card,
    is_graphable,
    logbook_card,
    map_card,
    markdown_card,
    mushroom_chips_card,
    mushroom_title_card,
    picture_glance_card,
    toggle_entities_chip,
    visible_entities,
    weather_chip,
)
from .icons import guess_area_icon

# Domain groups used to split a mixed-domain set of entities into titled,
# neatly-boxed sections instead of one flat grid. Switches/locks get a
# smaller column count than the rest, so each tile renders noticeably
# bigger - simple toggles read better big, dense sensor grids read better
# small.
_DOMAIN_GROUPS: tuple[tuple[str, frozenset[str], int | None], ...] = (
    ("Lights", frozenset({"light"}), None),
    ("Climate & Covers", frozenset({"climate", "cover", "fan"}), None),
    ("Media", frozenset({"media_player"}), None),
    ("Switches & Locks", frozenset({"switch", "lock", "input_boolean"}), 2),
    ("Sensors", frozenset({"sensor", "binary_sensor"}), None),
)


def _grouped_grid_cards(entities: list[EntityNode], theme: CardTheme) -> list[dict]:
    """Split mixed-domain entities into titled, domain-grouped grid cards."""
    remaining = list(entities)
    cards: list[dict] = []
    for title, domains, columns in _DOMAIN_GROUPS:
        group = [e for e in remaining if e.domain in domains]
        if not group:
            continue
        remaining = [e for e in remaining if e not in group]
        cards.append(grid([theme.entity(e) for e in group], columns=columns, title=title))
    if remaining:
        cards.append(grid([theme.entity(e) for e in remaining], title="Other"))
    return cards


def _category_entities(graph: RegistryGraph, category: str) -> list[EntityNode]:
    return visible_entities(
        [graph.entities[eid] for eid in graph.categories.get(category, []) if eid in graph.entities]
    )


def _area_entities(graph: RegistryGraph, area_id: str) -> list[EntityNode]:
    return visible_entities(
        [graph.entities[eid] for eid in graph.areas[area_id].entity_ids if eid in graph.entities]
    )


def build_home_view(graph: RegistryGraph, theme: CardTheme) -> dict:
    all_entities = visible_entities(graph.entities.values())
    cards: list[dict] = [
        mushroom_title_card(
            "Home",
            subtitle=f"{len(graph.areas)} rooms · {len(all_entities)} entities tracked",
        )
    ]

    chips = []
    if weather := next((e for e in all_entities if e.domain == "weather"), None):
        chips.append(weather_chip(weather.entity_id))
    if alarm := next((e for e in all_entities if e.domain == "alarm_control_panel"), None):
        chips.append({"type": "entity", "entity": alarm.entity_id})
    light_ids = [e.entity_id for e in all_entities if e.domain == "light"]
    if chip := toggle_entities_chip(light_ids, icon="mdi:lightbulb-group", icon_color="amber", service="light.toggle"):
        chips.append(chip)
    if chips_card := mushroom_chips_card(chips):
        cards.append(chips_card)

    location_ids = [entity.entity_id for entity in all_entities if entity.domain in LOCATION_DOMAINS]
    if location_ids:
        cards.append(map_card(location_ids, title="Family & Devices"))

    areas = sorted(graph.areas.values(), key=lambda a: a.name)
    if areas:
        cards.append(grid([area_card(area) for area in areas], title="Rooms"))

    highlight_ids = [
        entity.entity_id
        for entity in _category_entities(graph, CATEGORY_SECURITY) + _category_entities(graph, CATEGORY_UPDATES)
    ]
    if card := logbook_card(highlight_ids):
        cards.append(theme.separator("Recent Activity", icon="mdi:history"))
        cards.append(card)

    if len(cards) == 1:  # only the title card - nothing was discovered yet
        cards.append(markdown_card("No areas discovered yet."))

    return {"title": "Home", "path": "home", "icon": "mdi:home", "cards": cards}


def build_rooms_views(graph: RegistryGraph, theme: CardTheme) -> list[dict]:
    views = []
    for area in sorted(graph.areas.values(), key=lambda a: a.name):
        entities = _area_entities(graph, area.area_id)
        icon = area.icon or guess_area_icon(area.name)
        # The area name is already the view's own tab title, so sections
        # here are grouped by domain instead of repeating it.
        cards = _grouped_grid_cards(entities, theme) or [markdown_card("No entities in this area yet.")]
        views.append({"title": area.name, "path": area.area_id, "icon": icon, "cards": cards})
    if not views:
        views = [{"title": "Rooms", "path": "rooms", "cards": [markdown_card("No areas discovered yet.")]}]
    return views


def build_homelab_view(graph: RegistryGraph, theme: CardTheme) -> dict:
    devices = sorted(
        (d for d in graph.devices.values() if d.category == CATEGORY_HOMELAB and not d.disabled),
        key=lambda d: d.name,
    )
    cards = [card for device in devices if (card := theme.device(device, graph))]

    device_entity_ids = {eid for device in devices for eid in device.entity_ids}
    orphans = [e for e in _category_entities(graph, CATEGORY_HOMELAB) if e.entity_id not in device_entity_ids]
    if orphans:
        cards.append(grid([theme.entity(e) for e in orphans], title="Other"))

    return {
        "title": "Homelab",
        "path": "homelab",
        "icon": "mdi:server",
        "cards": cards or [markdown_card("No homelab entities discovered yet.")],
    }


def build_security_view(graph: RegistryGraph, theme: CardTheme) -> dict:
    entities = _category_entities(graph, CATEGORY_SECURITY)
    cameras = [e for e in entities if e.domain == "camera"]
    others = [e for e in entities if e.domain != "camera"]
    camera_device_ids = {camera.device_id for camera in cameras if camera.device_id}

    cards: list[dict] = []
    for camera in cameras:
        sibling_ids = [e.entity_id for e in others if camera.device_id and e.device_id == camera.device_id]
        cards.append(picture_glance_card(camera.entity_id, sibling_ids, title=camera.name))

    other_only = [e for e in others if e.device_id not in camera_device_ids]
    cards.extend(_grouped_grid_cards(other_only, theme))

    if card := logbook_card([e.entity_id for e in entities]):
        cards.append(theme.separator("Recent Events", icon="mdi:history"))
        cards.append(card)

    return {
        "title": "Security",
        "path": "security",
        "icon": "mdi:shield-home",
        "cards": cards or [markdown_card("No security entities discovered yet.")],
    }


def build_monitoring_view(graph: RegistryGraph, theme: CardTheme) -> dict:
    entities = _category_entities(graph, CATEGORY_NETWORK)
    graphable = [e for e in entities if is_graphable(e)]
    other = [e for e in entities if not is_graphable(e)]

    cards: list[dict] = []
    if trend_card := history_graph_card("Network Trends", [e.entity_id for e in graphable]):
        cards.append(trend_card)
    if graphable:
        cards.append(grid([theme.graph(e) for e in graphable], title="Individual Sensors"))
    if other:
        cards.append(grid([theme.entity(e) for e in other], title="Status"))

    return {
        "title": "Monitoring",
        "path": "monitoring",
        "icon": "mdi:chart-line",
        "cards": cards or [markdown_card("No monitoring entities discovered yet.")],
    }


def build_admin_view(graph: RegistryGraph, theme: CardTheme) -> dict:
    entities = _category_entities(graph, CATEGORY_UPDATES)
    cards: list[dict] = []
    if entities:
        cards.append(grid([theme.entity(e) for e in entities], title="Updates"))
    if card := logbook_card([e.entity_id for e in entities]):
        cards.append(theme.separator("Update History", icon="mdi:history"))
        cards.append(card)

    return {
        "title": "Admin",
        "path": "admin",
        "icon": "mdi:cog",
        "cards": cards or [markdown_card("No update entities discovered yet.")],
    }


def build_cloud_view(graph: RegistryGraph, theme: CardTheme) -> dict | None:
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
            cards.append(grid([theme.entity(e) for e in entities], title=area.name))

    if not cards:
        return None

    return {"title": "Cloud", "path": "cloud", "icon": "mdi:cloud", "cards": cards}
