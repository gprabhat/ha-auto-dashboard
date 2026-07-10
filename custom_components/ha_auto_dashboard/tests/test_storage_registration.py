"""Tests for the opt-in storage-mode dashboard registration.

Uses a minimal fake standing in for HA's internal `lovelace` dashboards
storage collection, since booting the real `lovelace` integration in a
unit test is heavier than what this module's own logic needs verified:
that it looks up `hass.data["lovelace"]["dashboards_collection"]`,
skips already-registered url_paths, and never raises when that shape
isn't present.
"""
from homeassistant.core import HomeAssistant

from custom_components.ha_auto_dashboard.dashboard.storage_registration import (
    async_register_storage_dashboards,
)


class _FakeDashboardsCollection:
    def __init__(self, existing: list[dict] | None = None) -> None:
        self._items = existing or []
        self.created: list[dict] = []

    def async_items(self) -> list[dict]:
        return self._items

    async def async_create_item(self, data: dict) -> dict:
        self.created.append(data)
        self._items.append(data)
        return data


async def test_register_storage_dashboards_creates_missing_ones(hass: HomeAssistant) -> None:
    collection = _FakeDashboardsCollection()
    hass.data["lovelace"] = {"dashboards_collection": collection}

    dashboards = {
        "auto_home": {"title": "Home", "icon": "mdi:home", "views": []},
        "auto_rooms": {"title": "Rooms", "icon": "mdi:floor-plan", "views": []},
    }
    await async_register_storage_dashboards(hass, dashboards)

    created_paths = {item["url_path"] for item in collection.created}
    assert created_paths == {"auto-home", "auto-rooms"}


async def test_register_storage_dashboards_skips_already_registered(hass: HomeAssistant) -> None:
    collection = _FakeDashboardsCollection(existing=[{"url_path": "auto-home"}])
    hass.data["lovelace"] = {"dashboards_collection": collection}

    dashboards = {"auto_home": {"title": "Home", "icon": "mdi:home", "views": []}}
    await async_register_storage_dashboards(hass, dashboards)

    assert collection.created == []


async def test_register_storage_dashboards_noop_when_lovelace_data_absent(
    hass: HomeAssistant,
) -> None:
    hass.data.pop("lovelace", None)

    # Must not raise even though there's nothing to register into.
    await async_register_storage_dashboards(hass, {"auto_home": {"title": "Home", "icon": "mdi:home", "views": []}})


async def test_register_storage_dashboards_noop_when_shape_unexpected(hass: HomeAssistant) -> None:
    hass.data["lovelace"] = {"dashboards": {}}  # no "dashboards_collection" key

    await async_register_storage_dashboards(hass, {"auto_home": {"title": "Home", "icon": "mdi:home", "views": []}})
