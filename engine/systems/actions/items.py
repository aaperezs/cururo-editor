"""Acciones de inventario (give_item, remove_item)."""

from engine.systems.action_registry import GameAction, register_action
from engine.repositories.repositorio_objetos import RepositorioObjetos


@register_action("give_item")
class GiveItem(GameAction):
    def execute(self, ctx, params):
        estado = ctx.state
        item = params.get("item", "")
        cantidad = int(params.get("cantidad", 1))
        if item and hasattr(estado, "inventario"):
            estado.inventario.agregar_item(item, cantidad)
            repo = RepositorioObjetos()
            cfg = repo.get_objeto(item)
            es_clave = cfg.get("tipo") == "objeto_clave" if cfg else False
            nombre = cfg.get("nombre", item) if cfg else item
            if es_clave:
                mensaje = f"¡Obtuviste [Objeto Clave] {nombre}!"
                estado.tiempo_mensaje = 90
                if hasattr(estado, "menu") and hasattr(estado.menu, "abrir_apartado"):
                    estado.menu.abrir_apartado("key_items")
            else:
                mensaje = f"¡{nombre} x{cantidad}!"
                estado.tiempo_mensaje = 60
            estado.mensaje_temporal = mensaje
        return False


@register_action("remove_item")
class RemoveItem(GameAction):
    def execute(self, ctx, params):
        estado = ctx.state
        item = params.get("item", "")
        cantidad = int(params.get("cantidad", 1))
        if item and hasattr(estado, "inventario"):
            estado.inventario.remover_item(item, cantidad)
        return False
