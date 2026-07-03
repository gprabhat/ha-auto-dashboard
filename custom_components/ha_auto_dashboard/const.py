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

# Domains rendered with a Mushroom-specific card; anything else falls back to
# the generic custom:mushroom-entity-card. Requires the "Mushroom" HACS
# frontend package to be installed as a Lovelace resource.
MUSHROOM_DOMAIN_CARDS: Final[dict[str, str]] = {
    "light": "custom:mushroom-light-card",
    "climate": "custom:mushroom-climate-card",
    "cover": "custom:mushroom-cover-card",
    "fan": "custom:mushroom-fan-card",
    "lock": "custom:mushroom-lock-card",
    "media_player": "custom:mushroom-media-player-card",
    "vacuum": "custom:mushroom-vacuum-card",
    "alarm_control_panel": "custom:mushroom-alarm-control-panel-card",
    "person": "custom:mushroom-person-card",
    "update": "custom:mushroom-update-card",
    "humidifier": "custom:mushroom-humidifier-card",
    "water_heater": "custom:mushroom-water-heater-card",
    "number": "custom:mushroom-number-card",
    "select": "custom:mushroom-select-card",
}
MUSHROOM_GENERIC_CARD: Final = "custom:mushroom-entity-card"

# Domains that natively carry a live location and belong on a map card.
LOCATION_DOMAINS: Final[tuple[str, ...]] = ("person", "device_tracker")
