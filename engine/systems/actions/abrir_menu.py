"""Acción abrir_menu: abre un menú del juego."""

from engine.systems.action_registry import GameAction, register_action


@register_action("abrir_menu")
class AbrirMenu(GameAction):
    def execute(self, ctx, params):
        menu_id = params.get("menu_id", "")
        if menu_id and hasattr(ctx.state, "menu") and hasattr(ctx.state.menu, "abrir_menu"):
            ctx.state.mostrando_inventario = True
            ctx.state.menu.abrir_menu(menu_id)
        return False
