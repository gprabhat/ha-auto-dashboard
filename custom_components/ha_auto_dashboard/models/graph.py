"""Plain data containers describing the discovered HA registry graph.

These are intentionally decoupled from Home Assistant's own registry entry
types so that the dashboard compiler (a later phase) can consume a stable,
serializable model regardless of HA-core internal changes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(slots=True)
class AreaNode:
    """A single area (room) and the devices/entities that live in it."""

    area_id: str
    name: str
    icon: str | None = None
    device_ids: list[str] = field(default_factory=list)
    entity_ids: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "area_id": self.area_id,
            "name": self.name,
            "icon": self.icon,
            "device_ids": list(self.device_ids),
            "entity_ids": list(self.entity_ids),
        }


@dataclass(slots=True)
class DeviceNode:
    """A single device and the entities it exposes."""

    device_id: str
    name: str
    area_id: str | None = None
    manufacturer: str | None = None
    model: str | None = None
    sw_version: str | None = None
    via_device_id: str | None = None
    disabled: bool = False
    entity_ids: list[str] = field(default_factory=list)
    category: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return {
            "device_id": self.device_id,
            "name": self.name,
            "area_id": self.area_id,
            "manufacturer": self.manufacturer,
            "model": self.model,
            "sw_version": self.sw_version,
            "via_device_id": self.via_device_id,
            "disabled": self.disabled,
            "entity_ids": list(self.entity_ids),
            "category": self.category,
        }


@dataclass(slots=True)
class EntityNode:
    """A single entity, enriched with the classifier's category."""

    entity_id: str
    name: str
    domain: str
    device_id: str | None = None
    area_id: str | None = None
    device_class: str | None = None
    platform: str | None = None
    disabled: bool = False
    hidden: bool = False
    category: str = "other"

    def to_dict(self) -> dict[str, Any]:
        return {
            "entity_id": self.entity_id,
            "name": self.name,
            "domain": self.domain,
            "device_id": self.device_id,
            "area_id": self.area_id,
            "device_class": self.device_class,
            "platform": self.platform,
            "disabled": self.disabled,
            "hidden": self.hidden,
            "category": self.category,
        }


@dataclass(slots=True)
class RegistryGraph:
    """The full discovered graph: areas, devices, entities and category index."""

    areas: dict[str, AreaNode] = field(default_factory=dict)
    devices: dict[str, DeviceNode] = field(default_factory=dict)
    entities: dict[str, EntityNode] = field(default_factory=dict)
    categories: dict[str, list[str]] = field(default_factory=dict)

    def stats(self) -> dict[str, int]:
        return {
            "areas": len(self.areas),
            "devices": len(self.devices),
            "entities": len(self.entities),
            **{f"category_{name}": len(ids) for name, ids in self.categories.items()},
        }

    def to_dict(self) -> dict[str, Any]:
        return {
            "areas": {k: v.to_dict() for k, v in self.areas.items()},
            "devices": {k: v.to_dict() for k, v in self.devices.items()},
            "entities": {k: v.to_dict() for k, v in self.entities.items()},
            "categories": {k: list(v) for k, v in self.categories.items()},
            "stats": self.stats(),
        }
