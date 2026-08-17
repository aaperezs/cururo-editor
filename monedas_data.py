# Editor de monedas (contadores de primera clase, data/monedas.json).
#
# Formato: {"monedas": [{"id", "label", "valor_inicial", "icono", "color", "principal"}]}
# - principal: máximo 1 moneda principal por juego.
# - El runtime lee este archivo vía RepositorioMonedas; la moneda "escamas"
#   se mantiene ligada a la snake (shim) mientras "escamas == largo" siga siendo un tema aparte.

import copy
import json
import os

from editor.project import get_current_project

_MONEDAS = []


def _get_path():
    p = get_current_project()
    return p.data_path("monedas.json") if p else None


def _load_monedas():
    global _MONEDAS
    _MONEDAS = []
    p = get_current_project()
    if not p:
        return
    path = p.data_path("monedas.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            lista = data.get("monedas")
            if isinstance(lista, list):
                _MONEDAS = lista
        except (json.JSONDecodeError, IOError):
            _MONEDAS = []


def _save_monedas():
    path = _get_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"monedas": _MONEDAS}, f, indent=2, ensure_ascii=False)


def get_all_monedas():
    """Lista de ids de monedas existentes."""
    return [m.get("id", "") for m in _MONEDAS]


def get_monedas():
    return copy.deepcopy(_MONEDAS)


def get_moneda(mid):
    for m in _MONEDAS:
        if m.get("id") == mid:
            return copy.deepcopy(m)
    return None


def set_moneda(mid, data):
    entry = copy.deepcopy(data)
    entry["id"] = mid
    for i, m in enumerate(_MONEDAS):
        if m.get("id") == mid:
            _MONEDAS[i] = entry
            _save_monedas()
            return True
    _MONEDAS.append(entry)
    _save_monedas()
    return True


def set_monedas(lista):
    """Reemplaza toda la lista de monedas y guarda en disco."""
    global _MONEDAS
    _MONEDAS = copy.deepcopy(lista)
    _save_monedas()
    return True


def delete_moneda(mid):
    for i, m in enumerate(_MONEDAS):
        if m.get("id") == mid:
            del _MONEDAS[i]
            _save_monedas()
            return True
    return False


def moneda_exists(mid):
    return mid in get_all_monedas()


def validar_monedas(lista):
    """Valida monedas. Devuelve (bloqueantes, advertencias)."""
    bloq, adv = [], []
    ids = set()
    principal_contados = 0
    for m in lista:
        mid = (m.get("id") or "").strip()
        if not mid:
            bloq.append("moneda sin id")
            continue
        if mid in ids:
            bloq.append(f"id de moneda duplicado '{mid}'")
        ids.add(mid)

        label = (m.get("label") or "").strip()
        if not label:
            adv.append(f"[{mid}] sin label (se usará el id)")

        vi = m.get("valor_inicial", 0)
        if not isinstance(vi, int):
            bloq.append(f"[{mid}] valor_inicial debe ser un entero")
        elif vi < 0:
            bloq.append(f"[{mid}] valor_inicial no puede ser negativo")

        color = m.get("color")
        if not isinstance(color, list) or len(color) != 3:
            bloq.append(f"[{mid}] color debe ser [r, g, b]")
        else:
            for canal in color:
                if not isinstance(canal, int) or not (0 <= canal <= 255):
                    bloq.append(f"[{mid}] canales de color deben ser enteros 0-255")
                    break

        if m.get("principal"):
            principal_contados += 1

    if principal_contados > 1:
        bloq.append("solo puede haber una moneda principal")
    return bloq, adv