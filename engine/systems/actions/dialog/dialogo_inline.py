"""Acción dialogo_inline: inicia un diálogo inline con líneas de texto."""

from engine.systems.action_registry import GameAction, register_action


@register_action("dialogo_inline")
class DialogoInline(GameAction):
    def execute(self, ctx, params):
        lineas = params.get("lineas", [])
        quien = params.get("quien", "")
        if lineas and ctx.dialog_service:
            ctx.dialog_service.iniciar_inline(lineas, nombre=quien)
            ctx.manager._bloqueo_por = "dialogo"
            return True
        return False
