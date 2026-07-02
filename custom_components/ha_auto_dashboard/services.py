"""Service (action) registration for HA Auto Dashboard."""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant, ServiceCall

from .const import DATA_COORDINATOR, DOMAIN, SERVICE_SCAN
from .coordinator import DiscoveryCoordinator

_LOGGER = logging.getLogger(__name__)


def async_setup_services(hass: HomeAssistant) -> None:
    """Register the `ha_auto_dashboard.scan` action, if not already registered."""
    if hass.services.has_service(DOMAIN, SERVICE_SCAN):
        return

    async def _async_handle_scan(call: ServiceCall) -> None:
        for entry_data in hass.data.get(DOMAIN, {}).values():
            coordinator: DiscoveryCoordinator = entry_data[DATA_COORDINATOR]
            await coordinator.async_request_refresh()
            _LOGGER.info(
                "HA Auto Dashboard scan complete: %s", coordinator.data.stats()
                if coordinator.data else "no data"
            )

    hass.services.async_register(DOMAIN, SERVICE_SCAN, _async_handle_scan)


def async_unload_services(hass: HomeAssistant) -> None:
    """Remove the `ha_auto_dashboard.scan` action once the last entry unloads."""
    if not hass.data.get(DOMAIN):
        hass.services.async_remove(DOMAIN, SERVICE_SCAN)
