"""Acción open_shop: abre una tienda."""

from engine.systems.action_registry import GameAction, register_action


@register_action("open_shop")
class OpenShop(GameAction):
    def execute(self, ctx, params):
        shop_id = params.get("shop_id", "") or params.get("shop", "")
        if shop_id and ctx.shop_service:
            shop = ctx.shop_service.get_shop(shop_id)
            if shop:
                ctx.state.shop_actual = shop
                if hasattr(ctx.state, "menu") and hasattr(ctx.state.menu, "abrir_menu"):
                    ctx.state.menu.abrir_menu("shop")
                ctx.state.mostrando_inventario = True
                ctx.manager._bloqueo_por = "shop"
                return True
        return False
