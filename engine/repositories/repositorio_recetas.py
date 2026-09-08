from .base import RepositorioBase


class RepositorioRecetas(RepositorioBase):
    """Repositorio de recetas de forja desde recetas.json"""

    def __init__(self):
        super().__init__("recetas.json")

    def get_receta(self, id_receta):
        """Obtiene una receta por su ID"""
        return self._data.get(id_receta)

    def get_todas(self):
        """Devuelve todas las recetas"""
        return dict(self._data)

    def puede_fabricar(self, id_receta, inventario):
        """Verifica si se puede fabricar una receta con el inventario dado"""
        receta = self.get_receta(id_receta)
        if not receta:
            return False
        requiere = receta.get("requiere", {})
        for material, cantidad in requiere.items():
            if inventario.get(material, 0) < cantidad:
                return False
        return True

    def consumir_materiales(self, id_receta, inventario):
        """Consume los materiales de una receta del inventario"""
        receta = self.get_receta(id_receta)
        if not receta:
            return False
        requiere = receta.get("requiere", {})
        for material, cantidad in requiere.items():
            if inventario.get(material, 0) < cantidad:
                return False
        for material, cantidad in requiere.items():
            inventario[material] -= cantidad
            if inventario[material] <= 0:
                del inventario[material]
        return True
