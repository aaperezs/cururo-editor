"""Eventos globales: eventos que afectan el estado del juego más allá de
los mapas, con el mismo patrón que los eventos del mapa.

    evento: { event_id, trigger, boss_id?, watched_event_id?,
              condiciones: [{tipo, params}], acciones: [{tipo, params}], once }

Triggers soportados:
    - on_boss_defeated:   se dispara al derrotar un boss (usa boss_id)
    - on_event_finalized: se dispara cuando un evento de mapa finaliza
                          (usa watched_event_id)

Acciones que afectan tiendas (apuntan por shop_id):
    - restock_shop       { shop_id, item_id? }   item vacío => toda la tienda
    - add_shop_stock     { shop_id, item_id, cantidad }
    - modify_shop_price  { shop_id, item_id, moneda, precio }
"""

import json

from engine.repositories.repositorio_eventos_globales import RepositorioEventosGlobales


class EventosGlobalesSystem:
    """Procesa eventos globales: carga, triggers, condiciones y acciones."""

    def __init__(self, estado):
        self.estado = estado
        self._repo = RepositorioEventosGlobales()
        self._eventos = self._repo.get_eventos()

    def recargar(self):
        self._eventos = self._repo.get_eventos()

    # ── Triggers ───────────────────────────────────────────────

    def on_boss_defeated(self, boss_id: str):
        """Dispara eventos globales con trigger on_boss_defeated."""
        for evento in self._eventos:
            if evento.get("trigger") != "on_boss_defeated":
                continue
            ev_boss = evento.get("boss_id", "")
            if ev_boss and ev_boss != boss_id:
                continue
            print(f"[EVENTO GLOBAL] on_boss_defeated boss={boss_id} ({evento.get('event_id', '')})")
            if self._check_conditions(evento.get("condiciones", [])):
                self._ejecutar_acciones(evento.get("acciones", []))

    def on_event_finalized(self, event_id: str):
        """Dispara eventos globales con trigger on_event_finalized que
        observan a event_id."""
        if not event_id:
            return
        for evento in self._eventos:
            if evento.get("trigger") != "on_event_finalized":
                continue
            watched = evento.get("watched_event_id", "")
            if watched != event_id:
                continue
            print(f"[EVENTO GLOBAL] on_event_finalized watched={event_id} ({evento.get('event_id', '')})")
            if self._check_conditions(evento.get("condiciones", [])):
                self._ejecutar_acciones(evento.get("acciones", []))

    # ── Condiciones ────────────────────────────────────────────

    def _check_conditions(self, condiciones) -> bool:
        from systems.conditions import evaluate_condition_node
        return evaluate_condition_node(
            condiciones, lambda cond: self._check_condition_hoja(cond)
        )

    def _check_condition_hoja(self, cond) -> bool:
        """Evalúa UNA condición global simple. Devuelve bool."""
        estado = self.estado
        ct = cond.get("tipo", "")
        params = cond.get("params", {})
        op = params.get("operador", ">=")
        valor = params.get("valor", 1)

        if ct == "flag":
            flag = params.get("flag", "")
            actual = estado.flags.get(flag, 0)
            if op in ("es_verdadero", "es_falso"):
                valido = bool(actual)
                if op == "es_verdadero" and not valido:
                    return False
                if op == "es_falso" and valido:
                    return False
                return True
            return self._eval(actual, op, int(valor))

        elif ct == "has_moneda":
            moneda = params.get("moneda", "")
            actual = estado.monedas.get(moneda, 0)
            return self._eval(actual, op, int(valor))

        elif ct == "item_count":
            item = params.get("item", "")
            actual = estado.inventario.cantidad(item)
            return self._eval(actual, op, int(valor))

        elif ct == "ability":
            ability = params.get("ability", "")
            tiene = estado.habilidades.tiene_habilidad(ability)
            if op == "tiene" and not tiene:
                return False
            if op == "no_tiene" and tiene:
                return False
            return True

        elif ct == "evaluar_evento":
            evento_id = params.get("evento_id", "")
            estado_esperado = params.get("estado", "finalizado")
            actual = estado.stack_manager._event_states.get(evento_id, "pendiente")
            return actual == estado_esperado

        return True

    def _eval(self, actual, op, esperado):
        if op == ">=": return actual >= esperado
        if op == "<=": return actual <= esperado
        if op == ">":  return actual > esperado
        if op == "<":  return actual < esperado
        if op == "==": return actual == esperado
        if op == "!=": return actual != esperado
        return True

    # ── Acciones ───────────────────────────────────────────────

    def _ejecutar_acciones(self, acciones):
        estado = self.estado
        for acc in acciones:
            tipo = acc.get("tipo", "")
            params = acc.get("params", {})
            if not hasattr(estado, "shop_system"):
                continue
            shop_system = estado.shop_system
            shop_id = params.get("shop_id", "")

            if tipo == "restock_shop":
                shop_system.restockear(shop_id, params.get("item_id", "") or None)

            elif tipo == "add_shop_stock":
                shop_system.anadir_stock(shop_id, params.get("item_id", ""),
                                         int(params.get("cantidad", 1)))

            elif tipo == "modify_shop_price":
                shop_system.modificar_precio(shop_id, params.get("item_id", ""),
                                             params.get("moneda", ""),
                                             int(params.get("precio", 0)))
