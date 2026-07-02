"""Discovery engine: turns HA registries into a RegistryGraph."""
from __future__ import annotations

from .graph_builder import async_build_graph

__all__ = ["async_build_graph"]
