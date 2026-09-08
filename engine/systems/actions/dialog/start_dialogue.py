"""Acción start_dialogue: inicia un diálogo con un personaje."""

from engine.systems.action_registry import GameAction, register_action


@register_action("start_dialogue")
class StartDialogue(GameAction):
    def execute(self, ctx, params):
        dialogo_id = params.get("dialogo_id", "")
        if "/" in dialogo_id and ctx.dialog_service:
            personaje, contexto = dialogo_id.split("/", 1)

            # Guardar opciones padre ANTES de iniciar sub-diálogo
            opciones_padre = None
            if (hasattr(ctx.state, "dialogo") and ctx.state.dialogo.activo
                    and ctx.state.dialogo.options):
                opciones_padre = ctx.state.dialogo.options[0].copy()

            al_terminar = None
            if opciones_padre:
                def callback_restaurar():
                    ctx.state.dialogo.options = [opciones_padre]
                    ctx.manager.mostrar_opciones_plano(ctx.state)
                al_terminar = callback_restaurar

            ctx.dialog_service.iniciar(
                personaje, contexto,
                al_terminar=al_terminar,
            )
            ctx.manager._bloqueo_por = "dialogo"
            return True
        return False
