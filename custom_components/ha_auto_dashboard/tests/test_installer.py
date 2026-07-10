"""Tests for writing compiled dashboards to disk."""
from pathlib import Path

import yaml
from homeassistant.core import HomeAssistant

from custom_components.ha_auto_dashboard.const import DASHBOARD_OUTPUT_DIR
from custom_components.ha_auto_dashboard.dashboard.installer import (
    async_compute_dashboard_diff,
    async_install_dashboards,
    configuration_snippet,
)


async def test_install_dashboards_writes_yaml_files(hass: HomeAssistant) -> None:
    dashboards = {
        "auto_home": {
            "title": "Home",
            "icon": "mdi:home",
            "views": [{"title": "Home", "path": "home", "cards": [{"type": "area", "area": "kitchen"}]}],
        }
    }

    written = await async_install_dashboards(hass, dashboards)

    assert len(written) == 1
    output_path = Path(hass.config.config_dir) / DASHBOARD_OUTPUT_DIR / "auto_home.yaml"
    assert str(output_path) == written[0]
    assert output_path.exists()

    content = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert content == {"views": dashboards["auto_home"]["views"]}


async def test_compute_dashboard_diff_none_when_nothing_changed(hass: HomeAssistant) -> None:
    dashboards = {
        "auto_home": {
            "title": "Home",
            "icon": "mdi:home",
            "views": [{"title": "Home", "path": "home", "cards": []}],
        }
    }
    await async_install_dashboards(hass, dashboards)

    assert await async_compute_dashboard_diff(hass, dashboards) is None


async def test_compute_dashboard_diff_shows_changes_without_writing(hass: HomeAssistant) -> None:
    original = {
        "auto_home": {
            "title": "Home",
            "icon": "mdi:home",
            "views": [{"title": "Home", "path": "home", "cards": []}],
        }
    }
    await async_install_dashboards(hass, original)

    changed = {
        "auto_home": {
            "title": "Home",
            "icon": "mdi:home",
            "views": [{"title": "Home", "path": "home", "cards": [{"type": "area", "area": "kitchen"}]}],
        }
    }
    diff = await async_compute_dashboard_diff(hass, changed)

    assert diff is not None
    assert "area" in diff

    output_path = Path(hass.config.config_dir) / DASHBOARD_OUTPUT_DIR / "auto_home.yaml"
    content = yaml.safe_load(output_path.read_text(encoding="utf-8"))
    assert content == {"views": original["auto_home"]["views"]}  # unchanged - diff doesn't write


async def test_compute_dashboard_diff_new_file_shows_as_addition(hass: HomeAssistant) -> None:
    dashboards = {
        "auto_home": {
            "title": "Home",
            "icon": "mdi:home",
            "views": [{"title": "Home", "path": "home", "cards": []}],
        }
    }

    diff = await async_compute_dashboard_diff(hass, dashboards)

    assert diff is not None
    assert "(current)" in diff
    assert "(new)" in diff


def test_configuration_snippet_one_entry_per_dashboard() -> None:
    dashboards = {
        "auto_home": {"title": "Home", "icon": "mdi:home", "views": []},
        "auto_rooms": {"title": "Rooms", "icon": "mdi:floor-plan", "views": []},
    }

    snippet = configuration_snippet(dashboards)

    assert "auto-home:" in snippet
    assert "auto-rooms:" in snippet
    assert "filename: dashboards/auto_home.yaml" in snippet
    assert "title: Home" in snippet
