from .base import RepositorioBase


class RepositorioJefes(RepositorioBase):
    """Repositorio de configuraciones de jefes desde bosses.json"""

    def __init__(self):
        super().__init__("bosses.json")

    def get_config(self, tipo):
        """Obtiene config de un jefe por su tipo"""
        return self._data.get(tipo, self._data.get("tronco", {}))
