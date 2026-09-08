from dataclasses import dataclass, field
from typing import Any


@dataclass
class ShopItem:
    """Ítem de una tienda con estado runtime (stock).

    La tienda SOLO tiene datos de tienda. El restock de items lo manejan
    los eventos globales (eventos_globales.json) vía acciones que apuntan
    por shop_id.
    """

    item_id: str
    precio: dict[str, int] = field(default_factory=dict)  # {"oro": 500, "escamas": 50}
    stock: int = 0
    stock_infinito: bool = False

    def __post_init__(self):
        # Stock inicial configurado (restaurado por restock_shop)
        self.stock_base = self.stock

    def restockear(self):
        """Restaura el stock al valor inicial configurado."""
        if self.stock_infinito:
            return
        self.stock = self.stock_base

    def puede_comprar(self, cantidad: int = 1) -> bool:
        if self.stock_infinito:
            return True
        return self.stock >= cantidad

    def comprar(self, cantidad: int = 1) -> bool:
        if not self.puede_comprar(cantidad):
            return False
        if not self.stock_infinito:
            self.stock -= cantidad
        return True


@dataclass
class Shop:
    """Tienda con items y configuración. Sin lógica de eventos."""

    shop_id: str
    nombre: str
    descripcion: str = ""
    moneda_principal: str = "oro"
    items: dict[str, ShopItem] = field(default_factory=dict)

    def get_item(self, item_id: str) -> ShopItem | None:
        return self.items.get(item_id)

    def get_items_disponibles(self, estado) -> list[ShopItem]:
        """Items visibles: stock_infinito o con stock disponible."""
        disponibles = []
        for item in self.items.values():
            if item.stock_infinito or item.stock > 0:
                disponibles.append(item)
        return disponibles

    def get_precio_compra(self, item_id: str) -> dict[str, int]:
        """Precio de venta al shop (trueque). La sección compra aún no está
        implementada: devuelve None (el shop no compra items)."""
        return None
