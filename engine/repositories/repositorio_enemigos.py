from .base import RepositorioBase


class RepositorioEnemigos(RepositorioBase):
    """Repositorio de configuraciones de enemigos desde enemigos.json"""

    def __init__(self):
        super().__init__("enemigos.json")
        self._char_map = self._data.get("char_map", {})
        self._melee = self._data.get("melee", {})
        self._shooter = self._data.get("shooter", {})

    def get_melee_config(self, subtipo):
        """Obtiene config de enemigo melee por subtipo"""
        return self._melee.get(subtipo, self._melee.get("horizontal", {}))

    def get_shooter_config(self, subtipo):
        """Obtiene config de enemigo shooter por subtipo"""
        return self._shooter.get(subtipo, self._shooter.get("shooter_h", {}))

    def get_enemigo_config(self, tipo, subtipo):
        """Obtiene config por tipo y subtipo (interfaz compatible con la antigua)"""
        if tipo == "melee":
            return self.get_melee_config(subtipo)
        elif tipo == "shooter":
            return self.get_shooter_config(subtipo)
        return {}

    def get_char_map(self):
        """Devuelve el mapeo de caracteres a (tipo, subtipo)"""
        return dict(self._char_map)
