"""Tests for detecting installed HACS frontend resources."""
from homeassistant.core import HomeAssistant

from custom_components.ha_auto_dashboard.dashboard.resources import async_detect_frontend_resources


class _FakeResources:
    def __init__(self, urls: list[str]) -> None:
        self._urls = urls

    def async_items(self) -> list[dict]:
        return [{"url": url} for url in self._urls]


async def test_detect_assumes_installed_when_resources_collection_unavailable(hass: HomeAssistant) -> None:
    resources = await async_detect_frontend_resources(hass)
    assert resources.mushroom is True
    assert resources.bubble_card is True
    assert resources.mini_graph_card is True
    assert resources.missing == []


async def test_detect_flags_missing_resources(hass: HomeAssistant) -> None:
    hass.data["lovelace"] = {
        "resources": _FakeResources(
            [
                "/hacsfiles/lovelace-mushroom/mushroom.js",
                # Bubble Card and mini-graph-card intentionally absent.
            ]
        )
    }

    resources = await async_detect_frontend_resources(hass)

    assert resources.mushroom is True
    assert resources.bubble_card is False
    assert resources.mini_graph_card is False
    assert resources.missing == ["Bubble Card", "mini-graph-card"]
    assert resources.all_present is False


async def test_detect_all_present(hass: HomeAssistant) -> None:
    hass.data["lovelace"] = {
        "resources": _FakeResources(
            [
                "/hacsfiles/lovelace-mushroom/mushroom.js",
                "/hacsfiles/bubble-card/bubble-card.js",
                "/hacsfiles/mini-graph-card/mini-graph-card-bundle.js",
            ]
        )
    }

    resources = await async_detect_frontend_resources(hass)
    assert resources.all_present is True
