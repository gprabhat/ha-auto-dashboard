"""Raises/clears HA Repairs issues for frontend-resource and registration gaps.

Both issues are informational rather than "fixable" (there's no automated
action HA can take: installing a HACS resource or editing configuration.yaml
are things only the user can do), so they're plain `is_fixable=False`
issues with a translation_key pointing at strings.json's "issues" section,
rather than a full Repairs fix-flow.
"""
from __future__ import annotations

from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from ..const import DOMAIN, ISSUE_MISSING_RESOURCES, ISSUE_REGISTER_DASHBOARDS
from .resources import FrontendResources


def async_update_resource_issue(hass: HomeAssistant, resources: FrontendResources) -> None:
    """Raise an issue while any of Mushroom/Bubble Card/mini-graph-card are
    missing, and clear it automatically once they're all detected."""
    if resources.missing:
        ir.async_create_issue(
            hass,
            DOMAIN,
            ISSUE_MISSING_RESOURCES,
            is_fixable=False,
            severity=ir.IssueSeverity.WARNING,
            translation_key=ISSUE_MISSING_RESOURCES,
            translation_placeholders={"missing": ", ".join(resources.missing)},
        )
    else:
        ir.async_delete_issue(hass, DOMAIN, ISSUE_MISSING_RESOURCES)


def _dashboards_registered(hass: HomeAssistant, dashboards: dict[str, dict]) -> bool:
    """Best-effort check: are our dashboards already declared in configuration.yaml?

    Relies on the internal `hass.data["lovelace"]["dashboards"]` structure,
    which isn't a guaranteed public API - if it can't tell, this returns
    False so the reminder issue stays open rather than silently vanishing.
    """
    lovelace_data = hass.data.get("lovelace")
    if not isinstance(lovelace_data, dict):
        return False
    configured = lovelace_data.get("dashboards")
    if not isinstance(configured, dict):
        return False
    expected = {slug.replace("_", "-") for slug in dashboards}
    return expected.issubset(configured.keys())


def async_update_registration_issue(hass: HomeAssistant, dashboards: dict[str, dict], snippet: str) -> None:
    """Raise an issue with the configuration.yaml snippet until the
    dashboards are registered, then clear it automatically."""
    if _dashboards_registered(hass, dashboards):
        ir.async_delete_issue(hass, DOMAIN, ISSUE_REGISTER_DASHBOARDS)
        return

    ir.async_create_issue(
        hass,
        DOMAIN,
        ISSUE_REGISTER_DASHBOARDS,
        is_fixable=False,
        severity=ir.IssueSeverity.WARNING,
        translation_key=ISSUE_REGISTER_DASHBOARDS,
        translation_placeholders={"snippet": snippet},
    )
