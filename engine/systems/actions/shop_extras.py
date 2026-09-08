"""Acciones migradas automaticamente desde stack_manager._ejecutar_accion.

NO EDITAR MANUALMENTE - generado por scripts/migrate_trivial_actions.py
"""

from engine.systems.action_registry import GameAction, register_action


from engine.configs.constants import TAMANO_CELDA

@register_action("restock_shop")
class RestockShop(GameAction):
    def execute(self, ctx, params):
        shop_id = params.get("shop_id", "")
        item_id = params.get("item_id", "")
        if shop_id and hasattr(ctx.state, "shop_system"):
            ctx.state.shop_system.restockear(shop_id, item_id or None)
        return False


@register_action("add_shop_stock")
class AddShopStock(GameAction):
    def execute(self, ctx, params):
        shop_id = params.get("shop_id", "")
        item_id = params.get("item_id", "")
        cantidad = int(params.get("cantidad", 1))
        if shop_id and item_id and hasattr(ctx.state, "shop_system"):
            ctx.state.shop_system.anadir_stock(shop_id, item_id, cantidad)
        return False


@register_action("modify_shop_price")
class ModifyShopPrice(GameAction):
    def execute(self, ctx, params):
        shop_id = params.get("shop_id", "")
        item_id = params.get("item_id", "")
        moneda = params.get("moneda", "")
        nuevo_precio = int(params.get("precio", 0))
        if shop_id and item_id and moneda and hasattr(ctx.state, "shop_system"):
            ctx.state.shop_system.modificar_precio(shop_id, item_id, moneda, nuevo_precio)
        return False
