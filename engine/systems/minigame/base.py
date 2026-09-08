class MiniJuegoBase:
    def __init__(self, config):
        self.config = config
        self._terminado = False

    def iniciar(self):
        self._terminado = False

    def handle_event(self, event):
        return False

    def actualizar(self, dt_ms):
        return self._terminado

    def dibujar(self, surface):
        pass

    def get_resultado(self):
        return self.config.get("flags_resultado", {})
