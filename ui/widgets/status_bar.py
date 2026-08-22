"""Status bar widget for transient messages."""

import pygame

from editor.widgets.base import Widget
from editor.ui.theme import Theme
from editor.ui.fonts import get_font_manager


class StatusBar(Widget):
    """Status strip for transient messages (saved, loaded, etc.)."""

    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        self.text = ""
        self._timer = 0
        self._duration = 180  # frames at 60fps = 3 seconds

    def set_text(self, text, duration=None):
        self.text = text
        self._timer = duration or self._duration

    def update(self, dt):
        if self._timer > 0:
            self._timer -= 1
            if self._timer <= 0:
                self.text = ""

    def draw(self, surface):
        if not self.visible or not self.text:
            return

        theme = Theme.get()
        r = self.get_abs_rect()
        font = get_font_manager().get(theme.font_sizes["caption"])

        def _c(c):
            return c.as_tuple() if hasattr(c, 'as_tuple') else c

        # Background
        pygame.draw.rect(surface, _c(theme.surface_elevated), r, border_radius=theme.radius_sm)
        pygame.draw.rect(surface, _c(theme.border), r, 1, border_radius=theme.radius_sm)

        # Text centered
        txt = font.render(self.text, True, _c(theme.text_dim))
        surface.blit(txt, (r.x + (r.w - txt.get_width()) // 2, r.y + (r.h - txt.get_height()) // 2))