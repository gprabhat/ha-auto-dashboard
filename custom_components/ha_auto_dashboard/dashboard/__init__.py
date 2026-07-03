"""Dashboard engine: compiles the discovery graph into Lovelace dashboards."""
from __future__ import annotations

from homeassistant.core import HomeAssistant

from ..models import RegistryGraph
from .compiler import compile_dashboards
from .installer import async_install_dashboards, configuration_snippet
from .issues import async_update_registration_issue, async_update_resource_issue
from .resources import async_detect_frontend_resources

__all__ = ["compile_dashboards", "async_install_dashboards", "async_generate_and_install"]


async def async_generate_and_install(hass: HomeAssistant, graph: RegistryGraph) -> list[str]:
    """Compile the graph into dashboards, write them, and keep the Repairs
    issues (missing frontend resources / registration reminder) in sync."""
    resources = await async_detect_frontend_resources(hass)
    dashboards = compile_dashboards(graph, resources)
    written = await async_install_dashboards(hass, dashboards)

    async_update_resource_issue(hass, resources)
    async_update_registration_issue(hass, dashboards, configuration_snippet(dashboards))

    return written
