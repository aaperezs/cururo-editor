"""Acción spawn_entity: genera una entidad en el mapa."""

from engine.systems.action_registry import GameAction, register_action

from engine.configs.constants import TAMANO_CELDA


@register_action("spawn_entity")
class SpawnEntity(GameAction):
    def execute(self, ctx, params):
        sprite_id = params.get("sprite_id", "")
        ox = int(params.get("offset_x", 0))
        oy = int(params.get("offset_y", 0))
        z = int(params.get("z", 0))
        x, y, _ = ctx.position
        sx = x + ox * TAMANO_CELDA
        sy = y + oy * TAMANO_CELDA
        if ctx.manager:
            ctx.manager.spawn_from_sprite(sprite_id, sx, sy)
        return False
