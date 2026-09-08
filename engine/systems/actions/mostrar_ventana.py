"""Acción mostrar_ventana: muestra una ventana de texto."""

from engine.systems.action_registry import GameAction, register_action


@register_action("mostrar_ventana")
class MostrarVentana(GameAction):
    def execute(self, ctx, params):
        ventana_id = params.get("ventana_id", "")
        if ventana_id and hasattr(ctx.state, "ventana"):
            ctx.state.ventana.iniciar(ventana_id)
            if ctx.manager:
                ctx.manager._bloqueo_por = "ventana"
            return True
        return False
