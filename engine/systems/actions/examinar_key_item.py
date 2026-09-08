"""Acción examinar_key_item: muestra la descripción de un objeto clave."""

from engine.systems.action_registry import GameAction, register_action


@register_action("examinar_key_item")
class ExaminarKeyItem(GameAction):
    def execute(self, ctx, params):
        item = params.get("item", "")
        if item and hasattr(ctx.state, "inventario"):
            from data.repo_objetos import RepositorioObjetos
            repo = RepositorioObjetos()
            cfg = repo.get_objeto(item)
            desc = cfg.get("descripcion", "Sin descripción") if cfg else "Sin descripción"
            ctx.state.mensaje_temporal = f"{desc}"
            ctx.state.tiempo_mensaje = 120
        return False
