"""Reads the Home Assistant device registry into DeviceNode models."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import device_registry as dr

from ..models import DeviceNode


def collect_devices(hass: HomeAssistant) -> dict[str, DeviceNode]:
    """Return every registered device, keyed by device_id."""
    registry = dr.async_get(hass)
    devices: dict[str, DeviceNode] = {}
    for device in registry.devices.values():
        name = device.name_by_user or device.name or device.id
        devices[device.id] = DeviceNode(
            device_id=device.id,
            name=name,
            area_id=device.area_id,
            manufacturer=device.manufacturer,
            model=device.model,
            sw_version=device.sw_version,
            via_device_id=device.via_device_id,
            disabled=device.disabled_by is not None,
        )
    return devices
