import os
import json
from editor.project import get_current_project

_cache = None


def _get_path():
    p = get_current_project()
    return p.data_path("bosses.json") if p else None


def _load():
    global _cache
    if _cache is None:
        path = _get_path()
        if path and os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                _cache = json.load(f)
        else:
            _cache = {}
    return _cache


def _save():
    path = _get_path()
    if not path:
        return
    with open(path, "w", encoding="utf-8") as f:
        json.dump(_cache, f, indent=2, ensure_ascii=False)


def get_all_bosses():
    data = _load()
    return sorted(data.keys())


def get_boss(boss_id):
    data = _load()
    return data.get(boss_id)


def set_boss(boss_id, config):
    data = _load()
    data[boss_id] = config
    _save()


def delete_boss(boss_id):
    data = _load()
    if boss_id in data:
        del data[boss_id]
        _save()


def create_boss(boss_id):
    data = _load()
    if boss_id in data:
        return False
    from editor.boss_fight_types import get_default_phase
    data[boss_id] = {
        "color": [100, 100, 100],
        "color_herido": [200, 50, 50],
        "nombre": boss_id,
        "vida_maxima": 80,
        "color_barra": [0, 200, 50],
        "icono": "?",
        "fight_type": "orbital",
        "proyectiles_necesarios": 3,
        "damage_per_cycle": 20,
        "phases": [
            get_default_phase("orbital")
        ]
    }
    _save()
    return True
