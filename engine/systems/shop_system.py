from engine.repositories.repositorio_tiendas import RepositorioTiendas
from engine.repositories.repositorio_objetos import RepositorioObjetos
from engine.repositories.repositorio_monedas import RepositorioMonedas
from engine.entities.shop import Shop, ShopItem


class ShopSystem:
    """Sistema central de tiendas: carga, stock, compra/venta.

    El restock de items lo manejan los eventos globales
    (eventos_globales.json) vía acciones que apuntan por shop_id.
    """

    def __init__(self):
        self._repo_tiendas = RepositorioTiendas()
        self._repo_objetos = RepositorioObjetos()
        self._repo_monedas = RepositorioMonedas()
        self._shops: dict[str, Shop] = {}
        self._cargar_tiendas()

    def _cargar_tiendas(self):
        self._shops = {}
        for shop_data in self._repo_tiendas.get_shops():
            shop = self._crear_shop_desde_data(shop_data)
            if shop.shop_id:
                self._shops[shop.shop_id] = shop

    def _crear_shop_desde_data(self, data: dict) -> Shop:
        items = {}
        for item_data in data.get("items", []):
            item_id = item_data.get("item_id", "")
            if not item_id:
                continue
            shop_item = ShopItem(
                item_id=item_id,
                precio=item_data.get("precio", {}),
                stock=item_data.get("stock", 0),
                stock_infinito=item_data.get("stock_infinito", False),
            )
            items[item_id] = shop_item

        shop = Shop(
            shop_id=data.get("shop_id", ""),
            nombre=data.get("nombre", ""),
            descripcion=data.get("descripcion", ""),
            moneda_principal=data.get("moneda_principal", "oro"),
            items=items,
        )
        return shop

    def get_shop(self, shop_id: str) -> Shop | None:
        return self._shops.get(shop_id)

    def get_todas_las_tiendas(self) -> list[Shop]:
        return list(self._shops.values())

    def _moneda_pago(self, shop: Shop, item: ShopItem) -> str:
        """Moneda con la que se paga un item: la principal de la tienda si está
        en el precio, si no la primera moneda del precio."""
        precio = item.precio or {}
        if shop.moneda_principal in precio:
            return shop.moneda_principal
        if precio:
            return next(iter(precio))
        return shop.moneda_principal

    def puede_comprar(self, estado, shop_id: str, item_id: str, cantidad: int = 1) -> tuple[bool, str]:
        shop = self.get_shop(shop_id)
        if not shop:
            return False, "Tienda no encontrada"
        item = shop.get_item(item_id)
        if not item:
            return False, "Ítem no existe en la tienda"
        if not item.puede_comprar(cantidad):
            return False, "Sin stock"
        moneda = self._moneda_pago(shop, item)
        precio = item.precio or {}
        costo = precio.get(moneda, 0) * cantidad
        if estado.monedas.get(moneda, 0) < costo:
            return False, f"Faltan {moneda}"
        return True, ""

    def comprar(self, estado, shop_id: str, item_id: str, cantidad: int = 1) -> tuple[bool, str]:
        ok, msg = self.puede_comprar(estado, shop_id, item_id, cantidad)
        if not ok:
            return False, msg

        shop = self.get_shop(shop_id)
        item = shop.get_item(item_id)
        moneda = self._moneda_pago(shop, item)
        precio = item.precio or {}
        costo = precio.get(moneda, 0) * cantidad

        estado.monedas.quitar(moneda, costo)
        estado.inventario.agregar_item(item_id, cantidad)
        item.comprar(cantidad)

        return True, f"Comprado {item_id} x{cantidad} por {costo} {moneda}"

    def puede_vender(self, estado, shop_id: str, item_id: str, cantidad: int = 1) -> tuple[bool, str, dict | None]:
        shop = self.get_shop(shop_id)
        if not shop:
            return False, "Tienda no encontrada", None
        if not estado.inventario.tiene_item(item_id, cantidad):
            return False, "No tienes ese ítem", None
        precio_compra = shop.get_precio_compra(item_id)
        if not precio_compra:
            return False, "Esta tienda no compra ese ítem", None
        return True, "", precio_compra

    def vender(self, estado, shop_id: str, item_id: str, cantidad: int = 1) -> tuple[bool, str]:
        ok, msg, precio_compra = self.puede_vender(estado, shop_id, item_id, cantidad)
        if not ok:
            return False, msg

        total = 0
        for moneda, valor in precio_compra.items():
            total = valor * cantidad
            estado.monedas.dar(moneda, total)

        estado.inventario.remover_item(item_id, cantidad)

        return True, f"Vendido {item_id} x{cantidad} por {total}"

    # ── Acciones de eventos globales ───────────────────────────

    def restockear(self, shop_id: str, item_id: str | None = None):
        """Restockea items: restaura el stock inicial configurado en shops.json."""
        shop = self.get_shop(shop_id)
        if not shop:
            return
        if item_id:
            item = shop.get_item(item_id)
            if item:
                item.restockear()
        else:
            for item in shop.items.values():
                item.restockear()

    def anadir_stock(self, shop_id: str, item_id: str, cantidad: int):
        shop = self.get_shop(shop_id)
        if not shop:
            return
        item = shop.get_item(item_id)
        if item:
            if item.stock_infinito:
                return
            item.stock += max(0, cantidad)

    def modificar_precio(self, shop_id: str, item_id: str, moneda: str, nuevo_precio: int):
        shop = self.get_shop(shop_id)
        if not shop:
            return
        item = shop.get_item(item_id)
        if item:
            item.precio[moneda] = nuevo_precio

    def get_estado_save(self) -> dict:
        """Estado para guardar en savegame."""
        estado = {}
        for shop_id, shop in self._shops.items():
            estado[shop_id] = {}
            for item_id, item in shop.items.items():
                estado[shop_id][item_id] = {
                    "stock": item.stock,
                }
        return estado

    def cargar_estado_save(self, estado_save: dict):
        """Carga estado desde savegame."""
        for shop_id, items_estado in estado_save.items():
            shop = self._shops.get(shop_id)
            if not shop:
                continue
            for item_id, item_estado in items_estado.items():
                item = shop.items.get(item_id)
                if item:
                    item.stock = item_estado.get("stock", item.stock)

    def get_config_item(self, item_id: str) -> dict | None:
        """Obtiene config base del item desde repositorio objetos."""
        return self._repo_objetos.get_objeto(item_id)
