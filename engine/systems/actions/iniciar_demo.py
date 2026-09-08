"""Acción iniciar_demo: inicia una demostración de habilidad."""

from engine.systems.action_registry import GameAction, register_action


@register_action("iniciar_demo")
class IniciarDemo(GameAction):
    def execute(self, ctx, params):
        demo_id = params.get("demo_id", "")
        if demo_id:
            ctx.state.demo_habilidad_pendiente = True
            ctx.state.demo_habilidad_id = demo_id
            nivel_origen = getattr(ctx.state, '_nivel_antes_arena',
                                   getattr(ctx.state.level_manager, 'obtener_id_actual', lambda: None)())
            if nivel_origen:
                ctx.state.nivel_origen = nivel_origen
        return False
