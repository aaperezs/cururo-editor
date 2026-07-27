import pygame
from editor.translation import I18n
from editor.widgets.base import Widget


class Label(Widget):
    def __init__(self, x, y, w, h, text="", color=(200, 200, 200), font_size=14, bold=False, align="left"):
        super().__init__(x, y, w, h)
        self.text = text
        self.color = color
        self.font_size = font_size
        self.bold = bold
        self.align = align

    def handle_event(self, event):
        return False

    def draw(self, surface):
        if not self.visible:
            return
        r = self._abs_rect()
        i = I18n.instancia()
        fuente = i.fuente(self.font_size, self.bold) if i else pygame.font.SysFont("Arial", self.font_size)
        txt = fuente.render(self.text, True, self.color)
        if self.align == "center":
            tx = r.x + (r.w - txt.get_width()) // 2
        elif self.align == "right":
            tx = r.x + r.w - txt.get_width() - 4
        else:
            tx = r.x + 4
        ty = r.y + (r.h - txt.get_height()) // 2
        surface.blit(txt, (tx, ty))
