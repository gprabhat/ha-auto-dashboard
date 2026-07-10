"""Tests for Dashboard Studio's card-id scheme and override merge logic."""
from custom_components.ha_auto_dashboard.dashboard.card_builder import grid
from custom_components.ha_auto_dashboard.dashboard.overrides import apply_overrides, card_id
from custom_components.ha_auto_dashboard.dashboard.resources import FrontendResources
from custom_components.ha_auto_dashboard.models import EntityNode, RegistryGraph

NONE_PRESENT = FrontendResources(mushroom=False, bubble_card=False, mini_graph_card=False)


def _view(path: str, cards: list[dict]) -> dict:
    return {"title": path, "path": path, "cards": cards}


def _graph_with(*entities: EntityNode) -> RegistryGraph:
    graph = RegistryGraph()
    for entity in entities:
        graph.entities[entity.entity_id] = entity
    return graph


def test_card_id_is_stable_for_entity_cards() -> None:
    card = {"type": "tile", "entity": "light.kitchen"}
    assert card_id("auto_rooms", "kitchen", card) == "auto_rooms:kitchen:entity:light.kitchen"


def test_card_id_uses_area_discriminator() -> None:
    card = {"type": "area", "area": "kitchen"}
    assert card_id("auto_home", "home", card) == "auto_home:home:area:kitchen"


def test_card_id_disambiguates_multiple_grids_in_the_same_view_by_title() -> None:
    lights = grid([{"type": "tile", "entity": "light.a"}], title="Lights")
    switches = grid([{"type": "tile", "entity": "switch.a"}], title="Switches & Locks")

    lights_id = card_id("auto_rooms", "kitchen", lights)
    switches_id = card_id("auto_rooms", "kitchen", switches)

    assert lights_id != switches_id
    assert lights_id == "auto_rooms:kitchen:grid:Lights"
    assert switches_id == "auto_rooms:kitchen:grid:Switches & Locks"


def test_card_id_falls_back_to_type_for_singleton_structural_cards() -> None:
    card = {"type": "map", "entities": []}
    assert card_id("auto_home", "home", card) == "auto_home:home:map"


def test_apply_overrides_hides_a_card() -> None:
    light = {"type": "tile", "entity": "light.a"}
    switch = {"type": "tile", "entity": "switch.a"}
    dashboards = {"auto_home": {"title": "Home", "icon": "mdi:home", "views": [_view("home", [light, switch])]}}
    overrides = {"cards": {"auto_home:home:entity:light.a": {"hidden": True}}}

    result = apply_overrides(overrides, dashboards, graph=RegistryGraph())

    cards = result["auto_home"]["views"][0]["cards"]
    assert cards == [switch]


def test_apply_overrides_hides_within_a_grid_and_drops_empty_grid() -> None:
    only_card = {"type": "tile", "entity": "switch.a"}
    section = grid([only_card], title="Switches")
    dashboards = {"auto_rooms": {"title": "Rooms", "icon": "mdi:floor-plan", "views": [_view("kitchen", [section])]}}
    overrides = {"cards": {"auto_rooms:kitchen:entity:switch.a": {"hidden": True}}}

    result = apply_overrides(overrides, dashboards, graph=RegistryGraph())

    assert result["auto_rooms"]["views"][0]["cards"] == []


def test_apply_overrides_renames_and_reicons_a_card() -> None:
    card = {"type": "tile", "entity": "light.a"}
    dashboards = {"auto_home": {"title": "Home", "icon": "mdi:home", "views": [_view("home", [card])]}}
    overrides = {
        "cards": {"auto_home:home:entity:light.a": {"name": "Reading Lamp", "icon": "mdi:lamp"}}
    }

    result = apply_overrides(overrides, dashboards, graph=RegistryGraph())

    updated = result["auto_home"]["views"][0]["cards"][0]
    assert updated["name"] == "Reading Lamp"
    assert updated["icon"] == "mdi:lamp"


def test_apply_overrides_reorders_a_container() -> None:
    a = {"type": "tile", "entity": "light.a"}
    b = {"type": "tile", "entity": "light.b"}
    c = {"type": "tile", "entity": "light.c"}
    dashboards = {"auto_home": {"title": "Home", "icon": "mdi:home", "views": [_view("home", [a, b, c])]}}
    overrides = {
        "cards": {
            "auto_home:home:entity:light.a": {"order": 2},
            "auto_home:home:entity:light.b": {"order": 0},
            "auto_home:home:entity:light.c": {"order": 1},
        }
    }

    result = apply_overrides(overrides, dashboards, graph=RegistryGraph())

    assert [c["entity"] for c in result["auto_home"]["views"][0]["cards"]] == [
        "light.b",
        "light.c",
        "light.a",
    ]


def test_apply_overrides_adds_a_new_entity_card() -> None:
    existing = {"type": "tile", "entity": "light.a"}
    dashboards = {"auto_home": {"title": "Home", "icon": "mdi:home", "views": [_view("home", [existing])]}}
    graph = _graph_with(EntityNode(entity_id="switch.new", name="New Switch", domain="switch"))
    overrides = {"added_cards": [{"dashboard": "auto_home", "view": "home", "entity_id": "switch.new"}]}

    result = apply_overrides(overrides, dashboards, graph=graph, resources=NONE_PRESENT)

    cards = result["auto_home"]["views"][0]["cards"]
    assert {"type": "tile", "entity": "switch.new"} in cards


def test_apply_overrides_add_is_idempotent_when_already_present() -> None:
    existing = {"type": "tile", "entity": "switch.new"}
    dashboards = {"auto_home": {"title": "Home", "icon": "mdi:home", "views": [_view("home", [existing])]}}
    graph = _graph_with(EntityNode(entity_id="switch.new", name="New Switch", domain="switch"))
    overrides = {"added_cards": [{"dashboard": "auto_home", "view": "home", "entity_id": "switch.new"}]}

    result = apply_overrides(overrides, dashboards, graph=graph, resources=NONE_PRESENT)

    assert result["auto_home"]["views"][0]["cards"] == [existing]


def test_apply_overrides_skips_added_card_for_stale_entity() -> None:
    dashboards = {"auto_home": {"title": "Home", "icon": "mdi:home", "views": [_view("home", [])]}}
    overrides = {"added_cards": [{"dashboard": "auto_home", "view": "home", "entity_id": "switch.gone"}]}

    result = apply_overrides(overrides, dashboards, graph=RegistryGraph())

    assert result["auto_home"]["views"][0]["cards"] == []


def test_apply_overrides_noop_with_empty_override_doc() -> None:
    card = {"type": "tile", "entity": "light.a"}
    dashboards = {"auto_home": {"title": "Home", "icon": "mdi:home", "views": [_view("home", [card])]}}

    result = apply_overrides({}, dashboards, graph=RegistryGraph())

    assert result["auto_home"]["views"][0]["cards"] == [card]
