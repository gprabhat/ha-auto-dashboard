"""Config flow for HA Auto Dashboard.

The integration is zero-configuration: adding it is a single confirmation
step and only one instance is allowed per HA installation.
"""
from __future__ import annotations

from typing import Any

from homeassistant.config_entries import ConfigFlow
from homeassistant.data_entry_flow import FlowResult

from .const import DOMAIN


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
