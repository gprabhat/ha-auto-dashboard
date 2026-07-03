"""Writes compiled dashboards to disk and prompts the user to register them.

Home Assistant does not expose a stable, public API for a custom integration
to register a YAML-mode Lovelace dashboard at runtime (that's normally done
via a `lovelace:` block in configuration.yaml, parsed at core startup). So
this stops one step short of fully automatic installation: it writes ready
to use YAML files under `<config>/dashboards/` and raises a persistent
notification with the exact snippet needed to register them, once, in
configuration.yaml. Every subsequent regeneration just rewrites the same
files in place - no further manual steps are needed after that.
"""
from __future__ import annotations

import logging
from pathlib import Path

import yaml
from homeassistant.core import HomeAssistant

from ..const import DASHBOARD_OUTPUT_DIR, DOMAIN

_LOGGER = logging.getLogger(__name__)

_NOTIFICATION_ID = f"{DOMAIN}_install_dashboards"


def _write_dashboard_files(config_dir: str, dashboards: dict[str, dict]) -> list[str]:
    output_dir = Path(config_dir) / DASHBOARD_OUTPUT_DIR
    output_dir.mkdir(parents=True, exist_ok=True)

    written: list[str] = []
    for slug, dashboard in dashboards.items():
        path = output_dir / f"{slug}.yaml"
        path.write_text(
            yaml.safe_dump({"views": dashboard["views"]}, sort_keys=False, allow_unicode=True),
            encoding="utf-8",
        )
        written.append(str(path))
    return written


def _configuration_snippet(dashboards: dict[str, dict]) -> str:
    lines = ["lovelace:", "  dashboards:"]
    for slug, dashboard in dashboards.items():
        url_path = slug.replace("_", "-")
        lines.append(f"    {url_path}:")
        lines.append("      mode: yaml")
        lines.append(f"      title: {dashboard['title']}")
        lines.append(f"      icon: {dashboard['icon']}")
        lines.append(f"      filename: {DASHBOARD_OUTPUT_DIR}/{slug}.yaml")
    return "\n".join(lines)


async def async_install_dashboards(hass: HomeAssistant, dashboards: dict[str, dict]) -> list[str]:
    """Write compiled dashboards to disk and notify the registration snippet."""
    written = await hass.async_add_executor_job(
        _write_dashboard_files, hass.config.config_dir, dashboards
    )
    _LOGGER.info("HA Auto Dashboard wrote %d dashboard file(s): %s", len(written), written)

    snippet = _configuration_snippet(dashboards)
    await hass.services.async_call(
        "persistent_notification",
        "create",
        {
            "notification_id": _NOTIFICATION_ID,
            "title": "HA Auto Dashboard: dashboards ready",
            "message": (
                f"Generated {len(written)} dashboard(s) in `dashboards/`. "
                "Add this to `configuration.yaml` and restart Home Assistant "
                "to register them (one-time step - future scans just "
                "rewrite the same files):\n\n"
                f"```yaml\n{snippet}\n```"
            ),
        },
        blocking=True,
    )

    return written
