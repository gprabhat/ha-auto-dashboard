"""Tests for the ha_auto_dashboard/studio/* websocket commands.

Deliberately does *not* go through the full `hass.config_entries.async_setup`
(which - via this integration's manifest dependencies - would also boot
`frontend`/`panel_custom` and their real HTTP server). That's exercised by
`test_dashboard_studio_panel.py` instead. Here we only need `websocket_api`
set up (the standard minimal pattern for testing websocket commands), plus
this integration's own coordinator/websocket registration wired up by hand.
"""
from homeassistant.config_entries import ConfigEntryState
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_auto_dashboard.const import DATA_COORDINATOR, DOMAIN
from custom_components.ha_auto_dashboard.coordinator import DiscoveryCoordinator
from custom_components.ha_auto_dashboard.dashboard import async_generate_and_install
from custom_components.ha_auto_dashboard.websocket_api import async_setup_websocket_api


async def _setup_entry(hass: HomeAssistant) -> MockConfigEntry:
    assert await async_setup_component(hass, "websocket_api", {})

    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    # async_config_entry_first_refresh() requires the entry to be in this
    # state, which normally only happens mid-way through the real
    # hass.config_entries.async_setup() flow this test deliberately skips.
    entry.mock_state(hass, ConfigEntryState.SETUP_IN_PROGRESS)

    coordinator = DiscoveryCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()
    await async_generate_and_install(hass, coordinator.data, entry=entry)
    hass.data.setdefault(DOMAIN, {})[entry.entry_id] = {DATA_COORDINATOR: coordinator}

    async_setup_websocket_api(hass)
    return entry


async def test_get_state_returns_dashboards_and_entities(hass: HomeAssistant, hass_ws_client) -> None:
    await _setup_entry(hass)
    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "ha_auto_dashboard/studio/get_state"})
    response = await client.receive_json()

    assert response["success"] is True
    assert "auto_home" in response["result"]["dashboards"]
    home_cards = response["result"]["dashboards"]["auto_home"]["views"][0]["cards"]
    assert all("_studio_id" in card for card in home_cards)
    assert response["result"]["overrides"] == {"cards": {}, "added_cards": []}
    assert isinstance(response["result"]["entities"], list)


async def test_save_overrides_persists_and_reapplies(hass: HomeAssistant, hass_ws_client) -> None:
    await _setup_entry(hass)
    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "ha_auto_dashboard/studio/get_state"})
    initial = await client.receive_json()
    home_cards = initial["result"]["dashboards"]["auto_home"]["views"][0]["cards"]
    a_card_id = home_cards[0]["_studio_id"]

    await client.send_json(
        {
            "id": 2,
            "type": "ha_auto_dashboard/studio/save_overrides",
            "overrides": {"cards": {a_card_id: {"hidden": True}}},
        }
    )
    saved = await client.receive_json()

    assert saved["success"] is True
    assert saved["result"]["overrides"]["cards"] == {a_card_id: {"hidden": True}}
    new_ids = {c["_studio_id"] for c in saved["result"]["dashboards"]["auto_home"]["views"][0]["cards"]}
    assert a_card_id not in new_ids


async def test_reset_clears_a_single_override(hass: HomeAssistant, hass_ws_client) -> None:
    await _setup_entry(hass)
    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "ha_auto_dashboard/studio/get_state"})
    initial = await client.receive_json()
    home_cards = initial["result"]["dashboards"]["auto_home"]["views"][0]["cards"]
    a_card_id = home_cards[0]["_studio_id"]

    await client.send_json(
        {
            "id": 2,
            "type": "ha_auto_dashboard/studio/save_overrides",
            "overrides": {"cards": {a_card_id: {"hidden": True}}},
        }
    )
    await client.receive_json()

    await client.send_json({"id": 3, "type": "ha_auto_dashboard/studio/reset", "card_id": a_card_id})
    reset = await client.receive_json()

    assert reset["success"] is True
    assert reset["result"]["overrides"]["cards"] == {}
    restored_ids = {c["_studio_id"] for c in reset["result"]["dashboards"]["auto_home"]["views"][0]["cards"]}
    assert a_card_id in restored_ids


async def test_reset_without_card_id_clears_everything(hass: HomeAssistant, hass_ws_client) -> None:
    await _setup_entry(hass)
    client = await hass_ws_client(hass)

    await client.send_json({"id": 1, "type": "ha_auto_dashboard/studio/get_state"})
    initial = await client.receive_json()
    home_cards = initial["result"]["dashboards"]["auto_home"]["views"][0]["cards"]
    a_card_id = home_cards[0]["_studio_id"]

    await client.send_json(
        {
            "id": 2,
            "type": "ha_auto_dashboard/studio/save_overrides",
            "overrides": {"cards": {a_card_id: {"name": "Renamed"}}},
        }
    )
    await client.receive_json()

    await client.send_json({"id": 3, "type": "ha_auto_dashboard/studio/reset"})
    reset = await client.receive_json()

    assert reset["result"]["overrides"] == {"cards": {}, "added_cards": []}
