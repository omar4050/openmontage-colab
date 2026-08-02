"""Adapter package for real model integrations.

Adapters are optional: each tries to import the underlying model/library at runtime and exposes
an `available` attribute and a `run(...)` method compatible with the abstractions.
"""
from .adapter_loader import get_component

__all__ = ["get_component"]
