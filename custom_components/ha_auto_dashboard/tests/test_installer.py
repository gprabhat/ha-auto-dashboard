"""Tests for writing compiled dashboards to disk."""
from pathlib import Path

import yaml
from homeassistant.core import HomeAssistant

from custom_components.ha_auto_dashboard.const import DASHBOARD_OUTPUT_DIR
from custom_components.ha_auto_dashboard.dashboard.installer import (
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
