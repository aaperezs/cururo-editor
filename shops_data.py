# Editor de tiendas (data/shops.json).
#
# Formato: {"shops": [{...}]}

import copy
import json
import os

from editor.project import get_current_project
from editor.monedas_data import get_all_monedas
from editor.contadores_data import get_all_contadores
from editor.items_data import get_all_items

_SHOPS = []


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


def get_all_shops():
    return [s.get("id", "") for s in _SHOPS]


def get_shops():
    return copy.deepcopy(_SHOPS)


def get_shop(sid):
    for s in _SHOPS:
        if s.get("id") == sid:
            return copy.deepcopy(s)
    return None


def set_shop(sid, data):
    entry = copy.deepcopy(data)
    entry["id"] = sid
    for i, s in enumerate(_SHOPS):
        if s.get("id") == sid:
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


def delete_shop(sid):
    for i, s in enumerate(_SHOPS):
        if s.get("id") == sid:
            del _SHOPS[i]
            _save_shops()
            return True
    return False


def shop_exists(sid):
    return sid in get_all_shops()


def validar_shops(lista):
    """Valida tiendas. Devuelve (bloqueantes, advertencias)."""
    bloq, adv = [], []
    ids = set()
    monedas_validas = set(get_all_monedas())
    contadores_validos = set(get_all_contadores())
    items_validos = set(get_all_items())

    for s in lista:
        sid = (s.get("id") or "").strip()
        if not sid:
            bloq.append("tienda sin id")
            continue
        if sid in ids:
            bloq.append(f"id de tienda duplicado '{sid}'")
        ids.add(sid)

        nombre = (s.get("nombre") or "").strip()
        if not nombre:
            adv.append(f"[{sid}] sin nombre (se usará el id)")

        moneda_ppal = s.get("moneda_principal", "")
        if moneda_ppal and moneda_ppal not in monedas_validas:
            bloq.append(f"[{sid}] moneda_principal '{moneda_ppal}' no existe en monedas.json")

        categorias = s.get("categorias", [])
        if categorias and not isinstance(categorias, list):
            bloq.append(f"[{sid}] categorias debe ser lista")

        # Validar items
        items = s.get("items", [])
        if not isinstance(items, list):
            bloq.append(f"[{sid}] items debe ser lista")
        else:
            for idx, item in enumerate(items):
                item_id = item.get("item_id", "")
                if not item_id:
                    bloq.append(f"[{sid}] item #{idx} sin item_id")
                elif item_id not in items_validos:
                    adv.append(f"[{sid}] item '{item_id}' no existe en items.json")

                precio = item.get("precio", {})
                if not isinstance(precio, dict):
                    bloq.append(f"[{sid}] item '{item_id}' precio debe ser dict")
                else:
                    for moneda, valor in precio.items():
                        if moneda not in monedas_validas:
                            bloq.append(f"[{sid}] item '{item_id}' moneda '{moneda}' no existe")
                        if not isinstance(valor, int) or valor < 0:
                            bloq.append(f"[{sid}] item '{item_id}' precio en '{moneda}' debe ser entero >= 0")

                moneda_compra = item.get("moneda_compra", "")
                if moneda_compra and moneda_compra not in monedas_validas:
                    bloq.append(f"[{sid}] item '{item_id}' moneda_compra '{moneda_compra}' no existe")

                stock = item.get("stock", 0)
                if not isinstance(stock, int) or stock < 0:
                    bloq.append(f"[{sid}] item '{item_id}' stock debe ser entero >= 0")

                max_stock = item.get("max_stock", 0)
                if not isinstance(max_stock, int) or max_stock < 0:
                    bloq.append(f"[{sid}] item '{item_id}' max_stock debe ser entero >= 0")
                elif max_stock < stock and not item.get("stock_infinito", False):
                    bloq.append(f"[{sid}] item '{item_id}' max_stock < stock")

                max_stack = item.get("max_stack", 1)
                if not isinstance(max_stack, int) or max_stack < 1:
                    bloq.append(f"[{sid}] item '{item_id}' max_stack debe ser entero >= 1")

                unlock = item.get("unlock")
                if unlock:
                    bloq_unlock, adv_unlock = _validar_unlock(unlock, contadores_validos, set(), set())
                    for b in bloq_unlock:
                        bloq.append(f"[{sid}] item '{item_id}' unlock: {b}")
                    for a in adv_unlock:
                        adv.append(f"[{sid}] item '{item_id}' unlock: {a}")

                restock = item.get("restock")
                if restock:
                    triggers = restock.get("triggers", [])
                    if not isinstance(triggers, list):
                        bloq.append(f"[{sid}] item '{item_id}' restock.triggers debe ser lista")
                    else:
                        for t in triggers:
                            if not isinstance(t, dict):
                                bloq.append(f"[{sid}] item '{item_id}' trigger debe ser dict")
                            elif t.get("tipo") == "evento":
                                # No validamos evento aquí (está en stacks)
                                pass
                            elif t.get("tipo") == "flag":
                                # No validamos flag aquí
                                pass
                            elif t.get("tipo") == "contador":
                                cnt = t.get("contador", "")
                                if cnt and cnt not in contadores_validos:
                                    adv.append(f"[{sid}] item '{item_id}' trigger contador '{cnt}' no existe")

                    cantidad = restock.get("cantidad", 1)
                    if not isinstance(cantidad, int) or cantidad < 1:
                        bloq.append(f"[{sid}] item '{item_id}' restock.cantidad debe ser entero >= 1")

        # Validar compra (trueque)
        compra = s.get("compra", {})
        if compra:
            items_aceptados = compra.get("items_aceptados", [])
            if items_aceptados != ["*"] and not isinstance(items_aceptados, list):
                bloq.append(f"[{sid}] compra.items_aceptados debe ser lista o ['*']")

            precios_compra = compra.get("precios_compra", {})
            if not isinstance(precios_compra, dict):
                bloq.append(f"[{sid}] compra.precios_compra debe ser dict")
            else:
                for item_id, precios in precios_compra.items():
                    if not isinstance(precios, dict):
                        bloq.append(f"[{sid}] compra.precios_compra['{item_id}'] debe ser dict")
                    else:
                        for moneda, valor in precios.items():
                            if moneda not in monedas_validas:
                                bloq.append(f"[{sid}] compra '{item_id}' moneda '{moneda}' no existe")
                            if not isinstance(valor, int) or valor < 0:
                                bloq.append(f"[{sid}] compra '{item_id}' precio en '{moneda}' debe ser >= 0")

    return bloq, adv


def _validar_unlock(unlock, contadores_validos, flags_validos, items_validos):
    bloq, adv = [], []
    if not isinstance(unlock, dict):
        bloq.append("unlock debe ser dict")
        return bloq, adv

    tipo = unlock.get("tipo", "AND")
    if tipo not in ("AND", "OR"):
        bloq.append("unlock.tipo debe ser 'AND' o 'OR'")

    condiciones = unlock.get("condiciones", [])
    if not isinstance(condiciones, list):
        bloq.append("unlock.condiciones debe ser lista")

    for c in condiciones:
        if not isinstance(c, dict):
            bloq.append("condición debe ser dict")
            continue
        tipo_c = c.get("tipo", "")
        if tipo_c == "contador":
            cnt = c.get("contador", "")
            if cnt and cnt not in contadores_validos:
                adv.append(f"unlock contador '{cnt}' no existe")
        elif tipo_c == "flag":
            flag = c.get("flag", "")
            if flag and flag not in flags_validos:
                adv.append(f"unlock flag '{flag}' no existe")
        elif tipo_c == "item":
            iid = c.get("item_id", "")
            if iid and iid not in items_validos:
                adv.append(f"unlock item '{iid}' no existe")
        else:
            adv.append(f"tipo de condición desconocido '{tipo_c}'")

    return bloq, adv