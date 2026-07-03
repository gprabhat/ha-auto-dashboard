"""Constants for the HA Auto Dashboard integration."""
from __future__ import annotations

from typing import Final

DOMAIN: Final = "ha_auto_dashboard"

# Config entry / options keys
CONF_SCAN_ON_STARTUP: Final = "scan_on_startup"
DEFAULT_SCAN_ON_STARTUP: Final = True

# hass.data keys
DATA_COORDINATOR: Final = "coordinator"

# Services
SERVICE_SCAN: Final = "scan"
SERVICE_GENERATE: Final = "generate"

# Where compiled dashboard YAML files are written, relative to the HA config dir.
DASHBOARD_OUTPUT_DIR: Final = "dashboards"

# Signal fired after a scan completes, carries the graph statistics.
SIGNAL_GRAPH_UPDATED: Final = f"{DOMAIN}_graph_updated"

# Entity/device/area categories produced by the classifier.
CATEGORY_HOMELAB: Final = "homelab"
CATEGORY_SECURITY: Final = "security"
CATEGORY_NETWORK: Final = "network"
CATEGORY_UPDATES: Final = "updates"
CATEGORY_ROOM: Final = "room"
CATEGORY_OTHER: Final = "other"

# Keyword lists used by the classifier to bucket entities/devices that are
# not tied to a specific area (homelab, security, network, updates, ...).
HOMELAB_KEYWORDS: Final[tuple[str, ...]] = (
    "homelab",
    "pve",
    "proxmox",
    "docker",
    "vaultwarden",
    "backup",
    "homeassistant",
)

SECURITY_KEYWORDS: Final[tuple[str, ...]] = (
    "camera",
    "alarm",
    "motion",
    "ezviz",
)

NETWORK_KEYWORDS: Final[tuple[str, ...]] = (
    "wan",
    "external_ip",
    "download",
    "upload",
    "speed",
)

UPDATE_DOMAIN: Final = "update"
