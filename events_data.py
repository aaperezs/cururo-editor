# Editor de eventos globales (data/eventos_globales.json).
#
# Eventos que afectan el estado global del juego, con el mismo patrón que
# los eventos del mapa: trigger → condiciones → acciones.
#
#   evento: {
#     event_id, trigger, boss_id?, watched_event_id?,
#     condiciones: [{tipo, params}],
#     acciones: [{tipo, params}],
#     once
#   }
#
# Triggers soportados (sin posición en el mapa):
#   - on_boss_defeated:   se dispara al derrotar un boss (usa boss_id)
#   - on_event_finalized: se dispara cuando un evento de mapa finaliza
#                         (usa watched_event_id)
#
# Acciones que afectan tiendas (params.shop_id desde la lista de tiendas):
#   - restock_shop       { shop_id, item_id? }        item vacío => toda la tienda
#   - add_shop_stock     { shop_id, item_id, cantidad }
#   - modify_shop_price  { shop_id, item_id, moneda, precio }

import copy
import json
import os

from editor.project import get_current_project

_EVENTOS_GLOBALES = []

# ── Triggers soportados ───────────────────────────────────────

GLOBAL_TRIGGERS = ["on_boss_defeated", "on_event_finalized"]

# ── Acciones que afectan tiendas ──────────────────────────────

GLOBAL_ACTION_TYPES = {
    "restock_shop": {
        "label": "Restockear Tienda",
        "params": {"shop_id": "", "item_id": ""},
    },
    "add_shop_stock": {
        "label": "Agregar Stock",
        "params": {"shop_id": "", "item_id": "", "cantidad": 1},
    },
    "modify_shop_price": {
        "label": "Modificar Precio",
        "params": {"shop_id": "", "item_id": "", "moneda": "", "precio": 0},
    },
}


def get_global_action_types():
    """Lista (id, label) para dropdown de acciones."""
    return [(k, v["label"]) for k, v in GLOBAL_ACTION_TYPES.items()]


def get_global_action_params(tipo):
    """Devuelve un dict de params base para el tipo de acción."""
    info = GLOBAL_ACTION_TYPES.get(tipo)
    if not info:
        return {}
    return copy.deepcopy(info["params"])


def get_global_triggers():
    """Lista de triggers soportados."""
    return GLOBAL_TRIGGERS


# ── Persistencia ──────────────────────────────────────────────

def _get_path():
    p = get_current_project()
    return p.data_path("eventos_globales.json") if p else None


def _load_eventos_globales():
    global _EVENTOS_GLOBALES
    _EVENTOS_GLOBALES = []
    p = get_current_project()
    if not p:
        return
    path = p.data_path("eventos_globales.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            lista = data.get("eventos")
            if isinstance(lista, list):
                _EVENTOS_GLOBALES = lista
        except (json.JSONDecodeError, IOError):
            _EVENTOS_GLOBALES = []


def _save_eventos_globales():
    path = _get_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"eventos": _EVENTOS_GLOBALES}, f, indent=2, ensure_ascii=False)


# ── API pública ───────────────────────────────────────────────

def get_all_eventos_globales():
    """Lista de event_ids de eventos globales."""
    return [e.get("event_id", "") for e in _EVENTOS_GLOBALES]


def get_eventos_globales():
    return copy.deepcopy(_EVENTOS_GLOBALES)


def get_evento_global(eid):
    for e in _EVENTOS_GLOBALES:
        if e.get("event_id") == eid:
            return copy.deepcopy(e)
    return None


def set_evento_global(eid, data):
    entry = copy.deepcopy(data)
    entry["event_id"] = eid
    for i, e in enumerate(_EVENTOS_GLOBALES):
        if e.get("event_id") == eid:
            _EVENTOS_GLOBALES[i] = entry
            _save_eventos_globales()
            return True
    _EVENTOS_GLOBALES.append(entry)
    _save_eventos_globales()
    return True


def set_eventos_globales(lista):
    global _EVENTOS_GLOBALES
    _EVENTOS_GLOBALES = copy.deepcopy(lista)
    _save_eventos_globales()
    return True


def delete_evento_global(eid):
    for i, e in enumerate(_EVENTOS_GLOBALES):
        if e.get("event_id") == eid:
            del _EVENTOS_GLOBALES[i]
            _save_eventos_globales()
            return True
    return False


def evento_global_exists(eid):
    return eid in get_all_eventos_globales()


# ── Validación ────────────────────────────────────────────────

def validar_eventos_globales(lista):
    """Valida eventos globales. Devuelve (bloqueantes, advertencias)."""
    bloq, adv = [], []
    ids = set()

    for e in lista:
        eid = (e.get("event_id") or "").strip()
        if not eid:
            bloq.append("evento sin event_id")
            continue
        if eid in ids:
            bloq.append(f"event_id duplicado '{eid}'")
        ids.add(eid)

        trigger = e.get("trigger", "")
        if trigger not in GLOBAL_TRIGGERS:
            bloq.append(f"[{eid}] trigger '{trigger}' no soportado")
        elif trigger == "on_boss_defeated":
            if not (e.get("boss_id") or "").strip():
                bloq.append(f"[{eid}] trigger on_boss_defeated requiere boss_id")
        elif trigger == "on_event_finalized":
            if not (e.get("watched_event_id") or "").strip():
                bloq.append(f"[{eid}] trigger on_event_finalized requiere watched_event_id")

        condiciones = e.get("condiciones", [])
        if not isinstance(condiciones, list):
            bloq.append(f"[{eid}] condiciones debe ser lista")

        acciones = e.get("acciones", [])
        if not isinstance(acciones, list):
            bloq.append(f"[{eid}] acciones debe ser lista")
        elif not acciones:
            adv.append(f"[{eid}] sin acciones")
        else:
            for idx, acc in enumerate(acciones):
                if not isinstance(acc, dict):
                    bloq.append(f"[{eid}] acción #{idx} debe ser dict")
                    continue
                b, a = _validar_accion(acc, idx, eid)
                bloq.extend(b)
                adv.extend(a)

    return bloq, adv


def _validar_accion(acc, idx, eid):
    """Valida una acción. Devuelve (bloqueantes, advertencias)."""
    bloq, adv = [], []
    tipo = acc.get("tipo", "")
    if tipo not in GLOBAL_ACTION_TYPES:
        bloq.append(f"[{eid}] acción #{idx} tipo '{tipo}' no soportado")
        return bloq, adv

    params = acc.get("params", {})
    if not isinstance(params, dict):
        bloq.append(f"[{eid}] acción #{idx} params debe ser dict")
        return bloq, adv

    from editor.shops_data import _load_shops, get_all_shops, get_shop
    from editor.monedas_data import _load_monedas, get_all_monedas
    _load_shops()
    _load_monedas()
    tiendas_validas = set(get_all_shops())
    monedas_validas = set(get_all_monedas())

    shop_id = params.get("shop_id", "")
    if not shop_id:
        bloq.append(f"[{eid}] acción #{idx} requiere shop_id")
    elif shop_id not in tiendas_validas:
        bloq.append(f"[{eid}] acción #{idx} shop '{shop_id}' no existe")
    else:
        shop = get_shop(shop_id)
        if shop:
            shop_items = {it.get("item_id") for it in shop.get("items", [])}
            if tipo in ("add_shop_stock", "modify_shop_price"):
                item_id = params.get("item_id", "")
                if not item_id:
                    bloq.append(f"[{eid}] acción #{idx} requiere item_id")
                elif item_id not in shop_items:
                    bloq.append(f"[{eid}] acción #{idx} item '{item_id}' no está en shop '{shop_id}'")
            elif tipo == "restock_shop":
                item_id = params.get("item_id", "")
                if item_id and item_id not in shop_items:
                    bloq.append(f"[{eid}] acción #{idx} item '{item_id}' no está en shop '{shop_id}'")

    if tipo == "add_shop_stock":
        cantidad = params.get("cantidad")
        if not isinstance(cantidad, int) or cantidad < 1:
            bloq.append(f"[{eid}] acción #{idx} cantidad debe ser entero >= 1")

    if tipo == "modify_shop_price":
        moneda = params.get("moneda", "")
        if not moneda:
            bloq.append(f"[{eid}] acción #{idx} requiere moneda")
        elif moneda not in monedas_validas:
            bloq.append(f"[{eid}] acción #{idx} moneda '{moneda}' no existe")
        precio = params.get("precio")
        if not isinstance(precio, int) or precio < 0:
            bloq.append(f"[{eid}] acción #{idx} precio debe ser entero >= 0")

    return bloq, adv
