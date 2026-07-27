import json
import os
import copy
from editor.project import get_current_project

_DIALOGOS_DATA = {}


def _get_path():
    p = get_current_project()
    if p:
        return p.data_path("dialogos.json")
    return None


def _load_dialogos():
    global _DIALOGOS_DATA
    _DIALOGOS_DATA = {}
    p = get_current_project()
    if not p:
        return
    path = p.data_path("dialogos.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _DIALOGOS_DATA = json.load(f)


def _save_dialogos():
    path = _get_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_DIALOGOS_DATA, f, indent=2, ensure_ascii=False)


def _parse_key(key):
    if "/" in key:
        parts = key.split("/", 1)
        return parts[0], parts[1]
    return key, ""


def _make_key(personaje, contexto):
    return f"{personaje}/{contexto}"


def get_all_dialogo_keys():
    keys = []
    for personaje, contextos in _DIALOGOS_DATA.items():
        for contexto in contextos:
            keys.append(_make_key(personaje, contexto))
    return sorted(keys)


def get_all_personajes():
    return sorted(_DIALOGOS_DATA.keys())


def get_contextos(personaje):
    d = _DIALOGOS_DATA.get(personaje, {})
    return sorted(d.keys())


def get_dialogo(personaje, contexto):
    d = _DIALOGOS_DATA.get(personaje, {}).get(contexto)
    return copy.deepcopy(d) if d else None


def get_dialogo_by_key(key):
    personaje, contexto = _parse_key(key)
    return get_dialogo(personaje, contexto)


def set_dialogo(personaje, contexto, lineas):
    if personaje not in _DIALOGOS_DATA:
        _DIALOGOS_DATA[personaje] = {}
    _DIALOGOS_DATA[personaje][contexto] = list(lineas)
    _save_dialogos()


def set_dialogo_by_key(key, lineas):
    personaje, contexto = _parse_key(key)
    set_dialogo(personaje, contexto, lineas)


def delete_dialogo(personaje, contexto):
    if personaje in _DIALOGOS_DATA and contexto in _DIALOGOS_DATA[personaje]:
        del _DIALOGOS_DATA[personaje][contexto]
        if not _DIALOGOS_DATA[personaje]:
            del _DIALOGOS_DATA[personaje]
        _save_dialogos()
        return True
    return False


def delete_dialogo_by_key(key):
    personaje, contexto = _parse_key(key)
    return delete_dialogo(personaje, contexto)


def dialogo_exists(personaje, contexto):
    return personaje in _DIALOGOS_DATA and contexto in _DIALOGOS_DATA[personaje]


def dialogo_exists_by_key(key):
    personaje, contexto = _parse_key(key)
    return dialogo_exists(personaje, contexto)


def create_dialogo(personaje, contexto):
    if personaje not in _DIALOGOS_DATA:
        _DIALOGOS_DATA[personaje] = {}
    if contexto in _DIALOGOS_DATA[personaje]:
        return False
    _DIALOGOS_DATA[personaje][contexto] = ["Nueva linea"]
    _save_dialogos()
    return True


def create_dialogo_by_key(key):
    personaje, contexto = _parse_key(key)
    return create_dialogo(personaje, contexto)


def rename_dialogo(old_key, new_key):
    if old_key == new_key:
        return True
    old_p, old_c = _parse_key(old_key)
    new_p, new_c = _parse_key(new_key)
    if old_p not in _DIALOGOS_DATA or old_c not in _DIALOGOS_DATA[old_p]:
        return False
    if new_p in _DIALOGOS_DATA and new_c in _DIALOGOS_DATA[new_p]:
        return False
    lineas = _DIALOGOS_DATA[old_p].pop(old_c)
    if not _DIALOGOS_DATA[old_p]:
        del _DIALOGOS_DATA[old_p]
    if new_p not in _DIALOGOS_DATA:
        _DIALOGOS_DATA[new_p] = {}
    _DIALOGOS_DATA[new_p][new_c] = lineas
    _save_dialogos()
    return True
