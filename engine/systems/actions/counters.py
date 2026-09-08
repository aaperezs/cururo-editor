"""Acciones migradas automaticamente desde stack_manager._ejecutar_accion.

NO EDITAR MANUALMENTE - generado por scripts/migrate_trivial_actions.py
"""

from engine.systems.action_registry import GameAction, register_action


from engine.configs.constants import TAMANO_CELDA

@register_action("increment_contador")
class IncrementContador(GameAction):
    def execute(self, ctx, params):
        contador_id = params.get("contador_id", "")
        cantidad = int(params.get("cantidad", 1))
        if contador_id and hasattr(ctx.state, "contadores"):
            ctx.state.contadores.add(contador_id, cantidad)
        return False


@register_action("set_contador")
class SetContador(GameAction):
    def execute(self, ctx, params):
        contador_id = params.get("contador_id", "")
        valor = int(params.get("valor", 0))
        if contador_id and hasattr(ctx.state, "contadores"):
            ctx.state.contadores.set(contador_id, valor)
        return False
