import json
import os
import sys

import pygame

from engine.configs import MOSTRAR_LOGS
from engine.configs.constants import TAMANO_CELDA
from engine.configs.game import VELOCIDAD_BASE
from engine.project_paths import levels_dir
from engine.repositories.repositorio_objetos import RepositorioObjetos

# Registra las acciones migradas al ActionRegistry (registry-first en _ejecutar_accion).
from engine.systems import actions  # noqa: F401

STACKS_DIR = levels_dir("mapas_stacks")


class StackManager:
    def __init__(self, estado):
        self.estado = estado
        self._stacks = {}
        self._nivel_id = None
        self._event_states = {}  # {event_id: "pendiente"|"finalizado"}
        self.bloqueado = False    # Blockea process_events mientras espera
        self.timer_hasta = 0      # Timestamp en ms hasta cuando esperar
        self._cola_acciones = []  # Acciones pendientes tras esperar
        self._cola_ctx = (0, 0, 0)  # (x, y, z) contexto de la cola
        self._bloqueo_por = None  # None, "timer", "dialogo", "ventana", "choice", "dialogo_tree"
        self._auto_direccion = None  # Dirección para auto_caminar
        self._arbol_dialogo = None  # Estado del arbol de diálogo en reproducción
        self._restaurar_options_callback = False  # Callback para restaurar Options tras acción bloqueante
        self._preload = {}           # Configuración de precarga del nivel
        self._onload_events = []     # Eventos a ejecutar al cargar el nivel

    def load_stacks(self, nivel_id):
        self._stacks = {}
        self._nivel_id = nivel_id
        self._preload = {}
        self._onload_events = []
        if not nivel_id:
            return
        path = os.path.join(STACKS_DIR, f"{nivel_id}_stacks.json")
        if not os.path.exists(path):
            return
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self._preload = data.get("preload", {})
            self._onload_events = data.get("onload_events", [])
            for s in data.get("stacks", []):
                pos = tuple(s["pos"])
                z = s.get("z", s.get("z_layer", 0))
                eventos = s.get("eventos", [])
                # Convert old format (capas -> eventos)
                if not eventos and "capas" in s:
                    capas = s.get("capas", [])
                    if capas:
                        for capa in capas:
                            capa_evs = capa.get("eventos", [])
                            for ev in capa_evs:
                                old_tipo = ev.get("tipo", "")
                                new_trigger = "contact" if old_tipo == "on_destroy" else \
                                              "interact" if old_tipo == "on_interact" else "contact"
                                eventos.append({
                                    "trigger": new_trigger,
                                    "condiciones": [],
                                    "acciones": [{"tipo": ev.get("accion", "show_message"),
                                                  "params": dict(ev.get("parametros", {}))}]
                                })
                # Migrate old condition format to new 6-type with operators
                for ev in eventos:
                    for cond in ev.get("condiciones", []):
                        ct = cond["tipo"]
                        p = cond["params"]
                        if ct == "has_escamas":
                            cond["tipo"] = "escamas"
                            p["operador"] = ">="
                            p["valor"] = p.pop("min", 1)
                        elif ct == "not_has_escamas":
                            cond["tipo"] = "escamas"
                            p["operador"] = "<"
                            p["valor"] = p.pop("cantidad", 1)
                        elif ct == "has_item":
                            cond["tipo"] = "item_count"
                            p["operador"] = ">="
                            p["valor"] = p.pop("cantidad_min", 1)
                        elif ct == "not_has_item":
                            cond["tipo"] = "item_count"
                            p["operador"] = "<"
                            p["valor"] = p.pop("cantidad", 1)
                        elif ct == "has_flag":
                            cond["tipo"] = "flag"
                            p["operador"] = "es_verdadero"
                        elif ct == "not_has_flag":
                            cond["tipo"] = "flag"
                            p["operador"] = "es_falso"
                        elif ct == "has_ability":
                            cond["tipo"] = "ability"
                            p["operador"] = "tiene"
                            p.pop("nivel_min", None)
                        elif ct == "not_has_ability":
                            cond["tipo"] = "ability"
                            p["operador"] = "no_tiene"
                        elif ct == "has_ability_equipped":
                            cond["tipo"] = "ability_equipped"
                            p["operador"] = "equipado"
                        elif ct == "not_has_ability_equipped":
                            cond["tipo"] = "ability_equipped"
                            p["operador"] = "no_equipado"
                        elif ct == "has_pp":
                            cond["tipo"] = "pp"
                            p["operador"] = ">="
                            p["valor"] = p.pop("min", 1)
                    # Migrar condición legacy "escamas" -> has_moneda (moneda="escamas")
                    for cond in ev.get("condiciones", []):
                        if cond.get("tipo") == "escamas":
                            cond["tipo"] = "has_moneda"
                            cond.setdefault("params", {}).setdefault("moneda", "escamas")
                    # Migrar acción legacy "remove_escamas" -> remove_moneda
                    for accion in ev.get("acciones", []):
                        if accion.get("tipo") == "remove_escamas":
                            accion["tipo"] = "remove_moneda"
                            accion.setdefault("params", {}).setdefault("moneda", "escamas")
                    # Homologar clave de shop: params["shop"] -> params["shop_id"]
                    for accion in ev.get("acciones", []):
                        p = accion.get("params", {})
                        if "shop" in p and "shop_id" not in p:
                            p["shop_id"] = p.pop("shop")
                s["eventos"] = eventos
                key = (pos[0], pos[1], z)
                self._stacks[key] = s
                # Register event IDs as pending (only if not already finalized)
                for ev in s.get("eventos", []):
                    eid = ev.get("id", "")
                    if eid and eid not in self._event_states:
                        self._event_states[eid] = "pendiente"
        except (json.JSONDecodeError, FileNotFoundError):
            pass

        # Filter out only once=True events that have been finalized (already executed)
        for key in list(self._stacks.keys()):
            stack = self._stacks[key]
            eventos = stack.get("eventos", [])
            eventos[:] = [ev for ev in eventos
                          if not (ev.get("once", False)
                                  and self._event_states.get(ev.get("id", "")) == "finalizado")]
            if not eventos:
                del self._stacks[key]

    def apply_preload(self):
        """Aplica configuración de precarga ANTES de generar entidades.

        Se ejecuta después de load_stacks() pero antes de:
        - cargar_entidades_nivel()
        - spawn_comida()
        - inicializar_arena_boss()
        """
        preload = self._preload

        # Resetear flags antes de aplicar nuevos
        if hasattr(self.estado, "no_comida_spawn"):
            self.estado.no_comida_spawn = False
        if hasattr(self.estado, "no_enemigos_spawn"):
            self.estado.no_enemigos_spawn = False

        if not preload:
            return

        # Aplicar flags iniciales
        flags_iniciales = preload.get("flags_iniciales", {})
        for flag, valor in flags_iniciales.items():
            if hasattr(self.estado, "flags"):
                self.estado.flags.set(flag, valor)

        # Aplicar configuración de spawns
        if preload.get("no_comida", False):
            self.estado.no_comida_spawn = True

        if preload.get("no_enemigos", False):
            self.estado.no_enemigos_spawn = True

        # Guardar música para aplicarla cuando AudioManager esté listo
        musica = preload.get("musica", "")
        if musica:
            self._preload_musica = musica

        if MOSTRAR_LOGS:
            print(f"[PRELOAD] Aplicado: {preload}")

    def execute_onload_events(self):
        """Ejecuta eventos con trigger 'onload' DESPUÉS de inicializar el nivel.

        Se ejecuta después de:
        - cargar_entidades_nivel()
        - spawn_comida()
        - inicializar_arena_boss()
        """
        for ev in self._onload_events:
            if ev.get("trigger") != "onload":
                continue

            # Evaluar condiciones
            if not self._check_conditions(ev.get("condiciones", [])):
                continue

            # Ejecutar acciones (sin posición específica, usar (0, 0))
            self._ejecutar_acciones(ev.get("acciones", []), 0, 0, 0)

            # Marcar como finalizado si es once
            eid = ev.get("id", "")
            if eid and ev.get("once", False):
                self._event_states[eid] = "finalizado"

            if MOSTRAR_LOGS:
                print(f"[ONLOAD] Evento ejecutado: {eid or 'sin_id'}")

    def get_stack_at(self, x, y, z=0):
        gx = x // TAMANO_CELDA
        gy = y // TAMANO_CELDA
        return self._stacks.get((gx, gy, z))

    def get_stack_grid(self, gx, gy, z=0):
        return self._stacks.get((gx, gy, z))

    def actualizar(self, estado):
        """Se llama cada frame. Procesa bloqueos por timer o diálogo."""
        # Guardar bloqueo anterior para detectar transiciones
        bloqueo_anterior = self._bloqueo_por

        if self._bloqueo_por == "timer":
            if pygame.time.get_ticks() >= self.timer_hasta:
                self.bloqueado = False
                self.timer_hasta = 0
                self._bloqueo_por = None
                acciones, self._cola_acciones = self._cola_acciones, []
                self._ejecutar_acciones(acciones, *self._cola_ctx)
        elif self._bloqueo_por == "dialogo":
            if not estado.dialogo.activo:
                self._bloqueo_por = None
                acciones, self._cola_acciones = self._cola_acciones, []
                self._ejecutar_acciones(acciones, *self._cola_ctx)
        elif self._bloqueo_por == "ventana":
            if not estado.ventana.activo:
                self._bloqueo_por = None
                acciones, self._cola_acciones = self._cola_acciones, []
                self._ejecutar_acciones(acciones, *self._cola_ctx)
        elif self._bloqueo_por == "choice":
            if not estado.mostrando_opciones:
                self._bloqueo_por = None
        elif self._bloqueo_por == "dialogo_tree":
            if not estado.dialogo.activo and not estado.mostrando_opciones:
                self._bloqueo_por = None
        elif self._bloqueo_por == "shop":
            if not getattr(estado, "shop_actual", None):
                if self._restaurar_options_callback:
                    self._bloqueo_por = "choice"
                else:
                    self._bloqueo_por = None
                    self._avanzar_arbol_dialogo(estado)
        elif self._bloqueo_por == "minijuego":
            if not estado.mostrando_minijuego:
                self._bloqueo_por = None

        # Callback automático: si venimos de dialogo/shop/minijuego y volvemos a choice,
        # y hay callback pendiente, restaurar Options
        if self._restaurar_options_callback:
            if bloqueo_anterior in ("dialogo", "shop", "minijuego") and self._bloqueo_por == "choice":
                self._restaurar_options_callback = False
                self._mostrar_opciones_plano(estado)

        if self._auto_direccion and hasattr(estado, "snake"):
            estado.snake.cambiar_direccion(self._auto_direccion)

    def process_events(self, x, y, trigger, jugador_z=None):
        if self.bloqueado:
            return
        gx = x // TAMANO_CELDA
        gy = y // TAMANO_CELDA
        stacks_here = [(k, v) for k, v in self._stacks.items()
                       if k[0] == gx and k[1] == gy]
        if not stacks_here:
            return
        for key, stack in stacks_here:
            z_layer = key[2]
            eventos = stack.get("eventos", [])
            eventos_removed = []
            for ev in eventos:
                if ev.get("trigger") == trigger:
                    print(f"[EVENTO] stack ({gx},{gy}) Z={z_layer} trigger={trigger} condiciones={len(ev.get('condiciones',[]))}")
                    if self._check_conditions(ev.get("condiciones", [])):
                        self._auto_direccion = None
                        print(f"[EVENTO] condiciones OK, ejecutando {len(ev.get('acciones',[]))} accion(es)")
                        self._ejecutar_acciones(ev.get("acciones", []), gx * TAMANO_CELDA, gy * TAMANO_CELDA, z_layer)
                        eid = ev.get("id", "")
                        actions = [a.get("tipo") for a in ev.get("acciones", [])]
                        auto_consume = "remove_sprite" in actions
                        if eid and (ev.get("once", False) or auto_consume):
                            self._event_states[eid] = "finalizado"
                            self._check_event_triggers(eid)
                        if ev.get("once", False) or auto_consume:
                            eventos_removed.append(ev)
                    else:
                        print("[EVENTO] condiciones NO cumplidas")
            for ev in eventos_removed:
                eventos.remove(ev)
            if eventos_removed:
                print(f"[EVENTO] {len(eventos_removed)} evento(s) eliminados (once=True o remove_sprite). Eventos restantes: {len(eventos)}")
            if not eventos:
                del self._stacks[key]
                print(f"[EVENTO] stack ({gx},{gy}) Z={z_layer} eliminado (sin eventos)")

    def on_hit(self, x, y, z=0, damage=0, attack_type=""):
        """Procesa eventos trigger on_hit con información del golpe"""
        gx = x // TAMANO_CELDA
        gy = y // TAMANO_CELDA
        stacks_here = [(k, v) for k, v in self._stacks.items()
                       if k[0] == gx and k[1] == gy
                       and k[2] == z]
        for key, stack in stacks_here:
            z_layer = key[2]
            eventos = stack.get("eventos", [])
            eventos_removed = []
            for ev in eventos:
                if ev.get("trigger") == "on_hit":
                    extra = {"damage": damage, "attack_type": attack_type}
                    if self._check_conditions(ev.get("condiciones", []), extra):
                        self._ejecutar_acciones(ev.get("acciones", []), gx * TAMANO_CELDA, gy * TAMANO_CELDA, z_layer)
                        eid = ev.get("id", "")
                        actions = [a.get("tipo") for a in ev.get("acciones", [])]
                        auto_consume = "remove_sprite" in actions
                        if eid and (ev.get("once", False) or auto_consume):
                            self._event_states[eid] = "finalizado"
                            self._check_event_triggers(eid)
                        if ev.get("once", False) or auto_consume:
                            eventos_removed.append(ev)
            for ev in eventos_removed:
                eventos.remove(ev)
            if not eventos:
                del self._stacks[key]

    def _check_event_triggers(self, eid):
        """Dispara eventos con trigger 'on_event_finalized' que observan a eid."""
        if not eid:
            return
        # Eventos globales que observan la finalización de este evento
        eg = getattr(self.estado, "eventos_globales", None)
        if eg is not None:
            eg.on_event_finalized(eid)
        for key, stack in list(self._stacks.items()):
            gx, gy, z_layer = key
            eventos = stack.get("eventos", [])
            eventos_removed = []
            for ev in eventos:
                if ev.get("trigger") == "on_event_finalized":
                    watched = ev.get("watched_event_id", "")
                    if watched != eid:
                        continue
                    print(f"[EVENTO] on_event_finalized ({gx},{gy}) Z={z_layer} watched={eid}")
                    if self._check_conditions(ev.get("condiciones", [])):
                        self._ejecutar_acciones(ev.get("acciones", []), gx * TAMANO_CELDA, gy * TAMANO_CELDA, z_layer)
                        eid2 = ev.get("id", "")
                        if eid2 and ev.get("once", False):
                            self._event_states[eid2] = "finalizado"
                            self._check_event_triggers(eid2)
                        if ev.get("once", False):
                            eventos_removed.append(ev)
            for ev in eventos_removed:
                eventos.remove(ev)
            if not eventos:
                del self._stacks[key]

    def on_boss_defeated(self, boss_id):
        """Busca y ejecuta eventos con trigger 'on_boss_defeated' cuyo boss_id coincida."""
        if self.bloqueado:
            return
        # Eventos globales que reaccionan a la derrota de este boss
        eg = getattr(self.estado, "eventos_globales", None)
        if eg is not None:
            eg.on_boss_defeated(boss_id)
        for key, stack in list(self._stacks.items()):
            gx, gy, z_layer = key
            eventos = stack.get("eventos", [])
            eventos_removed = []
            for ev in eventos:
                if ev.get("trigger") == "on_boss_defeated":
                    ev_boss = ev.get("boss_id", "")
                    if ev_boss and ev_boss != boss_id:
                        continue
                    from engine.configs.habilidades import HabilidadID
                    hid = getattr(HabilidadID, boss_id.upper(), boss_id)
                    extra = {"boss_id": boss_id, "boss_hid": hid}
                    print(f"[EVENTO] on_boss_defeated ({gx},{gy}) Z={z_layer} boss={boss_id}")
                    if self._check_conditions(ev.get("condiciones", []), extra):
                        self._ejecutar_acciones(ev.get("acciones", []), gx * TAMANO_CELDA, gy * TAMANO_CELDA, z_layer)
                        eid = ev.get("id", "")
                        if eid and ev.get("once", False):
                            self._event_states[eid] = "finalizado"
                        if ev.get("once", False):
                            eventos_removed.append(ev)
            for ev in eventos_removed:
                eventos.remove(ev)
            if not eventos:
                del self._stacks[key]

    def on_entity_destroyed(self, x, y, entidad_tipo, z=None):
        if z is None and hasattr(self.estado, "snake"):
            z = self.estado.snake.z
        self.process_events(x, y, "contact", z)

    def on_interact(self, x, y, entidad_tipo, z=None):
        if z is None and hasattr(self.estado, "snake"):
            z = self.estado.snake.z
        self.process_events(x, y, "interact", z)

    def _check_conditions(self, condiciones, extra=None, ctx=None):
        """Evalúa condiciones de un evento.

        Acepta un EventContext opcional. Si no se pasa, construye uno interno
        con self.estado y el extra dict (compatibilidad con llamadas previas).
        Soporta lista plana (AND implícito) y nodos compuestos operator/children.
        """
        if ctx is None:
            from engine.systems.event_context import EventContext
            ctx = EventContext(
                state=self.estado,
                source=getattr(self.estado, "snake", None),
                custom=extra or {},
            )
        from engine.systems.conditions import evaluate_condition_node
        return evaluate_condition_node(
            condiciones, lambda cond: self._check_condition_hoja(cond, ctx)
        )

    def _check_condition_hoja(self, cond, ctx) -> bool:
        """Evalúa UNA condición simple (hoja). Devuelve bool."""
        estado = ctx.state
        extra = ctx.custom
        ct = cond.get("tipo", "")
        params = cond.get("params", {})
        op = params.get("operador", ">=")
        valor = params.get("valor", 1)

        if ct == "escamas":
            if not hasattr(estado, "snake"):
                return False
            actual = estado.snake.get_escamas()
            return self._eval(actual, op, int(valor))

        elif ct == "has_moneda":
            actual = self._moneda_valor(params.get("moneda", ""))
            if actual is None:
                return False
            return self._eval(actual, op, int(valor))

        elif ct == "item_count":
            item = params.get("item", "")
            if ctx.inventario is None:
                return False
            actual = ctx.inventario.cantidad(item)
            return self._eval(actual, op, int(valor))

        elif ct == "flag":
            flag = params.get("flag", "")
            if ctx.flags is None:
                return False
            actual = ctx.flags.get(flag)
            if op in ("es_verdadero", "es_falso"):
                valido = bool(actual)
                if op == "es_verdadero" and not valido:
                    return False
                if op == "es_falso" and valido:
                    return False
                return True
            else:
                if actual is None:
                    return False
                esperado = params.get("valor", 1)
                if isinstance(actual, str) or isinstance(esperado, str):
                    if op not in ("==", "!="):
                        return False
                    return (op == "==") == (str(actual) == str(esperado))
                else:
                    if not isinstance(actual, (int, float)):
                        try:
                            actual = int(actual)
                        except (ValueError, TypeError):
                            return False
                    try:
                        esperado = int(esperado)
                    except (ValueError, TypeError):
                        esperado = 1
                    return self._eval(actual, op, esperado)

        elif ct == "ability":
            ability = params.get("ability", "")
            if ctx.habilidades is None:
                return False
            actual = ctx.habilidades.tiene_habilidad(ability)
            if op == "tiene" and not actual:
                return False
            if op == "no_tiene" and actual:
                return False
            return True

        elif ct == "ability_equipped":
            ability = params.get("ability", "")
            if ctx.habilidades is None:
                return False
            tiene = ctx.habilidades.tiene_habilidad(ability)
            equipada = ctx.habilidades.habilidad_equipada == ability
            if op == "equipado" and not (tiene and equipada):
                return False
            if op == "no_equipado" and (tiene and equipada):
                return False
            return True

        elif ct == "pp":
            if ctx.habilidades is None:
                return False
            actual = ctx.habilidades.get_pp_actual()
            return self._eval(actual, op, int(valor))

        elif ct == "evaluar_evento":
            evento_id = params.get("evento_id", "")
            estado_esperado = params.get("estado", "finalizado")
            actual = self._event_states.get(evento_id, "pendiente")
            return actual == estado_esperado

        elif ct == "damage":
            actual = extra.get("damage", 0)
            return self._eval(actual, op, int(valor))

        elif ct == "attack_type":
            esperado = params.get("valor", "")
            actual = extra.get("attack_type", "")
            if op == "==" and actual != esperado:
                return False
            if op == "!=" and actual == esperado:
                return False
            return True

        return True

    def _eval(self, actual, op, esperado):
        if op == ">=": return actual >= esperado
        if op == "<=": return actual <= esperado
        if op == ">":  return actual > esperado
        if op == "<":  return actual < esperado
        if op == "==": return actual == esperado
        if op == "!=": return actual != esperado
        return True

    # ── Monedas (contadores de primera clase) ──────────────
    # La moneda orm "escamas" sigue ligada a la snake (shim). Otras monedas
    # usan game_state.monedas. El desacople de "escamas == largo" es un tema aparte.

    def _moneda_valor(self, mid):
        estado = self.estado
        if mid == "escamas" and hasattr(estado, "snake"):
            return estado.snake.get_escamas()
        if hasattr(estado, "monedas"):
            if mid in estado.monedas.ids():
                return estado.monedas.get(mid, 0)
        return None

    def _moneda_dar(self, mid, cantidad):
        estado = self.estado
        if mid == "escamas" and hasattr(estado, "snake"):
            estado.snake.crecer(cantidad)
            return
        if hasattr(estado, "monedas"):
            estado.monedas.dar(mid, cantidad)

    def dar_moneda(self, mid, cantidad):
        """Alias público para _moneda_dar (usado por acciones migradas)."""
        self._moneda_dar(mid, cantidad)

    def _moneda_quitar(self, mid, cantidad):
        estado = self.estado
        if mid == "escamas" and hasattr(estado, "snake"):
            estado.snake.perder_escamas(cantidad)
            return
        if hasattr(estado, "monedas"):
            estado.monedas.quitar(mid, cantidad)

    def quitar_moneda(self, mid, cantidad):
        """Alias público para _moneda_quitar (usado por acciones migradas)."""
        self._moneda_quitar(mid, cantidad)

    # ── Árbol de diálogo ──────────────────────────────────

    def _avanzar_arbol_dialogo(self, estado):
        if not self._arbol_dialogo:
            self._bloqueo_por = None
            return
        ad = self._arbol_dialogo
        personaje = ad["personaje"]
        contexto = ad["contexto"]
        from engine.systems.dialogo import RUTA_DIALOGOS
        import json, os
        tree_data = None
        if os.path.exists(RUTA_DIALOGOS):
            with open(RUTA_DIALOGOS, "r", encoding="utf-8") as f:
                raw = json.load(f)
            ctx_data = raw.get(personaje, {}).get(contexto, {})
            if isinstance(ctx_data, dict) and "nodes" in ctx_data:
                tree_data = ctx_data

        if not tree_data:
            self._arbol_dialogo = None
            self._bloqueo_por = None
            return

        nodes = tree_data["nodes"]
        nid = ad.get("nid_actual")
        if not nid:
            if ad.get("_iniciado"):
                self._arbol_dialogo = None
                self._bloqueo_por = None
                return
            nid = tree_data.get("start", "")
            ad["_iniciado"] = True
        if not nid or nid not in nodes:
            self._arbol_dialogo = None
            self._bloqueo_por = None
            return

        node = nodes[nid]
        tipo = node.get("tipo", "")

        if tipo == "dialogo":
            texto = node.get("texto", "")
            quien = node.get("quien", personaje)
            estado.dialogo.iniciar_inline([texto], nombre=quien)
            ad["nid_actual"] = node.get("next", "")
            # Cuando termine el diálogo, seguimos
            estado.dialogo.al_terminar = lambda: self._on_arbol_dialogo_end(estado)

        elif tipo == "opcion":
            choices = node.get("choices", [])
            opts = []
            for ch in choices:
                opts.append({
                    "texto": ch.get("texto", ""),
                    "acciones": [{"tipo": "_arbol_choice", "params": {"destino": ch.get("next", "")}}],
                })
            estado.mostrando_opciones = True
            estado.opciones = opts
            estado.opcion_seleccionada = -1
            self._bloqueo_por = "choice"
            # Guardamos el contexto para cuando elijan
            ad["_pendiente"] = True

        elif tipo == "condicion":
            flag = node.get("flag", "")
            operador = node.get("operador", "==")
            valor = node.get("valor", "")
            if hasattr(estado, "flags"):
                actual = estado.flags.get(flag)
                if actual is None:
                    cumple = False
                elif isinstance(actual, str) or isinstance(valor, str):
                    cumple = (operador == "==" and str(actual) == str(valor)) or \
                             (operador == "!=" and str(actual) != str(valor))
                else:
                    try:
                        cumple = self._eval(actual, operador, int(valor))
                    except (ValueError, TypeError):
                        cumple = False
            else:
                cumple = False
            ad["nid_actual"] = node.get("next" if cumple else "next_false", "")
            self._avanzar_arbol_dialogo(estado)

        elif tipo == "accion":
            tipo_accion = node.get("tipo_accion", "")
            params = node.get("params", {})
            self._ejecutar_accion(tipo_accion, params, 0, 0, 0)
            ad["nid_actual"] = node.get("next", "")
            if tipo_accion == "open_shop":
                self._bloqueo_por = "shop"
                return
            self._avanzar_arbol_dialogo(estado)

        elif tipo == "salto":
            destino = node.get("destino", "")
            if "/" in destino:
                dp, dc = destino.split("/", 1)
                ad["personaje"] = dp
                ad["contexto"] = dc
                ad["nid_actual"] = None
                self._avanzar_arbol_dialogo(estado)
            else:
                self._arbol_dialogo = None
                self._bloqueo_por = None

        else:
            self._arbol_dialogo = None
            self._bloqueo_por = None

    def _on_arbol_dialogo_end(self, estado):
        if self._arbol_dialogo:
            nid = self._arbol_dialogo.get("nid_actual", "")
            if nid:
                self._avanzar_arbol_dialogo(estado)
            else:
                self._arbol_dialogo = None
                self._bloqueo_por = None

    def avanzar_arbol_dialogo(self, estado):
        """Alias público para _avanzar_arbol_dialogo (usado por acciones migradas)."""
        self._avanzar_arbol_dialogo(estado)

    def mostrar_opciones_plano(self, estado):
        """Alias público para _mostrar_opciones_plano (usado por acciones migradas)."""
        self._mostrar_opciones_plano(estado)

    def _ejecutar_acciones(self, acciones, x, y, z=0):
        for i, act in enumerate(acciones):
            print(f"[EVENTO] accion {i+1}: {act.get('tipo')} params={act.get('params', {})}")
            bloquea = self._ejecutar_accion(act.get("tipo"), act.get("params", {}), x, y, z)
            if bloquea:
                self._cola_acciones = acciones[i+1:]
                self._cola_ctx = (x, y, z)
                break

    def ejecutar_secuencia(self, acciones, ctx=None):
        self._cola_acciones = acciones
        self._cola_ctx = ctx if ctx is not None else (0, 0, 0)
        self._procesar_cola()

    def _procesar_cola(self):
        if not self._cola_acciones:
            return
        acciones = self._cola_acciones
        self._cola_acciones = []
        self._ejecutar_acciones(acciones, *self._cola_ctx)

    def ejecutar_ahora(self, accion_dict):
        tipo = accion_dict.get("tipo", "")
        params = accion_dict.get("params", {})
        self._ejecutar_accion(tipo, params, 0, 0, 0)

    def _mostrar_opciones_plano(self, estado):
        """Convierte options[0] de un diálogo plano a estado.opciones (acciones directas)."""
        options = getattr(estado.dialogo, "options", []) if hasattr(estado, "dialogo") else []
        if not options:
            self._bloqueo_por = None
            return
        opt = options[0]
        choices = opt.get("choices", [])
        estado.opcion_pregunta = opt.get("text", "")
        estado.opciones = []
        for ch in choices:
            params = {k: v for k, v in ch.items() if k not in ("text", "action")}
            # Homologar clave de shop legacy -> shop_id
            if "shop" in params and "shop_id" not in params:
                params["shop_id"] = params.pop("shop")
            estado.opciones.append({
                "texto": ch.get("text", ""),
                "acciones": [{"tipo": ch.get("action", ""), "params": params}],
            })
        estado.opcion_seleccionada = -1
        estado.mostrando_opciones = True
        self._bloqueo_por = "choice"

    def _ejecutar_accion(self, accion, params, x, y, z=0):
        estado = self.estado

        # Opt-out: acciones que NO restauran Options al terminar
        NO_RESTAURAR_OPTIONS = {"close_dialog", "open_save_menu", "open_load_menu"}

        # Detectar si estamos en modo Options
        en_modo_options = (self._bloqueo_por == "choice")

        # Registry-first: si la acción está migrada, ejecuta con EventContext.
        # Fallback legacy: si no está registrada o lanza excepción, cae al elif.
        from engine.systems.action_registry import get_action
        cls = get_action(accion)
        if cls is not None:
            from engine.systems.event_context import EventContext
            ctx = EventContext(
                state=estado,
                source=getattr(estado, "snake", None),
                position=(x, y, z),
                manager=self,
                dialog_service=getattr(estado, "dialogo", None),
                shop_service=getattr(estado, "shop_system", None),
                battle_service=getattr(estado, "arena_boss", None),
            )
            try:
                bloquea = bool(cls().execute(ctx, params))
                # Si estamos en modo Options y la acción bloquea, registrar callback
                # salvo que sea una acción de opt-out (close_dialog)
                if en_modo_options and bloquea and accion not in NO_RESTAURAR_OPTIONS:
                    self._restaurar_options_callback = True
                return bloquea
            except Exception as e:
                print(f"[EVENTO] acción registrada '{accion}' falló: {e}. Usando fallback legacy.")

        # Fallback: si la acción no está en el registry, buscar en internas
        if hasattr(self, '_ejecutar_accion_interna'):
            # Para acciones internas, verificar si es close_dialog
            if accion in NO_RESTAURAR_OPTIONS:
                return self._ejecutar_accion_interna(accion, params, estado)
            # Otras acciones internas en modo options
            if en_modo_options:
                self._restaurar_options_callback = True
            return self._ejecutar_accion_interna(accion, params, estado)
        return False

    def _ejecutar_accion_interna(self, accion, params, estado):
        if accion == "_arbol_choice":
            self._handle_arbol_choice(params, estado)
        elif accion == "accion_botton":
            self._handle_button_event(params, estado)
        elif accion == "esperar":
            return self._handle_wait(params)
        elif accion == "bloquear_eventos":
            self._handle_block_events(params)
        elif accion == "comando_automatico":
            self._handle_auto_command(params, estado)
        elif accion == "auto_caminar":
            self._handle_auto_walk(params)
        return False

    def _handle_arbol_choice(self, params, estado):
        destino = params.get("destino", "")
        if self._arbol_dialogo:
            self._arbol_dialogo["nid_actual"] = destino
            self._avanzar_arbol_dialogo(estado)

    def _handle_button_event(self, params, estado):
        tecla = params.get("tecla", "").upper()
        if MOSTRAR_LOGS: print(f"[BOTON] tecla={tecla}")
        if tecla == "Q":
            self.estado.ejecutar_golpe_q()

    def _handle_wait(self, params):
        segundos = float(params.get("segundos", 1))
        self.timer_hasta = pygame.time.get_ticks() + max(1, int(segundos * 1000))
        self._bloqueo_por = "timer"
        return True

    def _handle_block_events(self, params):
        bloquear = params.get("bloquear", True)
        if isinstance(bloquear, str):
            bloquear = bloquear.lower() in ("true", "1", "si")
        self.bloqueado = bool(bloquear)

    def _handle_auto_command(self, params, estado):
        comando = params.get("comando", "")
        if comando in ("DERECHA", "IZQUIERDA", "ARRIBA", "ABAJO"):
            if hasattr(estado, "snake"):
                estado.snake.cambiar_direccion(comando)
        elif comando == "ATAQUE":
            if hasattr(estado, "ejecutar_golpe_q"):
                estado.ejecutar_golpe_q()
        elif comando == "ACCION":
            if hasattr(estado, "stack_manager"):
                cabeza = estado.snake.get_cabeza()
                if cabeza:
                    dx = dy = 0
                    direccion = estado.snake.direccion
                    if direccion == "ARRIBA":    dy = -TAMANO_CELDA
                    elif direccion == "ABAJO":   dy = TAMANO_CELDA
                    elif direccion == "IZQUIERDA": dx = -TAMANO_CELDA
                    elif direccion == "DERECHA":  dx = TAMANO_CELDA
                    estado.stack_manager.process_events(cabeza[0] + dx, cabeza[1] + dy, "interact", estado.snake.z)

    def _handle_auto_walk(self, params):
        direccion = params.get("direccion", "").upper()
        if direccion in ("DERECHA", "IZQUIERDA", "ARRIBA", "ABAJO"):
            self._auto_direccion = direccion
        else:
            self._auto_direccion = None

    def _remover_entidades_en(self, estado, gx, gy):
        px = gx * TAMANO_CELDA
        py = gy * TAMANO_CELDA
        # Remover comida (entity singular)
        if hasattr(estado, "comida") and estado.comida:
            if estado.comida.x == px and estado.comida.y == py:
                estado.comida = None
        # Remover entidades de todas las listas
        listas = ["bloqueantes", "paredes", "bloques_acero", "hierba_alta",
                  "decorativos", "suelos", "enemigos"]
        for nombre_lista in listas:
            if not hasattr(estado, nombre_lista):
                continue
            lista = getattr(estado, nombre_lista)
            for ent in list(lista):
                if hasattr(ent, "x") and hasattr(ent, "y"):
                    if ent.x == px and ent.y == py:
                        lista.remove(ent)

    def remover_entidades_en(self, estado, gx, gy):
        """Alias público para _remover_entidades_en (usado por acciones migradas)."""
        self._remover_entidades_en(estado, gx, gy)

    def _spawn_from_sprite(self, sprite_id, x, y):
        from engine.levels.level_parser import _make_from_behavior

        from editor.elements import get_element

        el = get_element(sprite_id)
        if not el:
            return
        behavior = el.get("behavior", "decorative")
        if behavior in ("decorative", "spawn"):
            return

        entity, target = _make_from_behavior(x, y, sprite_id, el, {}, {}, {}, (0, 0), 0)
        if entity is None:
            return

        estado = self.estado

        if target == "collidables":
            from engine.entities.arbol import Arbol
            from engine.entities.bloque_acero import BloqueAcero
            from engine.entities.hierba_alta import HierbaAlta
            from engine.entities.pared import Pared
            from engine.entities.objeto_colision import ObjetoBloqueante
            if isinstance(entity, Pared) and hasattr(estado, "paredes"):
                estado.paredes.append(entity)
            elif isinstance(entity, ObjetoBloqueante) and not isinstance(entity, (BloqueAcero, Arbol)) and hasattr(estado, "bloqueantes"):
                estado.bloqueantes.append(entity)
            elif isinstance(entity, (BloqueAcero, Arbol)) and hasattr(estado, "bloques_acero"):
                estado.bloques_acero.append(entity)
            elif isinstance(entity, HierbaAlta) and hasattr(estado, "hierba_alta"):
                estado.hierba_alta.append(entity)
        elif target == "suelos" and hasattr(estado, "suelos"):
            estado.suelos.append(entity)
        elif target == "enemigos" and hasattr(estado, "enemigos"):
            estado.enemigos.append(entity)
        elif target == "comidas" and hasattr(estado, "comidas"):
            estado.comidas.append(entity)

        elif entity_name == "Arbol":
            from engine.entities.arbol import Arbol
            if hasattr(estado, "bloques_acero"):
                estado.bloques_acero.append(Arbol(x, y))

    def spawn_from_sprite(self, sprite_id, x, y):
        """Alias público para _spawn_from_sprite (usado por acciones migradas)."""
        self._spawn_from_sprite(sprite_id, x, y)

