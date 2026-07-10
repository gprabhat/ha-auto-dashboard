"""The HA Auto Dashboard integration."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import DiscoveryCoordinator
from .dashboard import async_generate_and_install
from .services import async_setup_services, async_unload_services

PLATFORMS: list[str] = []


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up HA Auto Dashboard from a config entry."""
    coordinator = DiscoveryCoordinator(hass, entry)

    async def _async_regenerate_dashboards() -> None:
        if coordinator.data is not None:
            await async_generate_and_install(hass, coordinator.data, entry=entry)

    def _schedule_regenerate() -> None:
        hass.async_create_task(_async_regenerate_dashboards())

    async def _async_options_updated(hass: HomeAssistant, entry: ConfigEntry) -> None:
        # Exclusions changed - rescan (and thus regenerate) right away
        # instead of waiting for the next registry event or safety-net poll.
        await coordinator.async_request_refresh()

    await coordinator.async_config_entry_first_refresh()
    coordinator.async_setup_registry_listeners()
    remove_listener = coordinator.async_add_listener(_schedule_regenerate)
    remove_options_listener = entry.add_update_listener(_async_options_updated)

    # Every subsequent scan (registry change or the 6h safety-net poll) keeps
    # the generated dashboards in sync automatically.
    await _async_regenerate_dashboards()

    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {
        DATA_COORDINATOR: coordinator,
        "remove_listener": remove_listener,
        "remove_options_listener": remove_options_listener,
    }

    async_setup_services(hass)

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    entry_data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    if entry_data:
        entry_data["remove_listener"]()
        entry_data["remove_options_listener"]()
        coordinator: DiscoveryCoordinator = entry_data[DATA_COORDINATOR]
        coordinator.async_unload()

    async_unload_services(hass)

    return True
