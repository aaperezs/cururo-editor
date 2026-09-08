class FlagsManager:
    """Gestiona flags del juego (variables de estado para branching y condiciones)"""

    def __init__(self):
        self._data = {}

    def get(self, nombre, default=None):
        return self._data.get(nombre, default)

    def set(self, nombre, valor):
        self._data[nombre] = valor

    def add(self, nombre, cantidad):
        actual = self._data.get(nombre, 0)
        if not isinstance(actual, (int, float)):
            actual = 0
        self._data[nombre] = actual + cantidad

    def check(self, nombre, operador, valor):
        actual = self._data.get(nombre)
        if operador in ("es_verdadero",):
            return bool(actual) is True
        if operador in ("es_falso",):
            return bool(actual) is False
        if actual is None:
            return False
        if isinstance(valor, str):
            try:
                valor = int(valor)
            except ValueError:
                try:
                    valor = float(valor)
                except ValueError:
                    pass
        if operador == ">=":
            return actual >= valor
        if operador == "<=":
            return actual <= valor
        if operador == ">":
            return actual > valor
        if operador == "<":
            return actual < valor
        if operador == "==":
            return actual == valor
        if operador == "!=":
            return actual != valor
        return False

    def __contains__(self, nombre):
        return nombre in self._data

    def __repr__(self):
        return repr(self._data)
