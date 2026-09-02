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
    if pk == "personaje_id":
        return [("", "(ninguno)")]
    if pk == "posicion":
        return [("izquierda", "Izquierda"), ("centro", "Centro"), ("derecha", "Derecha")]
    if pk == "expresion":
        return [("normal", "Normal"), ("sorprendido", "Sorprendido"), ("triste", "Triste"), ("enojado", "Enojado")]
    if pk == "modo":
        return [("fill", "Rellenar"), ("tile", "Mosaico")]
    if pk == "menu_id":
        return [("inventory", "Inventario"), ("skills", "Habilidades"), ("map", "Mapa")]
    if pk == "minijuego_id":
        return [("", "(ninguno)")]
    if pk == "contador_id":
        return [("", "(ninguno)")]
    if pk == "item_id":
        return get_item_list()
    return []


# ── Trigger / Condition / Action types ─────────────────────

TRIGGERS = ["contact", "interact", "on_hit", "on_boss_defeated", "on_event_finalized"]

CONDITION_TYPES = [
    # ── Condiciones originales (con operadores) ──
    "has_moneda", "item_count", "flag", "ability", "ability_equipped", "pp",
    "evaluar_evento", "damage",
    # ── Condiciones simples (sin operadores) ──
    "has_ability", "has_ability_equipped", "has_escamas", "has_flag",
    "has_item", "has_pp",
    "not_has_ability", "not_has_ability_equipped", "not_has_escamas",
    "not_has_flag", "not_has_item",
    # ── Condiciones especializadas ──
    "attack_type", "escamas",
]

ACTION_TYPES = [
    # ── Mensajes y UI ──
    "show_message", "mostrar_ventana", "mostrar_opciones",
    "mostrar_personaje", "ocultar_personaje", "ocultar_todos_personajes",
    "cambiar_fondo",
    # ── Diálogo ──
    "start_dialogue", "close_dialog", "dialogo_inline", "dialogo_tree",
    # ── Sprite y Mapa ──
    "replace_sprite", "remove_sprite", "spawn_entity", "change_map",
    # ── Jugador ──
    "give_item", "remove_item", "give_moneda", "remove_moneda",
    "remove_escamas", "avanzar", "despertar", "cambiar_skin",
    "bloquear_mandos",
    # ── Combate ──
    "damage", "start_boss_fight", "mostrar_boss",
    # ── Habilidades ──
    "consume_pp", "desbloquear_habilidad", "equipar_habilidad",
    # ── Flags y Contadores ──
    "set_flag", "clear_flag", "add_flag",
    "increment_contador", "set_contador",
    # ── Tienda ──
    "open_shop", "close_shop", "abrir_menu",
    "restock_shop", "add_shop_stock", "modify_shop_price",
    # ── Audio ──
    "play_bgm", "stop_bgm", "play_sfx",
    "set_bgm_volume", "set_sfx_volume", "set_volume",
    # ── Sistema ──
    "set_resolution", "run_script", "save_game", "load_game",
    "open_save_menu", "open_load_menu", "close_save_menu",
    "mover_a", "examinar_key_item",
    # ── Escenas y Minijuegos ──
    "ir_a_escena", "iniciar_minijuego", "iniciar_demo", "fin_demo",
]

CONDITION_PARAMS: dict[str, dict[str, Any]] = {
    # ── Condiciones originales (con operadores) ──
    "has_moneda": {"moneda": "", "operador": ">=", "valor": 1},
    "item_count": {"item": "", "operador": ">=", "valor": 1},
    "flag": {"flag": "", "operador": "es_verdadero"},
    "ability": {"ability": "", "operador": "tiene"},
    "ability_equipped": {"ability": "", "operador": "equipado"},
    "pp": {"operador": ">=", "valor": 1},
    "evaluar_evento": {"evento_id": "", "estado": "finalizado"},
    "damage": {"operador": ">=", "valor": 1},
    # ── Condiciones simples (sin operadores) ──
    "has_ability": {"ability": ""},
    "has_ability_equipped": {"ability": ""},
    "has_escamas": {},
    "has_flag": {"flag": ""},
    "has_item": {"item": ""},
    "has_pp": {},
    "not_has_ability": {"ability": ""},
    "not_has_ability_equipped": {"ability": ""},
    "not_has_escamas": {},
    "not_has_flag": {"flag": ""},
    "not_has_item": {"item": ""},
    # ── Condiciones especializadas ──
    "attack_type": {"attack_type": ""},
    "escamas": {"operador": ">=", "valor": 1},
}

ACTION_PARAMS: dict[str, dict[str, Any]] = {
    # ── Mensajes y UI ──
    "show_message": {"mensaje": ""},
    "mostrar_ventana": {"ventana_id": ""},
    "mostrar_opciones": {"opciones": []},
    "mostrar_personaje": {"personaje_id": "", "posicion": "centro", "expresion": "normal"},
    "ocultar_personaje": {"personaje_id": ""},
    "ocultar_todos_personajes": {},
    "cambiar_fondo": {"sprite_id": "", "modo": "fill"},
    # ── Diálogo ──
    "start_dialogue": {"dialogo_id": ""},
    "close_dialog": {},
    "dialogo_inline": {"lineas": [], "quien": ""},
    "dialogo_tree": {"dialogo_id": ""},
    # ── Sprite y Mapa ──
    "replace_sprite": {"sprite_id": ""},
    "remove_sprite": {},
    "spawn_entity": {"sprite_id": "", "offset_x": 0, "offset_y": 0, "z": 0},
    "change_map": {"nivel": "", "exit_id": ""},
    # ── Jugador ──
    "give_item": {"item": "", "cantidad": 1},
    "remove_item": {"item": "", "cantidad": 1},
    "give_moneda": {"moneda": "", "cantidad": 1},
    "remove_moneda": {"moneda": "", "cantidad": 1},
    "remove_escamas": {"cantidad": 1},
    "avanzar": {"direccion": ""},
    "despertar": {},
    "cambiar_skin": {"skin": ""},
    "bloquear_mandos": {"bloquear": True},
    # ── Combate ──
    "damage": {"cantidad": 1, "mensaje": ""},
    "start_boss_fight": {},
    "mostrar_boss": {"visible": True},
    # ── Habilidades ──
    "consume_pp": {"cantidad": 1},
    "desbloquear_habilidad": {"habilidad": ""},
    "equipar_habilidad": {"habilidad": ""},
    # ── Flags y Contadores ──
    "set_flag": {"flag": ""},
    "clear_flag": {"flag": ""},
    "add_flag": {"flag": "", "cantidad": 1},
    "increment_contador": {"contador_id": "", "cantidad": 1},
    "set_contador": {"contador_id": "", "valor": 0},
    # ── Tienda ──
    "open_shop": {"shop_id": ""},
    "close_shop": {},
    "abrir_menu": {"menu_id": ""},
    "restock_shop": {"shop_id": "", "item_id": ""},
    "add_shop_stock": {"shop_id": "", "item_id": "", "cantidad": 1},
    "modify_shop_price": {"shop_id": "", "item_id": "", "moneda": "", "precio": 0},
    # ── Audio ──
    "play_bgm": {"asset_id": "", "fade_ms": 0},
    "stop_bgm": {"fade_ms": 0},
    "play_sfx": {"asset_id": ""},
    "set_bgm_volume": {"volumen": 1.0},
    "set_sfx_volume": {"volumen": 1.0},
    "set_volume": {"volumen": 1.0},
    # ── Sistema ──
    "set_resolution": {"ancho": 0, "alto": 0},
    "run_script": {"function_name": "", "args": ""},
    "save_game": {"slot": 1, "dev": False},
    "load_game": {"slot": 1, "dev": False},
    "open_save_menu": {},
    "open_load_menu": {},
    "close_save_menu": {},
    "mover_a": {"evento_id": ""},
    "examinar_key_item": {"item": ""},
    # ── Escenas y Minijuegos ──
    "ir_a_escena": {"capitulo": 0, "escena": 0},
    "iniciar_minijuego": {"minijuego_id": ""},
    "iniciar_demo": {"demo_id": ""},
    "fin_demo": {},
}

# Param keys that should show a dropdown instead of text field
DROPDOWN_PARAMS = {
    "ability", "item", "sprite_id", "nivel", "operador", "estado",
    "bloquear", "visible", "habilidad", "demo_id", "boss_id",
    "ventana_id", "direccion", "moneda", "shop_id", "item_id",
    "personaje_id", "posicion", "expresion", "modo", "menu_id",
    "minijuego_id", "contador_id",
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
