import pygame


class BaseScreen:
    def __init__(self, config=None):
        self.config = config or {}
        self.duration_ms = self.config.get("duration_ms", 0)
        self._elapsed_ms = 0

    def handle_event(self, event):
        return False

    def update(self, dt_ms):
        if self.duration_ms > 0:
            self._elapsed_ms += dt_ms
            if self._elapsed_ms >= self.duration_ms:
                return True
        return False

    def draw(self, surface):
        pass
