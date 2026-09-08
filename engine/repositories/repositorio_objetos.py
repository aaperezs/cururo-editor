import json
import os

from .base import RUTA_DATA, RepositorioBase


class RepositorioObjetos(RepositorioBase):
    """Repositorio de objetos/equipamiento desde objetos.json + items.json"""

    def __init__(self):
        super().__init__("objetos.json")
        self._cargar_items()

    def _cargar_items(self):
        ruta = os.path.join(RUTA_DATA, "items.json")
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                items = json.load(f)
            self._data.update(items)
        except FileNotFoundError:
            pass

    def get_objeto(self, id_objeto):
        """Obtiene un objeto por su ID"""
        return self._data.get(id_objeto)

    def get_todos(self):
        """Devuelve todos los objetos"""
        return dict(self._data)

    def get_por_slot(self, slot):
        """Filtra objetos por slot (cabeza, cuello, cola)"""
        return {
            oid: obj for oid, obj in self._data.items()
            if obj.get("slot") == slot
        }
