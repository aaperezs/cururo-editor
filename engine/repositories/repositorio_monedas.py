from .base import RepositorioBase


class RepositorioMonedas(RepositorioBase):
    """Repositorio de definiciones de monedas desde data/monedas.json.

    Formato: {"monedas": [{"id", "label", "valor_inicial", "icono", "color", "principal"}]}
    """

    def __init__(self):
        super().__init__("monedas.json")

    def get_definiciones(self):
        lista = self._data.get("monedas", [])
        if not isinstance(lista, list):
            return []
        return [m for m in lista if isinstance(m, dict)]

    def get_por_id(self, mid):
        for m in self.get_definiciones():
            if m.get("id") == mid:
                return m
        return None