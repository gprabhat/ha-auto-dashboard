"""Smoke test for Dashboard Studio's sidebar panel registration, exercised
through a real config entry setup (this is the one place we deliberately
pull in `frontend`/`panel_custom` via the manifest's declared dependencies -
see test_websocket_api.py's docstring for why the websocket command tests
avoid doing that)."""
from homeassistant.components.frontend import DATA_PANELS
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_auto_dashboard.const import DOMAIN
from custom_components.ha_auto_dashboard.panel import PANEL_URL_PATH


async def test_setup_entry_registers_sidebar_panel(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    panels = hass.data[DATA_PANELS]
    assert PANEL_URL_PATH in panels
    panel = panels[PANEL_URL_PATH]
    assert panel.sidebar_title == "Dashboard Studio"
    assert panel.require_admin is True


async def test_unload_entry_removes_sidebar_panel(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()

    assert PANEL_URL_PATH not in hass.data[DATA_PANELS]
