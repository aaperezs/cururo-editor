from collections import deque

import pygame


class FloatingText:
    __slots__ = ("texto", "x", "y", "timer", "max_timer", "color",
                 "dx", "dy", "fade_out", "font_size", "active")

    def __init__(self, texto="", x=0, y=0, timer=30, max_timer=30,
                 color=(255, 255, 200), dx=0, dy=-1, fade_out=True,
                 font_size=16):
        self.texto = texto
        self.x = x
        self.y = y
        self.timer = timer
        self.max_timer = max_timer
        self.color = color
        self.dx = dx
        self.dy = dy
        self.fade_out = fade_out
        self.font_size = font_size
        self.active = True


class TextService:
    """Floating text pool with configurable animations."""

    def __init__(self, pool_size=32):
        self._pool = deque(maxlen=pool_size)
        self._font_cache = {}

    def spawn(self, texto, x, y, timer=30, color=None, dx=0, dy=-1,
              fade_out=True, font_size=16):
        color = color or (255, 255, 200)
        ft = FloatingText(texto, x, y, timer, timer, color,
                          dx, dy, fade_out, font_size)
        self._pool.append(ft)
        return ft

    def update(self):
        for ft in list(self._pool):
            ft.timer -= 1
            ft.x += ft.dx
            ft.y += ft.dy
            if ft.timer <= 0:
                ft.active = False
                self._pool.remove(ft)

    def draw(self, surface):
        for ft in self._pool:
            font = self._get_font(ft.font_size)
            txt = font.render(ft.texto, True, ft.color)
            if ft.fade_out and ft.max_timer > 0:
                alpha = max(0, int(255 * ft.timer / ft.max_timer))
                txt.set_alpha(alpha)
            surface.blit(txt, (ft.x - txt.get_width() // 2, ft.y - txt.get_height() // 2))

    def clear(self):
        self._pool.clear()

    def _get_font(self, size):
        if size not in self._font_cache:
            self._font_cache[size] = pygame.font.SysFont("Arial", size)
        return self._font_cache[size]
