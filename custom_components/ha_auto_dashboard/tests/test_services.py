"""End-to-end tests for the `ha_auto_dashboard.generate`/`scan` services,
exercised through a real config entry setup."""
from pathlib import Path

import pytest
import voluptuous as vol
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_auto_dashboard.const import DASHBOARD_OUTPUT_DIR, DOMAIN, SERVICE_GENERATE
from custom_components.ha_auto_dashboard.dashboard.compiler import DASHBOARD_HOME


async def _setup_entry(hass: HomeAssistant) -> MockConfigEntry:
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    return entry


async def test_generate_service_scoped_to_one_view_writes_only_that_file(
    hass: HomeAssistant,
) -> None:
    await _setup_entry(hass)

    # Setup already did a full (unscoped) generate - clear it out so this
    # test only sees what the scoped service call itself writes.
    dashboards_dir = Path(hass.config.config_dir) / DASHBOARD_OUTPUT_DIR
    for existing in dashboards_dir.glob("*.yaml"):
        existing.unlink()

    await hass.services.async_call(
        DOMAIN, SERVICE_GENERATE, {"view": "home"}, blocking=True
    )
    await hass.async_block_till_done()

    written = list(dashboards_dir.glob("*.yaml"))
    assert [p.stem for p in written] == [DASHBOARD_HOME]


async def test_generate_service_rejects_unknown_view(hass: HomeAssistant) -> None:
    await _setup_entry(hass)

    with pytest.raises(vol.Invalid):
        await hass.services.async_call(
            DOMAIN, SERVICE_GENERATE, {"view": "not_a_real_view"}, blocking=True
        )
