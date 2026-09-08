"""Acción close_dialog: cierra el diálogo activo."""

from engine.systems.action_registry import GameAction, register_action


@register_action("close_dialog")
class CloseDialog(GameAction):
    def execute(self, ctx, params):
        farewell = params.get("farewell_text", "")

        if farewell and ctx.dialog_service:
            # Obtener nombre del personaje actual del diálogo activo
            nombre = ""
            if hasattr(ctx.state, "dialogo"):
                nombre = getattr(ctx.state.dialogo, "personaje_nombre", "")

            def callback_cerrar_farewell():
                # Cerrar todo después de mostrar el farewell
                if ctx.dialog_service:
                    ctx.dialog_service.activo = False
                    ctx.dialog_service.terminado = False
                    ctx.dialog_service.al_terminar = None
                ctx.state.mostrando_opciones = False
                ctx.state.opciones = []
                if hasattr(ctx.state, "dialogo"):
                    ctx.state.dialogo.options = []
                ctx.manager._bloqueo_por = None
                if hasattr(ctx.state, "menu") and hasattr(ctx.state.menu, "cerrar"):
                    ctx.state.menu.cerrar()

            ctx.dialog_service.iniciar_inline(
                [farewell],
                nombre=nombre,
                al_terminar=callback_cerrar_farewell,
            )
            ctx.manager._bloqueo_por = "dialogo"
            return True

        # Sin farewell: cerrar directamente (comportamiento actual)
        if ctx.dialog_service:
            ctx.dialog_service.activo = False
            ctx.dialog_service.terminado = True
            ctx.dialog_service.al_terminar = None
        ctx.state.mostrando_opciones = False
        ctx.state.opciones = []
        if hasattr(ctx.state, "dialogo"):
            ctx.state.dialogo.options = []
        ctx.manager._bloqueo_por = None
        return True
