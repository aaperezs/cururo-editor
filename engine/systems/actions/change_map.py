"""Acción change_map: cambia de nivel/mapa."""

from engine.systems.action_registry import GameAction, register_action


@register_action("change_map")
class ChangeMap(GameAction):
    def execute(self, ctx, params):
        nivel = params.get("nivel", "")
        exit_id = params.get("exit_id", "")
        if nivel and hasattr(ctx.state, "cambiar_nivel"):
            ctx.state.gate_destino = nivel
            ctx.state.gate_salida_id = exit_id if exit_id else None
            ctx.state.cambiando_nivel = True
        return False
