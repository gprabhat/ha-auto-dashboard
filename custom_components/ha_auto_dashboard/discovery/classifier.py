"""Buckets entities and devices into dashboard categories.

Classification is keyword/domain based rather than ML based: it is cheap,
deterministic, and easy for a user to reason about ("why did this end up in
Homelab?"). Precedence (highest first):

1. ``update`` domain entities always go to Updates.
2. Homelab / Security / Network keyword matches on the entity_id or name.
3. Entities tied to an area become Room entities.
4. Everything else falls back to Other.
"""
from __future__ import annotations

from collections import Counter

from ..const import (
    CATEGORY_HOMELAB,
    CATEGORY_NETWORK,
    CATEGORY_OTHER,
    CATEGORY_ROOM,
    CATEGORY_SECURITY,
    CATEGORY_UPDATES,
    HOMELAB_KEYWORDS,
    NETWORK_KEYWORDS,
    SECURITY_KEYWORDS,
    UPDATE_DOMAIN,
)
from ..models import DeviceNode, EntityNode

_KEYWORD_CATEGORIES: tuple[tuple[str, tuple[str, ...]], ...] = (
    (CATEGORY_HOMELAB, HOMELAB_KEYWORDS),
    (CATEGORY_SECURITY, SECURITY_KEYWORDS),
    (CATEGORY_NETWORK, NETWORK_KEYWORDS),
)


def _matches_keywords(haystack: str, keywords: tuple[str, ...]) -> bool:
    return any(keyword in haystack for keyword in keywords)


def classify_entity(entity: EntityNode) -> str:
    """Return the category for a single entity."""
    if entity.domain == UPDATE_DOMAIN:
        return CATEGORY_UPDATES

    haystack = f"{entity.entity_id} {entity.name}".lower()
    for category, keywords in _KEYWORD_CATEGORIES:
        if _matches_keywords(haystack, keywords):
            return category

    if entity.area_id:
        return CATEGORY_ROOM

    return CATEGORY_OTHER


def classify_device(device: DeviceNode, entities: list[EntityNode]) -> str:
    """Return the category for a device, derived from its own name and its
    entities' categories (majority vote, falling back to keyword match on
    the device name itself).
    """
    haystack = device.name.lower()
    for category, keywords in _KEYWORD_CATEGORIES:
        if _matches_keywords(haystack, keywords):
            return category

    if entities:
        counts = Counter(classify_entity(entity) for entity in entities)
        # Ignore "other" when a more specific category is available.
        ranked = [cat for cat, _ in counts.most_common() if cat != CATEGORY_OTHER]
        if ranked:
            return ranked[0]

    if device.area_id:
        return CATEGORY_ROOM

    return CATEGORY_OTHER
