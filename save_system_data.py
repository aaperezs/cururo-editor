# Editor de configuración del sistema de guardado (data/save_system.json).
#
# Formato: {"save_system": {...config...}}

import copy
import json
import os

from editor.project import get_current_project

_CONFIG = {}


def _get_path():
    p = get_current_project()
    return p.data_path("save_system.json") if p else None


def _load_config():
    global _CONFIG
    _CONFIG = {}
    p = get_current_project()
    if not p:
        return
    path = p.data_path("save_system.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            cfg = data.get("save_system")
            if isinstance(cfg, dict):
                _CONFIG = cfg
        except (json.JSONDecodeError, IOError):
            _CONFIG = {}


def _save_config():
    path = _get_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"save_system": _CONFIG}, f, indent=2, ensure_ascii=False)


def get_config():
    return copy.deepcopy(_CONFIG)


def set_config(cfg):
    global _CONFIG
    _CONFIG = copy.deepcopy(cfg)


def get_field(field, default=None):
    return _CONFIG.get(field, default)


def set_field(field, value):
    _CONFIG[field] = value


def validar_config(config):
    """Valida la configuración. Retorna (ok, errores)."""
    errores = []
    slots = config.get("slots", 10)
    if not isinstance(slots, int) or slots < 1 or slots > 99:
        errores.append("Slots debe ser 1-99")

    validaciones = config.get("validaciones", {})
    min_slots = validaciones.get("min_slots", 1)
    max_slots = validaciones.get("max_slots", 99)
    if min_slots > max_slots:
        errores.append("min_slots > max_slots")

    item_id = config.get("save_point_item_id", "")
    if not item_id:
        errores.append("Item de guardado requerido")

    entity_type = config.get("save_point_entity_type", "")
    if not entity_type:
        errores.append("Entidad save point requerida")

    schema = config.get("schema", {})
    include = schema.get("include", [])
    if not include:
        errores.append("Schema include vacío")

    return len(errores) == 0, errores
