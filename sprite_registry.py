import os
from editor.project import get_current_project

_BASE_REGISTRY = {
    "pasto":              {"file": "pasto",           "display": "Pasto",           "char": "&"},
    "pasto_esteril":      {"file": "pasto_esteril",   "display": "Pasto esteril",    "char": None},
    "piso_piedra":        {"file": "piso_piedra",     "display": "Piso piedra",     "char": "_"},
    "pared":              {"file": "pared",           "display": "Pared",           "char": "*"},
    "bloque_acero":       {"file": "bloque_acero",   "display": "Bloque acero",    "char": "#"},
    "roca":               {"file": "roca",            "display": "Roca",            "char": "R"},
    "roca_grieta":        {"file": "roca_grieta",     "display": "Roca grieta",     "char": None},
    "roca_hielo":         {"file": "roca_hielo",      "display": "Roca hielo",      "char": "F"},
    "roca_nieve":         {"file": "roca_nieve",      "display": "Roca nieve",      "char": "N"},
    "arbol":              {"file": "arbol",           "display": "Árbol",           "char": "A"},
    "hierba_0":           {"file": "hierba_0",        "display": "Hierba 0",        "char": None},
    "hierba_1":           {"file": "hierba_1",        "display": "Hierba 1",        "char": None},
    "hierba_2":           {"file": "hierba_2",        "display": "Hierba 2",        "char": None},
    "cofre":              {"file": None,              "display": "Cofre",           "char": "$"},
    "comida_normal":      {"file": "comida_normal",   "display": "Comida normal",   "char": "O"},
    "comida_mana":        {"file": "comida_mana",     "display": "Comida mana",     "char": "M"},
    "comida_dorada":      {"file": "comida_dorada",   "display": "Comida dorada",   "char": "G"},
    "enemigo_melee_v":    {"file": "enemigo_melee",   "display": "Enemigo V",       "char": "V"},
    "enemigo_melee_h":    {"file": "enemigo_melee",   "display": "Enemigo H",       "char": "H"},
    "enemigo_melee_c":    {"file": "enemigo_melee",   "display": "Enemigo C",       "char": "C"},
    "enemigo_shooter_h":  {"file": "enemigo_shooter", "display": "Shooter H",       "char": "S"},
    "enemigo_shooter_v":  {"file": "enemigo_shooter", "display": "Shooter V",       "char": "T"},
    "inicio":             {"file": "spawn_hero",      "display": "Inicio",          "char": "I"},
    "portal":             {"file": "portal",          "display": "Portal",          "char": "P"},
    "jefe":               {"file": "boss",            "display": "Jefe",            "char": "B"},
    "restricted":         {"file": None,              "display": "Restringido",     "char": "="},
    "portal_jefe":        {"file": None,              "display": "Portal jefe",      "char": "J"},
    "portal_salida":      {"file": None,              "display": "Portal salida",     "char": "K"},
    "escalera":           {"file": None,              "display": "Escalera",         "char": "E"},
    "gate":               {"file": "gate",            "display": "Gate",             "char": "D"},
    "tiara":              {"file": "tiara",           "display": "Tiara",            "char": "W"},
    "deco_0":             {"file": "deco_0",          "display": "Decoracion 0",     "char": "1"},
    "deco_1":             {"file": "deco_1",          "display": "Decoracion 1",     "char": "2"},
    "deco_2":             {"file": "deco_2",          "display": "Decoracion 2",     "char": "3"},
    "deco_3":             {"file": "deco_3",          "display": "Decoracion 3",     "char": "4"},
    "spawn_hero":         {"file": "spawn_hero",      "display": "Spawn heroe",      "char": "h"},
}

_BUILT_KEYS = set(_BASE_REGISTRY.keys())
_DYNAMIC_ENTRIES = {}

# Single mutable dict shared by all getters — mutated on reload
_MERGED = dict(_BASE_REGISTRY)
_MERGED_NEEDS_REBUILD = True


def _rebuild_merged():
    global _MERGED, _MERGED_NEEDS_REBUILD
    if not _MERGED_NEEDS_REBUILD:
        return
    _MERGED.clear()
    _MERGED.update(_BASE_REGISTRY)
    _MERGED.update(_DYNAMIC_ENTRIES)
    _MERGED_NEEDS_REBUILD = False


def _scan_assets():
    global _MERGED_NEEDS_REBUILD
    _DYNAMIC_ENTRIES.clear()
    p = get_current_project()
    if not p:
        return
    assets_dir = p.assets_path()
    if not os.path.isdir(assets_dir):
        return
    for fname in sorted(os.listdir(assets_dir)):
        if not fname.lower().endswith(".png"):
            continue
        stem = os.path.splitext(fname)[0]
        if stem in _BUILT_KEYS and _BASE_REGISTRY.get(stem, {}).get("file") is not None:
            continue
        if stem in _DYNAMIC_ENTRIES:
            continue
        display = stem.replace("_", " ").title()
        _DYNAMIC_ENTRIES[stem] = {"file": stem, "display": display, "char": None}
    _MERGED_NEEDS_REBUILD = True


def get_sprite_registry():
    _scan_assets()
    _rebuild_merged()
    return _MERGED


def get_sprite_options():
    reg = get_sprite_registry()
    items = []
    for sid in sorted(reg.keys()):
        info = reg[sid]
        items.append((sid, info.get("display", sid)))
    return items


def sprite_registry_reload():
    _DYNAMIC_ENTRIES.clear()
    _MERGED_NEEDS_REBUILD = True


def get_multi_tile_info(sprite_id):
    reg = get_sprite_registry()
    info = reg.get(sprite_id)
    if info and info.get("multi"):
        return info
    return None

def get_multi_tile_tiles(sprite_id):
    info = get_multi_tile_info(sprite_id)
    if info:
        return info.get("tiles", [])
    return []

def is_multi_tile(sprite_id):
    info = get_multi_tile_info(sprite_id)
    return info is not None

def compute_multi_dims(sprite_id):
    info = get_multi_tile_info(sprite_id)
    if not info:
        return 1, 1
    tiles = info.get("tiles", [])
    rows = max(t.get("row", 0) for t in tiles) + 1 if tiles else 1
    cols = max(t.get("col", 0) for t in tiles) + 1 if tiles else 1
    return rows, cols

# Backward-compat exports — references the same mutable dict
SPRITE_REGISTRY = _MERGED

# Backward-compat: CHAR_TO_SPRITE / SPRITE_TO_CHAR only from base
CHAR_TO_SPRITE = {}
for sid, info in _BASE_REGISTRY.items():
    c = info["char"]
    if c is not None:
        CHAR_TO_SPRITE[c] = sid

SPRITE_TO_CHAR = {sid: info["char"] for sid, info in _BASE_REGISTRY.items() if info["char"] is not None}
