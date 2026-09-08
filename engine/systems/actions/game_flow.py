"""Acciones migradas automaticamente desde stack_manager._ejecutar_accion.

NO EDITAR MANUALMENTE - generado por scripts/migrate_trivial_actions.py
"""

from engine.systems.action_registry import GameAction, register_action


from engine.configs.constants import TAMANO_CELDA

@register_action("fin_demo")
class FinDemo(GameAction):
    def execute(self, ctx, params):
        ctx.state.volver_a_menu = True
        ctx.state.corriendo = False
        return False
