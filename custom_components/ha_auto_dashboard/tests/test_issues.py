"""Tests for the Repairs issues raised for missing resources/registration."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers import issue_registry as ir

from custom_components.ha_auto_dashboard.const import (
    DOMAIN,
    ISSUE_MISSING_RESOURCES,
    ISSUE_REGISTER_DASHBOARDS,
)
from custom_components.ha_auto_dashboard.dashboard.issues import (
    async_update_registration_issue,
    async_update_resource_issue,
)
from custom_components.ha_auto_dashboard.dashboard.resources import FrontendResources


def test_resource_issue_created_when_something_missing(hass: HomeAssistant) -> None:
    resources = FrontendResources(mushroom=True, bubble_card=False, mini_graph_card=True)
    async_update_resource_issue(hass, resources)

    issue = ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_MISSING_RESOURCES)
    assert issue is not None
    assert issue.translation_placeholders == {"missing": "Bubble Card"}


def test_resource_issue_cleared_once_all_present(hass: HomeAssistant) -> None:
    missing = FrontendResources(mushroom=False, bubble_card=True, mini_graph_card=True)
    async_update_resource_issue(hass, missing)
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_MISSING_RESOURCES) is not None

    all_present = FrontendResources(mushroom=True, bubble_card=True, mini_graph_card=True)
    async_update_resource_issue(hass, all_present)
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_MISSING_RESOURCES) is None


def test_registration_issue_created_when_not_registered(hass: HomeAssistant) -> None:
    dashboards = {"auto_home": {"title": "Home", "icon": "mdi:home", "views": []}}
    async_update_registration_issue(hass, dashboards, "lovelace:\n  dashboards:\n    auto-home: ...")

    issue = ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_REGISTER_DASHBOARDS)
    assert issue is not None
    assert "auto-home" in issue.translation_placeholders["snippet"]


def test_registration_issue_cleared_once_dashboards_are_registered(hass: HomeAssistant) -> None:
    dashboards = {"auto_home": {"title": "Home", "icon": "mdi:home", "views": []}}
    async_update_registration_issue(hass, dashboards, "snippet")
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_REGISTER_DASHBOARDS) is not None

    hass.data["lovelace"] = {"dashboards": {"auto-home": object()}}
    async_update_registration_issue(hass, dashboards, "snippet")
    assert ir.async_get(hass).async_get_issue(DOMAIN, ISSUE_REGISTER_DASHBOARDS) is None
