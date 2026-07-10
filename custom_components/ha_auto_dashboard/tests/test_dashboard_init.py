"""Tests for async_generate_and_install: the write/scope/confirm-gate glue."""
from pathlib import Path

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_auto_dashboard.const import (
    CONF_REQUIRE_CONFIRMATION,
    DASHBOARD_OUTPUT_DIR,
    DOMAIN,
    ISSUE_PENDING_DASHBOARD_CHANGE,
)
from custom_components.ha_auto_dashboard.dashboard import async_generate_and_install
from custom_components.ha_auto_dashboard.dashboard.compiler import DASHBOARD_HOME
from custom_components.ha_auto_dashboard.models import AreaNode, RegistryGraph


def _sample_graph() -> RegistryGraph:
    graph = RegistryGraph()
    graph.areas["kitchen"] = AreaNode(area_id="kitchen", name="Kitchen")
    return graph


async def test_generate_and_install_writes_by_default(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    written = await async_generate_and_install(hass, _sample_graph(), entry=entry)

    assert len(written) > 0
    for path in written:
        assert Path(path).exists()


async def test_generate_and_install_scoped_view_writes_only_that_slug(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    written = await async_generate_and_install(hass, _sample_graph(), entry=entry, view="home")

    assert len(written) == 1
    assert written[0].endswith(f"{DASHBOARD_HOME}.yaml")


async def test_generate_and_install_holds_back_write_when_confirmation_required(
    hass: HomeAssistant,
) -> None:
    entry = MockConfigEntry(domain=DOMAIN, options={CONF_REQUIRE_CONFIRMATION: True})
    entry.add_to_hass(hass)

    written = await async_generate_and_install(hass, _sample_graph(), entry=entry, view="home")

    assert written == []
    output_path = Path(hass.config.config_dir) / DASHBOARD_OUTPUT_DIR / f"{DASHBOARD_HOME}.yaml"
    assert not output_path.exists()

    issue = ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_PENDING_DASHBOARD_CHANGE)
    assert issue is not None
    assert "diff" in issue.translation_placeholders


async def test_generate_and_install_applies_immediately_when_no_diff(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN, options={CONF_REQUIRE_CONFIRMATION: True})
    entry.add_to_hass(hass)

    # First call with confirmation off writes the file directly, so the
    # second (confirmation-required) call for identical content has
    # nothing to confirm.
    plain_entry = MockConfigEntry(domain=DOMAIN)
    plain_entry.add_to_hass(hass)
    await async_generate_and_install(hass, _sample_graph(), entry=plain_entry, view="home")

    written = await async_generate_and_install(hass, _sample_graph(), entry=entry, view="home")

    assert len(written) == 1
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_PENDING_DASHBOARD_CHANGE) is None
