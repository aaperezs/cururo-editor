import pygame


class EyedropperTool:
    id = "eyedropper"
    name_key = "sprite.eyedropper"

    def __init__(self):
        self.on_pick = None

    def on_mouse_down(self, surface, pos, color):
        x, y = pos
        if 0 <= x < surface.get_width() and 0 <= y < surface.get_height():
            picked = surface.get_at((x, y))
            if self.on_pick:
                self.on_pick(picked)

    def on_mouse_move(self, surface, pos, color):
        pass

    def on_mouse_up(self, surface, pos, color):
        pass
