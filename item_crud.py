"""Item CRUD operations. Pure logic — no pygame."""

from __future__ import annotations

import json
import os
from typing import Any, Dict, Optional

from editor.element_crud import generate_new_id
from editor.items_data import (
    get_all_items, get_item, set_item, delete_item, create_item,
    rename_item, item_exists,
)


def create_new_item() -> str:
    """Create a new item with auto-incremented ID. Returns the new ID."""
    iid = generate_new_id("item_nuevo", get_all_items())
    create_item(iid)
    return iid


def clone_item(source_id: str) -> Optional[str]:
    """Clone an existing item. Returns the new ID or None."""
    data = get_item(source_id)
    if not data:
        return None
    iid = generate_new_id(source_id + "_copia", get_all_items())
    set_item(iid, data)
    return iid


def delete_item_by_id(item_id: str) -> None:
    """Delete an item by ID."""
    delete_item(item_id)


def rename_item_with_refs(old_id: str, new_id: str, project) -> int:
    """Rename item and update cross-references in elementos.json and stacks.

    Returns count of updated files.
    """
    if item_exists(new_id):
        return 0
    if not rename_item(old_id, new_id):
        return 0

    updated = 0
    if project:
        updated += _update_elementos_refs(old_id, new_id, project)
        updated += _update_stack_refs(old_id, new_id, project)
        updated += _update_dialogos_refs(old_id, new_id, project)

    return updated


def _walk_replace(obj, old_id: str, new_id: str) -> bool:
    """Recursively replace references to old_id in a JSON-like structure.

    Updates any value stored under a key named "item" or "item_id" that equals
    old_id. Covers actions, conditions, dialog choices and drop tables.
    """
    changed = False
    if isinstance(obj, dict):
        for key in list(obj.keys()):
            if key in ("item", "item_id") and obj[key] == old_id:
                obj[key] = new_id
                changed = True
            elif isinstance(obj[key], (dict, list)):
                if _walk_replace(obj[key], old_id, new_id):
                    changed = True
    elif isinstance(obj, list):
        for i, item in enumerate(obj):
            if isinstance(item, (dict, list)):
                if _walk_replace(item, old_id, new_id):
                    changed = True
    return changed


def _update_elementos_refs(old_id: str, new_id: str, project) -> int:
    el_path = project.data_path("elementos.json")
    if not os.path.exists(el_path):
        return 0
    try:
        with open(el_path, "r", encoding="utf-8") as f:
            el_data = json.load(f)
        changed = _walk_replace(el_data, old_id, new_id)
        if changed:
            with open(el_path, "w", encoding="utf-8") as f:
                json.dump(el_data, f, indent=2, ensure_ascii=False)
            return 1
    except Exception:
        pass
    return 0


def _update_stack_refs(old_id: str, new_id: str, project) -> int:
    stacks_dir = project.stacks_path()
    if not os.path.isdir(stacks_dir):
        return 0
    updated = 0
    for fname in os.listdir(stacks_dir):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(stacks_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            changed = _walk_replace(data, old_id, new_id)
            if changed:
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                updated += 1
        except Exception:
            pass
    return updated


def _update_dialogos_refs(old_id: str, new_id: str, project) -> int:
    """Update item refs inside data/dialogos.json (choices/params of actions)."""
    d_path = project.data_path("dialogos.json")
    if not os.path.exists(d_path):
        return 0
    try:
        with open(d_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        changed = _walk_replace(data, old_id, new_id)
        if changed:
            with open(d_path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            return 1
    except Exception:
        pass
    return 0
