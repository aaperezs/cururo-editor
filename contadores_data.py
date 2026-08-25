# Editor de contadores de progresión (data/contadores.json).
#
# Formato: {"contadores": [{"id", "nombre", "inicial", "maximo", "descripcion"}]}

import copy
import json
import os

from editor.project import get_current_project

_CONTADORES = []


def _get_path():
    p = get_current_project()
    return p.data_path("contadores.json") if p else None


def _load_contadores():
    global _CONTADORES
    _CONTADORES = []
    p = get_current_project()
    if not p:
        return
    path = p.data_path("contadores.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            lista = data.get("contadores")
            if isinstance(lista, list):
                _CONTADORES = lista
        except (json.JSONDecodeError, IOError):
            _CONTADORES = []


def _save_contadores():
    path = _get_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"contadores": _CONTADORES}, f, indent=2, ensure_ascii=False)


def get_all_contadores():
    """Lista de ids de contadores existentes."""
    return [c.get("id", "") for c in _CONTADORES]


def get_contadores():
    return copy.deepcopy(_CONTADORES)


def get_contador(cid):
    for c in _CONTADORES:
        if c.get("id") == cid:
            return copy.deepcopy(c)
    return None


def set_contador(cid, data):
    entry = copy.deepcopy(data)
    entry["id"] = cid
    for i, c in enumerate(_CONTADORES):
        if c.get("id") == cid:
            _CONTADORES[i] = entry
            _save_contadores()
            return True
    _CONTADORES.append(entry)
    _save_contadores()
    return True


def set_contadores(lista):
    global _CONTADORES
    _CONTADORES = copy.deepcopy(lista)
    _save_contadores()
    return True


def delete_contador(cid):
    for i, c in enumerate(_CONTADORES):
        if c.get("id") == cid:
            del _CONTADORES[i]
            _save_contadores()
            return True
    return False


def contador_exists(cid):
    return cid in get_all_contadores()


def validar_contadores(lista):
    """Valida contadores. Devuelve (bloqueantes, advertencias)."""
    bloq, adv = [], []
    ids = set()
    for c in lista:
        cid = (c.get("id") or "").strip()
        if not cid:
            bloq.append("contador sin id")
            continue
        if cid in ids:
            bloq.append(f"id de contador duplicado '{cid}'")
        ids.add(cid)

        nombre = (c.get("nombre") or "").strip()
        if not nombre:
            adv.append(f"[{cid}] sin nombre (se usará el id)")

        vi = c.get("inicial", 0)
        if not isinstance(vi, int):
            bloq.append(f"[{cid}] inicial debe ser un entero")
        elif vi < 0:
            bloq.append(f"[{cid}] inicial no puede ser negativo")

        maximo = c.get("maximo", 999999)
        if not isinstance(maximo, int):
            bloq.append(f"[{cid}] maximo debe ser un entero")
        elif maximo < vi:
            bloq.append(f"[{cid}] maximo debe ser >= inicial")

        desc = c.get("descripcion", "")
        if not isinstance(desc, str):
            adv.append(f"[{cid}] descripcion debe ser texto")

    return bloq, adv