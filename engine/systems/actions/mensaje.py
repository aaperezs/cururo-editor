"""Acción show_message (legacy -> registry)."""

from engine.systems.action_registry import GameAction, register_action


@register_action("show_message")
class ShowMessage(GameAction):
    def execute(self, ctx, params):
        mensaje = params.get("mensaje", "")
        if mensaje:
            ctx.state.mensaje_temporal = mensaje
            ctx.state.tiempo_mensaje = 90
        return False
