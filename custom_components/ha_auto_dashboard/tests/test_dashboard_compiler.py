"""Unit tests for the dashboard compiler/factory/card_builder (pure functions, no hass)."""
from custom_components.ha_auto_dashboard.const import CATEGORY_HOMELAB, CATEGORY_ROOM, CATEGORY_SECURITY
from custom_components.ha_auto_dashboard.dashboard.card_builder import (
    CardTheme,
    area_card,
    grid,
    is_graphable,
    map_card,
    picture_glance_card,
)
from custom_components.ha_auto_dashboard.dashboard.compiler import (
    DASHBOARD_CLOUD,
    DASHBOARD_HOME,
    DASHBOARD_HOMELAB,
    DASHBOARD_MONITORING,
    DASHBOARD_ROOMS,
    DASHBOARD_SECURITY,
    compile_dashboards,
)
from custom_components.ha_auto_dashboard.dashboard.icons import guess_area_icon
from custom_components.ha_auto_dashboard.dashboard.resources import FrontendResources
from custom_components.ha_auto_dashboard.models import AreaNode, DeviceNode, EntityNode, RegistryGraph

ALL_PRESENT = FrontendResources(mushroom=True, bubble_card=True, mini_graph_card=True)
NONE_PRESENT = FrontendResources(mushroom=False, bubble_card=False, mini_graph_card=False)


def _sample_graph() -> RegistryGraph:
    graph = RegistryGraph()

    kitchen = AreaNode(area_id="kitchen", name="Kitchen")
    graph.areas["kitchen"] = kitchen

    light = EntityNode(
        entity_id="light.kitchen_ceiling",
        name="Kitchen Ceiling",
        domain="light",
        area_id="kitchen",
        category=CATEGORY_ROOM,
    )
    graph.entities[light.entity_id] = light
    kitchen.entity_ids.append(light.entity_id)

    pve = DeviceNode(device_id="pve1", name="Proxmox PVE2 Node", category=CATEGORY_HOMELAB)
    cpu_sensor = EntityNode(
        entity_id="sensor.pve2_cpu_usage",
        name="PVE2 CPU Usage",
        domain="sensor",
        device_id="pve1",
        category=CATEGORY_HOMELAB,
        unit_of_measurement="%",
    )
    pve.entity_ids.append(cpu_sensor.entity_id)
    graph.devices["pve1"] = pve
    graph.entities[cpu_sensor.entity_id] = cpu_sensor

    camera = EntityNode(
        entity_id="camera.front_door",
        name="Front Door Camera",
        domain="camera",
        category=CATEGORY_SECURITY,
    )
    graph.entities[camera.entity_id] = camera

    graph.categories = {
        CATEGORY_ROOM: [light.entity_id],
        CATEGORY_HOMELAB: [cpu_sensor.entity_id],
        CATEGORY_SECURITY: [camera.entity_id],
        "other": [],
    }
    return graph


def test_area_card() -> None:
    area = AreaNode(area_id="kitchen", name="Kitchen")
    assert area_card(area) == {"type": "area", "area": "kitchen"}


def test_grid_columns_scale_with_card_count() -> None:
    assert grid([{"a": 1}])["columns"] == 1
    assert grid([{"a": 1}, {"a": 2}, {"a": 3}])["columns"] == 3
    assert grid([{"a": i} for i in range(10)])["columns"] == 4  # capped at 4


def test_guess_area_icon_matches_keywords() -> None:
    assert guess_area_icon("Kitchen") == "mdi:chef-hat"
    assert guess_area_icon("2nd Bedroom") == "mdi:bed"
    assert guess_area_icon("Cloud Server") == "mdi:cloud"
    assert guess_area_icon("Something Unrelated") == "mdi:home-outline"


def test_is_graphable_requires_sensor_domain_and_unit() -> None:
    graphable = EntityNode(entity_id="sensor.a", name="A", domain="sensor", unit_of_measurement="W")
    non_numeric_sensor = EntityNode(entity_id="sensor.b", name="B", domain="sensor")
    non_sensor = EntityNode(entity_id="switch.a", name="A", domain="switch", unit_of_measurement="W")

    assert is_graphable(graphable) is True
    assert is_graphable(non_numeric_sensor) is False
    assert is_graphable(non_sensor) is False


def test_theme_uses_mushroom_and_mini_graph_when_available() -> None:
    theme = CardTheme(ALL_PRESENT)
    light = EntityNode(entity_id="light.a", name="A", domain="light")
    sensor = EntityNode(entity_id="sensor.a", name="A", domain="sensor", unit_of_measurement="W")

    assert theme.entity(light) == {"type": "custom:mushroom-light-card", "entity": "light.a"}
    assert theme.entity(sensor)["type"] == "custom:mini-graph-card"
    assert theme.separator("Kitchen")["type"] == "custom:bubble-card"


def test_theme_falls_back_to_native_cards_when_resources_missing() -> None:
    theme = CardTheme(NONE_PRESENT)
    light = EntityNode(entity_id="light.a", name="A", domain="light")
    switch = EntityNode(entity_id="switch.a", name="A", domain="switch")
    sensor = EntityNode(entity_id="sensor.a", name="A", domain="sensor", unit_of_measurement="W")

    assert theme.entity(light) == {"type": "light", "entity": "light.a"}
    assert theme.entity(switch) == {"type": "tile", "entity": "switch.a"}
    assert theme.entity(sensor)["type"] == "sensor"
    assert theme.entity(sensor)["graph"] == "line"
    assert theme.separator("Kitchen") == {"type": "heading", "heading": "Kitchen"}


def test_theme_device_excludes_disabled_entities() -> None:
    graph = RegistryGraph()
    device = DeviceNode(device_id="d1", name="Hub")
    visible = EntityNode(entity_id="switch.a", name="A", domain="switch", device_id="d1")
    disabled = EntityNode(entity_id="switch.b", name="B", domain="switch", device_id="d1", disabled=True)
    device.entity_ids = [visible.entity_id, disabled.entity_id]
    graph.devices["d1"] = device
    graph.entities[visible.entity_id] = visible
    graph.entities[disabled.entity_id] = disabled

    theme = CardTheme(ALL_PRESENT)
    card = theme.device(device, graph)
    assert card is not None
    assert card["type"] == "vertical-stack"
    grid_card = card["cards"][1]
    assert grid_card["type"] == "grid"
    assert grid_card["cards"] == [theme.entity(visible)]


def test_theme_device_none_when_no_visible_entities() -> None:
    graph = RegistryGraph()
    device = DeviceNode(device_id="d1", name="Hub")
    graph.devices["d1"] = device
    assert CardTheme(ALL_PRESENT).device(device, graph) is None


def test_map_card() -> None:
    assert map_card(["person.alice"], title="Family") == {
        "type": "map",
        "entities": [{"entity": "person.alice"}],
        "title": "Family",
    }


def test_picture_glance_card() -> None:
    assert picture_glance_card("camera.front_door", ["binary_sensor.motion"]) == {
        "type": "picture-glance",
        "camera_image": "camera.front_door",
        "entities": ["binary_sensor.motion"],
    }


def test_compile_dashboards_produces_expected_slugs() -> None:
    dashboards = compile_dashboards(_sample_graph())

    assert set(dashboards) >= {
        DASHBOARD_HOME,
        DASHBOARD_ROOMS,
        DASHBOARD_HOMELAB,
        DASHBOARD_SECURITY,
    }
    # No cloud-related area in the sample graph.
    assert DASHBOARD_CLOUD not in dashboards


def test_compile_dashboards_home_has_title_and_area_grid() -> None:
    dashboards = compile_dashboards(_sample_graph())
    home_cards = dashboards[DASHBOARD_HOME]["views"][0]["cards"]
    assert home_cards[0]["type"] == "custom:mushroom-title-card"
    grid_cards = next(c for c in home_cards if c.get("type") == "grid")
    assert {"type": "area", "area": "kitchen"} in grid_cards["cards"]


def test_compile_dashboards_home_fallback_when_graph_empty() -> None:
    dashboards = compile_dashboards(RegistryGraph())
    home_cards = dashboards[DASHBOARD_HOME]["views"][0]["cards"]
    assert home_cards[-1] == {"type": "markdown", "content": "No areas discovered yet."}


def test_compile_dashboards_rooms_has_one_view_per_area() -> None:
    dashboards = compile_dashboards(_sample_graph())
    rooms_views = dashboards[DASHBOARD_ROOMS]["views"]
    assert [view["path"] for view in rooms_views] == ["kitchen"]
    grid_card = rooms_views[0]["cards"][1]
    assert grid_card["cards"] == [{"type": "custom:mushroom-light-card", "entity": "light.kitchen_ceiling"}]


def test_compile_dashboards_homelab_uses_mini_graph_for_numeric_sensor() -> None:
    dashboards = compile_dashboards(_sample_graph())
    homelab_cards = dashboards[DASHBOARD_HOMELAB]["views"][0]["cards"]
    device_stack = homelab_cards[0]
    grid_card = device_stack["cards"][1]
    assert grid_card["cards"][0]["type"] == "custom:mini-graph-card"


def test_compile_dashboards_security_uses_picture_glance_for_camera() -> None:
    dashboards = compile_dashboards(_sample_graph())
    security_cards = dashboards[DASHBOARD_SECURITY]["views"][0]["cards"]
    assert any(c.get("type") == "picture-glance" for c in security_cards)


def test_compile_dashboards_monitoring_omitted_when_empty() -> None:
    dashboards = compile_dashboards(_sample_graph())
    monitoring_cards = dashboards[DASHBOARD_MONITORING]["views"][0]["cards"]
    assert monitoring_cards == [{"type": "markdown", "content": "No monitoring entities discovered yet."}]


def test_compile_dashboards_respects_missing_resources() -> None:
    dashboards = compile_dashboards(_sample_graph(), NONE_PRESENT)
    rooms_views = dashboards[DASHBOARD_ROOMS]["views"]
    grid_card = rooms_views[0]["cards"][1]
    assert grid_card["cards"] == [{"type": "light", "entity": "light.kitchen_ceiling"}]


def test_compile_dashboards_cloud_only_when_cloud_area_present() -> None:
    graph = _sample_graph()
    cloud_area = AreaNode(area_id="cloud_server", name="Cloud Server")
    entity = EntityNode(
        entity_id="sensor.cloud_backup_status",
        name="Cloud Backup Status",
        domain="sensor",
        area_id="cloud_server",
    )
    cloud_area.entity_ids.append(entity.entity_id)
    graph.areas["cloud_server"] = cloud_area
    graph.entities[entity.entity_id] = entity

    dashboards = compile_dashboards(graph)
    assert DASHBOARD_CLOUD in dashboards
    grid_card = dashboards[DASHBOARD_CLOUD]["views"][0]["cards"][1]
    assert grid_card["cards"] == [{"type": "custom:mushroom-entity-card", "entity": entity.entity_id}]
