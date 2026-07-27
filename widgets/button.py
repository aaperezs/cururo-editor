import pygame
from editor.translation import I18n
from editor.widgets.base import Widget


class Button(Widget):
    BORDER_RADIUS = 6

    def __init__(self, x, y, w, h, text="", icon=None, color=None, hover_color=None,
                 text_color=None, callback=None, toggle=False):
        super().__init__(x, y, w, h)
        self._text = text
        self.icon = icon
        self.callback = callback
        self.pressed = False
        self.hover = False
        self.toggle = toggle
        self.toggled = False
        self.offset_y = 0

        base = color or (60, 70, 80)
        self.color_sup = base
        self.color_inf = tuple(min(255, c + 20) for c in base)
        self.color_hover = hover_color or (80, 95, 110)
        self.color_activo = tuple(max(0, c - 25) for c in base)
        self.text_color = text_color or (220, 220, 220)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, value):
        self._text = value

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        abs_r = self._abs_rect()
        hit_r = pygame.Rect(abs_r.x, abs_r.y + self.offset_y, abs_r.w, abs_r.h)

        if event.type == pygame.MOUSEMOTION:
            self.hover = hit_r.collidepoint(event.pos)
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if hit_r.collidepoint(event.pos):
                self.pressed = True
                self.offset_y = 2
                return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self.pressed:
                self.pressed = False
                self.offset_y = 0
                if abs_r.collidepoint(event.pos):
                    if self.toggle:
                        self.toggled = not self.toggled
                    if self.callback:
                        self.callback()
                    return True
        return False

    def _get_font(self):
        i18n = I18n.instancia()
        return i18n.fuente(14) if i18n else pygame.font.SysFont("Arial", 14)

    def draw(self, surface):
        if not self.visible:
            return
        r = self._abs_rect()
        draw_r = pygame.Rect(r.x, r.y + self.offset_y, r.w, r.h)

        # State colors
        if self.toggled:
            sup = tuple(min(255, c + 25) for c in self.color_sup)
            inf = tuple(min(255, c + 25) for c in self.color_inf)
        elif self.pressed:
            sup = self.color_activo
            inf = tuple(max(0, c - 10) for c in self.color_activo)
        elif self.hover and self.enabled:
            sup = self.color_hover
            inf = tuple(min(255, c + 18) for c in self.color_hover)
        else:
            sup = self.color_sup
            inf = self.color_inf

        # 1. Drop shadow
        if not self.pressed:
            shadow = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            pygame.draw.rect(shadow, (0, 0, 0, 65), shadow.get_rect(), border_radius=self.BORDER_RADIUS)
            surface.blit(shadow, (r.x + 3, r.y + 3 + self.offset_y))

        # 2. Gradient fill line-by-line
        for i in range(draw_r.h):
            t = i / max(draw_r.h - 1, 1)
            c = (int(sup[0] * (1 - t) + inf[0] * t),
                 int(sup[1] * (1 - t) + inf[1] * t),
                 int(sup[2] * (1 - t) + inf[2] * t))
            pygame.draw.line(surface, c, (draw_r.x, draw_r.y + i),
                             (draw_r.right - 1, draw_r.y + i))

        # 3. Rounded border
        pygame.draw.rect(surface, (0, 0, 0), draw_r, 2, border_radius=self.BORDER_RADIUS)

        # 4. Icon or text
        if self.icon:
            ix = draw_r.x + (draw_r.w - self.icon.get_width()) // 2
            iy = draw_r.y + (draw_r.h - self.icon.get_height()) // 2
            surface.blit(self.icon, (ix, iy))
        elif self._text:
            txt = self._get_font().render(self._text, True, self.text_color)
            tx = draw_r.x + (draw_r.w - txt.get_width()) // 2
            ty = draw_r.y + (draw_r.h - txt.get_height()) // 2
            surface.blit(txt, (tx, ty))


# --- Icon generator ---

import os as _os
_ICO_DIR = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), "assets", "ico")


def make_icon(name, size=20, color=None):
    path = _os.path.join(_ICO_DIR, f"ico_{name}.png")
    if _os.path.exists(path):
        try:
            img = pygame.image.load(path).convert_alpha()
            if img.get_width() != size or img.get_height() != size:
                img = pygame.transform.smoothscale(img, (size, size))
            return img
        except (pygame.error, Exception):
            pass
    return None
