"""Unit tests for the keyword/domain based classifier."""
from custom_components.ha_auto_dashboard.const import (
    CATEGORY_HOMELAB,
    CATEGORY_NETWORK,
    CATEGORY_OTHER,
    CATEGORY_ROOM,
    CATEGORY_SECURITY,
    CATEGORY_UPDATES,
)
from custom_components.ha_auto_dashboard.discovery.classifier import (
    classify_device,
    classify_entity,
)
from custom_components.ha_auto_dashboard.models import DeviceNode, EntityNode


def _entity(entity_id: str, *, domain: str | None = None, area_id: str | None = None) -> EntityNode:
    return EntityNode(
        entity_id=entity_id,
        name=entity_id,
        domain=domain or entity_id.split(".", 1)[0],
        area_id=area_id,
    )


def test_update_domain_always_updates_category() -> None:
    entity = _entity("update.core_update")
    assert classify_entity(entity) == CATEGORY_UPDATES


def test_homelab_keyword_match() -> None:
    entity = _entity("sensor.pve2_cpu_usage")
    assert classify_entity(entity) == CATEGORY_HOMELAB


def test_security_keyword_match() -> None:
    entity = _entity("binary_sensor.front_door_motion")
    assert classify_entity(entity) == CATEGORY_SECURITY


def test_network_keyword_match() -> None:
    entity = _entity("sensor.wan_download_speed")
    assert classify_entity(entity) == CATEGORY_NETWORK


def test_area_only_entity_is_room() -> None:
    entity = _entity("light.ceiling", area_id="kitchen")
    assert classify_entity(entity) == CATEGORY_ROOM


def test_no_area_no_keyword_is_other() -> None:
    entity = _entity("sensor.misc_counter")
    assert classify_entity(entity) == CATEGORY_OTHER


def test_device_classified_by_own_name_keyword() -> None:
    device = DeviceNode(device_id="d1", name="Proxmox PVE2 Node")
    assert classify_device(device, []) == CATEGORY_HOMELAB


def test_device_classified_by_majority_entity_category() -> None:
    device = DeviceNode(device_id="d1", name="Generic Hub", area_id="kitchen")
    entities = [
        _entity("sensor.wan_download_speed"),
        _entity("sensor.wan_upload_speed"),
        _entity("light.kitchen_ceiling", area_id="kitchen"),
    ]
    assert classify_device(device, entities) == CATEGORY_NETWORK


def test_device_falls_back_to_room_when_area_set() -> None:
    device = DeviceNode(device_id="d1", name="Generic Light", area_id="kitchen")
    entities = [_entity("light.kitchen_ceiling", area_id="kitchen")]
    assert classify_device(device, entities) == CATEGORY_ROOM
