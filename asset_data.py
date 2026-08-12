import json
import os
import copy
import shutil
from editor.project import get_current_project

_ASSETS_DATA = {}


def _get_path():
    p = get_current_project()
    if p:
        return p.data_path("assets.json")
    return None


def _load_assets():
    global _ASSETS_DATA
    _ASSETS_DATA = {}
    p = get_current_project()
    if not p:
        return
    path = p.data_path("assets.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            _ASSETS_DATA = json.load(f)


def _save_assets():
    path = _get_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_ASSETS_DATA, f, indent=2, ensure_ascii=False)


def get_assets():
    return dict(_ASSETS_DATA)


def get_asset(aid):
    return copy.deepcopy(_ASSETS_DATA.get(aid))


def get_assets_by_type(tipo):
    return {k: v for k, v in _ASSETS_DATA.items() if v.get("tipo") == tipo}


def get_asset_list(tipo=None):
    items = []
    for aid, info in _ASSETS_DATA.items():
        if tipo and info.get("tipo") != tipo:
            continue
        items.append((aid, info.get("nombre", aid)))
    return sorted(items)


ASSET_TIPOS = {
    "background": "Fondo",
    "character": "Personaje",
    "cg": "CG Ilustración",
    "sprite": "Sprite",
    "icon": "Icono",
    "bgm": "Música (BGM)",
    "sfx": "Efecto de sonido (SFX)",
}

MODO_POSICION = {
    "fill": "Rellenar",
    "fit": "Ajustar",
    "center": "Centrado",
}


def import_asset(origen, aid, tipo="background", meta=None):
    """Copia un archivo al directorio assets/ del proyecto y lo registra."""
    p = get_current_project()
    if not p or not os.path.exists(origen):
        return False
    ext = os.path.splitext(origen)[1].lower()
    if ext not in (".png", ".jpg", ".jpeg", ".wav", ".ogg", ".mp3"):
        return False
    os.makedirs(p.assets_path(), exist_ok=True)
    dest = p.assets_path(f"{aid}{ext}")
    shutil.copy2(origen, dest)
    _ASSETS_DATA[aid] = {
        "nombre": meta.get("nombre", aid) if meta else aid,
        "tipo": tipo,
        "archivo": f"{aid}{ext}",
        "modo_posicion": meta.get("modo_posicion", "fill") if meta else "fill",
        "desbloqueo_flag": meta.get("desbloqueo_flag", "") if meta else "",
    }
    _save_assets()
    return True


def set_asset_meta(aid, meta):
    if aid in _ASSETS_DATA:
        _ASSETS_DATA[aid].update(meta)
        _save_assets()
        return True
    return False


def delete_asset(aid):
    if aid in _ASSETS_DATA:
        info = _ASSETS_DATA[aid]
        p = get_current_project()
        if p and info.get("archivo"):
            fpath = p.assets_path(info["archivo"])
            if os.path.exists(fpath):
                os.remove(fpath)
        del _ASSETS_DATA[aid]
        _save_assets()
        return True
    return False


def asset_path(aid):
    p = get_current_project()
    if not p:
        return None
    info = _ASSETS_DATA.get(aid)
    if not info or not info.get("archivo"):
        return None
    fpath = p.assets_path(info["archivo"])
    return fpath if os.path.exists(fpath) else None


def get_available_extensions():
    return "PNG (*.png);;JPG (*.jpg *.jpeg);;WAV (*.wav);;OGG (*.ogg);;MP3 (*.mp3)"
