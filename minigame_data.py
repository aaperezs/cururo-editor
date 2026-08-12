import json
import os
import copy
from editor.project import get_current_project


_MINIGAMES_DATA = {}


def _get_path():
    p = get_current_project()
    if p:
        return p.data_path("minijuegos.json")
    return None


def _load_minigames():
    global _MINIGAMES_DATA
    _MINIGAMES_DATA = {}
    p = get_current_project()
    if not p:
        return
    path = p.data_path("minijuegos.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                _MINIGAMES_DATA = json.load(f)
        except Exception:
            _MINIGAMES_DATA = {}


def _save_minigames():
    path = _get_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_MINIGAMES_DATA, f, indent=2, ensure_ascii=False)


TIPOS_MINIJUEGO = {
    "recoleccion": "Recolección",
    "timing": "Timing",
    "puzzle": "Puzzle",
}


def get_minigames():
    return copy.deepcopy(_MINIGAMES_DATA)


def get_minigame(mid):
    return copy.deepcopy(_MINIGAMES_DATA.get(mid))


def set_minigame(mid, data):
    _MINIGAMES_DATA[mid] = copy.deepcopy(data)
    _save_minigames()


def add_minigame(mid=None, tipo="recoleccion"):
    if not mid:
        n = 1
        while f"minijuego_{n}" in _MINIGAMES_DATA:
            n += 1
        mid = f"minijuego_{n}"
    if mid in _MINIGAMES_DATA:
        return False
    if tipo == "recoleccion":
        _MINIGAMES_DATA[mid] = {
            "tipo": "recoleccion",
            "nombre": mid,
            "tiempo_limite": 30,
            "objetivo": 10,
            "items": [
                {"x": 150, "y": 150, "radio": 20, "puntos": 1, "color": [200, 200, 50]},
                {"x": 400, "y": 200, "radio": 20, "puntos": 1, "color": [200, 200, 50]},
                {"x": 650, "y": 300, "radio": 20, "puntos": 1, "color": [200, 200, 50]},
            ],
            "flags_resultado": {f"{mid}_completado": True},
        }
    elif tipo == "timing":
        _MINIGAMES_DATA[mid] = {
            "tipo": "timing",
            "nombre": mid,
            "secuencia": [
                {"tecla": "SPACE", "tiempo_ms": 2000, "ventana_ms": 400},
                {"tecla": "UP", "tiempo_ms": 4000, "ventana_ms": 400},
                {"tecla": "SPACE", "tiempo_ms": 6000, "ventana_ms": 400},
            ],
            "flags_resultado": {f"{mid}_completado": True},
        }
    elif tipo == "puzzle":
        _MINIGAMES_DATA[mid] = {
            "tipo": "puzzle",
            "nombre": mid,
            "grid": [3, 3],
            "tile_size": 80,
            "flags_resultado": {f"{mid}_completado": True},
        }
    _save_minigames()
    return True


def delete_minigame(mid):
    if mid in _MINIGAMES_DATA:
        del _MINIGAMES_DATA[mid]
        _save_minigames()
        return True
    return False


def get_minigame_types():
    return [(k, v) for k, v in TIPOS_MINIJUEGO.items()]
