import copy
import json
import os

from editor.project import get_current_project

_MENUS_DATA = []


def _get_path():
    p = get_current_project()
    if p:
        return p.data_path("menus.json")
    return None


def _load_menus():
    """Carga data/menus.json del proyecto actual (si no existe, lista vacía)."""
    global _MENUS_DATA
    _MENUS_DATA = []
    p = get_current_project()
    if not p:
        return
    path = p.data_path("menus.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            menus = data.get("menus")
            if isinstance(menus, list):
                _MENUS_DATA = menus
        except (json.JSONDecodeError, IOError):
            _MENUS_DATA = []


def _save_menus():
    path = _get_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"menus": _MENUS_DATA}, f, indent=2, ensure_ascii=False)


def get_all_menus():
    return [m.get("id") for m in _MENUS_DATA]


def get_menu(mid):
    for m in _MENUS_DATA:
        if m.get("id") == mid:
            return copy.deepcopy(m)
    return None


def set_menu(mid, data):
    entry = copy.deepcopy(data)
    entry["id"] = mid
    for i, m in enumerate(_MENUS_DATA):
        if m.get("id") == mid:
            _MENUS_DATA[i] = entry
            _save_menus()
            return True
    _MENUS_DATA.append(entry)
    _save_menus()
    return True


def delete_menu(mid):
    for i, m in enumerate(_MENUS_DATA):
        if m.get("id") == mid:
            del _MENUS_DATA[i]
            _save_menus()
            return True
    return False


def menu_exists(mid):
    return mid in get_all_menus()


def create_menu(mid):
    if menu_exists(mid):
        return False
    _MENUS_DATA.append({
        "id": mid,
        "tecla": "",
        "titulo": mid.upper(),
        "apartados": [
            {"id": "apartado_1", "nombre": "Apartado 1", "tipo": "lista"},
        ],
    })
    _save_menus()
    return True


def rename_menu(old_id, new_id):
    if old_id == new_id:
        return True
    if new_id in get_all_menus():
        return False
    for m in _MENUS_DATA:
        if m.get("id") == old_id:
            m["id"] = new_id
            _save_menus()
            return True
    return False