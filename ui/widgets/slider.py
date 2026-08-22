"""Slider widget for the editor UI."""

import pygame

from editor.widgets.base import Widget
from editor.ui.theme import Theme
from editor.ui.fonts import get_font_manager


class Slider(Widget):
    """Themed horizontal slider."""
    
    def __init__(self, x, y, w, h, min_val=0, max_val=100, default=50, label=""):
        super().__init__(x, y, w, h)
        self.min_val = min_val
        self.max_val = max_val
        self.value = default
        self.label = label
        self._dragging = False
        self._label_font = None
    
    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        
        r = self.get_abs_rect()
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button in (1, 3):
            if r.collidepoint(event.pos):
                self._dragging = True
                self._update_from_mouse(event.pos)
                return True
        
        if event.type == pygame.MOUSEBUTTONUP and event.button in (1, 3):
            if self._dragging:
                self._dragging = False
                return True
        
        if event.type == pygame.MOUSEMOTION and self._dragging:
            self._update_from_mouse(event.pos)
            return True
        
        return False
    
    def _update_from_mouse(self, pos):
        mx, _ = pos
        r = self.get_abs_rect()
        track_x = r.x + 8
        track_w = r.w - 16
        rel = max(0, min(1, (mx - track_x) / track_w))
        self.value = self.min_val + rel * (self.max_val - self.min_val)
    
    def draw(self, surface):
        if not self.visible:
            return
        
        theme = Theme.get()
        r = self.get_abs_rect()
        font = get_font_manager().get(theme.font_sizes["body"])
        
        def _c(c):
            return c.as_tuple() if hasattr(c, 'as_tuple') else c
        
        # Label
        if self.label:
            txt = font.render(self.label, True, _c(theme.text))
            surface.blit(txt, (r.x, r.y + (r.h - txt.get_height()) // 2))
        
        # Track
        track_x = r.x + 8
        track_y = r.y + (r.h - 4) // 2
        track_w = r.w - 16
        track_h = 4
        
        pygame.draw.rect(surface, _c(theme.border), (track_x, track_y, track_w, track_h), border_radius=2)
        
        # Filled portion
        rel = (self.value - self.min_val) / (self.max_val - self.min_val)
        fill_w = int(track_w * rel)
        if fill_w > 0:
            pygame.draw.rect(surface, _c(theme.accent), (track_x, track_y, fill_w, track_h), border_radius=2)
        
        # Thumb
        thumb_x = track_x + int(track_w * rel) - 8
        thumb_y = r.y + (r.h - 16) // 2
        pygame.draw.circle(surface, _c(theme.accent), (thumb_x + 8, thumb_y + 8), 8)
        pygame.draw.circle(surface, _c(theme.border), (thumb_x + 8, thumb_y + 8), 8, 1)
        
        # Value text
        val_txt = font.render(str(int(self.value)), True, _c(theme.text_dim))
        surface.blit(val_txt, (r.x + r.w - val_txt.get_width(), r.y + (r.h - val_txt.get_height()) // 2))