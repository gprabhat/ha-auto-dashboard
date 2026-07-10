"""Persisted user customizations (Dashboard Studio) layered onto the
compiled dashboards right before they're written.

Cards have no identifier of their own - `compiler.py`/`dashboard_factory.py`
rebuild every view from scratch on every compile - so overrides are keyed
by a deterministic id derived from card *content* (the entity_id, or a
type-based discriminator for the handful of non-entity structural cards),
never from position. That's what lets a saved override survive the next
scan even though the graph (and therefore card order) may have shifted.

The only nesting this needs to handle is the single level `dashboard_factory.py`
ever produces: a top-level `grid` card wrapping a list of leaf entity/area
cards (used to group entities into titled sections). No view builder nests
a grid inside another grid.
"""
from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

from ..const import DOMAIN
from ..models import RegistryGraph
from .card_builder import CardTheme
from .resources import FrontendResources

_STORE_VERSION = 1


class OverridesStore:
    """Thin wrapper around a per-config-entry `Store` for the override doc."""

    def __init__(self, hass: HomeAssistant, entry_id: str) -> None:
        self._store: Store = Store(hass, _STORE_VERSION, f"{DOMAIN}_studio_overrides_{entry_id}")

    async def async_load(self) -> dict[str, Any]:
        data = await self._store.async_load()
        return data or {"cards": {}, "added_cards": []}

    async def async_save(self, data: dict[str, Any]) -> None:
        await self._store.async_save(data)


def card_id(dashboard_slug: str, view_path: str, card: dict) -> str:
    """A deterministic id for a card, derived from content rather than
    position so a saved override still applies to "the same" card after
    regeneration even when unrelated parts of the graph changed."""
    if entity_id := card.get("entity"):
        return f"{dashboard_slug}:{view_path}:entity:{entity_id}"

    card_type = card.get("type", "unknown")
    if card_type == "area":
        return f"{dashboard_slug}:{view_path}:area:{card.get('area')}"
    if card_type == "picture-glance":
        return f"{dashboard_slug}:{view_path}:picture-glance:{card.get('camera_image')}"
    if card_type == "grid":
        # Every `grid` call in dashboard_factory.py passes a `title`
        # ("Lights", "Switches & Locks", a device name, an area name, ...)
        # and a view routinely has several grids - without this, all of
        # them would collapse onto the same `type`-only id below.
        return f"{dashboard_slug}:{view_path}:grid:{card.get('title') or 'untitled'}"
    # Singleton-per-view structural cards (map/logbook/history-graph/
    # markdown/heading/chips/title/grid-section): at most one of each type
    # exists in any given view today, so the type alone is stable enough.
    return f"{dashboard_slug}:{view_path}:{card_type}"


def _iter_containers(view: dict) -> list[list[dict]]:
    """Every card list that can directly hold a reorderable/hideable leaf
    card: the view's own top-level `cards`, plus the `cards` list of any
    top-level `grid` card."""
    containers = [view["cards"]]
    for card in view["cards"]:
        if card.get("type") == "grid":
            containers.append(card["cards"])
    return containers


def _apply_card_overrides(dashboard_slug: str, view: dict, card_overrides: dict[str, dict]) -> None:
    """Mutates `view` in place: drops hidden cards, applies name/icon
    overrides, and re-sorts each container by its cards' `order` override.

    Cards without an explicit `order` keep their generated position
    (`order` defaults to the card's original index) - the Studio UI is
    expected to assign `order` to every card in a container it reorders,
    not just the one that moved, which keeps this a simple stable sort
    rather than needing to interleave sparse explicit orders with
    unordered ones.
    """
    for container in _iter_containers(view):
        indexed: list[tuple[int, dict]] = []
        for index, card in enumerate(container):
            cid = card_id(dashboard_slug, view["path"], card)
            override = card_overrides.get(cid)
            if override and override.get("hidden"):
                continue
            if override:
                if override.get("name"):
                    card["name"] = override["name"]
                if override.get("icon"):
                    card["icon"] = override["icon"]
            order = override.get("order") if override else None
            indexed.append((order if order is not None else index, card))
        indexed.sort(key=lambda pair: pair[0])
        container[:] = [card for _, card in indexed]

    # A grid section whose entities were all hidden has nothing left to show.
    view["cards"] = [card for card in view["cards"] if card.get("type") != "grid" or card["cards"]]


def _apply_added_cards(
    added_cards: list[dict], dashboards: dict[str, dict], graph: RegistryGraph, theme: CardTheme
) -> None:
    for added in added_cards:
        dashboard = dashboards.get(added.get("dashboard"))
        if dashboard is None:
            continue
        view = next((v for v in dashboard["views"] if v["path"] == added.get("view")), None)
        if view is None:
            continue
        entity = graph.entities.get(added.get("entity_id"))
        if entity is None:
            continue

        wanted_id = card_id(added["dashboard"], view["path"], {"entity": entity.entity_id})
        already_present = any(
            card_id(added["dashboard"], view["path"], card) == wanted_id
            for container in _iter_containers(view)
            for card in container
        )
        if already_present:
            continue

        view["cards"].append(theme.entity(entity))


def studio_payload(dashboards: dict[str, dict]) -> dict[str, dict]:
    """A copy of `dashboards` with each card's stable id injected as
    `_studio_id`, for the Dashboard Studio panel to address cards by.

    Never write this to disk - build it from a `dashboards` value that
    isn't also being passed to the installer, so `_studio_id` never leaks
    into the actual Lovelace YAML.
    """
    payload: dict[str, dict] = {}
    for slug, dashboard in dashboards.items():
        views = []
        for view in dashboard["views"]:
            cards = []
            for card in view["cards"]:
                card_copy = dict(card)
                card_copy["_studio_id"] = card_id(slug, view["path"], card)
                if card.get("type") == "grid":
                    card_copy["cards"] = [
                        {**inner, "_studio_id": card_id(slug, view["path"], inner)}
                        for inner in card["cards"]
                    ]
                cards.append(card_copy)
            views.append({**view, "cards": cards})
        payload[slug] = {**dashboard, "views": views}
    return payload


def apply_overrides(
    overrides: dict[str, Any],
    dashboards: dict[str, dict],
    *,
    graph: RegistryGraph,
    resources: FrontendResources | None = None,
) -> dict[str, dict]:
    """Layer a saved Dashboard Studio override doc onto freshly compiled
    dashboards: splice in any added entities first (so they're subject to
    the same hide/rename/reorder pass as generated cards), then apply
    per-card hide/rename/reorder. Mutates and returns `dashboards`."""
    theme = CardTheme(resources)
    _apply_added_cards(overrides.get("added_cards", []), dashboards, graph, theme)

    card_overrides = overrides.get("cards", {})
    for dashboard_slug, dashboard in dashboards.items():
        for view in dashboard["views"]:
            _apply_card_overrides(dashboard_slug, view, card_overrides)

    return dashboards
