"""Tests for the config flow (single confirmation step) and the options
flow (exclusions + opt-in toggles)."""
from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResultType
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_auto_dashboard.const import (
    CONF_EXCLUDED_AREAS,
    CONF_EXCLUDED_ENTITIES,
    CONF_REQUIRE_CONFIRMATION,
    CONF_STORAGE_MODE,
    DOMAIN,
)


async def test_user_flow_creates_single_entry(hass: HomeAssistant) -> None:
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert result2["title"] == "HA Auto Dashboard"
    assert result2["data"] == {}


async def test_user_flow_aborts_when_already_configured(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN, unique_id=DOMAIN)
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == FlowResultType.ABORT
    assert result["reason"] == "already_configured"


async def test_options_flow_defaults_from_existing_options(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(
        domain=DOMAIN,
        options={CONF_EXCLUDED_AREAS: ["kitchen"], CONF_REQUIRE_CONFIRMATION: True},
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    assert result["type"] == FlowResultType.FORM
    assert result["step_id"] == "init"


async def test_options_flow_saves_new_values(hass: HomeAssistant) -> None:
    entry = MockConfigEntry(domain=DOMAIN)
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    result2 = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            CONF_EXCLUDED_AREAS: ["kitchen"],
            CONF_EXCLUDED_ENTITIES: ["light.attic"],
            CONF_REQUIRE_CONFIRMATION: True,
            CONF_STORAGE_MODE: False,
        },
    )

    assert result2["type"] == FlowResultType.CREATE_ENTRY
    assert entry.options[CONF_EXCLUDED_AREAS] == ["kitchen"]
    assert entry.options[CONF_EXCLUDED_ENTITIES] == ["light.attic"]
    assert entry.options[CONF_REQUIRE_CONFIRMATION] is True
    assert entry.options[CONF_STORAGE_MODE] is False
