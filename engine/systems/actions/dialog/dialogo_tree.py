"""Acción dialogo_tree: inicia un árbol de diálogo."""

from engine.systems.action_registry import GameAction, register_action


@register_action("dialogo_tree")
class DialogoTree(GameAction):
    def execute(self, ctx, params):
        dialogo_id = params.get("dialogo_id", "")
        if "/" in dialogo_id and ctx.dialog_service:
            personaje, contexto = dialogo_id.split("/", 1)
            ctx.manager._arbol_dialogo = {
                "personaje": personaje,
                "contexto": contexto,
                "nid_actual": None,
                "_iniciado": False,
            }
            ctx.manager.avanzar_arbol_dialogo(ctx.state)
            ctx.manager._bloqueo_por = "dialogo_tree"
            return True
        return False
