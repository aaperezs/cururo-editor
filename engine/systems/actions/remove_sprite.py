"""Acción remove_sprite: elimina un tile y sus entidades."""

from engine.systems.action_registry import GameAction, register_action

from engine.configs.constants import TAMANO_CELDA


@register_action("remove_sprite")
class RemoveSprite(GameAction):
    def execute(self, ctx, params):
        x, y, z = ctx.position
        gx = x // TAMANO_CELDA
        gy = y // TAMANO_CELDA
        print(f"[REMOVE_SPRITE] ctx.position=({x},{y},{z}) gx={gx} gy={gy}")
        if hasattr(ctx.state, "remove_tile_sprite"):
            ctx.state.remove_tile_sprite(gx, gy, z)
        return False
