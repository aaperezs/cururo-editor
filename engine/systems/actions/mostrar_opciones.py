"""Acción mostrar_opciones: muestra opciones de selección."""

from engine.systems.action_registry import GameAction, register_action


@register_action("mostrar_opciones")
class MostrarOpciones(GameAction):
    def execute(self, ctx, params):
        opciones_data = params.get("opciones", [])
        if opciones_data and hasattr(ctx.state, "mostrando_opciones"):
            ctx.state.mostrando_opciones = True
            ctx.state.opciones = opciones_data
            ctx.state.opcion_seleccionada = -1
            ctx.manager._bloqueo_por = "choice"
            return True
        return False
