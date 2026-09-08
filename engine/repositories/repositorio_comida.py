from .base import RepositorioBase


class RepositorioComida(RepositorioBase):
    """Repositorio de configuraciones de comida desde comida.json"""

    def __init__(self):
        super().__init__("comida.json")
        self._tipos = self._data.get("tipos", {})
        self._probs = self._data.get("probabilidades", {})

    def get_tipo(self, nombre):
        """Obtiene config de un tipo de comida por nombre"""
        return self._tipos.get(nombre)

    def get_tipos(self):
        """Devuelve todos los tipos"""
        return dict(self._tipos)

    def get_probabilidad(self, tipo):
        """Devuelve probabilidad de spawn para un tipo"""
        return self._probs.get(tipo, 0)
