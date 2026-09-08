import pygame

from engine.entities.save_manager import SaveManager, SaveCorruptError
from engine.repositories import RepositorioSaveSystem


class SaveSystem:
    """Sistema central de guardado: serialización, slots, autosave, dev mode.

    La lógica de QUÉ se requiere para guardar (item, zona, etc.)
    se define por el usuario en los eventos/stacks del editor.
    Este sistema solo provee las acciones base.
    """

    def __init__(self, estado):
        self._estado = estado
        self._manager = SaveManager()
        self._repo_config = RepositorioSaveSystem()
        self._config = self._repo_config.get_config()
        self._dev_mode = self._repo_config.get_dev_mode()

    @property
    def manager(self):
        return self._manager

    @property
    def repo_config(self):
        return self._repo_config

    # ── Guardar ──

    def guardar_slot(self, slot: int, dev: bool = False) -> tuple[bool, str]:
        """Guarda el estado actual en un slot."""
        try:
            if not dev:
                validaciones = self._repo_config.get_validaciones()
                if validaciones.get("requiere_item_para_guardar", False):
                    item_id = self._repo_config.get_save_point_item_id()
                    if item_id:
                        inv = getattr(self._estado, "inventario", None)
                        if not inv or not inv.tiene_item(item_id):
                            return False, f"Se requiere {item_id} para guardar"

            ok = self._manager.guardar(self._estado, slot, dev=dev)
            if ok:
                prefijo = "[DEV] " if dev else ""
                return True, f"{prefijo}Guardado en slot {slot}"
            return False, "Error al guardar"
        except Exception as e:
            return False, f"Error: {e}"

    # ── Cargar ──

    def cargar_slot(self, slot: int, dev: bool = False) -> tuple[bool, str]:
        """Carga el estado desde un slot."""
        try:
            estado_data = self._manager.cargar(slot, dev=dev)
            if estado_data is None:
                return False, f"Slot {slot} vacío"

            self._aplicar_estado(estado_data)
            prefijo = "[DEV] " if dev else ""
            return True, f"{prefijo}Cargado desde slot {slot}"
        except SaveCorruptError as e:
            return False, str(e)
        except Exception as e:
            return False, f"Error al cargar: {e}"

    def _aplicar_estado(self, data: dict):
        """Aplica un dict de estado cargado al GameState actual."""
        if "snake" in data:
            snake_data = data["snake"]
            snake = self._estado.snake
            if "body" in snake_data:
                snake.body = snake_data["body"]
            if "direccion" in snake_data:
                snake.direccion = snake_data["direccion"]
            if "invencible" in snake_data:
                snake.invencible = snake_data["invencible"]
            if "deuda" in snake_data:
                snake.deuda = snake_data["deuda"]
            if "skin_actual" in snake_data:
                snake.skin_actual = snake_data["skin_actual"]

        if "inventario" in data:
            inv = self._estado.inventario
            inv_data = data["inventario"]
            inv.items.clear()
            for iid, obj_data in inv_data.get("items", {}).items():
                from engine.entities.inventario import Objeto
                inv.items[iid] = Objeto(iid, obj_data.get("cantidad", 1))
            inv.equipo.clear()
            for slot_name, item_id in inv_data.get("equipo", {}).items():
                inv.equipar(item_id)

        if "monedas" in data:
            for mid, val in data["monedas"].items():
                self._estado.monedas._valores[mid] = val

        if "flags" in data:
            self._estado.flags._data.update(data["flags"])

        if "contadores" in data:
            self._estado.contadores.cargar_estado(data["contadores"])

        if "shop_state" in data:
            self._estado.shop_system.cargar_estado_save(data["shop_state"])

        if "nivel_actual" in data:
            nivel_id = data["nivel_actual"]
            if nivel_id != self._estado.level_manager.obtener_id_actual():
                self._estado.cambiar_nivel(nivel_id)

        if "posicion_mundo" in data:
            pos = data["posicion_mundo"]
            if self._estado.snake.body:
                self._estado.snake.body[0] = list(pos)

        if "camera" in data:
            cam = data["camera"]
            self._estado.camera.x = cam.get("x", 0)
            self._estado.camera.y = cam.get("y", 0)

        if "habilidades" in data:
            hab = data["habilidades"]
            if "habilidad_equipada" in hab:
                self._estado.habilidades.habilidad_equipada = hab["habilidad_equipada"]
            if "pp_actual" in hab:
                self._estado.habilidades.pp_actual = hab["pp_actual"]

    # ── Autosave ──

    def autosave(self, trigger: str):
        """Ejecuta autosave si el trigger está habilitado."""
        triggers = self._repo_config.get_autosave_triggers()
        if trigger not in triggers:
            return
        self._manager.guardar(self._estado, 0, dev=False)

    # ── Dev Mode ──

    def is_dev_mode(self):
        return self._dev_mode.get("enabled", False)

    def dev_save(self, slot: int = 1) -> tuple[bool, str]:
        if not self.is_dev_mode():
            return False, "Dev mode desactivado"
        return self.guardar_slot(slot, dev=True)

    def dev_load(self, slot: int = 1) -> tuple[bool, str]:
        if not self.is_dev_mode():
            return False, "Dev mode desactivado"
        return self.cargar_slot(slot, dev=True)
