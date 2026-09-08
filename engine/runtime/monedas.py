class MonedasManager:
    """Gestiona las monedas del juego (contadores de primera clase).

    Los valores actuales se inicializan desde las definiciones de
    data/monedas.json (valor_inicial).

    La moneda orm "escamas" la resuelve el stack_manager vía snake (shim,
    "escamas == largo de la snake" es un tema aparte).
    """

    def __init__(self, definiciones):
        self._defs = {}
        self._valores = {}
        for m in definiciones:
            mid = m.get("id")
            if not mid:
                continue
            self._defs[mid] = m
            self._valores[mid] = m.get("valor_inicial", 0)

    def get(self, mid, default=0):
        return self._valores.get(mid, default)

    def dar(self, mid, cantidad):
        self._valores[mid] = self._valores.get(mid, 0) + max(0, int(cantidad))

    def quitar(self, mid, cantidad):
        actual = self._valores.get(mid, 0)
        self._valores[mid] = max(0, actual - max(0, int(cantidad)))

    def definir(self, mid):
        return self._defs.get(mid)

    def ids(self):
        return list(self._defs.keys())

    def principal(self):
        for mid, m in self._defs.items():
            if m.get("principal"):
                return mid
        return None

    def get_definiciones(self):
        return list(self._defs.values())

    def __repr__(self):
        return repr(self._valores)