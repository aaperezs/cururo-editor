import pygame
from .base import Container


class Panel(Container):
    def __init__(self, x, y, w, h, bg_color=(40, 45, 50), border_color=(60, 65, 70), title=""):
        super().__init__(x, y, w, h)
        self.bg_color = bg_color
        self.border_color = border_color
        self.title = title

    def draw(self, surface):
        if not self.visible:
            return
        r = self.get_abs_rect()
        pygame.draw.rect(surface, self.bg_color, r)
        if self.border_color:
            pygame.draw.rect(surface, self.border_color, r, 1)
        if self.title:
            from editor.translation import I18n
            i18n = I18n.instancia()
            fuente = i18n.fuente(12, bold=True) if i18n else pygame.font.SysFont("Arial", 12, bold=True)
            txt = fuente.render(self.title, True, (180, 190, 200))
            surface.blit(txt, (r.x + 6, r.y + 4))
        super().draw(surface)
