"""Tooltip widget for the editor UI."""

import pygame

from editor.widgets.base import Widget
from editor.ui.theme import Theme
from editor.ui.fonts import get_font_manager


class Tooltip(Widget):
    """Floating tooltip box that follows the mouse."""

    def __init__(self):
        super().__init__(0, 0, 0, 0)
        self.text = ""
        self._visible = False
        self._mouse_pos = (0, 0)
        self._padding = 6

    def show(self, text, pos):
        self.text = text
        self._mouse_pos = pos
        self._visible = bool(text)

    def hide(self):
        self._visible = False
        self.text = ""

    def draw(self, surface):
        if not self._visible or not self.text:
            return
        theme = Theme.get()
        font = get_font_manager().get(theme.font_sizes["caption"])
        txt = font.render(self.text, True, theme.text.as_rgb())
        w = txt.get_width() + self._padding * 2
        h = txt.get_height() + self._padding * 2

        # Position: below-right of mouse, clamped to screen
        x = self._mouse_pos[0] + 12
        y = self._mouse_pos[1] + 12
        screen_w, screen_h = pygame.display.get_surface().get_size()
        if x + w > screen_w:
            x = self._mouse_pos[0] - w - 12
        if y + h > screen_h:
            y = self._mouse_pos[1] - h - 12

        rect = pygame.Rect(x, y, w, h)
        pygame.draw.rect(surface, theme.surface_elevated.as_rgb(), rect,
                         border_radius=theme.radius_sm)
        pygame.draw.rect(surface, theme.border.as_rgb(), rect, 1,
                         border_radius=theme.radius_sm)
        surface.blit(txt, (x + self._padding, y + self._padding))
