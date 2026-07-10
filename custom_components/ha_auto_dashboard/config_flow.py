"""Config/options flow for HA Auto Dashboard.

The config flow itself is zero-configuration: adding the integration is a
single confirmation step and only one instance is allowed per HA
installation. All actual user-facing settings (area/entity exclusion,
storage-mode dashboards, confirm-before-apply) live in the options flow.
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.config_entries import ConfigEntry, ConfigFlow, OptionsFlow
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import selector

from .const import (
    CONF_EXCLUDED_AREAS,
    CONF_EXCLUDED_ENTITIES,
    CONF_REQUIRE_CONFIRMATION,
    CONF_STORAGE_MODE,
    DEFAULT_EXCLUDED_AREAS,
    DEFAULT_EXCLUDED_ENTITIES,
    DEFAULT_REQUIRE_CONFIRMATION,
    DEFAULT_STORAGE_MODE,
    DOMAIN,
)


class HaAutoDashboardConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle the (single-step, single-instance) config flow."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Confirm setup; no user input is required."""
        await self.async_set_unique_id(DOMAIN)
        self._abort_if_unique_id_configured()

        if user_input is not None:
            return self.async_create_entry(title="HA Auto Dashboard", data={})

        return self.async_show_form(step_id="user")

    @staticmethod
    def async_get_options_flow(config_entry: ConfigEntry) -> HaAutoDashboardOptionsFlow:
        return HaAutoDashboardOptionsFlow()


class HaAutoDashboardOptionsFlow(OptionsFlow):
    """Single-step options flow: exclusions plus the opt-in toggles.

    `self.config_entry` is populated by the base `OptionsFlow` class itself
    (HA core 2024.12+) - do not set it manually here, that pattern is
    deprecated.
    """

    async def async_step_init(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        options = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Optional(
                    CONF_EXCLUDED_AREAS,
                    default=list(options.get(CONF_EXCLUDED_AREAS, DEFAULT_EXCLUDED_AREAS)),
                ): selector.AreaSelector(selector.AreaSelectorConfig(multiple=True)),
                vol.Optional(
                    CONF_EXCLUDED_ENTITIES,
                    default=list(options.get(CONF_EXCLUDED_ENTITIES, DEFAULT_EXCLUDED_ENTITIES)),
                ): selector.EntitySelector(selector.EntitySelectorConfig(multiple=True)),
                vol.Optional(
                    CONF_REQUIRE_CONFIRMATION,
                    default=options.get(CONF_REQUIRE_CONFIRMATION, DEFAULT_REQUIRE_CONFIRMATION),
                ): bool,
                vol.Optional(
                    CONF_STORAGE_MODE,
                    default=options.get(CONF_STORAGE_MODE, DEFAULT_STORAGE_MODE),
                ): bool,
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)
