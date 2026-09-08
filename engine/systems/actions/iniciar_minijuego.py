"""Acción iniciar_minijuego: inicia un minijuego."""

from engine.systems.action_registry import GameAction, register_action


@register_action("iniciar_minijuego")
class IniciarMinijuego(GameAction):
    def execute(self, ctx, params):
        minijuego_id = params.get("minijuego_id", "")
        if minijuego_id and hasattr(ctx.state, "sistema_minijuego"):
            ok = ctx.state.sistema_minijuego.iniciar(minijuego_id)
            if ok:
                ctx.state.mostrando_minijuego = True
                ctx.state.minijuego_id = minijuego_id
                ctx.manager._bloqueo_por = "minijuego"
                return True
        return False
