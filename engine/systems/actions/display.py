"""Acciones migradas automaticamente desde stack_manager._ejecutar_accion.

NO EDITAR MANUALMENTE - generado por scripts/migrate_trivial_actions.py
"""

from engine.systems.action_registry import GameAction, register_action


from engine.configs.constants import TAMANO_CELDA

@register_action("replace_sprite")
class ReplaceSprite(GameAction):
    def execute(self, ctx, params):
        x, y, z = ctx.position
        sprite_id = params.get("sprite_id", "")
        gx = x // TAMANO_CELDA
        gy = y // TAMANO_CELDA
        print(f"[REPLACE_SPRITE] ctx.position=({x},{y},{z}) gx={gx} gy={gy} sprite_id='{sprite_id}'")
        if hasattr(ctx.state, "replace_tile_sprite"):
            ctx.state.replace_tile_sprite(gx, gy, sprite_id, z)
        return False


@register_action("cambiar_fondo")
class CambiarFondo(GameAction):
    def execute(self, ctx, params):
        sprite_id = params.get("sprite_id", "")
        if sprite_id and hasattr(ctx.state, "fondo_activo"):
            ctx.state.fondo_activo = sprite_id
            ctx.state.fondo_modo = params.get("modo", "fill")
        return False
