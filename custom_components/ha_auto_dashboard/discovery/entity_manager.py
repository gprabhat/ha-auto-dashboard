"""Reads the Home Assistant entity registry into EntityNode models."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import entity_registry as er

from ..models import DeviceNode, EntityNode


def collect_entities(
    hass: HomeAssistant, devices: dict[str, DeviceNode]
) -> dict[str, EntityNode]:
    """Return every registered entity, keyed by entity_id.

    Falls back to the owning device's area when the entity itself has no
    area override, mirroring how HA resolves an entity's effective area.
    """
    registry = er.async_get(hass)
    entities: dict[str, EntityNode] = {}
    for entry in registry.entities.values():
        device = devices.get(entry.device_id) if entry.device_id else None
        area_id = entry.area_id or (device.area_id if device else None)
        name = entry.name or entry.original_name or entry.entity_id
        entities[entry.entity_id] = EntityNode(
            entity_id=entry.entity_id,
            name=name,
            domain=entry.domain,
            device_id=entry.device_id,
            area_id=area_id,
            device_class=entry.device_class or entry.original_device_class,
            platform=entry.platform,
            disabled=entry.disabled_by is not None,
            hidden=entry.hidden_by is not None,
        )
    return entities
