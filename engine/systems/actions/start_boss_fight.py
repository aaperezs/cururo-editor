"""Acción start_boss_fight: inicia un combate de boss."""

from engine.systems.action_registry import GameAction, register_action


@register_action("start_boss_fight")
class StartBossFight(GameAction):
    def execute(self, ctx, params):
        if ctx.battle_service and hasattr(ctx.state, 'arena_boss') and ctx.state.arena_boss:
            arena = ctx.state.arena_boss
            boss = getattr(ctx.state, 'boss', None)
            if boss and boss.vivo:
                if getattr(arena, 'es_nivel_completo', False):
                    arena.activar_combate(ctx.state.snake, ctx.state)
                else:
                    punto_entrada = (arena.x + 60, arena.y + arena.alto - 60)
                    arena.activar_con_entrada(boss, punto_entrada, ctx.state.snake, ctx.state)
        return False
