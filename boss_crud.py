"""Boss CRUD operations. Pure logic — no pygame."""

from __future__ import annotations

import copy
from typing import Any, Dict, List, Optional

from editor.boss_data import create_boss, delete_boss, get_all_bosses, get_boss, set_boss
from editor.boss_fight_types import get_default_phase
from editor.element_crud import generate_new_id


def create_new_boss() -> str:
    """Create a new boss with auto-incremented ID. Returns the new ID."""
    bid = generate_new_id("nuevo_boss", get_all_bosses())
    create_boss(bid)
    return bid


def clone_boss(source_id: str) -> Optional[str]:
    """Clone an existing boss. Returns the new ID or None."""
    boss = get_boss(source_id)
    if not boss:
        return None
    bid = generate_new_id(source_id + "_copia", get_all_bosses())
    set_boss(bid, copy.deepcopy(boss))
    return bid


def delete_boss_by_id(boss_id: str) -> None:
    """Delete a boss by ID."""
    delete_boss(boss_id)


def save_boss(boss_id: str, fields: Dict[str, Any]) -> bool:
    """Save boss fields. Returns True on success."""
    boss = get_boss(boss_id)
    if not boss:
        return False
    boss.update(fields)
    set_boss(boss_id, boss)
    return True


def add_phase(boss_id: str) -> bool:
    """Add a new phase to a boss. Returns True on success."""
    boss = get_boss(boss_id)
    if not boss:
        return False
    ftype = boss.get("fight_type", "orbital")
    default = get_default_phase(ftype)
    phases = boss.get("phases", [])
    if phases:
        last_th = phases[-1].get("hp_threshold", 0.0)
        default["hp_threshold"] = last_th / 2 if last_th > 0 else 0.0
    else:
        default["hp_threshold"] = 0.5
    boss.setdefault("phases", []).append(default)
    boss["phases"] = sorted(boss["phases"], key=lambda p: -p.get("hp_threshold", 0.0))
    set_boss(boss_id, boss)
    return True


def delete_phase(boss_id: str, phase_idx: int) -> bool:
    """Delete a phase at index. Returns True on success."""
    boss = get_boss(boss_id)
    if not boss:
        return False
    phases = boss.get("phases", [])
    if phase_idx < 0 or phase_idx >= len(phases):
        return False
    if len(phases) <= 1:
        return False
    phases.pop(phase_idx)
    set_boss(boss_id, boss)
    return True
