"""Label widget for the editor UI."""

import pygame

from editor.widgets.base import Widget
from editor.ui.theme import Theme
from editor.ui.fonts import get_font_manager


class Label(Widget):
    """Themed text label."""
    
    def __init__(self, x, y, w, h, text="", bold=False, align="left", color=None, font_size=None):
        super().__init__(x, y, w, h)
        self.text = text
        self.bold = bold
        self.align = align  # "left", "center", "right"
        self.color = color
        self.font_size = font_size
    
    def draw(self, surface):
        if not self.visible or not self.text:
            return
        
        theme = Theme.get()
        font = get_font_manager().get(self.font_size or theme.font_sizes["body"], bold=self.bold)
        color = self.color or theme.text
        if hasattr(color, 'as_rgb'):
            color = color.as_rgb()
        
        txt = font.render(self.text, True, color)
        
        r = self.get_abs_rect()
        if self.align == "center":
            x = r.x + (r.w - txt.get_width()) // 2
        elif self.align == "right":
            x = r.x + r.w - txt.get_width()
        else:
            x = r.x
        
        y = r.y + (r.h - txt.get_height()) // 2
        surface.blit(txt, (x, y))
    
    def layout(self):
        pass  # Label size is fixed by parent