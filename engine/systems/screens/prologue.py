import sys

import pygame

from engine.systems.prologo import PrologoSystem


class PrologueScreen:
    def __init__(self, config=None):
        self.config = config or {}
        self.duration_ms = self.config.get("duration_ms", 0)
        self._elapsed_ms = 0
        self._prologo = PrologoSystem()
        self._prologo.iniciar()

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_SPACE, pygame.K_RETURN):
            self._prologo.avanzar()
            return self._prologo.terminado
        return False

    def update(self, dt_ms):
        self._prologo.actualizar()
        if self.duration_ms > 0:
            self._elapsed_ms += dt_ms
            if self._elapsed_ms >= self.duration_ms:
                return True
        return False

    def draw(self, surface):
        self._prologo.dibujar(surface)
