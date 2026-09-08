class ContadoresManager:
    """Gestiona contadores de progresión del juego.

    Los valores actuales se inicializan desde las definiciones de
    data/contadores.json (inicial). Cada contador tiene un máximo configurable.
    """

    def __init__(self, definiciones):
        self._defs = {}
        self._valores = {}
        for c in definiciones:
            cid = c.get("id")
            if not cid:
                continue
            self._defs[cid] = c
            self._valores[cid] = c.get("inicial", 0)

    def get(self, cid, default=0):
        return self._valores.get(cid, default)

    def set(self, cid, valor):
        maxv = self._defs.get(cid, {}).get("maximo", 999999)
        self._valores[cid] = max(0, min(int(valor), maxv))

    def add(self, cid, cantidad):
        actual = self._valores.get(cid, 0)
        maxv = self._defs.get(cid, {}).get("maximo", 999999)
        self._valores[cid] = max(0, min(actual + int(cantidad), maxv))

    def sub(self, cid, cantidad):
        actual = self._valores.get(cid, 0)
        self._valores[cid] = max(0, actual - int(cantidad))

    def check(self, cid, operador, valor):
        """Evalúa condición: operador en (==, !=, >, >=, <, <=)"""
        actual = self._valores.get(cid, 0)
        try:
            v = int(valor)
        except (ValueError, TypeError):
            try:
                v = float(valor)
            except (ValueError, TypeError):
                return False

        if operador == "==":
            return actual == v
        if operador == "!=":
            return actual != v
        if operador == ">":
            return actual > v
        if operador == ">=":
            return actual >= v
        if operador == "<":
            return actual < v
        if operador == "<=":
            return actual <= v
        return False

    def definir(self, cid):
        return self._defs.get(cid)

    def ids(self):
        return list(self._defs.keys())

    def get_estado(self):
        """Estado para guardar en savegame"""
        return dict(self._valores)

    def cargar_estado(self, estado):
        """Carga estado desde savegame"""
        if isinstance(estado, dict):
            for cid, valor in estado.items():
                if cid in self._defs:
                    self.set(cid, valor)

    def __repr__(self):
        return repr(self._valores)