"""The HA Auto Dashboard integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import DiscoveryCoordinator
from .services import async_setup_services, async_unload_services

PLATFORMS: list[str] = []


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA Auto Dashboard from a config entry."""
    coordinator = DiscoveryCoordinator(hass)
    await coordinator.async_config_entry_first_refresh()
    coordinator.async_setup_registry_listeners()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
    }

    async_setup_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    entry_data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if entry_data:
        coordinator: DiscoveryCoordinator = entry_data[DATA_COORDINATOR]
        coordinator.async_unload()

    async_unload_services(hass)

    return True
