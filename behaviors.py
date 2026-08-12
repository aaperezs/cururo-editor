import json
import os
from copy import deepcopy
from editor.project import get_current_project

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
        _BEHAVIORS_DATA = {}
    _rebuild_constants()


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


BEHAVIORS = {}
DEFAULT_ELEMENT_PROPERTIES = {}


def _rebuild_constants():
    _ensure_loaded()
    BEHAVIORS.clear()
    BEHAVIORS.update(_BEHAVIORS_DATA)
    DEFAULT_ELEMENT_PROPERTIES.clear()
    for bid, bdata in _BEHAVIORS_DATA.items():
        DEFAULT_ELEMENT_PROPERTIES[bid] = {}
        for pkey, pdata in bdata.get("properties", {}).items():
            DEFAULT_ELEMENT_PROPERTIES[bid][pkey] = pdata.get("default")


_rebuild_constants()
