"""DataUpdateCoordinator that keeps the discovery graph up to date."""
from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import timedelta

from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN
from .discovery import async_build_graph
from .models import RegistryGraph

_LOGGER = logging.getLogger(__name__)

# Registries rarely change; this is a safety-net poll interval on top of the
# event-driven refresh triggered by registry updates (see _async_setup_listeners).
_SCAN_INTERVAL = timedelta(hours=6)


class DiscoveryCoordinator(DataUpdateCoordinator[RegistryGraph]):
    """Owns the discovered RegistryGraph and refreshes it on demand."""

    def __init__(self, hass: HomeAssistant) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name=f"{DOMAIN} discovery",
            update_interval=_SCAN_INTERVAL,
        )
        self._remove_listeners: list[Callable[[], None]] = []

    async def _async_update_data(self) -> RegistryGraph:
        return await async_build_graph(self.hass)

    @callback
    def async_setup_registry_listeners(self) -> None:
        """Trigger a rescan whenever the area/device/entity registries change."""

        @callback
        def _handle_registry_update(_event) -> None:
            self.hass.async_create_task(self.async_request_refresh())

        self._remove_listeners = [
            self.hass.bus.async_listen(ar.EVENT_AREA_REGISTRY_UPDATED, _handle_registry_update),
            self.hass.bus.async_listen(dr.EVENT_DEVICE_REGISTRY_UPDATED, _handle_registry_update),
            self.hass.bus.async_listen(er.EVENT_ENTITY_REGISTRY_UPDATED, _handle_registry_update),
        ]

    @callback
    def async_unload(self) -> None:
        for remove in self._remove_listeners:
            remove()
        self._remove_listeners = []
