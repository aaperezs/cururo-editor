"""Event editor constants, color palette, layout values, and data provider functions.

Pure data with no pygame_gui dependency.
Extracted from EventEditorWidget (event_editor_widget.py) for testability and reuse.
"""

from __future__ import annotations

import os
from typing import Any


# ── Data provider functions ────────────────────────────────

def get_map_list() -> list[tuple[str, str]]:
    from editor.project import get_current_project
    p = get_current_project()
    if not p:
        return []
    maps_dir = os.path.join(p.root, "levels", "mapas")
    if not os.path.isdir(maps_dir):
        return []
    seen: set[str] = set()
    maps: list[tuple[str, str]] = []
    for f in sorted(os.listdir(maps_dir)):
        if not f.endswith(".json"):
            continue
        base = f[:-5]
        if base.endswith("_meta") or base.endswith("_z1") or base.endswith("_z2") or base.endswith("_z3") or base.endswith("_z4"):
            continue
        if base in seen:
            continue
        seen.add(base)
        maps.append((base, base))
    return maps


def get_boss_list() -> list[tuple[str, str]]:
    from editor.boss_data import get_all_bosses
    return [(b, b) for b in get_all_bosses()]


def get_moneda_list() -> list[tuple[str, str]]:
    from editor.monedas_data import get_monedas
    return [(m.get("id", ""), m.get("label") or m.get("id", "")) for m in get_monedas()]


def get_param_options(pk: str, ct: str | None = None) -> list[tuple[str, str]]:
    """Resolve dropdown options for a given param key."""
    from editor.ability_data import get_ability_list, get_skin_list
    from editor.items_data import get_item_list
    from editor.sprite_registry import get_sprite_options

    if pk == "moneda":
        return get_moneda_list()
    if pk == "ability":
        return get_ability_list()
    if pk == "item":
        return get_item_list()
    if pk == "sprite_id":
        return get_sprite_options()
    if pk == "nivel":
        return get_map_list()
    if pk == "shop_id":
        from editor.shops_data import get_all_shops
        return [("", "(ninguna)")] + [(s, s) for s in sorted(get_all_shops())]
    if pk == "operador" and ct:
        return COND_OPERATOR_OPTIONS.get(ct, [])
    if pk == "estado":
        return [("pendiente", "Pendiente"), ("finalizado", "Finalizado")]
    if pk == "bloquear":
        return [("True", "Bloquear"), ("False", "Desbloquear")]
    if pk == "visible":
        return [("True", "Visible"), ("False", "Oculto")]
    if pk == "habilidad":
        return get_ability_list()
    if pk == "skin":
        return get_skin_list()
    if pk == "demo_id":
        return [("golpe_cabeza", "Golpe de Cabeza")]
    if pk == "boss_id":
        return get_boss_list()
    if pk == "ventana_id":
        import json
        from editor.project import get_current_project
        p = get_current_project()
        if p:
            path = os.path.join(p.root, "data", "text_screens.json")
            if os.path.exists(path):
                try:
                    with open(path, encoding="utf-8") as f:
                        data = json.load(f)
                    return [(v, v) for v in sorted(data.keys())]
                except Exception:
                    pass
        return []
    if pk == "direccion":
        return [("ARRIBA", "Arriba"), ("ABAJO", "Abajo"), ("IZQUIERDA", "Izquierda"), ("DERECHA", "Derecha")]
    if pk == "tecla":
        return [("Q", "Q (Habilidad)")]
    return []


# ── Trigger / Condition / Action types ─────────────────────

TRIGGERS = ["contact", "interact", "on_hit", "on_boss_defeated", "on_event_finalized"]

CONDITION_TYPES = [
    "has_moneda", "item_count", "flag", "ability", "ability_equipped", "pp",
    "evaluar_evento", "damage",
]

ACTION_TYPES = [
    "show_message", "replace_sprite", "remove_sprite", "spawn_entity",
    "start_dialogue", "change_map", "mover_a",
    "give_item", "remove_item", "consume_pp",
    "set_flag", "clear_flag", "give_moneda", "remove_moneda", "damage",
    "run_script", "start_boss_fight", "iniciar_dialogo", "esperar",
    "bloquear_eventos", "bloquear_mandos",
    "desbloquear_habilidad", "equipar_habilidad", "cambiar_skin",
    "mostrar_boss", "iniciar_demo", "mostrar_ventana",
    "avanzar", "accion_botton",
    "open_shop", "close_shop", "dialogo_tree",
]

CONDITION_PARAMS: dict[str, dict[str, Any]] = {
    "has_moneda": {"moneda": "", "operador": ">=", "valor": 1},
    "item_count": {"item": "", "operador": ">=", "valor": 1},
    "flag": {"flag": "", "operador": "es_verdadero"},
    "ability": {"ability": "", "operador": "tiene"},
    "ability_equipped": {"ability": "", "operador": "equipado"},
    "pp": {"operador": ">=", "valor": 1},
    "evaluar_evento": {"evento_id": "", "estado": "finalizado"},
    "damage": {"operador": ">=", "valor": 1},
}

ACTION_PARAMS: dict[str, dict[str, Any]] = {
    "show_message": {"mensaje": ""},
    "replace_sprite": {"sprite_id": ""},
    "remove_sprite": {},
    "spawn_entity": {"sprite_id": "", "offset_x": 0, "offset_y": 0, "z": 0},
    "start_dialogue": {"dialogo_id": ""},
    "change_map": {"nivel": "", "exit_id": ""},
    "mover_a": {"evento_id": ""},
    "give_item": {"item": "", "cantidad": 1},
    "remove_item": {"item": "", "cantidad": 1},
    "consume_pp": {"cantidad": 1},
    "set_flag": {"flag": ""},
    "clear_flag": {"flag": ""},
    "give_moneda": {"moneda": "", "cantidad": 1},
    "remove_moneda": {"moneda": "", "cantidad": 1},
    "damage": {"cantidad": 1, "mensaje": ""},
    "run_script": {"function_name": "", "args": ""},
    "start_boss_fight": {},
    "iniciar_dialogo": {"dialogo_id": ""},
    "esperar": {"segundos": 1},
    "bloquear_eventos": {"bloquear": True},
    "bloquear_mandos": {"bloquear": True},
    "desbloquear_habilidad": {"habilidad": ""},
    "equipar_habilidad": {"habilidad": ""},
    "cambiar_skin": {"skin": ""},
    "mostrar_boss": {"visible": True},
    "iniciar_demo": {"demo_id": ""},
    "mostrar_ventana": {"ventana_id": ""},
    "avanzar": {"direccion": ""},
    "accion_botton": {"tecla": ""},
    "open_shop": {"shop_id": ""},
    "close_shop": {},
    "dialogo_tree": {"dialogo_id": ""},
}

# Param keys that should show a dropdown instead of text field
DROPDOWN_PARAMS = {
    "ability", "item", "sprite_id", "nivel", "operador", "estado",
    "bloquear", "visible", "habilidad", "demo_id", "boss_id",
    "ventana_id", "direccion", "tecla", "moneda", "shop_id",
}

# Operator options per condition type
COND_OPERATOR_OPTIONS: dict[str, list[tuple[str, str]]] = {
    "has_moneda": [(">=", ">="), ("<=", "<="), (">", ">"), ("<", "<"), ("==", "=="), ("!=", "!=")],
    "item_count": [(">=", ">="), ("<=", "<="), (">", ">"), ("<", "<"), ("==", "=="), ("!=", "!=")],
    "pp": [(">=", ">="), ("<=", "<="), (">", ">"), ("<", "<"), ("==", "=="), ("!=", "!=")],
    "flag": [("es_verdadero", "Es verdadero"), ("es_falso", "Es falso")],
    "ability": [("tiene", "Tiene"), ("no_tiene", "No tiene")],
    "ability_equipped": [("equipado", "Equipado"), ("no_equipado", "No equipado")],
}


# ── Color palette ──────────────────────────────────────────

COL_BG = (35, 40, 45)
COL_BORDER = (55, 60, 65)
COL_CARD_BG = (45, 50, 58)
COL_CARD_BORDER = (60, 65, 75)
COL_TEXT = (220, 220, 220)
COL_TEXT_DIM = (160, 165, 175)
COL_ACCENT = (70, 130, 200)
COL_GREEN = (60, 120, 60)
COL_RED = (180, 60, 60)
COL_EDIT_BG = (60, 80, 120)
COL_FIELD_BG = (50, 55, 65)
COL_FIELD_BORDER = (70, 75, 85)


# ── Layout constants ───────────────────────────────────────

CARD_MARGIN = 12
INDENT = 10
TRIGGER_W = 100
