import pygame
from collections import deque


class BucketTool:
    id = "bucket"
    name_key = "sprite.bucket"

    def __init__(self):
        self.color = (255, 255, 255)

    def on_mouse_down(self, surface, pos, color):
        self.color = color
        x, y = pos
        w, h = surface.get_size()
        if x < 0 or x >= w or y < 0 or y >= h:
            return
        target_color = surface.get_at((x, y))
        if target_color == color:
            return
        self._flood_fill(surface, x, y, target_color, color)

    def on_mouse_move(self, surface, pos, color):
        pass

    def on_mouse_up(self, surface, pos, color):
        pass

    def _flood_fill(self, surface, sx, sy, target, replacement):
        w, h = surface.get_size()
        q = deque()
        q.append((sx, sy))
        visited = set()
        while q:
            x, y = q.popleft()
            if (x, y) in visited:
                continue
            if x < 0 or x >= w or y < 0 or y >= h:
                continue
            try:
                px = surface.get_at((x, y))
            except IndexError:
                continue
            if px != target:
                continue
            visited.add((x, y))
            surface.set_at((x, y), replacement)
            q.append((x + 1, y))
            q.append((x - 1, y))
            q.append((x, y + 1))
            q.append((x, y - 1))
