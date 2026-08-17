# Editor de bindings de controles (data/controles.json).
#
# Formato: {"controles": [{"accion", "tecla"}]}
# El renderer "controles" del runtime lee este archivo (solo lectura).

import copy
import json
import os

from editor.project import get_current_project

_CONTROLES = []


def _get_path():
    p = get_current_project()
    return p.data_path("controles.json") if p else None


def _load_controles():
    global _CONTROLES
    _CONTROLES = []
    p = get_current_project()
    if not p:
        return
    path = p.data_path("controles.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            lista = data.get("controles")
            if isinstance(lista, list):
                _CONTROLES = lista
        except (json.JSONDecodeError, IOError):
            _CONTROLES = []


def _save_controles():
    path = _get_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"controles": _CONTROLES}, f, indent=2, ensure_ascii=False)


def get_all_controles():
    """Lista de acciones de bindings existentes."""
    return [c.get("accion", "") for c in _CONTROLES]


def get_controles():
    return copy.deepcopy(_CONTROLES)


def set_controles(lista):
    global _CONTROLES
    _CONTROLES = copy.deepcopy(lista)
    _save_controles()
    return True


def validar_controles(lista):
    """Valida bindings. Devuelve (bloqueantes, advertencias)."""
    bloq, adv = [], []
    teclas = {}
    for c in lista:
        accion = (c.get("accion") or "").strip()
        tecla = (c.get("tecla") or "").strip()
        if not accion:
            adv.append("binding sin acción")
        if not tecla:
            adv.append(f"[{accion}] sin tecla")
        if tecla and tecla in teclas and teclas[tecla] != accion:
            bloq.append(f"Tecla '{tecla}' duplicada ('{teclas[tecla]}' y '{accion}')")
        teclas[tecla] = accion
    return bloq, adv
