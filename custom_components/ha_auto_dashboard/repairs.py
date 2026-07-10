"""Repairs fix-flow: confirm-before-apply gate for pending dashboard changes.

Only used when the `require_confirmation` option is on. When a scan
produces different dashboard YAML than what's on disk, `async_generate_and_install`
(in `dashboard/__init__.py`) raises a fixable Repairs issue instead of
writing immediately; this flow shows the diff and applies the change once
the user confirms it.
"""
from __future__ import annotations

from typing import Any

import voluptuous as vol
from homeassistant.components.repairs import RepairsFlow
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers import issue_registry as ir

from .const import DOMAIN, ISSUE_PENDING_DASHBOARD_CHANGE
from .dashboard import _async_apply_dashboards


async def async_create_fix_flow(
    hass: HomeAssistant, issue_id: str, data: dict[str, Any] | None
) -> RepairsFlow:
    if issue_id == ISSUE_PENDING_DASHBOARD_CHANGE:
        return PendingDashboardChangeFlow(data or {})
    raise ValueError(f"No fix flow for issue_id: {issue_id}")


class PendingDashboardChangeFlow(RepairsFlow):
    """Single confirm step: apply the dashboards that were held back
    pending user approval, then clear the issue."""

    def __init__(self, data: dict[str, Any]) -> None:
        self._data = data

    async def async_step_init(self, user_input: dict[str, str] | None = None) -> FlowResult:
        return await self.async_step_confirm()

    async def async_step_confirm(self, user_input: dict[str, str] | None = None) -> FlowResult:
        if user_input is not None:
            entry = self.hass.config_entries.async_get_entry(self._data.get("entry_id"))
            if entry is not None:
                await _async_apply_dashboards(
                    self.hass,
                    entry,
                    self._data.get("dashboards", {}),
                    update_registration_issue=self._data.get("update_registration_issue", True),
                )
            ir.async_delete_issue(self.hass, DOMAIN, ISSUE_PENDING_DASHBOARD_CHANGE)
            return self.async_create_entry(title="", data={})

        return self.async_show_form(step_id="confirm", data_schema=vol.Schema({}))
