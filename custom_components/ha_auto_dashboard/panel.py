"""Registers the Dashboard Studio sidebar panel and serves its frontend
JS from `www/`.
"""
from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.components import panel_custom
from homeassistant.core import HomeAssistant

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

PANEL_URL_PATH = "ha-auto-dashboard-studio"
_JS_URL_PATH = f"/{DOMAIN}_studio_frontend"
_WWW_DIR = Path(__file__).parent / "www"
_PANEL_REGISTERED = f"{DOMAIN}_panel_registered"


async def _async_register_static_paths(hass: HomeAssistant) -> None:
    """Serve `www/` at `_JS_URL_PATH`.

    `hass.http.register_static_path` was removed in HA core 2025.7 in
    favor of the non-blocking `async_register_static_paths`; this repo's
    floor is HA 2025.1 (where both exist), so the older API is kept as a
    defensive fallback rather than a hard requirement - same "never let
    a version-sensitive HA surface break setup" posture as
    `dashboard/storage_registration.py`.
    """
    try:
        from homeassistant.components.http import StaticPathConfig

        await hass.http.async_register_static_paths(
            [StaticPathConfig(_JS_URL_PATH, str(_WWW_DIR), cache_headers=False)]
        )
    except Exception:  # noqa: BLE001 - fall back rather than block setup on an HA-core mismatch
        _LOGGER.debug(
            "async_register_static_paths unavailable, falling back to register_static_path",
            exc_info=True,
        )
        hass.http.register_static_path(_JS_URL_PATH, str(_WWW_DIR), cache_headers=False)


async def async_register_panel(hass: HomeAssistant) -> None:
    """Register the Dashboard Studio sidebar panel, once."""
    if hass.data.get(_PANEL_REGISTERED):
        return

    await _async_register_static_paths(hass)

    await panel_custom.async_register_panel(
        hass,
        webcomponent_name="ha-auto-dashboard-studio-panel",
        frontend_url_path=PANEL_URL_PATH,
        sidebar_title="Dashboard Studio",
        sidebar_icon="mdi:view-dashboard-edit",
        module_url=f"{_JS_URL_PATH}/dashboard-studio-panel.js",
        embed_iframe=False,
        require_admin=True,
    )
    hass.data[_PANEL_REGISTERED] = True


async def async_unregister_panel(hass: HomeAssistant) -> None:
    """Remove the sidebar panel on the last entry's unload."""
    if not hass.data.pop(_PANEL_REGISTERED, False):
        return
    try:
        from homeassistant.components.frontend import async_remove_panel

        async_remove_panel(hass, PANEL_URL_PATH)
    except Exception:  # noqa: BLE001 - best-effort cleanup, must never block unload
        _LOGGER.debug("Could not remove the Dashboard Studio panel on unload", exc_info=True)
