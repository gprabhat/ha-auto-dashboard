"""Reads the Home Assistant area registry into AreaNode models."""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar

from ..models import AreaNode


def collect_areas(hass: HomeAssistant) -> dict[str, AreaNode]:
    """Return every registered area, keyed by area_id."""
    registry = ar.async_get(hass)
    return {
        area.id: AreaNode(area_id=area.id, name=area.name, icon=area.icon)
        for area in registry.async_list_areas()
    }
