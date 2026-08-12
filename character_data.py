import json
import os
import copy
from editor.project import get_current_project


_CHARACTERS_DATA = {}
_PROTECTED_CHARS = set()


def _get_path():
    p = get_current_project()
    if p:
        return p.data_path("personajes.json")
    return None


def _load_characters():
    global _CHARACTERS_DATA, _PROTECTED_CHARS
    _CHARACTERS_DATA = {}
    p = get_current_project()
    if not p:
        return
    path = p.data_path("personajes.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _CHARACTERS_DATA.update(data.get("personajes", {}))
        _PROTECTED_CHARS = set(data.get("protegidos", []))


def _save_characters():
    path = _get_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    existing = {}
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            existing = json.load(f)
    existing["personajes"] = dict(_CHARACTERS_DATA)
    existing["protegidos"] = list(_PROTECTED_CHARS)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)


def get_characters():
    return dict(_CHARACTERS_DATA)


def get_character(cid):
    d = _CHARACTERS_DATA.get(cid)
    return copy.deepcopy(d) if d else None


def get_character_list():
    items = []
    for cid, cfg in _CHARACTERS_DATA.items():
        items.append((cid, cfg.get("nombre", cid)))
    return items


def set_character(cid, data):
    _CHARACTERS_DATA[cid] = copy.deepcopy(data)
    _save_characters()


def delete_character(cid):
    if cid in _PROTECTED_CHARS:
        return False
    if cid in _CHARACTERS_DATA:
        del _CHARACTERS_DATA[cid]
        _save_characters()
        return True
    return False


def create_character(cid):
    if cid in _CHARACTERS_DATA:
        return False
    data = {
        "nombre": cid,
        "color_texto": [255, 255, 255],
        "retratos": {},
    }
    _CHARACTERS_DATA[cid] = data
    _save_characters()
    return True


def is_protected(cid):
    return cid in _PROTECTED_CHARS
