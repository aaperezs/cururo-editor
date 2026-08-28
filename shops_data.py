# Editor de tiendas (data/shops.json).
#
# Formato: {"shops": [{...}]}
#
# Estructura v2:
#   tienda: { shop_id, nombre, descripcion, moneda_principal, items }
#   item:   { item_id, precio, stock_infinito, stock? }
#
# La tienda SOLO tiene datos de tienda. El restock/unlock de items lo
# manejan los eventos globales (eventos_globales.json) vía acciones que
# apuntan por shop_id.
#
# Migración automática v1→v2 al cargar.

import copy
import datetime
import json
import os
import shutil

from editor.project import get_current_project
from editor.monedas_data import get_all_monedas
from editor.items_data import get_all_items

_SHOPS = []


# ── Persistencia ──────────────────────────────────────────────

def _get_path():
    p = get_current_project()
    return p.data_path("shops.json") if p else None


def _load_shops():
    global _SHOPS
    _SHOPS = []
    p = get_current_project()
    if not p:
        return
    path = p.data_path("shops.json")
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            lista = data.get("shops")
            if isinstance(lista, list):
                # Migración automática v1→v2
                if lista and _es_version_1(lista):
                    backup = path + f".backup_{datetime.datetime.now():%Y%m%d_%H%M%S}"
                    shutil.copy2(path, backup)
                    lista = [migrar_shop_v1_a_v2(s) for s in lista]
                    # Guardar v2
                    with open(path, "w", encoding="utf-8") as f:
                        json.dump({"shops": lista}, f, indent=2, ensure_ascii=False)
                _SHOPS = lista
        except (json.JSONDecodeError, IOError):
            _SHOPS = []


def _save_shops():
    path = _get_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump({"shops": _SHOPS}, f, indent=2, ensure_ascii=False)


# ── API pública ───────────────────────────────────────────────

def get_all_shops():
    return [s.get("shop_id", "") for s in _SHOPS]


def get_shops():
    return copy.deepcopy(_SHOPS)


def get_shop(shop_id):
    for s in _SHOPS:
        if s.get("shop_id") == shop_id:
            return copy.deepcopy(s)
    return None


def set_shop(shop_id, data):
    entry = copy.deepcopy(data)
    entry["shop_id"] = shop_id
    for i, s in enumerate(_SHOPS):
        if s.get("shop_id") == shop_id:
            _SHOPS[i] = entry
            _save_shops()
            return True
    _SHOPS.append(entry)
    _save_shops()
    return True


def set_shops(lista):
    global _SHOPS
    _SHOPS = copy.deepcopy(lista)
    _save_shops()
    return True


def delete_shop(shop_id):
    for i, s in enumerate(_SHOPS):
        if s.get("shop_id") == shop_id:
            del _SHOPS[i]
            _save_shops()
            return True
    return False


def shop_exists(shop_id):
    return shop_id in get_all_shops()


# ── Migración v1 → v2 ────────────────────────────────────────

_V1_MARKERS = ["id", "categorias", "compra"]
_V1_ITEM_MARKERS = ["max_stock", "max_stack", "restock",
                    "visible_si_bloqueado", "moneda_compra", "unlock"]


def _es_version_1(lista_shops):
    """Detecta si la lista de tiendas es v1 (usa 'id' o campos v1)."""
    for s in lista_shops:
        if s.get("id") is not None and s.get("shop_id") is None:
            return True
        for item in s.get("items", []):
            if any(k in item for k in _V1_ITEM_MARKERS):
                return True
    return False


def migrar_shop_v1_a_v2(shop):
    """Migra una tienda v1 a v2. Función pura."""
    shop = copy.deepcopy(shop)
    if shop.get("id") is not None and shop.get("shop_id") is None:
        shop["shop_id"] = shop.pop("id")
    shop.pop("categorias", None)
    shop.pop("compra", None)

    for item in shop.get("items", []):
        _migrar_item_v1_a_v2(item)

    return shop


def _migrar_item_v1_a_v2(item):
    """Migra un item v1 a v2."""
    item.setdefault("stock_infinito", False)
    for k in _V1_ITEM_MARKERS:
        item.pop(k, None)


# ── Validación v2 ─────────────────────────────────────────────

def validar_shops(lista):
    """Valida tiendas v2. Devuelve (bloqueantes, advertencias)."""
    bloq, adv = [], []
    ids = set()
    from editor.monedas_data import _load_monedas
    from editor.items_data import _load_items
    _load_monedas()
    _load_items()
    monedas_validas = set(get_all_monedas())
    items_validos = set(get_all_items())

    for s in lista:
        sid = (s.get("shop_id") or "").strip()
        if not sid:
            bloq.append("tienda sin shop_id")
            continue
        if sid in ids:
            bloq.append(f"shop_id duplicado '{sid}'")
        ids.add(sid)

        nombre = (s.get("nombre") or "").strip()
        if not nombre:
            adv.append(f"[{sid}] sin nombre (se usará el shop_id)")

        moneda_ppal = s.get("moneda_principal", "")
        if moneda_ppal and moneda_ppal not in monedas_validas:
            bloq.append(f"[{sid}] moneda_principal '{moneda_ppal}' no existe en monedas.json")

        items = s.get("items", [])
        if not isinstance(items, list):
            bloq.append(f"[{sid}] items debe ser lista")
        else:
            for idx, item in enumerate(items):
                b, a = _validar_item_v2(item, idx, sid, monedas_validas, items_validos)
                bloq.extend(b)
                adv.extend(a)

    return bloq, adv


def _validar_item_v2(item, idx, sid, monedas_validas, items_validos):
    """Valida un item v2."""
    bloq, adv = [], []

    item_id = item.get("item_id", "")
    if not item_id:
        bloq.append(f"[{sid}] item #{idx} sin item_id")
        return bloq, adv
    if item_id not in items_validos:
        adv.append(f"[{sid}] item '{item_id}' no existe en items.json")

    precio = item.get("precio", {})
    if not isinstance(precio, dict) or not precio:
        bloq.append(f"[{sid}] item '{item_id}' precio debe ser dict no vacío")
    else:
        for moneda, valor in precio.items():
            if moneda not in monedas_validas:
                bloq.append(f"[{sid}] item '{item_id}' moneda '{moneda}' no existe")
            if not isinstance(valor, int) or valor < 0:
                bloq.append(f"[{sid}] item '{item_id}' precio en '{moneda}' debe ser entero >= 0")

    stock_infinito = item.get("stock_infinito", True)
    if not isinstance(stock_infinito, bool):
        bloq.append(f"[{sid}] item '{item_id}' stock_infinito debe ser bool")

    if not stock_infinito:
        stock = item.get("stock", 0)
        if not isinstance(stock, int) or stock < 0:
            bloq.append(f"[{sid}] item '{item_id}' stock debe ser entero >= 0")

    return bloq, adv
