"""Dashboard engine: compiles the discovery graph into Lovelace dashboards."""
from __future__ import annotations

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from ..const import (
    CONF_REQUIRE_CONFIRMATION,
    CONF_STORAGE_MODE,
    DEFAULT_REQUIRE_CONFIRMATION,
    DEFAULT_STORAGE_MODE,
    DOMAIN,
    ISSUE_PENDING_DASHBOARD_CHANGE,
)
from ..models import RegistryGraph
from .compiler import VIEW_SLUGS, compile_dashboards
from .installer import async_compute_dashboard_diff, async_install_dashboards, configuration_snippet
from .issues import async_update_registration_issue, async_update_resource_issue
from .overrides import OverridesStore, apply_overrides
from .resources import async_detect_frontend_resources
from .storage_registration import async_register_storage_dashboards

__all__ = ["compile_dashboards", "async_install_dashboards", "async_generate_and_install"]


async def _async_apply_dashboards(
    hass: HomeAssistant,
    entry: ConfigEntry,
    dashboards: dict[str, dict],
    *,
    update_registration_issue: bool,
) -> list[str]:
    """Write dashboard files, optionally register storage-mode dashboards,
    and keep the registration Repairs issue in sync.

    Shared by the ungated `async_generate_and_install` path and the
    Repairs confirm-flow in `repairs.py`, which calls this directly once
    the user approves a pending change.
    """
    written = await async_install_dashboards(hass, dashboards)

    if entry.options.get(CONF_STORAGE_MODE, DEFAULT_STORAGE_MODE):
        await async_register_storage_dashboards(hass, dashboards)
    elif update_registration_issue:
        async_update_registration_issue(hass, dashboards, configuration_snippet(dashboards))

    return written


async def async_generate_and_install(
    hass: HomeAssistant,
    graph: RegistryGraph,
    *,
    entry: ConfigEntry,
    view: str | None = None,
) -> list[str]:
    """Compile the graph into dashboards, then either write them
    immediately or - if `require_confirmation` is on and something
    changed - raise a fixable Repairs issue and hold off writing until
    the user confirms.

    `view` optionally scopes compilation (and the write) to a single
    dashboard (one of `compiler.VIEW_SLUGS`'s short names); the
    registration-reminder issue is only updated on a full (unscoped) run,
    since it reflects the complete dashboard set.

    Any Dashboard Studio overrides (hidden/renamed/reordered/added cards)
    are layered on right after compiling and before the confirm-gate diff,
    so a require_confirmation diff only ever surfaces genuine
    auto-generation changes - not the user's own already-saved edits.
    """
    resources = await async_detect_frontend_resources(hass)
    only = VIEW_SLUGS.get(view) if view else None
    dashboards = compile_dashboards(graph, resources, only=only)

    overrides = await OverridesStore(hass, entry.entry_id).async_load()
    dashboards = apply_overrides(overrides, dashboards, graph=graph, resources=resources)

    async_update_resource_issue(hass, resources)

    if entry.options.get(CONF_REQUIRE_CONFIRMATION, DEFAULT_REQUIRE_CONFIRMATION):
        diff = await async_compute_dashboard_diff(hass, dashboards)
        if diff:
            ir.async_create_issue(
                hass,
                DOMAIN,
                ISSUE_PENDING_DASHBOARD_CHANGE,
                is_fixable=True,
                severity=ir.IssueSeverity.WARNING,
                translation_key=ISSUE_PENDING_DASHBOARD_CHANGE,
                translation_placeholders={"diff": diff},
                data={
                    "entry_id": entry.entry_id,
                    "dashboards": dashboards,
                    "update_registration_issue": view is None,
                },
            )
            return []
        ir.async_delete_issue(hass, DOMAIN, ISSUE_PENDING_DASHBOARD_CHANGE)

    return await _async_apply_dashboards(
        hass, entry, dashboards, update_registration_issue=view is None
    )
