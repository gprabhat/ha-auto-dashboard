"""Dashboard engine: compiles the discovery graph into Lovelace dashboards."""
from __future__ import annotations

from homeassistant.core import HomeAssistant

from ..models import RegistryGraph
from .compiler import compile_dashboards
from .installer import async_install_dashboards

__all__ = ["compile_dashboards", "async_install_dashboards", "async_generate_and_install"]


async def async_generate_and_install(hass: HomeAssistant, graph: RegistryGraph) -> list[str]:
    """Compile the graph into dashboards and write/announce them in one step."""
    dashboards = compile_dashboards(graph)
    return await async_install_dashboards(hass, dashboards)
