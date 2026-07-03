"""Unit tests for the dashboard compiler/factory/card_builder (pure functions, no hass)."""
from custom_components.ha_auto_dashboard.const import CATEGORY_HOMELAB, CATEGORY_ROOM, CATEGORY_SECURITY
from custom_components.ha_auto_dashboard.dashboard.card_builder import (
    area_card,
    device_card,
    entities_card,
    picture_entity_card,
)
from custom_components.ha_auto_dashboard.dashboard.compiler import (
    DASHBOARD_CLOUD,
    DASHBOARD_HOME,
    DASHBOARD_HOMELAB,
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


def test_entities_card_omitted_when_empty() -> None:
    assert entities_card("Empty", []) is None
    assert entities_card("Lights", ["light.a"]) == {
        "type": "entities",
        "title": "Lights",
        "entities": ["light.a"],
    }


def test_device_card_excludes_disabled_entities() -> None:
    graph = RegistryGraph()
    device = DeviceNode(device_id="d1", name="Hub")
    visible = EntityNode(entity_id="sensor.a", name="A", domain="sensor", device_id="d1")
    disabled = EntityNode(entity_id="sensor.b", name="B", domain="sensor", device_id="d1", disabled=True)
    device.entity_ids = [visible.entity_id, disabled.entity_id]
    graph.devices["d1"] = device
    graph.entities[visible.entity_id] = visible
    graph.entities[disabled.entity_id] = disabled

    card = device_card(device, graph)
    assert card == {"type": "entities", "title": "Hub", "entities": ["sensor.a"]}


def test_picture_entity_card() -> None:
    assert picture_entity_card("camera.front_door") == {
        "type": "picture-entity",
        "entity": "camera.front_door",
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
    assert {"type": "area", "area": "kitchen"} in home_cards


def test_compile_dashboards_rooms_has_one_view_per_area() -> None:
    dashboards = compile_dashboards(_sample_graph())
    rooms_views = dashboards[DASHBOARD_ROOMS]["views"]
    assert [view["path"] for view in rooms_views] == ["kitchen"]
    assert rooms_views[0]["cards"] == [
        {"type": "entities", "title": "Kitchen", "entities": ["light.kitchen_ceiling"]}
    ]


def test_compile_dashboards_security_separates_cameras() -> None:
    dashboards = compile_dashboards(_sample_graph())
    security_cards = dashboards[DASHBOARD_SECURITY]["views"][0]["cards"]
    assert {"type": "picture-entity", "entity": "camera.front_door"} in security_cards


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
    assert dashboards[DASHBOARD_CLOUD]["views"][0]["cards"] == [
        {"type": "entities", "title": "Cloud Server", "entities": [entity.entity_id]}
    ]
