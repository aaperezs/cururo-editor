"""Acción save_game: guarda el juego."""

from engine.systems.action_registry import GameAction, register_action


@register_action("save_game")
class SaveGame(GameAction):
    def execute(self, ctx, params):
        slot = int(params.get("slot", 1))
        dev = params.get("dev", False)
        if isinstance(dev, str):
            dev = dev.lower() in ("true", "1", "si")
        if hasattr(ctx.state, "save_system"):
            ok, msg = ctx.state.save_system.guardar_slot(slot, dev=dev)
            ctx.state.mensaje_temporal = msg
            ctx.state.tiempo_mensaje = 90
            if ok and not dev:
                validaciones = ctx.state.save_system.repo_config.get_validaciones()
                if validaciones.get("item_se_consume", False):
                    item_id = ctx.state.save_system.repo_config.get_save_point_item_id()
                    if item_id and hasattr(ctx.state, "inventario"):
                        ctx.state.inventario.remover_item(item_id)
        return False
