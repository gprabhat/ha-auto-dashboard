"""Diagnostics support for HA Auto Dashboard."""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import DiscoveryCoordinator
from .dashboard import compile_dashboards


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: ConfigEntry
) -> dict[str, Any]:
    """Return the current discovery graph, its stats, and the compiled dashboards."""
    coordinator: DiscoveryCoordinator = hass.data[DOMAIN][entry.entry_id][
        DATA_COORDINATOR
    ]
    graph = coordinator.data

    if graph is None:
        return {"stats": {}, "graph": None, "dashboards": None}

    dashboards = compile_dashboards(graph)
    dashboard_summary = {
        slug: {"title": dashboard["title"], "view_count": len(dashboard["views"])}
        for slug, dashboard in dashboards.items()
    }

    return {
        "stats": graph.stats(),
        "graph": graph.to_dict(),
        "dashboards": dashboard_summary,
    }
