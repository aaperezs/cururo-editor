import json
import os
import copy
from editor.project import get_current_project


_AUDIO_DATA = {}
_TIPOS_AUDIO = {
    "bgm": "Música de fondo",
    "sfx": "Efecto de sonido",
}


def _get_path():
    p = get_current_project()
    if p:
        return p.data_path("audio.json")
    return None


def _load_audio():
    global _AUDIO_DATA
    _AUDIO_DATA = {}
    p = get_current_project()
    if not p:
        return
    path = p.data_path("audio.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                _AUDIO_DATA = json.load(f)
        except Exception:
            _AUDIO_DATA = {}


def _save_audio():
    path = _get_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_AUDIO_DATA, f, indent=2, ensure_ascii=False)


def get_audio_list():
    items = []
    for aid, info in _AUDIO_DATA.items():
        items.append((aid, info.get("nombre", aid)))
    return sorted(items)


def get_audio(aid):
    return copy.deepcopy(_AUDIO_DATA.get(aid))


def set_audio(aid, data):
    _AUDIO_DATA[aid] = copy.deepcopy(data)
    _save_audio()


def add_audio(aid, asset_id, tipo="bgm"):
    if aid in _AUDIO_DATA:
        return False
    _AUDIO_DATA[aid] = {
        "asset_id": asset_id,
        "tipo": tipo,
        "nombre": aid,
        "volumen": 0.7,
        "loop": tipo == "bgm",
        "scene_default": "",
    }
    _save_audio()
    return True


def delete_audio(aid):
    if aid in _AUDIO_DATA:
        del _AUDIO_DATA[aid]
        _save_audio()
        return True
    return False


def get_audio_types():
    return [(k, v) for k, v in _TIPOS_AUDIO.items()]
