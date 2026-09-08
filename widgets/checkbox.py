import pygame

from editor.widgets.base import Widget


class Checkbox(Widget):
    """Checkbox rectangular 22x22 con X azul."""
    def __init__(self, x, y, w=22, h=22, checked=False):
        super().__init__(x, y, w, h)
        self.checked = checked
        self.callback = None

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._abs_rect().collidepoint(event.pos):
                self.checked = not self.checked
                if self.callback:
                    self.callback(self.checked)
                return True
        return False

    def draw(self, surface):
        if not self.visible:
            return
        r = self._abs_rect()
        pygame.draw.rect(surface, (30, 32, 36), r, border_radius=4)
        pygame.draw.rect(surface, (60, 65, 75), r, 2, border_radius=4)
        if self.checked:
            pygame.draw.line(surface, (70, 130, 200),
                             (r.x + 4, r.y + 8), (r.x + 14, r.y + 18), 3)
            pygame.draw.line(surface, (70, 130, 200),
                             (r.x + 14, r.y + 8), (r.x + 4, r.y + 18), 3)
