import pygame


class Camera:
    def __init__(self, width, height):
        self.x = 0.0
        self.y = 0.0
        self.width = width
        self.height = height
        self.smoothing = 0.1
        self.bounds = None

    def follow(self, target_x, target_y, center=True):
        if center:
            dx = target_x - self.width // 2 - self.x
            dy = target_y - self.height // 2 - self.y
        else:
            dx = target_x - self.x
            dy = target_y - self.y
        self.x += dx * self.smoothing
        self.y += dy * self.smoothing
        self._clamp()

    def snap_to(self, target_x, target_y, center=True):
        if center:
            self.x = target_x - self.width // 2
            self.y = target_y - self.height // 2
        else:
            self.x = target_x
            self.y = target_y
        self._clamp()

    def apply(self, rect):
        if isinstance(rect, pygame.Rect):
            return pygame.Rect(rect.x - self.x, rect.y - self.y, rect.w, rect.h)
        if isinstance(rect, (list, tuple)) and len(rect) == 2:
            return (rect[0] - self.x, rect[1] - self.y)
        if isinstance(rect, (list, tuple)) and len(rect) == 4:
            return (rect[0] - self.x, rect[1] - self.y, rect[2], rect[3])
        return rect

    def apply_x(self, x):
        return x - self.x

    def apply_y(self, y):
        return y - self.y

    def set_pos(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self._clamp()

    def set_bounds(self, min_x, min_y, max_x, max_y):
        self.bounds = (min_x, min_y, max_x, max_y)
        self._clamp()

    def _clamp(self):
        if self.bounds:
            min_x, min_y, max_x, max_y = self.bounds
            self.x = max(min_x, min(self.x, max_x))
            self.y = max(min_y, min(self.y, max_y))

    def get_offset(self):
        return (int(self.x), int(self.y))

    def reset(self):
        self.x = 0.0
        self.y = 0.0
        self.smoothing = 0.1
        self.bounds = None

    def is_visible(self, rect):
        if isinstance(rect, pygame.Rect):
            return rect.colliderect(pygame.Rect(self.x, self.y, self.width, self.height))
        x, y, w, h = rect
        return not (x + w < self.x or x > self.x + self.width or
                    y + h < self.y or y > self.y + self.height)
