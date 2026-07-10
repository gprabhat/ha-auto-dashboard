"""WebSocket API backing the Dashboard Studio panel.

All commands are admin-only (editing dashboards is an admin action) and
operate on the single config entry this integration supports.
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components import websocket_api
from homeassistant.core import HomeAssistant, callback

from .const import DATA_COORDINATOR, DOMAIN
from .coordinator import DiscoveryCoordinator
from .dashboard import async_generate_and_install
from .dashboard.compiler import compile_dashboards
from .dashboard.overrides import OverridesStore, apply_overrides, studio_payload
from .dashboard.resources import async_detect_frontend_resources


def _get_coordinator(hass: HomeAssistant) -> DiscoveryCoordinator | None:
    entry_data = next(iter(hass.data.get(DOMAIN, {}).values()), None)
    return entry_data[DATA_COORDINATOR] if entry_data else None


async def _build_state_message(hass: HomeAssistant, coordinator: DiscoveryCoordinator) -> dict[str, Any]:
    graph = coordinator.data
    resources = await async_detect_frontend_resources(hass)
    dashboards = compile_dashboards(graph, resources)

    overrides = await OverridesStore(hass, coordinator.entry.entry_id).async_load()
    dashboards = apply_overrides(overrides, dashboards, graph=graph, resources=resources)

    return {
        "dashboards": studio_payload(dashboards),
        "overrides": overrides,
        "entities": [
            {
                "entity_id": entity.entity_id,
                "name": entity.name,
                "domain": entity.domain,
                "area_id": entity.area_id,
                "category": entity.category,
            }
            for entity in graph.entities.values()
            if not entity.disabled and not entity.hidden
        ],
    }


@websocket_api.require_admin
@websocket_api.websocket_command({vol.Required("type"): "ha_auto_dashboard/studio/get_state"})
@websocket_api.async_response
async def ws_get_state(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    coordinator = _get_coordinator(hass)
    if coordinator is None:
        connection.send_error(msg["id"], "not_setup", "HA Auto Dashboard is not set up")
        return
    if coordinator.data is None:
        connection.send_error(msg["id"], "no_data", "No scan has completed yet")
        return

    connection.send_result(msg["id"], await _build_state_message(hass, coordinator))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "ha_auto_dashboard/studio/save_overrides",
        vol.Required("overrides"): dict,
    }
)
@websocket_api.async_response
async def ws_save_overrides(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    coordinator = _get_coordinator(hass)
    if coordinator is None:
        connection.send_error(msg["id"], "not_setup", "HA Auto Dashboard is not set up")
        return
    if coordinator.data is None:
        connection.send_error(msg["id"], "no_data", "No scan has completed yet")
        return

    overrides = {
        "cards": msg["overrides"].get("cards", {}),
        "added_cards": msg["overrides"].get("added_cards", []),
    }
    await OverridesStore(hass, coordinator.entry.entry_id).async_save(overrides)
    await async_generate_and_install(hass, coordinator.data, entry=coordinator.entry)

    connection.send_result(msg["id"], await _build_state_message(hass, coordinator))


@websocket_api.require_admin
@websocket_api.websocket_command(
    {
        vol.Required("type"): "ha_auto_dashboard/studio/reset",
        vol.Optional("card_id"): str,
    }
)
@websocket_api.async_response
async def ws_reset(hass: HomeAssistant, connection: websocket_api.ActiveConnection, msg: dict) -> None:
    coordinator = _get_coordinator(hass)
    if coordinator is None:
        connection.send_error(msg["id"], "not_setup", "HA Auto Dashboard is not set up")
        return

    store = OverridesStore(hass, coordinator.entry.entry_id)
    target = msg.get("card_id")
    if target:
        overrides = await store.async_load()
        overrides.setdefault("cards", {}).pop(target, None)
        entity_id = target.rsplit(":entity:", 1)[-1] if ":entity:" in target else None
        overrides["added_cards"] = [
            added for added in overrides.get("added_cards", []) if added.get("entity_id") != entity_id
        ]
        await store.async_save(overrides)
    else:
        await store.async_save({"cards": {}, "added_cards": []})

    if coordinator.data is not None:
        await async_generate_and_install(hass, coordinator.data, entry=coordinator.entry)

    connection.send_result(msg["id"], await _build_state_message(hass, coordinator))


@callback
def async_setup_websocket_api(hass: HomeAssistant) -> None:
    """Register the `ha_auto_dashboard/studio/*` commands, once."""
    if hass.data.get(f"{DOMAIN}_websocket_api_registered"):
        return
    websocket_api.async_register_command(hass, ws_get_state)
    websocket_api.async_register_command(hass, ws_save_overrides)
    websocket_api.async_register_command(hass, ws_reset)
    hass.data[f"{DOMAIN}_websocket_api_registered"] = True
