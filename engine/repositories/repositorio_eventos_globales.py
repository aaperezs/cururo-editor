from .base import RepositorioBase


class RepositorioEventosGlobales(RepositorioBase):
    """Repositorio de eventos globales desde data/eventos_globales.json.

    Formato: {"eventos": [{event_id, trigger, ...}]}
    """

    def __init__(self):
        super().__init__("eventos_globales.json")

    def get_eventos(self):
        lista = self._data.get("eventos", [])
        if not isinstance(lista, list):
            return []
        return [e for e in lista if isinstance(e, dict)]
