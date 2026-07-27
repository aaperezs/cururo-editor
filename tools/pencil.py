import pygame


class PencilTool:
    id = "pencil"
    name_key = "sprite.pencil"

    def __init__(self, color=(255, 255, 255)):
        self.color = color
        self._drawing = False
        self._last_pos = None
        self._symmetry = "off"

    def set_symmetry(self, mode):
        self._symmetry = mode

    def on_mouse_down(self, surface, pos, color):
        self.color = color
        self._drawing = True
        self._last_pos = pos
        self._draw_pixel(surface, pos, color)

    def on_mouse_move(self, surface, pos, color):
        if not self._drawing:
            return
        self.color = color
        if self._last_pos:
            self._draw_line(surface, self._last_pos, pos, color)
        self._last_pos = pos

    def on_mouse_up(self, surface, pos, color):
        self._drawing = False
        self._last_pos = None

    def _draw_pixel(self, surface, pos, color):
        x, y = pos
        if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
            surface.set_at((x, y), color)
            self._draw_symmetry(surface, x, y, color)

    def _draw_symmetry(self, surface, x, y, color):
        if self._symmetry == "off":
            return
        w = surface.get_width()
        h = surface.get_height()
        mx = w - 1 - x
        my = h - 1 - y
        if self._symmetry == "horizontal":
            if 0 <= mx < w:
                surface.set_at((mx, y), color)
        elif self._symmetry == "vertical":
            if 0 <= my < h:
                surface.set_at((x, my), color)
        elif self._symmetry == "both":
            if 0 <= mx < w:
                surface.set_at((mx, y), color)
            if 0 <= my < h:
                surface.set_at((x, my), color)
            if 0 <= mx < w and 0 <= my < h:
                surface.set_at((mx, my), color)

    def _draw_line(self, surface, p1, p2, color):
        x1, y1 = p1
        x2, y2 = p2
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        while True:
            self._draw_pixel(surface, (x1, y1), color)
            if x1 == x2 and y1 == y2:
                break
            e2 = err * 2
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy
