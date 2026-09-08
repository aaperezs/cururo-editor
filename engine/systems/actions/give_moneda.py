"""Acción give_moneda: da monedas/escamas al jugador."""

from engine.systems.action_registry import GameAction, register_action


@register_action("give_moneda")
class GiveMoneda(GameAction):
    def execute(self, ctx, params):
        moneda = params.get("moneda", "")
        cantidad = int(params.get("cantidad", 1))
        if ctx.manager:
            ctx.manager.dar_moneda(moneda, cantidad)
        return False
