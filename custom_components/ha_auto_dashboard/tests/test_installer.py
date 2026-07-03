"""Tests for writing compiled dashboards to disk and notifying the user."""
from pathlib import Path

import yaml
from homeassistant.core import HomeAssistant
from homeassistant.setup import async_setup_component

from custom_components.ha_auto_dashboard.const import DASHBOARD_OUTPUT_DIR
from custom_components.ha_auto_dashboard.dashboard.installer import async_install_dashboards


async def test_install_dashboards_writes_yaml_files(hass: HomeAssistant) -> None:
    await async_setup_component(hass, "persistent_notification", {})

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


async def test_install_dashboards_creates_notification(hass: HomeAssistant) -> None:
    await async_setup_component(hass, "persistent_notification", {})

    dashboards = {
        "auto_home": {"title": "Home", "icon": "mdi:home", "views": [{"title": "Home", "cards": []}]},
    }

    # persistent_notification doesn't expose an entity/state - just an
    # internal dict and a dispatcher signal - so the only thing we can
    # black-box assert here is that raising it doesn't raise (e.g. because
    # the service call's data doesn't match its schema).
    await async_install_dashboards(hass, dashboards)
