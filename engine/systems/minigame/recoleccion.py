import random
import pygame

from .base import MiniJuegoBase


class RecoleccionMiniJuego(MiniJuegoBase):
    def __init__(self, config):
        super().__init__(config)
        self.tiempo_limite = config.get("tiempo_limite", 30) * 1000
        self.objetivo = config.get("objetivo", 5)
        self.items = [dict(it) for it in config.get("items", [])]
        self._elapsed = 0
        self._score = 0
        self._cursor = [400, 300]
        self._c_width = config.get("canvas_w", 800)
        self._c_height = config.get("canvas_h", 600)
        self._font = None

    def iniciar(self):
        super().iniciar()
        self._elapsed = 0
        self._score = 0
        self._cursor = [self._c_width // 2, self._c_height // 2]
        for it in self.items:
            it["recogido"] = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            step = 20
            if event.key == pygame.K_UP:
                self._cursor[1] = max(0, self._cursor[1] - step)
            elif event.key == pygame.K_DOWN:
                self._cursor[1] = min(self._c_height, self._cursor[1] + step)
            elif event.key == pygame.K_LEFT:
                self._cursor[0] = max(0, self._cursor[0] - step)
            elif event.key == pygame.K_RIGHT:
                self._cursor[0] = min(self._c_width, self._cursor[0] + step)
            elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                self._intentar_recoger()
        return False

    def _intentar_recoger(self):
        cx, cy = self._cursor
        for it in self.items:
            if it.get("recogido"):
                continue
            ix = it.get("x", 0)
            iy = it.get("y", 0)
            r = it.get("radio", 20)
            if (cx - ix) ** 2 + (cy - iy) ** 2 <= r ** 2:
                it["recogido"] = True
                self._score += it.get("puntos", 1)

    def actualizar(self, dt_ms):
        if self._terminado:
            return True
        self._elapsed += dt_ms
        if self._elapsed >= self.tiempo_limite or self._score >= self.objetivo:
            self._terminado = True
            return True
        return False

    def dibujar(self, surface):
        surface.fill((20, 25, 35))
        remaining = max(0, (self.tiempo_limite - self._elapsed) // 1000)
        if not self._font:
            self._font = pygame.font.SysFont("Arial", 20)
        info = self._font.render(
            f"Recolecta: {self._score}/{self.objetivo}  Tiempo: {remaining}s",
            True, (200, 220, 240)
        )
        surface.blit(info, (10, 10))
        for it in self.items:
            if it.get("recogido"):
                continue
            ix = it.get("x", 0)
            iy = it.get("y", 0)
            r = it.get("radio", 20)
            color = tuple(it.get("color", [200, 200, 50]))
            pygame.draw.circle(surface, color, (ix, iy), r)
            pygame.draw.circle(surface, (255, 255, 200), (ix, iy), r, 2)
        cx, cy = self._cursor
        pygame.draw.circle(surface, (100, 200, 255), (cx, cy), 8, 2)
        pygame.draw.line(surface, (100, 200, 255), (cx - 12, cy), (cx + 12, cy), 2)
        pygame.draw.line(surface, (100, 200, 255), (cx, cy - 12), (cx, cy + 12), 2)

    def get_resultado(self):
        return self.config.get("flags_resultado", {})
