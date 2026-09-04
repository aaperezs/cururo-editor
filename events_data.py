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
    # ── Mensajes y UI ──
    "show_message": {"label": "Mostrar Mensaje", "params": {"mensaje": ""}},
    "mostrar_ventana": {"label": "Mostrar Ventana", "params": {"ventana_id": ""}},
    "mostrar_opciones": {"label": "Mostrar Opciones", "params": {"opciones": []}},
    "mostrar_personaje": {"label": "Mostrar Personaje", "params": {"personaje_id": "", "posicion": "centro", "expresion": "normal"}},
    "ocultar_personaje": {"label": "Ocultar Personaje", "params": {"personaje_id": ""}},
    "ocultar_todos_personajes": {"label": "Ocultar Todos", "params": {}},
    "cambiar_fondo": {"label": "Cambiar Fondo", "params": {"sprite_id": "", "modo": "fill"}},
    # ── Diálogo ──
    "start_dialogue": {"label": "Iniciar Diálogo", "params": {"dialogo_id": ""}},
    "close_dialog": {"label": "Cerrar Diálogo", "params": {"farewell_text": ""}},
    "dialogo_inline": {"label": "Diálogo Inline", "params": {"lineas": [], "quien": ""}},
    "dialogo_tree": {"label": "Árbol de Diálogo", "params": {"dialogo_id": ""}},
    # ── Sprite y Mapa ──
    "replace_sprite": {"label": "Reemplazar Sprite", "params": {"sprite_id": ""}},
    "remove_sprite": {"label": "Eliminar Sprite", "params": {}},
    "spawn_entity": {"label": "Generar Entidad", "params": {"sprite_id": "", "offset_x": 0, "offset_y": 0, "z": 0}},
    "change_map": {"label": "Cambiar Mapa", "params": {"nivel": "", "exit_id": ""}},
    # ── Jugador ──
    "give_item": {"label": "Dar Objeto", "params": {"item": "", "cantidad": 1}},
    "remove_item": {"label": "Quitar Objeto", "params": {"item": "", "cantidad": 1}},
    "give_moneda": {"label": "Dar Moneda", "params": {"moneda": "", "cantidad": 1}},
    "remove_moneda": {"label": "Quitar Moneda", "params": {"moneda": "", "cantidad": 1}},
    "remove_escamas": {"label": "Quitar Escamas", "params": {"cantidad": 1}},
    "avanzar": {"label": "Avanzar", "params": {"direccion": ""}},
    "despertar": {"label": "Despertar", "params": {}},
    "cambiar_skin": {"label": "Cambiar Skin", "params": {"skin": ""}},
    "bloquear_mandos": {"label": "Bloquear Mandos", "params": {"bloquear": True}},
    # ── Combate ──
    "damage": {"label": "Daño", "params": {"cantidad": 1, "mensaje": ""}},
    "start_boss_fight": {"label": "Iniciar Boss Fight", "params": {}},
    "mostrar_boss": {"label": "Mostrar Boss", "params": {"visible": True}},
    # ── Habilidades ──
    "consume_pp": {"label": "Consumir PP", "params": {"cantidad": 1}},
    "desbloquear_habilidad": {"label": "Desbloquear Habilidad", "params": {"habilidad": ""}},
    "equipar_habilidad": {"label": "Equipar Habilidad", "params": {"habilidad": ""}},
    # ── Flags y Contadores ──
    "set_flag": {"label": "Establecer Flag", "params": {"flag": ""}},
    "clear_flag": {"label": "Limpiar Flag", "params": {"flag": ""}},
    "add_flag": {"label": "Incrementar Flag", "params": {"flag": "", "cantidad": 1}},
    "increment_contador": {"label": "Incrementar Contador", "params": {"contador_id": "", "cantidad": 1}},
    "set_contador": {"label": "Establecer Contador", "params": {"contador_id": "", "valor": 0}},
    # ── Tienda ──
    "open_shop": {"label": "Abrir Tienda", "params": {"shop_id": ""}},
    "close_shop": {"label": "Cerrar Tienda", "params": {}},
    "abrir_menu": {"label": "Abrir Menú", "params": {"menu_id": ""}},
    "restock_shop": {"label": "Restockear Tienda", "params": {"shop_id": "", "item_id": ""}},
    "add_shop_stock": {"label": "Agregar Stock", "params": {"shop_id": "", "item_id": "", "cantidad": 1}},
    "modify_shop_price": {"label": "Modificar Precio", "params": {"shop_id": "", "item_id": "", "moneda": "", "precio": 0}},
    # ── Audio ──
    "play_bgm": {"label": "Reproducir Música", "params": {"asset_id": "", "fade_ms": 0}},
    "stop_bgm": {"label": "Detener Música", "params": {"fade_ms": 0}},
    "play_sfx": {"label": "Reproducir Efecto", "params": {"asset_id": ""}},
    "set_bgm_volume": {"label": "Volumen Música", "params": {"volumen": 1.0}},
    "set_sfx_volume": {"label": "Volumen Efectos", "params": {"volumen": 1.0}},
    "set_volume": {"label": "Volumen General", "params": {"volumen": 1.0}},
    # ── Sistema ──
    "set_resolution": {"label": "Cambiar Resolución", "params": {"ancho": 0, "alto": 0}},
    "run_script": {"label": "Ejecutar Script", "params": {"function_name": "", "args": ""}},
    "save_game": {"label": "Guardar Juego", "params": {"slot": 1, "dev": False}},
    "load_game": {"label": "Cargar Juego", "params": {"slot": 1, "dev": False}},
    "open_save_menu": {"label": "Abrir Menú Guardar", "params": {}},
    "open_load_menu": {"label": "Abrir Menú Cargar", "params": {}},
    "close_save_menu": {"label": "Cerrar Menú Guardar", "params": {}},
    "mover_a": {"label": "Mover a Evento", "params": {"evento_id": ""}},
    "examinar_key_item": {"label": "Examinar Objeto Clave", "params": {"item": ""}},
    # ── Escenas y Minijuegos ──
    "ir_a_escena": {"label": "Ir a Escena", "params": {"capitulo": 0, "escena": 0}},
    "iniciar_minijuego": {"label": "Iniciar Minijuego", "params": {"minijuego_id": ""}},
    "iniciar_demo": {"label": "Iniciar Demo", "params": {"demo_id": ""}},
    "fin_demo": {"label": "Fin Demo", "params": {}},
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
