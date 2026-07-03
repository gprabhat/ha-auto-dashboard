"""Guesses a friendlier icon for an area when it has none set."""
from __future__ import annotations

# Order matters: first keyword match wins, so put more specific terms
# (e.g. "living") before generic ones.
_AREA_ICON_KEYWORDS: tuple[tuple[str, str], ...] = (
    ("kitchen", "mdi:chef-hat"),
    ("living", "mdi:sofa"),
    ("bedroom", "mdi:bed"),
    ("bathroom", "mdi:shower"),
    ("laundry", "mdi:washing-machine"),
    ("garage", "mdi:garage"),
    ("office", "mdi:desk"),
    ("dining", "mdi:silverware-fork-knife"),
    ("garden", "mdi:flower"),
    ("yard", "mdi:flower"),
    ("hall", "mdi:door"),
    ("media", "mdi:television"),
    ("cloud", "mdi:cloud"),
    ("server", "mdi:server"),
    ("nursery", "mdi:baby-face-outline"),
    ("gym", "mdi:dumbbell"),
    ("basement", "mdi:stairs"),
    ("attic", "mdi:home-roof"),
)

_DEFAULT_AREA_ICON = "mdi:home-outline"


def guess_area_icon(area_name: str) -> str:
    """Return a keyword-matched icon for an area name, or a sensible default."""
    lowered = area_name.lower()
    for keyword, icon in _AREA_ICON_KEYWORDS:
        if keyword in lowered:
            return icon
    return _DEFAULT_AREA_ICON
