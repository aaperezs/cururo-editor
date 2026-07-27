import json
import os
from copy import deepcopy
from editor.project import get_current_project

_HARDCODED_BEHAVIORS = {
    "decorative": {
        "label": "Decorativo",
        "group": "decoracion",
        "class_path": None,
        "target_list": None,
        "properties": {
            "animation": {"type": "string", "default": "", "label": "Animacion"}
        }
    },
    "spawn": {
        "label": "Spawn",
        "group": "decoracion",
        "class_path": None,
        "target_list": None,
        "properties": {}
    },
    "suelo": {
        "label": "Suelo",
        "group": "terreno",
        "class_path": "entities.suelo.Suelo",
        "target_list": "suelos",
        "properties": {
            "no_food_spawn": {"type": "bool", "default": False, "label": "Sin comida"}
        }
    },
    "bloqueante": {
        "label": "Bloqueante",
        "group": "obstaculos",
        "class_path": "entities.objeto_colision.ObjetoBloqueante",
        "target_list": "collidables",
        "properties": {
            "solid": {"type": "bool", "default": True, "label": "Solido"},
            "destructible": {"type": "bool", "default": False, "label": "Destructible"},
            "destructible_hp": {"type": "int", "default": 2, "label": "HP", "min": 1},
            "pushable": {"type": "bool", "default": False, "label": "Empujable"},
            "animation": {"type": "string", "default": "", "label": "Animacion"},
            "cracked_sprite": {"type": "string", "default": "", "label": "Sprite agrietado"}
        }
    },
    "peligroso": {
        "label": "Peligroso",
        "group": "obstaculos",
        "class_path": "entities.objeto_colision.ObjetoPeligroso",
        "target_list": "collidables",
        "properties": {
            "solid": {"type": "bool", "default": True, "label": "Solido"},
            "damage_type": {"type": "choice", "options": ["mata", "danio"], "default": "mata", "label": "Tipo danio"},
            "animation": {"type": "string", "default": "", "label": "Animacion"}
        }
    },
    "hierba": {
        "label": "Hierba",
        "group": "decoracion",
        "class_path": "entities.hierba_alta.HierbaAlta",
        "target_list": "hierba_alta",
        "properties": {
            "solid": {"type": "bool", "default": False, "label": "Solido"},
            "animation": {"type": "string", "default": "", "label": "Animacion"}
        }
    },
    "food": {
        "label": "Comida",
        "group": "items",
        "class_path": "entities.food.Food",
        "target_list": "comidas",
        "properties": {
            "solid": {"type": "bool", "default": False, "label": "Solido"},
            "food_type": {"type": "choice", "options": ["normal", "mana", "dorada"], "default": "normal", "label": "Tipo comida"},
            "animation": {"type": "string", "default": "", "label": "Animacion"}
        }
    },
    "enemigo_melee": {
        "label": "Enemigo melee",
        "group": "enemigos",
        "class_path": "entities.enemigos.EnemyMelee",
        "target_list": "enemigos",
        "properties": {
            "solid": {"type": "bool", "default": True, "label": "Solido"},
            "damage_type": {"type": "choice", "options": ["mata", "danio"], "default": "mata", "label": "Tipo danio"},
            "destructible": {"type": "bool", "default": True, "label": "Destructible"},
            "patron": {"type": "choice", "options": ["vertical", "horizontal", "circular"], "default": "vertical", "label": "Patron"},
            "drops": {"type": "drop_list", "default": [], "label": "Drops"}
        }
    },
    "enemigo_shooter": {
        "label": "Enemigo shooter",
        "group": "enemigos",
        "class_path": "entities.enemigos.Eldir",
        "target_list": "enemigos",
        "properties": {
            "solid": {"type": "bool", "default": True, "label": "Solido"},
            "damage_type": {"type": "choice", "options": ["mata", "danio"], "default": "mata", "label": "Tipo danio"},
            "destructible": {"type": "bool", "default": True, "label": "Destructible"},
            "patron": {"type": "choice", "options": ["shooter_h", "shooter_v"], "default": "shooter_h", "label": "Patron"},
            "drops": {"type": "drop_list", "default": [], "label": "Drops"}
        }
    },
    "boss": {
        "label": "Jefe",
        "group": "enemigos",
        "class_path": "entities.boss.Boss",
        "target_list": "jefes",
        "properties": {
            "solid": {"type": "bool", "default": False, "label": "Solido"}
        }
    },
    "multi_tile": {
        "label": "Multi-tile",
        "group": "decoracion",
        "class_path": None,
        "target_list": None,
        "properties": {
            "tile_rows": {"type": "int", "default": 1, "label": "Filas", "min": 1, "max": 2},
            "tile_cols": {"type": "int", "default": 1, "label": "Columnas", "min": 1, "max": 2},
        }
    },
}

_BEHAVIORS_DATA = None


def _get_path():
    p = get_current_project()
    if p:
        return p.data_path("behaviors.json")
    return None


def _load():
    global _BEHAVIORS_DATA
    path = _get_path()
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _BEHAVIORS_DATA = json.load(f)
    else:
        _BEHAVIORS_DATA = dict(_HARDCODED_BEHAVIORS)
        _save()


def _save():
    path = _get_path()
    if not path or _BEHAVIORS_DATA is None:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_BEHAVIORS_DATA, f, indent=2, ensure_ascii=False)


def _ensure_loaded():
    if _BEHAVIORS_DATA is None:
        _load()


def get_behaviors():
    _ensure_loaded()
    return dict(_BEHAVIORS_DATA)


def get_behavior(bid):
    _ensure_loaded()
    data = _BEHAVIORS_DATA.get(bid)
    if data:
        from copy import deepcopy
        return deepcopy(data)
    return None


def set_behavior(bid, data):
    _ensure_loaded()
    _BEHAVIORS_DATA[bid] = data
    _save()


def delete_behavior(bid):
    _ensure_loaded()
    if bid in _BEHAVIORS_DATA:
        del _BEHAVIORS_DATA[bid]
        _save()


def create_behavior(bid, data):
    set_behavior(bid, data)


def get_behavior_list():
    _ensure_loaded()
    return [(bid, bdata["label"]) for bid, bdata in _BEHAVIORS_DATA.items()]


def get_behavior_groups():
    _ensure_loaded()
    groups = set()
    for bdata in _BEHAVIORS_DATA.values():
        g = bdata.get("group")
        if g:
            groups.add(g)
    return sorted(groups)


# Backward-compatible constants (lazy computed from data)
BEHAVIORS = {}
DEFAULT_ELEMENT_PROPERTIES = {}


def _rebuild_constants():
    global BEHAVIORS, DEFAULT_ELEMENT_PROPERTIES
    _ensure_loaded()
    BEHAVIORS = dict(_BEHAVIORS_DATA)
    DEFAULT_ELEMENT_PROPERTIES = {}
    for bid, bdata in _BEHAVIORS_DATA.items():
        DEFAULT_ELEMENT_PROPERTIES[bid] = {}
        for pkey, pdata in bdata.get("properties", {}).items():
            DEFAULT_ELEMENT_PROPERTIES[bid][pkey] = pdata.get("default")


# Auto-rebuild on first import
_rebuild_constants()
