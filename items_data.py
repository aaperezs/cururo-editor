import json
import os
import copy
from editor.project import get_current_project

_ITEMS_DATA = {}


def _get_path():
    p = get_current_project()
    if p:
        return p.data_path("items.json")
    return None


def _load_items():
    global _ITEMS_DATA
    _ITEMS_DATA = {}
    p = get_current_project()
    if not p:
        return
    path = p.data_path("items.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _ITEMS_DATA = json.load(f)


def _save_items():
    path = _get_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_ITEMS_DATA, f, indent=2, ensure_ascii=False)


def get_all_items():
    return sorted(_ITEMS_DATA.keys())


def get_item(iid):
    d = _ITEMS_DATA.get(iid)
    return copy.deepcopy(d) if d else None


def get_item_list():
    items = []
    for iid, cfg in _ITEMS_DATA.items():
        items.append((iid, cfg.get("nombre", iid)))
    return items


def set_item(iid, data):
    _ITEMS_DATA[iid] = copy.deepcopy(data)
    _save_items()


def delete_item(iid):
    if iid in _ITEMS_DATA:
        del _ITEMS_DATA[iid]
        _save_items()
        return True
    return False


def item_exists(iid):
    return iid in _ITEMS_DATA


def rename_item(old_id, new_id):
    if old_id == new_id:
        return True
    if new_id in _ITEMS_DATA:
        return False
    if old_id not in _ITEMS_DATA:
        return False
    _ITEMS_DATA[new_id] = _ITEMS_DATA.pop(old_id)
    _save_items()
    return True


def create_item(iid):
    if iid in _ITEMS_DATA:
        return False
    data = {
        "nombre": iid,
        "descripcion": "",
        "sprite_id": "",
        "tipo": "equipo",
        "slot": "cabeza",
        "rareza": "comun",
        "key_id": "",
        "efectos": [],
    }
    _ITEMS_DATA[iid] = data
    _save_items()
    return True
