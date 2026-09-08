"""Acción mover_a: mueve al jugador a la posición de un evento."""

from engine.systems.action_registry import GameAction, register_action

from engine.configs.constants import TAMANO_CELDA


@register_action("mover_a")
class MoverA(GameAction):
    def execute(self, ctx, params):
        evento_id = params.get("evento_id", "")
        if evento_id and ctx.manager and hasattr(ctx.state, "snake"):
            for (gx, gy, z), stack in list(ctx.manager._stacks.items()):
                for ev in stack.get("eventos", []):
                    if ev.get("id") == evento_id:
                        px = gx * TAMANO_CELDA
                        py = gy * TAMANO_CELDA
                        ctx.state.snake.body = [[px, py]]
                        ctx.state.snake.iniciar_dormido((px, py))
                        print(f"[EVENTO] mover_a -> evento '{evento_id}' en ({gx},{gy}) Z={z}")
                        return False
        return False
