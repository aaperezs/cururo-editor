"""Acción remove_moneda: quita monedas/escamas al jugador."""

from engine.systems.action_registry import GameAction, register_action


@register_action("remove_moneda")
class RemoveMoneda(GameAction):
    def execute(self, ctx, params):
        moneda = params.get("moneda", "")
        cantidad = int(params.get("cantidad", 1))
        if ctx.manager:
            ctx.manager.quitar_moneda(moneda, cantidad)
        return False
