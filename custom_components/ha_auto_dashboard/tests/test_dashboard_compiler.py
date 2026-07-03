"""Unit tests for the dashboard compiler/factory/card_builder (pure functions, no hass)."""
from custom_components.ha_auto_dashboard.const import CATEGORY_HOMELAB, CATEGORY_ROOM, CATEGORY_SECURITY
from custom_components.ha_auto_dashboard.dashboard.card_builder import (
    area_card,
    device_card,
    entity_card,
    is_graphable,
    map_card,
    mini_graph_card,
    mushroom_card,
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
from custom_components.ha_auto_dashboard.models import AreaNode, DeviceNode, EntityNode, RegistryGraph


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


def test_mushroom_card_uses_domain_specific_type() -> None:
    light = EntityNode(entity_id="light.a", name="A", domain="light")
    assert mushroom_card(light) == {"type": "custom:mushroom-light-card", "entity": "light.a"}


def test_mushroom_card_falls_back_to_generic_for_unmapped_domain() -> None:
    switch = EntityNode(entity_id="switch.a", name="A", domain="switch")
    assert mushroom_card(switch) == {"type": "custom:mushroom-entity-card", "entity": "switch.a"}


def test_is_graphable_requires_sensor_domain_and_unit() -> None:
    graphable = EntityNode(entity_id="sensor.a", name="A", domain="sensor", unit_of_measurement="W")
    non_numeric_sensor = EntityNode(entity_id="sensor.b", name="B", domain="sensor")
    non_sensor = EntityNode(entity_id="switch.a", name="A", domain="switch", unit_of_measurement="W")

    assert is_graphable(graphable) is True
    assert is_graphable(non_numeric_sensor) is False
    assert is_graphable(non_sensor) is False


def test_entity_card_routes_graphable_sensors_to_mini_graph() -> None:
    sensor = EntityNode(entity_id="sensor.a", name="A", domain="sensor", unit_of_measurement="W")
    assert entity_card(sensor) == mini_graph_card(sensor)
    assert entity_card(sensor)["type"] == "custom:mini-graph-card"


def test_entity_card_routes_others_to_mushroom() -> None:
    light = EntityNode(entity_id="light.a", name="A", domain="light")
    assert entity_card(light) == mushroom_card(light)


def test_device_card_excludes_disabled_entities() -> None:
    graph = RegistryGraph()
    device = DeviceNode(device_id="d1", name="Hub")
    visible = EntityNode(entity_id="switch.a", name="A", domain="switch", device_id="d1")
    disabled = EntityNode(entity_id="switch.b", name="B", domain="switch", device_id="d1", disabled=True)
    device.entity_ids = [visible.entity_id, disabled.entity_id]
    graph.devices["d1"] = device
    graph.entities[visible.entity_id] = visible
    graph.entities[disabled.entity_id] = disabled

    card = device_card(device, graph)
    assert card is not None
    assert card["type"] == "vertical-stack"
    grid_card = card["cards"][1]
    assert grid_card["type"] == "grid"
    assert grid_card["cards"] == [mushroom_card(visible)]


def test_device_card_none_when_no_visible_entities() -> None:
    graph = RegistryGraph()
    device = DeviceNode(device_id="d1", name="Hub")
    graph.devices["d1"] = device
    assert device_card(device, graph) is None


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


def test_compile_dashboards_home_has_area_card() -> None:
    dashboards = compile_dashboards(_sample_graph())
    home_cards = dashboards[DASHBOARD_HOME]["views"][0]["cards"]
    grid_cards = next(c for c in home_cards if c.get("type") == "grid")
    assert {"type": "area", "area": "kitchen"} in grid_cards["cards"]


def test_compile_dashboards_rooms_has_one_view_per_area() -> None:
    dashboards = compile_dashboards(_sample_graph())
    rooms_views = dashboards[DASHBOARD_ROOMS]["views"]
    assert [view["path"] for view in rooms_views] == ["kitchen"]
    grid_card = rooms_views[0]["cards"][1]
    assert grid_card["cards"] == [
        {"type": "custom:mushroom-light-card", "entity": "light.kitchen_ceiling"}
    ]


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
