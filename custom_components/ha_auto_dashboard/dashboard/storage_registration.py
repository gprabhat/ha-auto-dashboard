"""Best-effort registration of compiled dashboards as HA storage-mode
dashboards (opt-in via the `storage_mode` option), so dashboards show up
in Home Assistant immediately without the manual configuration.yaml step.

Home Assistant has no public, stable API for a non-`lovelace` integration
to create a storage-mode dashboard at runtime as of HA core 2025.1 - this
reaches into `hass.data["lovelace"]`'s internal dashboard collection
(the same mechanism the frontend's "+ Add Dashboard" button uses). Every
access is defensively guarded so a future core refactor just disables
this opt-in path (falling back to file-only mode) instead of breaking
setup.
"""
from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)


def _get_dashboards_collection(hass: HomeAssistant):
    """Best-effort lookup of the lovelace storage dashboards collection.
    Returns None if the internal shape isn't what's expected."""
    lovelace_data = hass.data.get("lovelace")
    if lovelace_data is None:
        return None
    if isinstance(lovelace_data, dict):
        return lovelace_data.get("dashboards_collection")
    return getattr(lovelace_data, "dashboards_collection", None)


async def async_register_storage_dashboards(hass: HomeAssistant, dashboards: dict[str, dict]) -> None:
    """Create a storage-mode dashboard for each compiled slug that isn't
    registered yet. Never raises - logs and no-ops on any unexpected
    internal shape so this stays a pure add-on to the file-write path."""
    try:
        collection = _get_dashboards_collection(hass)
        if collection is None:
            _LOGGER.debug(
                "Storage-mode dashboard registration skipped: lovelace "
                "dashboards collection not found"
            )
            return

        existing = {item["url_path"] for item in collection.async_items()}
        for slug, dashboard in dashboards.items():
            url_path = slug.replace("_", "-")
            if url_path in existing:
                continue
            await collection.async_create_item(
                {
                    "title": dashboard["title"],
                    "icon": dashboard["icon"],
                    "url_path": url_path,
                    "mode": "storage",
                    "show_in_sidebar": True,
                    "require_admin": False,
                }
            )
            _LOGGER.info("HA Auto Dashboard registered storage-mode dashboard: %s", url_path)
    except Exception:  # noqa: BLE001 - undocumented HA internals must never break setup
        _LOGGER.warning(
            "Storage-mode dashboard registration failed (Home Assistant's internal "
            "lovelace storage API may have changed) - dashboards remain available as "
            "files under dashboards/ for manual registration",
            exc_info=True,
        )
