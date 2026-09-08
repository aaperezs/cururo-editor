import random

from .base import RepositorioBase


class RepositorioBotin(RepositorioBase):
    """Repositorio de botín (drops) desde botin.json"""

    def __init__(self):
        super().__init__("botin.json")

    def get_evento(self, evento_id):
        """Obtiene un evento por su ID"""
        return self._data.get(evento_id)

    def get_todos(self):
        """Devuelve todos los eventos posibles"""
        return dict(self._data)

    def obtener_drop_aleatorio(self):
        """Selecciona un drop aleatorio según las probabilidades"""
        rand = random.random()
        acumulado = 0.0
        for eid, evento in self._data.items():
            acumulado += evento.get("probabilidad", 0)
            if rand < acumulado:
                return eid, dict(evento)
        return None, None
