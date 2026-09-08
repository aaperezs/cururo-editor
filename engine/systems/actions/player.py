"""Acciones migradas automaticamente desde stack_manager._ejecutar_accion.

NO EDITAR MANUALMENTE - generado por scripts/migrate_trivial_actions.py
"""

from engine.systems.action_registry import GameAction, register_action


from engine.configs.constants import TAMANO_CELDA

@register_action("remove_escamas")
class RemoveEscamas(GameAction):
    def execute(self, ctx, params):
        cantidad = int(params.get("cantidad", 1))
        if hasattr(ctx.state, "snake"):
            ctx.state.snake.perder_escamas(cantidad)
        return False


@register_action("bloquear_mandos")
class BloquearMandos(GameAction):
    def execute(self, ctx, params):
        bloquear = params.get("bloquear", True)
        if isinstance(bloquear, str):
            bloquear = bloquear.lower() in ("true", "1", "si")
        ctx.state.mandos_bloqueados = bool(bloquear)
        return False


@register_action("cambiar_skin")
class CambiarSkin(GameAction):
    def execute(self, ctx, params):
        skin = params.get("skin", "")
        if skin and hasattr(ctx.state, "snake"):
            ctx.state.snake.set_skin(skin)
        return False


@register_action("avanzar")
class Avanzar(GameAction):
    def execute(self, ctx, params):
        direccion = params.get("direccion", "")
        if direccion and hasattr(ctx.state, "snake"):
            ctx.state.snake.cambiar_direccion(direccion.upper())
            ctx.state.snake.mover()
        return False


@register_action("despertar")
class Despertar(GameAction):
    def execute(self, ctx, params):
        if hasattr(ctx.state, "snake"):
            ctx.state.snake.despertar()
        return False
