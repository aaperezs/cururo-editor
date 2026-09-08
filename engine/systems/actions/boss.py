"""Acciones migradas automaticamente desde stack_manager._ejecutar_accion.

NO EDITAR MANUALMENTE - generado por scripts/migrate_trivial_actions.py
"""

from engine.systems.action_registry import GameAction, register_action


from engine.configs.constants import TAMANO_CELDA

@register_action("mostrar_boss")
class MostrarBoss(GameAction):
    def execute(self, ctx, params):
        visible = params.get("visible", True)
        if isinstance(visible, str):
            visible = visible.lower() in ("true", "1", "si")
        if hasattr(ctx.state, "boss") and ctx.state.boss:
            ctx.state.boss.vivo = bool(visible)
        return False
