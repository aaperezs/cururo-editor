from .base import RepositorioBase


class RepositorioTiendas(RepositorioBase):
    """Repositorio de definiciones de tiendas desde data/shops.json.

    Formato: {"shops": [{...}]}
    """

    def __init__(self):
        super().__init__("shops.json")

    def get_shops(self):
        lista = self._data.get("shops", [])
        if not isinstance(lista, list):
            return []
        return [s for s in lista if isinstance(s, dict)]

    def get_shop(self, shop_id):
        for s in self.get_shops():
            if s.get("shop_id") == shop_id:
                return s
        return None