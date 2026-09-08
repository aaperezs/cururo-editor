import pygame

from .base import MiniJuegoBase


class TimingMiniJuego(MiniJuegoBase):
    def __init__(self, config):
        super().__init__(config)
        self.secuencia = list(config.get("secuencia", []))
        self._elapsed = 0
        self._current = 0
        self._score = 0
        self._total = len(self.secuencia)
        self._failed = False
        self._font = None
        self._c_width = config.get("canvas_w", 800)
        self._c_height = config.get("canvas_h", 600)

    def iniciar(self):
        super().iniciar()
        self._elapsed = 0
        self._current = 0
        self._score = 0
        self._failed = False

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN and self._current < self._total:
            step = self.secuencia[self._current]
            tecla_esperada = step.get("tecla", "SPACE")
            tecla_map = {
                "UP": pygame.K_UP, "DOWN": pygame.K_DOWN,
                "LEFT": pygame.K_LEFT, "RIGHT": pygame.K_RIGHT,
                "SPACE": pygame.K_SPACE, "RETURN": pygame.K_RETURN,
                "Z": pygame.K_z, "X": pygame.K_x,
            }
            expected = tecla_map.get(tecla_esperada.upper(), pygame.K_SPACE)
            ventana_ms = step.get("ventana_ms", 300)
            step_time = step.get("tiempo_ms", 0)
            diff = abs(self._elapsed - step_time)
            if event.key == expected:
                if diff <= ventana_ms:
                    self._score += 1
                else:
                    self._failed = True
                self._current += 1
        return False

    def actualizar(self, dt_ms):
        if self._terminado:
            return True
        self._elapsed += dt_ms
        if self._current >= self._total or self._failed:
            self._terminado = True
            return True
        if self._total > 0:
            last_time = self.secuencia[-1].get("tiempo_ms", 0) + 2000
            if self._elapsed >= last_time:
                self._terminado = True
                return True
        return False

    def dibujar(self, surface):
        surface.fill((15, 18, 30))
        if not self._font:
            self._font = pygame.font.SysFont("Arial", 22)
        cw, ch = self._c_width, self._c_height
        cx, cy = cw // 2, ch // 2
        info = self._font.render(
            f"Timing: {self._score}/{self._total}", True, (200, 220, 240)
        )
        surface.blit(info, (10, 10))
        if self._current < self._total:
            step = self.secuencia[self._current]
            tecla = step.get("tecla", "SPACE")
            prompt = self._font.render(f"Presiona: {tecla}", True, (220, 200, 100))
            surface.blit(prompt, (cx - prompt.get_width() // 2, cy - 40))
            step_time = step.get("tiempo_ms", 0)
            ventana_ms = step.get("ventana_ms", 300)
            bar_w = cw - 100
            bar_h = 16
            bar_x = 50
            bar_y = ch - 80
            progress = min(1.0, self._elapsed / max(1, step_time)) if step_time > 0 else 0
            pygame.draw.rect(surface, (40, 45, 55), (bar_x, bar_y, bar_w, bar_h))
            fill_w = int(bar_w * progress)
            pygame.draw.rect(surface, (70, 140, 200), (bar_x, bar_y, fill_w, bar_h))
            win_start = max(0, (step_time - ventana_ms) / max(1, step_time)) if step_time > 0 else 0
            win_end = min(1.0, (step_time + ventana_ms) / max(1, step_time)) if step_time > 0 else 0
            ws = bar_x + int(bar_w * win_start)
            we = bar_x + int(bar_w * win_end)
            pygame.draw.rect(surface, (100, 220, 100, 80), (ws, bar_y - 2, we - ws, bar_h + 4), 2)
            if self._failed:
                fail = self._font.render("!FALLASTE!", True, (220, 60, 60))
                surface.blit(fail, (cx - fail.get_width() // 2, cy + 20))
        if self._current >= self._total and not self._failed:
            done = self._font.render("Completado!", True, (100, 220, 100))
            surface.blit(done, (cx - done.get_width() // 2, cy))

    def get_resultado(self):
        res = dict(self.config.get("flags_resultado", {}))
        res["timing_score"] = self._score
        res["timing_total"] = self._total
        return res
