"""Detects which optional HACS frontend resources are actually installed.

Mushroom, Bubble Card and mini-graph-card are Lovelace *resources*, not
part of Home Assistant core - if a dashboard references one that isn't
registered, that card renders as "custom element doesn't exist" instead
of the entity it was meant to show. Rather than assume they're always
present, the compiler checks the Lovelace resources collection first and
falls back to native HA cards for anything missing.
"""
from __future__ import annotations

from dataclasses import dataclass

from homeassistant.core import HomeAssistant

MUSHROOM_MARKER = "mushroom"
BUBBLE_CARD_MARKER = "bubble-card"
MINI_GRAPH_CARD_MARKER = "mini-graph-card"


@dataclass(slots=True)
class FrontendResources:
    """Which optional frontend resources are registered as Lovelace resources."""

    mushroom: bool
    bubble_card: bool
    mini_graph_card: bool

    @property
    def missing(self) -> list[str]:
        missing = []
        if not self.mushroom:
            missing.append("Mushroom")
        if not self.bubble_card:
            missing.append("Bubble Card")
        if not self.mini_graph_card:
            missing.append("mini-graph-card")
        return missing

    @property
    def all_present(self) -> bool:
        return not self.missing


ALL_PRESENT = FrontendResources(mushroom=True, bubble_card=True, mini_graph_card=True)


async def async_detect_frontend_resources(hass: HomeAssistant) -> FrontendResources:
    """Best-effort detection via the Lovelace storage resources collection.

    If the resources collection isn't reachable (e.g. Lovelace hasn't
    finished loading yet, resources are managed purely via YAML, or the
    internal structure has changed), this assumes everything is
    installed rather than silently downgrading a correctly configured
    setup.
    """
    urls: list[str] = []
    lovelace_data = hass.data.get("lovelace")
    if isinstance(lovelace_data, dict):
        resources = lovelace_data.get("resources")
        if resources is not None and hasattr(resources, "async_items"):
            urls = [item.get("url", "") for item in resources.async_items()]

    if not urls:
        return ALL_PRESENT

    joined = " ".join(urls).lower()
    return FrontendResources(
        mushroom=MUSHROOM_MARKER in joined,
        bubble_card=BUBBLE_CARD_MARKER in joined,
        mini_graph_card=MINI_GRAPH_CARD_MARKER in joined,
    )
