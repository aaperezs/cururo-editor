"""Custom behavior CRUD operations. Pure logic — no pygame."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

from editor.behaviors import (
    get_behaviors, get_behavior, set_behavior, delete_behavior,
    get_behavior_list,
)


def create_new_behavior() -> str:
    """Create a new custom behavior with defaults. Returns the new ID."""
    base = "custom_behavior"
    bid = base
    n = 1
    all_ids = [b[0] for b in get_behavior_list()]
    while bid in all_ids:
        bid = f"{base}_{n}"
        n += 1
    data = {
        "id": bid,
        "label": bid,
        "group": "custom",
        "class_path": "",
        "target_list": "elementos",
        "properties": {},
    }
    set_behavior(bid, data)
    return bid


def save_behavior(bid: str, data: Dict[str, Any], old_id: Optional[str] = None) -> bool:
    """Save behavior data. Handles inline ID rename (delete+recreate).

    Returns True on success.
    """
    if old_id and old_id != bid:
        delete_behavior(old_id)
    set_behavior(bid, data)
    return True


def delete_behavior_by_id(bid: str) -> None:
    """Delete a behavior by ID."""
    delete_behavior(bid)


def add_property_to_behavior(bid: str) -> bool:
    """Add a new empty property to a behavior. Returns True on success."""
    beh = get_behavior(bid)
    if not beh:
        return False
    props = beh.setdefault("properties", {})
    n = len(props) + 1
    key = f"prop_{n}"
    while key in props:
        key = f"prop_{n}"
        n += 1
    props[key] = {"type": "bool", "label": key, "default": False}
    set_behavior(bid, beh)
    return True


def remove_property_from_behavior(bid: str, prop_key: str) -> bool:
    """Remove a property from a behavior. Returns True on success."""
    beh = get_behavior(bid)
    if not beh:
        return False
    props = beh.get("properties", {})
    if prop_key in props:
        del props[prop_key]
        set_behavior(bid, beh)
        return True
    return False
