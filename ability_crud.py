"""Ability CRUD operations. Pure logic — no pygame."""

from __future__ import annotations

import copy
from typing import Optional

from editor.ability_data import (
    get_abilities, get_ability, set_ability, delete_ability,
    create_ability, is_protected,
)
from editor.element_crud import generate_new_id


def create_new_ability() -> str:
    """Create a new ability with auto-incremented ID. Returns the new ID."""
    hid = generate_new_id("habilidad_nueva", list(get_abilities().keys()))
    create_ability(hid)
    return hid


def clone_ability(source_id: str) -> Optional[str]:
    """Clone an existing ability. Returns the new ID or None."""
    data = get_ability(source_id)
    if not data:
        return None
    hid = generate_new_id(source_id + "_copia", list(get_abilities().keys()))
    set_ability(hid, copy.deepcopy(data))
    return hid


def delete_ability_by_id(ability_id: str) -> bool:
    """Delete an ability. Returns False if protected."""
    if is_protected(ability_id):
        return False
    delete_ability(ability_id)
    return True
