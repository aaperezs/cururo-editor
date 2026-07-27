import copy
import json
import os

from editor.project import get_current_project

_ANIMS_DATA = {}


def _get_path():
    p = get_current_project()
    if p:
        return p.data_path("animations.json")
    return None


def _load():
    global _ANIMS_DATA
    _ANIMS_DATA = {}
    p = get_current_project()
    if not p:
        return
    path = p.data_path("animations.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _ANIMS_DATA.update(json.load(f))


def _save():
    path = _get_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_ANIMS_DATA, f, indent=2, ensure_ascii=False)


def get_all():
    return sorted(_ANIMS_DATA.keys())


def get(name):
    d = _ANIMS_DATA.get(name)
    return copy.deepcopy(d) if d else None


def set(name, data):
    _ANIMS_DATA[name] = copy.deepcopy(data)
    _save()


def delete(name):
    if name in _ANIMS_DATA:
        del _ANIMS_DATA[name]
        _save()
        return True
    return False


def create(name):
    if name in _ANIMS_DATA:
        return False
    data = {
        "frames": [],
        "interval": 500,
    }
    _ANIMS_DATA[name] = data
    _save()
    return True


def get_names():
    items = []
    for name, cfg in _ANIMS_DATA.items():
        label = f"{name} ({cfg.get('interval', 500)}ms)"
        items.append((name, label))
    return items
