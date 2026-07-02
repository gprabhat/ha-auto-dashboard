"""Diagnostics support for HA Auto Dashboard."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import DiscoveryCoordinator


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return the current discovery graph and its summary statistics."""
    coordinator: DiscoveryCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    graph = coordinator.data

    if graph is None:
        return {"stats": {}, "graph": None}

    return {"stats": graph.stats(), "graph": graph.to_dict()}
