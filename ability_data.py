import json
import os
import copy
from editor.project import get_current_project

_ABILITIES_DATA = {}
_SKINS_DATA = {}
_PROTECTED_ABILITIES = {"base"}


def _get_path():
    p = get_current_project()
    if p:
        return p.data_path("habilidades.json")
    return None


def _load_abilities():
    global _ABILITIES_DATA, _SKINS_DATA
    _ABILITIES_DATA = {}
    _SKINS_DATA = {}
    p = get_current_project()
    if not p:
        return
    path = p.data_path("habilidades.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        _ABILITIES_DATA.update(data.get("habilidades", {}))
        _SKINS_DATA.update(data.get("skins", {}))


def _save_abilities():
    path = _get_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "r", encoding="utf-8") as f:
        existing = json.load(f)
    existing["habilidades"] = dict(_ABILITIES_DATA)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, indent=2, ensure_ascii=False)


def get_abilities():
    return dict(_ABILITIES_DATA)


def get_ability(hid):
    d = _ABILITIES_DATA.get(hid)
    return copy.deepcopy(d) if d else None


def get_ability_list():
    items = []
    for hid, cfg in _ABILITIES_DATA.items():
        items.append((hid, cfg.get("nombre", hid)))
    return items


def get_skin_list():
    return [(sid, sid) for sid in _SKINS_DATA.keys()]


def set_ability(hid, data):
    _ABILITIES_DATA[hid] = copy.deepcopy(data)
    _save_abilities()


def delete_ability(hid):
    if hid in _PROTECTED_ABILITIES:
        return False
    if hid in _ABILITIES_DATA:
        del _ABILITIES_DATA[hid]
        _save_abilities()
        return True
    return False


def create_ability(hid):
    if hid in _ABILITIES_DATA:
        return False
    data = {
        "nombre": hid,
        "descripcion": "",
        "pp_max": 3,
        "color": [0, 255, 0],
        "tecla": "Q",
        "efecto": "base",
        "skin": "base",
    }
    _ABILITIES_DATA[hid] = data
    _save_abilities()
    return True


def is_protected(hid):
    return hid in _PROTECTED_ABILITIES
