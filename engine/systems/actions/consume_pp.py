"""Acción consume_pp: consume puntos de poder."""

from engine.systems.action_registry import GameAction, register_action


@register_action("consume_pp")
class ConsumePp(GameAction):
    def execute(self, ctx, params):
        cantidad = int(params.get("cantidad", 1))
        if hasattr(ctx.state, "habilidades"):
            for _ in range(cantidad):
                ctx.state.habilidades.usar_habilidad()
        return False
