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

    Returns count of updated stack files.
    """
    if item_exists(new_id):
        return 0
    if not rename_item(old_id, new_id):
        return 0

    updated_stacks = 0
    if project:
        _update_elementos_refs(old_id, new_id, project)
        updated_stacks = _update_stack_refs(old_id, new_id, project)

    return updated_stacks


def _update_elementos_refs(old_id: str, new_id: str, project) -> None:
    el_path = project.data_path("elementos.json")
    if not os.path.exists(el_path):
        return
    try:
        with open(el_path, "r", encoding="utf-8") as f:
            el_data = json.load(f)
        changed = False
        for eid, eobj in el_data.items():
            for pk, pv in eobj.get("properties", {}).items():
                if isinstance(pv, list):
                    for drop in pv:
                        if isinstance(drop, dict) and drop.get("item") == old_id:
                            drop["item"] = new_id
                            changed = True
        if changed:
            with open(el_path, "w", encoding="utf-8") as f:
                json.dump(el_data, f, indent=2, ensure_ascii=False)
    except Exception:
        pass


def _update_stack_refs(old_id: str, new_id: str, project) -> int:
    stacks_dir = project.data_path("stacks")
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
            changed = False
            for ev in data.get("events", []):
                if ev.get("event") in ("give_item", "remove_item"):
                    params = ev.get("params", {})
                    if params.get("item_id") == old_id:
                        params["item_id"] = new_id
                        changed = True
            if changed:
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                updated += 1
        except Exception:
            pass
    return updated
