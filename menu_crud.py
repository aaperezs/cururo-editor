"""CRUD operations for menus, apartados, config items, and controls.

Pure dict manipulation — no pygame_gui dependency.
Extracted from MenuTab (menu_panel.py) for testability.
"""

from __future__ import annotations

import copy
from typing import Any

from editor.menu_data import (
    create_menu,
    delete_menu,
    get_menu,
    menu_exists,
    rename_menu,
    set_menu,
)


# ── Type aliases ───────────────────────────────────────────

Menu = dict[str, Any]
Apartado = dict[str, Any]
ConfigItem = dict[str, Any]
Control = dict[str, Any]


# ── Menu CRUD ──────────────────────────────────────────────

def create_new_menu(template: str | None = None) -> str | None:
    """Create a new menu with auto-incremented ID. Returns the new ID or None."""
    base = "menu_nuevo"
    mid = base
    n = 1
    while menu_exists(mid):
        mid = f"{base}_{n}"
        n += 1
    create_menu(mid, plantilla=template or "vacio")
    return mid


def clone_menu(source_id: str) -> str | None:
    """Clone an existing menu. Returns the new ID or None."""
    data = get_menu(source_id)
    if not data:
        return None
    base = source_id + "_copia"
    mid = base
    n = 1
    while menu_exists(mid):
        mid = f"{base}_{n}"
        n += 1
    set_menu(mid, data)
    return mid


def delete_menu_by_id(menu_id: str) -> None:
    """Delete a menu by ID."""
    delete_menu(menu_id)


def rename_menu_by_id(old_id: str, new_id: str) -> bool:
    """Rename a menu. Returns True on success."""
    if menu_exists(new_id):
        return False
    return rename_menu(old_id, new_id)


# ── Apartado CRUD ──────────────────────────────────────────

def move_apartado(menu: Menu, idx: int, direction: int) -> int | None:
    """Move an apartado by direction (+1/-1). Returns new index or None."""
    apartados = menu.get("apartados", [])
    nuevo = idx + direction
    if not (0 <= idx < len(apartados)) or not (0 <= nuevo < len(apartados)):
        return None
    apartados[idx], apartados[nuevo] = apartados[nuevo], apartados[idx]
    return nuevo


def add_apartado(menu: Menu) -> int:
    """Add a new apartado. Returns its index."""
    apartados = menu.setdefault("apartados", [])
    n = len(apartados) + 1
    apartados.append({
        "id": f"apartado_{n}",
        "nombre": f"Apartado {n}",
        "tipo": "lista",
    })
    return len(apartados) - 1


def delete_apartado(menu: Menu, idx: int) -> int | None:
    """Delete an apartado at idx. Returns new selected index or None if empty."""
    apartados = menu.get("apartados", [])
    if 0 <= idx < len(apartados):
        del apartados[idx]
    new_idx = max(0, min(idx - 1, len(apartados) - 1))
    if not apartados:
        return None
    return new_idx


# ── Config Item CRUD ───────────────────────────────────────

def add_config_item(config_items: list[ConfigItem], config_key: str) -> int:
    """Add a new config item (item/flag/stat). Returns its index."""
    n = len(config_items) + 1
    if config_key == "items":
        config_items.append({
            "id": f"item_{n}", "nombre": f"Item {n}", "descripcion": "",
        })
    elif config_key == "flags":
        config_items.append({
            "id": f"flag_{n}", "nombre": f"Flag {n}", "default": "0",
        })
    else:
        config_items.append({
            "id": f"stat_{n}", "nombre": f"Stat {n}", "valor": "",
        })
    return len(config_items) - 1


def delete_config_item(config_items: list[ConfigItem], idx: int) -> int | None:
    """Delete a config item at idx. Returns new selected index or None if empty."""
    if 0 <= idx < len(config_items):
        del config_items[idx]
    new_idx = max(0, min(idx - 1, len(config_items) - 1))
    if not config_items:
        return None
    return new_idx


def duplicate_config_item(config_items: list[ConfigItem], idx: int) -> int | None:
    """Duplicate a config item. Returns index of the duplicate or None."""
    if not (0 <= idx < len(config_items)):
        return None
    dup = copy.deepcopy(config_items[idx])
    dup["id"] = (dup.get("id", "") or "item") + "_copia"
    config_items.append(dup)
    return len(config_items) - 1


# ── Control CRUD ───────────────────────────────────────────

def add_control(controls: list[Control]) -> int:
    """Add a new control binding. Returns its index."""
    n = len(controls) + 1
    controls.append({"accion": f"Acci\u00f3n {n}", "tecla": ""})
    return len(controls) - 1


def delete_control(controls: list[Control], idx: int) -> int | None:
    """Delete a control at idx. Returns new selected index or None if empty."""
    if 0 <= idx < len(controls):
        del controls[idx]
    new_idx = max(0, min(idx - 1, len(controls) - 1))
    if not controls:
        return None
    return new_idx


def duplicate_control(controls: list[Control], idx: int) -> int | None:
    """Duplicate a control binding. Returns index of the duplicate or None."""
    if not (0 <= idx < len(controls)):
        return None
    dup = copy.deepcopy(controls[idx])
    dup["accion"] = (dup.get("accion", "") or "Acci\u00f3n") + "_copia"
    controls.append(dup)
    return len(controls) - 1
