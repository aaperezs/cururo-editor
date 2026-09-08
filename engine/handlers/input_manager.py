import sys

import pygame


class InputManager:
    """Unified input handler: maps keys to actions. Supports rebinding."""

    _DEFAULT_MAP = {
        # Movement
        pygame.K_UP: "MOVE_UP",
        pygame.K_DOWN: "MOVE_DOWN",
        pygame.K_LEFT: "MOVE_LEFT",
        pygame.K_RIGHT: "MOVE_RIGHT",
        # Interaction
        pygame.K_e: "INTERACT",
        # Skills
        pygame.K_q: "USE_SKILL",
        pygame.K_TAB: "NEXT_SKILL",
        # Menus
        pygame.K_p: "TOGGLE_PAUSE",
        pygame.K_f: "TOGGLE_FORGE",
        pygame.K_t: "TOGGLE_TRADE",
        pygame.K_i: "TOGGLE_INVENTORY",
        # Dialogue
        pygame.K_SPACE: "DIALOGUE_ADVANCE",
        pygame.K_RETURN: "DIALOGUE_ADVANCE",
        # Game over
        pygame.K_r: "RESTART",
        # Forge/inventory navigation
        pygame.K_ESCAPE: "CLOSE_MENU",
        # Debug
        pygame.K_F3: "TOGGLE_GODMODE",
    }

    _DIR_MAP = {
        "MOVE_UP": "ARRIBA",
        "MOVE_DOWN": "ABAJO",
        "MOVE_LEFT": "IZQUIERDA",
        "MOVE_RIGHT": "DERECHA",
    }

    _TRADE_MAP = {
        pygame.K_1: "TRADE_1",
        pygame.K_3: "TRADE_3",
        pygame.K_5: "TRADE_5",
        pygame.K_d: "TRADE_BORROW",
    }

    def __init__(self, estado, mostrar_mensaje):
        self.estado = estado
        self.mostrar_mensaje = mostrar_mensaje
        self._action_map = dict(self._DEFAULT_MAP)

    def rebind(self, key, action):
        self._action_map[key] = action

    def process_events(self):
        estado = self.estado
        for evento in pygame.event.get():
            if evento.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if evento.type == pygame.KEYDOWN:
                self._handle_key(evento.key)

    def _handle_key(self, key):
        estado = self.estado

        # Minigame overrides everything
        if estado.mostrando_minijuego:
            event = pygame.event.Event(pygame.KEYDOWN, key=key)
            estado.sistema_minijuego.handle_event(event)
            return

        # Choice box overrides dialogue
        if estado.mostrando_opciones:
            if key == pygame.K_UP:
                estado.opcion_seleccionada = max(0, estado.opcion_seleccionada - 1) if estado.opcion_seleccionada >= 0 else len(estado.opciones) - 1
            elif key == pygame.K_DOWN:
                estado.opcion_seleccionada = (estado.opcion_seleccionada + 1) % len(estado.opciones) if estado.opcion_seleccionada >= 0 else 0
            elif key in (pygame.K_SPACE, pygame.K_RETURN):
                if 0 <= estado.opcion_seleccionada < len(estado.opciones):
                    opcion = estado.opciones[estado.opcion_seleccionada]
                    estado.mostrando_opciones = False
                    acciones_opcion = opcion.get("acciones", [])
                    cola_restante = estado.stack_manager._cola_acciones
                    cola_ctx = estado.stack_manager._cola_ctx
                    estado.stack_manager._cola_acciones = []
                    estado.stack_manager.ejecutar_secuencia(acciones_opcion + cola_restante, ctx=cola_ctx)
            return

        # Dialogue overrides everything
        if estado.dialogo.activo:
            if key in (pygame.K_SPACE, pygame.K_RETURN):
                estado.dialogo.avanzar()
            return

        # Ventana
        if estado.ventana.activo:
            if key in (pygame.K_SPACE, pygame.K_RETURN):
                estado.ventana.avanzar()
            return

        # Game over
        if estado.game_over:
            if key == pygame.K_r:
                estado.reiniciar()
            elif key == pygame.K_ESCAPE:
                pygame.quit()
                sys.exit()
            return

        # Forge
        if estado.mostrando_forja:
            self._handle_forge(key)
            return

        # Inventory
        if estado.mostrando_inventario:
            self._handle_inventory(key)
            return

        # Menus editables (data/menus.json): abrir por tecla configurada
        menu_tecla = getattr(estado.menu, "menu_id_por_tecla", None)
        if menu_tecla:
            menu_id = menu_tecla(pygame.key.name(key))
            if menu_id and hasattr(estado.menu, "abrir_menu"):
                estado.mostrando_inventario = True
                estado.menu.abrir_menu(menu_id)
                return

        # Trade
        if estado.mostrando_trueque:
            self._handle_trade(key)
            return

        # Dev mode hotkeys (F5/F9)
        if hasattr(estado, "save_system") and estado.save_system.is_dev_mode():
            if key == pygame.K_F5:
                ok, msg = estado.save_system.dev_save(1)
                estado.mensaje_temporal = msg
                estado.tiempo_mensaje = 90
                return
            elif key == pygame.K_F9:
                ok, msg = estado.save_system.dev_load(1)
                estado.mensaje_temporal = msg
                estado.tiempo_mensaje = 90
                return

        # World controls
        self._handle_world(key)

    def _handle_forge(self, key):
        estado = self.estado
        if key == pygame.K_ESCAPE:
            estado.mostrando_forja = False
        elif key == pygame.K_UP:
            estado.sistema_forja.seleccion = max(0, estado.sistema_forja.seleccion - 1)
        elif key == pygame.K_DOWN:
            recetas = list(estado.sistema_forja._repo.get_todas().keys())
            estado.sistema_forja.seleccion = min(len(recetas) - 1, estado.sistema_forja.seleccion + 1)
        elif key == pygame.K_RETURN:
            estado.sistema_forja.fabricar_seleccion()

    def _handle_inventory(self, key):
        estado = self.estado
        menu = estado.menu
        if key == pygame.K_ESCAPE:
            estado.mostrando_inventario = False
            if getattr(estado, "shop_actual", None) is not None:
                estado.shop_actual = None
                if hasattr(estado.menu, "cerrar"):
                    estado.menu.cerrar()
        elif key == pygame.K_TAB:
            menu.cambiar_apartado(1)
        elif key == pygame.K_LEFT:
            if not self._cycle_opcion(estado, -1):
                menu.cambiar_apartado(-1)
        elif key == pygame.K_RIGHT:
            if not self._cycle_opcion(estado, 1):
                menu.cambiar_apartado(1)
        elif key == pygame.K_UP:
            max_items = self._menu_item_count(estado)
            menu.seleccion = max(0, menu.seleccion - 1)
            if max_items > 0:
                menu.seleccion = min(menu.seleccion, max_items - 1)
        elif key == pygame.K_DOWN:
            max_items = self._menu_item_count(estado)
            if max_items > 0:
                menu.seleccion = (menu.seleccion + 1) % max_items
        elif key == pygame.K_RETURN:
            self._inventory_activate()
        elif key == pygame.K_x:
            self._inventory_drop()

    def _panel_cls(self, menu):
        from engine.systems.ui.components.inventory_panels import PANELES_APARTADO, RENDERERS

        tipo = getattr(menu, "apartado_tipo", None) or getattr(menu, "apartado_id", None)
        cls = RENDERERS.get(tipo)
        if cls:
            return cls
        return PANELES_APARTADO.get(getattr(menu, "apartado_id", None))

    def _menu_item_count(self, estado):
        cls = self._panel_cls(estado.menu)
        if not cls:
            return 0
        config = getattr(estado.menu, "apartado_config", {})
        return cls(None, None, config=config).item_count(estado)

    def _inventory_items_ids(self):
        estado = self.estado
        return [iid for iid in estado.inventario.items if estado.inventario.es_consumible(iid)]

    def _inventory_drop(self):
        estado = self.estado
        menu = estado.menu
        tipo = getattr(menu, "apartado_tipo", None)
        if tipo != "lista_consumibles" and menu.apartado_id != "items":
            return
        lista = self._inventory_items_ids()
        if 0 <= menu.seleccion < len(lista):
            iid = lista[menu.seleccion]
            estado.inventario.consumir_item(iid, 1)
            if menu.seleccion >= len(self._inventory_items_ids()) and menu.seleccion > 0:
                menu.seleccion -= 1

    def _cycle_opcion(self, estado, direccion):
        """Cicla la opción del ítem seleccionado si tiene `opciones` y aplica la acción.

        Retorna True si cicló (el ítem tenía opciones); False si no, para que
        LEFT/RIGHT sigan cambiando de apartado como antes.
        """
        menu = estado.menu
        cls = self._panel_cls(menu)
        if not cls:
            return False
        config = getattr(menu, "apartado_config", {})
        panel = cls(None, None, config=config)
        items = panel._items(estado) if hasattr(panel, "_items") else []
        if not (0 <= menu.seleccion < len(items)):
            return False
        it = items[menu.seleccion]
        opciones = getattr(it, "opciones", None) if hasattr(it, "opciones") else it.get("opciones") if hasattr(it, "get") else None
        if not opciones:
            return False
        indices = getattr(menu, "opcion_indices", {})
        item_id = getattr(it, "item_id", "") or (it.get("id", "") if hasattr(it, "get") else "")
        key = item_id if item_id else f"@{menu.seleccion}"
        idx = indices.get(key)
        if idx is None:
            # Primer press: partir del índice persistido (match con user_prefs),
            # no de 0 (evita salto al último con LEFT).
            idx = panel._indice_opcion(it, estado)
        idx = (idx + direccion) % len(opciones)
        indices[key] = idx
        self._inventory_activate()
        return True

    def _inventory_activate(self):
        estado = self.estado
        cls = self._panel_cls(estado.menu)
        if not cls:
            return
        config = getattr(estado.menu, "apartado_config", {})
        accion = cls(None, None, config=config).accion_seleccionada(estado)
        if accion:
            self._ejecutar_accion_menu(accion, estado)

    def _ejecutar_accion_menu(self, accion, estado):
        menu = estado.menu
        tipo = accion.get("tipo")
        if tipo == "equipar_habilidad":
            hid = accion.get("habilidad")
            if estado.habilidades.equipar_habilidad(hid):
                hab = estado.habilidades.get_habilidad_equipada()
                if hab:
                    estado.snake.set_skin(hab.get("efecto"))
        elif tipo == "usar_item":
            iid = accion.get("item")
            if estado.inventario.usar_item(iid, estado):
                if menu.seleccion >= len(self._inventory_items_ids()) and menu.seleccion > 0:
                    menu.seleccion -= 1
        elif tipo == "desequipar_slot":
            estado.inventario.desequipar(accion.get("slot"))
            estado.inventario.aplicar_todos_efectos(estado.snake, estado)
        elif tipo == "equipar_slot":
            self._equipar_slot(accion.get("slot"), estado)
        else:
            estado.stack_manager.ejecutar_ahora(accion)

    def _equipar_slot(self, slot_id, estado):
        inv = estado.inventario
        if inv.get_equipado(slot_id):
            inv.desequipar(slot_id)
        else:
            # Equipar el primer equipable del inventario que encaje en el slot
            for iid in list(inv.items):
                config = inv.get_config(iid)
                if config and config.get("slot") == slot_id:
                    inv.equipar(iid)
                    inv.consumir_item(iid, 1)
                    break
        inv.aplicar_todos_efectos(estado.snake, estado)

    def _handle_trade(self, key):
        estado = self.estado
        if key == pygame.K_1:
            if estado.snake.vender_segmentos(1):
                self.mostrar_mensaje("Vendiste 1 segmento!", 60)
                estado.mostrando_trueque = False
        elif key == pygame.K_3:
            if estado.snake.vender_segmentos(3):
                self.mostrar_mensaje("Vendiste 3 segmentos!", 60)
                estado.mostrando_trueque = False
        elif key == pygame.K_5:
            if estado.snake.vender_segmentos(5):
                self.mostrar_mensaje("Vendiste 5 segmentos!", 60)
                estado.mostrando_trueque = False
        elif key == pygame.K_d:
            if estado.snake.pedir_prestado(3):
                self.mostrar_mensaje("Pediste prestado! Velocidad aumentada.", 60)
                estado.mostrando_trueque = False
        elif key == pygame.K_ESCAPE:
            estado.mostrando_trueque = False

    def _cycle_skill(self):
        estado = self.estado
        estado.habilidades.cambiar_habilidad(1)
        hab = estado.habilidades.get_habilidad_equipada()
        if hab:
            estado.snake.set_skin(hab.get("efecto"))

    def _interact(self):
        estado = self.estado
        cabeza = estado.snake.get_cabeza()
        if not cabeza:
            return
        from engine.configs import TAMANO_CELDA
        dx = dy = 0
        if estado.snake.direccion == "ARRIBA":    dy = -TAMANO_CELDA
        elif estado.snake.direccion == "ABAJO":   dy = TAMANO_CELDA
        elif estado.snake.direccion == "IZQUIERDA": dx = -TAMANO_CELDA
        elif estado.snake.direccion == "DERECHA":  dx = TAMANO_CELDA
        target_x = cabeza[0] + dx
        target_y = cabeza[1] + dy

        estado.stack_manager.process_events(target_x, target_y, "interact", estado.snake.z)

    def _handle_world(self, key):
        estado = self.estado
        if estado.mandos_bloqueados:
            return

        action = self._action_map.get(key)

        # Movement (handled even if not in action_map for non-bound keys during sleep)
        if key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
            self._apply_direction(key, estado)
            return

        if action == "INTERACT":
            self._interact()
        elif action == "USE_SKILL":
            self.estado.ejecutar_golpe_q()
        elif action == "NEXT_SKILL":
            self._cycle_skill()
        elif action == "TOGGLE_PAUSE":
            estado.pausa = not estado.pausa
        elif action == "TOGGLE_FORGE":
            estado.mostrando_forja = not estado.mostrando_forja
        elif action == "TOGGLE_TRADE":
            estado.mostrando_trueque = not estado.mostrando_trueque
        elif action == "TOGGLE_INVENTORY":
            estado.mostrando_inventario = not estado.mostrando_inventario
            if estado.mostrando_inventario:
                estado.menu.abrir()
        elif action == "TOGGLE_GODMODE":
            estado.god_mode = not estado.god_mode
            msg = "DEBUG: God Mode ON" if estado.god_mode else "DEBUG: God Mode OFF"
            self.mostrar_mensaje(msg, 90)

    def _apply_direction(self, key, estado):
        dir_map = {
            pygame.K_UP: "ARRIBA",
            pygame.K_DOWN: "ABAJO",
            pygame.K_LEFT: "IZQUIERDA",
            pygame.K_RIGHT: "DERECHA",
        }
        direction = dir_map[key]
        estado.snake.cambiar_direccion(direction)

    def get_action_name(self, action):
        """Get the key name for an action (for UI display)."""
        for key, act in self._action_map.items():
            if act == action:
                return pygame.key.name(key)
        return "?"
