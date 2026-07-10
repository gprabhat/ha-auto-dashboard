"""Integration tests for the discovery graph builder against a real hass registry."""
from homeassistant.core import HomeAssistant
from homeassistant.helpers import area_registry as ar
from homeassistant.helpers import device_registry as dr
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.ha_auto_dashboard.const import CATEGORY_HOMELAB, CATEGORY_ROOM
from custom_components.ha_auto_dashboard.discovery.graph_builder import async_build_graph


async def test_build_graph_links_area_device_entity(hass: HomeAssistant) -> None:
    area_registry = ar.async_get(hass)
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    kitchen = area_registry.async_create("Kitchen")

    config_entry = MockConfigEntry(domain="mock")
    config_entry.add_to_hass(hass)

    device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={("mock", "light-hub-1")},
        name="Kitchen Light Hub",
    )
    device_registry.async_update_device(device.id, area_id=kitchen.id)

    entity_entry = entity_registry.async_get_or_create(
        domain="light",
        platform="mock",
        unique_id="kitchen-ceiling",
        device_id=device.id,
        original_name="Kitchen Ceiling Light",
    )

    graph = await async_build_graph(hass)

    assert kitchen.id in graph.areas
    assert device.id in graph.devices
    assert entity_entry.entity_id in graph.entities

    entity_node = graph.entities[entity_entry.entity_id]
    assert entity_node.area_id == kitchen.id
    assert entity_node.category == CATEGORY_ROOM

    device_node = graph.devices[device.id]
    assert entity_entry.entity_id in device_node.entity_ids
    assert device_node.category == CATEGORY_ROOM

    area_node = graph.areas[kitchen.id]
    assert device.id in area_node.device_ids
    assert entity_entry.entity_id in area_node.entity_ids


async def test_build_graph_excludes_area_and_cascades_to_its_devices_and_entities(
    hass: HomeAssistant,
) -> None:
    area_registry = ar.async_get(hass)
    device_registry = dr.async_get(hass)
    entity_registry = er.async_get(hass)

    kitchen = area_registry.async_create("Kitchen")
    bedroom = area_registry.async_create("Bedroom")

    config_entry = MockConfigEntry(domain="mock")
    config_entry.add_to_hass(hass)

    kitchen_device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={("mock", "kitchen-hub")},
        name="Kitchen Hub",
    )
    device_registry.async_update_device(kitchen_device.id, area_id=kitchen.id)
    kitchen_entity = entity_registry.async_get_or_create(
        domain="light",
        platform="mock",
        unique_id="kitchen-ceiling",
        device_id=kitchen_device.id,
        original_name="Kitchen Ceiling Light",
    )

    bedroom_device = device_registry.async_get_or_create(
        config_entry_id=config_entry.entry_id,
        identifiers={("mock", "bedroom-hub")},
        name="Bedroom Hub",
    )
    device_registry.async_update_device(bedroom_device.id, area_id=bedroom.id)
    bedroom_entity = entity_registry.async_get_or_create(
        domain="light",
        platform="mock",
        unique_id="bedroom-ceiling",
        device_id=bedroom_device.id,
        original_name="Bedroom Ceiling Light",
    )

    graph = await async_build_graph(hass, excluded_areas={kitchen.id})

    assert kitchen.id not in graph.areas
    assert kitchen_device.id not in graph.devices
    assert kitchen_entity.entity_id not in graph.entities

    assert bedroom.id in graph.areas
    assert bedroom_device.id in graph.devices
    assert bedroom_entity.entity_id in graph.entities


async def test_build_graph_excludes_specific_entity(hass: HomeAssistant) -> None:
    entity_registry = er.async_get(hass)
    kept = entity_registry.async_get_or_create(
        domain="sensor", platform="mock", unique_id="keep-me"
    )
    excluded = entity_registry.async_get_or_create(
        domain="sensor", platform="mock", unique_id="exclude-me"
    )

    graph = await async_build_graph(hass, excluded_entities={excluded.entity_id})

    assert kept.entity_id in graph.entities
    assert excluded.entity_id not in graph.entities


async def test_build_graph_classifies_homelab_entity(hass: HomeAssistant) -> None:
    entity_registry = er.async_get(hass)
    entity_entry = entity_registry.async_get_or_create(
        domain="sensor",
        platform="mock",
        unique_id="pve2-cpu",
        suggested_object_id="pve2_cpu_usage",
    )

    graph = await async_build_graph(hass)

    assert graph.entities[entity_entry.entity_id].category == CATEGORY_HOMELAB
    assert entity_entry.entity_id in graph.categories[CATEGORY_HOMELAB]
