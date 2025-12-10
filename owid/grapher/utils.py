# -*- coding: utf-8 -*-
#
#  utils.py
#  owid-grapher-py
#

from dataclasses import asdict
from typing import Any, Dict, TypeVar

T = TypeVar("T")


def _prune_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Remove empty values from a dictionary recursively."""
    out: Dict[str, Any] = {}
    for k, v in d.items():
        if v not in (None, [], {}):
            if isinstance(v, dict):
                out[k] = _prune_dict(v)
            elif isinstance(v, list):
                out[k] = [
                    _prune_dict(x) if isinstance(x, dict) else x
                    for x in v
                    if x not in (None, [], {})
                ]
            else:
                out[k] = v
    return out


def _snake_to_camel(name: str) -> str:
    """Convert snake_case to camelCase."""
    components = name.split("_")
    return components[0] + "".join(x.title() for x in components[1:])


def _to_camel_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    """Convert all keys in a dict from snake_case to camelCase recursively."""
    out: Dict[str, Any] = {}
    for k, v in d.items():
        camel_key = _snake_to_camel(k)
        if isinstance(v, dict):
            out[camel_key] = _to_camel_dict(v)
        elif isinstance(v, list):
            out[camel_key] = [
                _to_camel_dict(x) if isinstance(x, dict) else x for x in v
            ]
        else:
            out[camel_key] = v
    return out


def pruned_camel_json(cls: T) -> T:
    """Decorator that adds a to_dict method with camelCase keys and pruned empty values."""

    def to_dict(self: Any) -> Dict[str, Any]:
        return _prune_dict(_to_camel_dict(asdict(self)))

    cls.to_dict = to_dict  # type: ignore
    return cls
