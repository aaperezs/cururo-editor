import json
import os
import copy
from editor.project import get_current_project


_SCENES_DATA = []
_TITLE_DATA = {}


def _get_path():
    p = get_current_project()
    if p:
        return p.data_path("scenes.json")
    return None


def _load_scenes():
    global _SCENES_DATA, _TITLE_DATA
    _SCENES_DATA = []
    _TITLE_DATA = {}
    p = get_current_project()
    if not p:
        return
    path = p.data_path("scenes.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        _SCENES_DATA = raw.get("chapters", [])
        _TITLE_DATA = raw.get("titulo", {})


def _save_scenes():
    path = _get_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    payload = {"chapters": _SCENES_DATA, "titulo": _TITLE_DATA}
    with open(path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2, ensure_ascii=False)


TIPO_ESCENA = {
    "dialogo": "Diálogo",
    "minijuego": "Minijuego",
    "cg": "CG Ilustración",
    "ending": "Final",
}


def get_chapters():
    return copy.deepcopy(_SCENES_DATA)


def get_chapter(cidx):
    if 0 <= cidx < len(_SCENES_DATA):
        return copy.deepcopy(_SCENES_DATA[cidx])
    return None


def set_chapter(cidx, data):
    if 0 <= cidx < len(_SCENES_DATA):
        _SCENES_DATA[cidx] = copy.deepcopy(data)
        _save_scenes()
        return True
    return False


def add_chapter(cid=None, nombre=None):
    if not cid:
        n = 1
        while any(ch.get("id") == f"capitulo_{n}" for ch in _SCENES_DATA):
            n += 1
        cid = f"capitulo_{n}"
    if any(ch.get("id") == cid for ch in _SCENES_DATA):
        return False
    _SCENES_DATA.append({
        "id": cid,
        "nombre": nombre or cid,
        "escenas": [],
    })
    _save_scenes()
    return True


def delete_chapter(cidx):
    if 0 <= cidx < len(_SCENES_DATA):
        del _SCENES_DATA[cidx]
        _save_scenes()
        return True
    return False


def move_chapter(cidx, direction):
    ni = cidx + direction
    if 0 <= ni < len(_SCENES_DATA):
        _SCENES_DATA[cidx], _SCENES_DATA[ni] = _SCENES_DATA[ni], _SCENES_DATA[cidx]
        _save_scenes()
        return True
    return False


def get_scenes(cidx):
    if 0 <= cidx < len(_SCENES_DATA):
        return copy.deepcopy(_SCENES_DATA[cidx].get("escenas", []))
    return []


def get_scene(cidx, sidx):
    scenes = get_scenes(cidx)
    if 0 <= sidx < len(scenes):
        return scenes[sidx]
    return None


def set_scene(cidx, sidx, data):
    if 0 <= cidx < len(_SCENES_DATA):
        scenes = _SCENES_DATA[cidx].get("escenas", [])
        if 0 <= sidx < len(scenes):
            scenes[sidx] = copy.deepcopy(data)
            _save_scenes()
            return True
    return False


def add_scene(cidx, tipo="dialogo"):
    if 0 <= cidx < len(_SCENES_DATA):
        n = len(_SCENES_DATA[cidx].get("escenas", [])) + 1
        sid = f"escena_{n}"
        scenes = _SCENES_DATA[cidx].setdefault("escenas", [])
        scenes.append({
            "id": sid,
            "tipo": tipo,
            "dialogo_id": "",
            "nivel_id": "",
            "asset_id": "",
            "condicion_entrada": {},
        })
        _save_scenes()
        return sid
    return None


def delete_scene(cidx, sidx):
    if 0 <= cidx < len(_SCENES_DATA):
        scenes = _SCENES_DATA[cidx].get("escenas", [])
        if 0 <= sidx < len(scenes):
            del scenes[sidx]
            _save_scenes()
            return True
    return False


def move_scene(cidx, sidx, direction):
    ni = sidx + direction
    if 0 <= cidx < len(_SCENES_DATA):
        scenes = _SCENES_DATA[cidx].get("escenas", [])
        if 0 <= ni < len(scenes):
            scenes[sidx], scenes[ni] = scenes[ni], scenes[sidx]
            _save_scenes()
            return True
    return False


def get_title_data():
    return copy.deepcopy(_TITLE_DATA)


def set_title_data(data):
    global _TITLE_DATA
    _TITLE_DATA.update(data)
    _save_scenes()


def get_available_scene_types():
    return [(k, v) for k, v in TIPO_ESCENA.items()]


ENUM_SCENE_TYPES = {
    "dialogo": {"fields": ["dialogo_id"]},
    "minijuego": {"fields": ["nivel_id"]},
    "cg": {"fields": ["asset_id"]},
    "ending": {"fields": []},
}
