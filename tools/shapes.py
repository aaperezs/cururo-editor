import pygame


class ShapeTool:
    id = "shapes"
    name_key = "sprite.shapes"

    def __init__(self, color=(255, 255, 255)):
        self.color = color
        self.shape = "rect"
        self.filled = False
        self._dragging = False
        self._start = None
        self._end = None

    def set_shape(self, shape):
        self.shape = shape
        self._dragging = False
        self._start = None
        self._end = None

    def set_filled(self, filled):
        self.filled = filled

    def on_mouse_down(self, surface, pos, color):
        self.color = color
        self._dragging = True
        self._start = pos
        self._end = pos

    def on_mouse_move(self, surface, pos, color):
        if not self._dragging:
            return
        self.color = color
        self._end = pos

    def on_mouse_up(self, surface, pos, color):
        if not self._dragging:
            return
        self._dragging = False
        self._commit(surface)

    def _bounds(self, surface):
        return (surface.get_width(), surface.get_height())

    def _norm_rect(self):
        x1, y1 = self._start
        x2, y2 = self._end
        return pygame.Rect(min(x1, x2), min(y1, y2),
                           abs(x2 - x1) + 1, abs(y2 - y1) + 1)

    def _clamp(self, rect, w, h):
        rect.clamp_ip(pygame.Rect(0, 0, w, h))
        return rect

    def _commit(self, surface):
        w, h = self._bounds(surface)
        color = tuple(self.color)
        if self.shape == "line":
            p1 = (self._start[0], self._start[1])
            p2 = (self._end[0], self._end[1])
            if self._clamp(pygame.Rect(min(p1[0], p2[0]), min(p1[1], p2[1]),
                                       abs(p2[0] - p1[0]) + 1, abs(p2[1] - p1[1]) + 1), w, h):
                pygame.draw.line(surface, color, p1, p2, 1)
            return
        rect = self._clamp(self._norm_rect(), w, h)
        if rect.w < 1 or rect.h < 1:
            return
        if self.shape == "rect":
            pygame.draw.rect(surface, color, rect, 0 if self.filled else 1)
        elif self.shape == "ellipse":
            pygame.draw.ellipse(surface, color, rect, 0 if self.filled else 1)

    def draw_overlay(self, surface, canvas):
        if not self._dragging or self._start is None or self._end is None:
            return
        zoom = canvas.get_zoom()
        color = (0, 200, 255)
        if self.shape == "line":
            s = canvas.surface_to_screen(*self._start)
            e = canvas.surface_to_screen(*self._end)
            pygame.draw.line(surface, color, s, e, max(1, zoom // 8))
            return
        r = self._norm_rect()
        sx, sy = canvas.surface_to_screen(r.x, r.y)
        sw = max(1, r.w * zoom)
        sh = max(1, r.h * zoom)
        overlay = pygame.Rect(sx, sy, sw, sh)
        if self.shape == "rect":
            pygame.draw.rect(surface, color, overlay, max(1, zoom // 8))
        elif self.shape == "ellipse":
            pygame.draw.ellipse(surface, color, overlay, max(1, zoom // 8))
