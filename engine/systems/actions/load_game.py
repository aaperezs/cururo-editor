"""Acción load_game: carga el juego."""

from engine.systems.action_registry import GameAction, register_action


@register_action("load_game")
class LoadGame(GameAction):
    def execute(self, ctx, params):
        slot = int(params.get("slot", 1))
        dev = params.get("dev", False)
        if isinstance(dev, str):
            dev = dev.lower() in ("true", "1", "si")
        if hasattr(ctx.state, "save_system"):
            ok, msg = ctx.state.save_system.cargar_slot(slot, dev=dev)
            ctx.state.mensaje_temporal = msg
            ctx.state.tiempo_mensaje = 90
        return False
