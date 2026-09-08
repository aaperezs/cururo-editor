from .base import RepositorioBase


class RepositorioHabilidades(RepositorioBase):
    """Repositorio de habilidades y skins desde habilidades.json"""

    def __init__(self):
        super().__init__("habilidades.json")
        self._habilidades = self._data.get("habilidades", {})
        self._skins = self._data.get("skins", {})
        self._iniciales = self._data.get("iniciales", [])

    def get_habilidad(self, hid):
        """Obtiene config de una habilidad por su ID"""
        return self._habilidades.get(hid)

    def get_todas(self):
        """Devuelve todas las habilidades"""
        return dict(self._habilidades)

    def get_skin(self, efecto):
        """Devuelve colores de skin para un efecto"""
        return self._skins.get(efecto, self._skins.get("base", {}))

    def get_iniciales(self):
        """Devuelve lista de habilidades iniciales"""
        return list(self._iniciales)

    def get_habilidad_por_efecto(self, efecto):
        """Devuelve el ID de la habilidad por su efecto"""
        for hid, config in self._habilidades.items():
            if config.get("efecto") == efecto:
                return hid
        return None
