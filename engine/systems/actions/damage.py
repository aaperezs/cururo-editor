"""Acción damage: inflige daño al jugador."""

from engine.systems.action_registry import GameAction, register_action


@register_action("damage")
class Damage(GameAction):
    def execute(self, ctx, params):
        x, y, z = ctx.position
        cantidad = int(params.get("cantidad", 1))
        if not hasattr(ctx.state, "snake"):
            return False
        snake = ctx.state.snake
        if snake.invencible or getattr(ctx.state, "god_mode", False):
            return False
        if snake.get_longitud() <= 3:
            ctx.state.game_over = True
            ctx.state.death_cause = "Daño letal en evento"
            return False
        max_perder = snake.get_longitud() - 3
        if cantidad > max_perder:
            cantidad = max_perder
        if cantidad <= 0:
            return False
        perdidos = snake.perder_segmentos(cantidad)
        if perdidos:
            from engine.entities.segmento_perdido import SegmentoPerdido
            for pos in perdidos:
                if pos:
                    seg = SegmentoPerdido(pos[0], pos[1],
                        ctx.state.nivel_ancho, ctx.state.nivel_alto)
                    ctx.state.segmentos_perdidos.append(seg)
            from engine.systems.event_bus import EventoDamageInfligido
            ctx.state.event_bus.publicar(EventoDamageInfligido(
                cantidad=len(perdidos),
                fuente="event",
                posicion=(x, y),
            ))
            mensaje = params.get("mensaje", f"¡Perdiste {len(perdidos)} segmentos!")
            ctx.state.mensaje_temporal = mensaje
            ctx.state.tiempo_mensaje = 60
        return False
