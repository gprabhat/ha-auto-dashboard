"""Compiles the discovery graph into named Lovelace dashboard configs."""
from __future__ import annotations

from typing import Final

from ..models import RegistryGraph
from . import dashboard_factory as factory
from .card_builder import CardTheme
from .resources import FrontendResources

DASHBOARD_HOME: Final = "auto_home"
DASHBOARD_ROOMS: Final = "auto_rooms"
DASHBOARD_HOMELAB: Final = "auto_homelab"
DASHBOARD_SECURITY: Final = "auto_security"
DASHBOARD_MONITORING: Final = "auto_monitoring"
DASHBOARD_ADMIN: Final = "auto_admin"
DASHBOARD_CLOUD: Final = "auto_cloud"


def compile_dashboards(graph: RegistryGraph, resources: FrontendResources | None = None) -> dict[str, dict]:
    """Return ``{slug: {"title", "icon", "views": [...]}}`` for every dashboard.

    `resources` controls which optional HACS frontend cards (Mushroom,
    Bubble Card, mini-graph-card) get used; anything not detected as
    installed falls back to a native HA card instead. Defaults to
    assuming everything is installed when not given (e.g. in tests).

    The Cloud dashboard is only included when the graph has a cloud-related
    area; the rest are always produced (with a placeholder card when empty)
    so the installer always has a stable, predictable set of files to write.
    """
    theme = CardTheme(resources)

    dashboards: dict[str, dict] = {
        DASHBOARD_HOME: {
            "title": "Home",
            "icon": "mdi:home",
            "views": [factory.build_home_view(graph, theme)],
        },
        DASHBOARD_ROOMS: {
            "title": "Rooms",
            "icon": "mdi:floor-plan",
            "views": factory.build_rooms_views(graph, theme),
        },
        DASHBOARD_HOMELAB: {
            "title": "Homelab",
            "icon": "mdi:server",
            "views": [factory.build_homelab_view(graph, theme)],
        },
        DASHBOARD_SECURITY: {
            "title": "Security",
            "icon": "mdi:shield-home",
            "views": [factory.build_security_view(graph, theme)],
        },
        DASHBOARD_MONITORING: {
            "title": "Monitoring",
            "icon": "mdi:chart-line",
            "views": [factory.build_monitoring_view(graph, theme)],
        },
        DASHBOARD_ADMIN: {
            "title": "Admin",
            "icon": "mdi:cog",
            "views": [factory.build_admin_view(graph, theme)],
        },
    }

    if cloud_view := factory.build_cloud_view(graph, theme):
        dashboards[DASHBOARD_CLOUD] = {
            "title": "Cloud",
            "icon": "mdi:cloud",
            "views": [cloud_view],
        }

    return dashboards
