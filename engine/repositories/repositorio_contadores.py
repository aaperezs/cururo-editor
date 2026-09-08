from .base import RepositorioBase


class RepositorioContadores(RepositorioBase):
    """Repositorio de definiciones de contadores desde data/contadores.json.

    Formato: {"contadores": [{"id", "nombre", "inicial", "maximo", "descripcion"}]}
    """

    def __init__(self):
        super().__init__("contadores.json")

    def get_definiciones(self):
        lista = self._data.get("contadores", [])
        if not isinstance(lista, list):
            return []
        return [c for c in lista if isinstance(c, dict)]

    def get_por_id(self, cid):
        for c in self.get_definiciones():
            if c.get("id") == cid:
                return c
        return None