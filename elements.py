import json
import os
from copy import deepcopy
from editor.project import get_current_project

_ELEMENTOS_DATA = {}


def _get_path():
    p = get_current_project()
    if p:
        return p.data_path("elementos.json")
    return None


def _load_elements():
    global _ELEMENTOS_DATA
    path = _get_path()
    if path and os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _ELEMENTOS_DATA = json.load(f)
    else:
        _ELEMENTOS_DATA = {}


def _save_elements():
    path = _get_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_ELEMENTOS_DATA, f, indent=2, ensure_ascii=False)


def get_element(element_id):
    if not _ELEMENTOS_DATA:
        _load_elements()
    return deepcopy(_ELEMENTOS_DATA.get(element_id))


def get_all_elements():
    if not _ELEMENTOS_DATA:
        _load_elements()
    return list(_ELEMENTOS_DATA.keys())


def get_element_properties(element_id):
    el = get_element(element_id)
    if el:
        return dict(el.get("properties", {}))
    return {}


def set_element(element_id, data):
    if not _ELEMENTOS_DATA:
        _load_elements()
    _ELEMENTOS_DATA[element_id] = data
    _save_elements()


def delete_element(element_id):
    if not _ELEMENTOS_DATA:
        _load_elements()
    if element_id in _ELEMENTOS_DATA:
        del _ELEMENTOS_DATA[element_id]
        _save_elements()


def element_exists(element_id):
    if not _ELEMENTOS_DATA:
        _load_elements()
    return element_id in _ELEMENTOS_DATA


def rename_element(old_id, new_id):
    if old_id == new_id:
        return True
    if not _ELEMENTOS_DATA:
        _load_elements()
    if new_id in _ELEMENTOS_DATA:
        return False
    if old_id not in _ELEMENTOS_DATA:
        return False
    _ELEMENTOS_DATA[new_id] = _ELEMENTOS_DATA.pop(old_id)
    _save_elements()
    return True


def create_element(element_id, sprite_id, name, behavior, properties=None, tileset_idx=None):
    data = {
        "sprite_id": sprite_id,
        "name": name,
        "behavior": behavior,
        "properties": properties or {},
    }
    if tileset_idx is not None:
        data["tileset_idx"] = tileset_idx
    set_element(element_id, data)
    return data


def get_element_name(element_id):
    el = get_element(element_id)
    return el.get("name", element_id) if el else element_id


def get_element_sprite_id(element_id):
    el = get_element(element_id)
    if not el:
        return None
    # If element has tileset_idx, return special format for tileset rendering
    if "tileset_idx" in el:
        return f"tileset:{el['tileset_idx']}"
    return el.get("sprite_id")


def get_element_tileset_idx(element_id):
    el = get_element(element_id)
    if el and "tileset_idx" in el:
        return el["tileset_idx"]
    return None


def set_element_tileset_idx(element_id, tileset_idx):
    el = get_element(element_id)
    if not el:
        return False
    if tileset_idx is not None:
        el["tileset_idx"] = tileset_idx
    else:
        el.pop("tileset_idx", None)
    set_element(element_id, el)
    return True


def get_element_behavior(element_id):
    el = get_element(element_id)
    return el.get("behavior") if el else None


def get_element_subtiles(element_id):
    el = get_element(element_id)
    if not el:
        return []
    return el.get("subtiles", [])


def set_element_subtile(element_id, col, row, data):
    el = get_element(element_id)
    if not el:
        return False
    subtiles = el.setdefault("subtiles", [])
    for st in subtiles:
        if st.get("col") == col and st.get("row") == row:
            st.update(data)
            set_element(element_id, el)
            return True
    data["col"] = col
    data["row"] = row
    subtiles.append(data)
    set_element(element_id, el)
    return True


def is_multi_tile_element(element_id):
    el = get_element(element_id)
    return el.get("multi_tile", False) if el else False
