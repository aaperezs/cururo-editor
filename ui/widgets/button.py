"""Button widgets for the editor UI."""

import pygame

from editor.widgets.base import Widget
from editor.ui.theme import Theme
from editor.ui.icons import get_icon_factory
from editor.ui.fonts import get_font_manager


class Button(Widget):
    """Themed button with multiple variants."""
    
    VARIANT_DEFAULT = "default"
    VARIANT_PRIMARY = "primary"
    VARIANT_DANGER = "danger"
    VARIANT_GHOST = "ghost"
    
    def __init__(self, x, y, w, h, text="", callback=None, toggle=False,
                 variant=VARIANT_DEFAULT, icon=None, icon_size=14, tooltip=None):
        super().__init__(x, y, w, h)
        self.text = text
        self.callback = callback
        self.toggle = toggle
        self.toggled = False
        self.variant = variant
        self.icon = icon
        self.icon_size = icon_size
        self.tooltip = tooltip
        self._hover = False
        self._pressed = False
        self._icon_surf = None
        if icon:
            self._icon_surf = get_icon_factory().get(icon, icon_size)
    
    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        
        if event.type == pygame.MOUSEMOTION:
            self._hover = self.get_abs_rect().collidepoint(event.pos)
            return self._hover
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.get_abs_rect().collidepoint(event.pos):
                self._pressed = True
                return True
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._pressed and self.get_abs_rect().collidepoint(event.pos):
                self._pressed = False
                if self.toggle:
                    self.toggled = not self.toggled
                if self.callback:
                    self.callback()
                return True
            self._pressed = False
        
        return False
    
    def draw(self, surface):
        if not self.visible:
            return
        
        theme = Theme.get()
        r = self.get_abs_rect()
        
        def _c(c):
            return c.as_tuple() if hasattr(c, 'as_tuple') else c
        
        # Determine colors based on state
        if not self.enabled:
            bg = _c(theme.bg_disabled)
            border = _c(theme.border_disabled)
            text_c = _c(theme.text_disabled)
        elif self._pressed:
            bg = _c(theme.accent_active)
            border = _c(theme.accent_active)
            text_c = (255, 255, 255, 255)
        elif self.toggled:
            bg = _c(theme.accent)
            border = _c(theme.accent)
            text_c = (255, 255, 255, 255)
        elif self._hover:
            bg = _c(theme.bg_hover)
            border = _c(theme.border_focus)
            text_c = _c(theme.text)
        else:
            if self.variant == self.VARIANT_PRIMARY:
                bg = _c(theme.accent)
                border = _c(theme.accent)
                text_c = (255, 255, 255, 255)
            elif self.variant == self.VARIANT_DANGER:
                bg = _c(theme.danger)
                border = _c(theme.danger)
                text_c = (255, 255, 255, 255)
            elif self.variant == self.VARIANT_GHOST:
                bg = (0, 0, 0, 0)
                border = _c(theme.border)
                text_c = _c(theme.text)
            else:
                bg = _c(theme.surface)
                border = _c(theme.border)
                text_c = _c(theme.text)
        
        # Background
        if bg[3] < 255:
            bg_surf = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            bg_surf.fill(bg)
            surface.blit(bg_surf, r.topleft)
        else:
            pygame.draw.rect(surface, bg, r, border_radius=theme.radius)
        
        # Border
        if self.variant != self.VARIANT_GHOST or self._hover or self.toggled:
            pygame.draw.rect(surface, border, r, 2, border_radius=theme.radius)
        
        # Icon + text
        font = get_font_manager().get_bold(theme.font_sizes["body"])
        content_w = 0
        if self._icon_surf:
            content_w += self._icon_surf.get_width() + 4
        if self.text:
            content_w += font.size(self.text)[0]
        
        cx = r.x + (r.w - content_w) // 2
        cy = r.y + (r.h - font.get_height()) // 2
        
        if self._icon_surf:
            surface.blit(self._icon_surf, (cx, cy + (font.get_height() - self._icon_surf.get_height()) // 2))
            cx += self._icon_surf.get_width() + 4
        
        if self.text:
            txt = font.render(self.text, True, text_c)
            surface.blit(txt, (cx, cy))


class IconButton(Button):
    """Square icon-only button."""
    
    def __init__(self, x, y, size, icon, callback=None, toggle=False,
                 variant=Button.VARIANT_DEFAULT, tooltip=None):
        super().__init__(x, y, size, size, "", callback, toggle, variant, icon, size - 8, tooltip=tooltip)
    
    def draw(self, surface):
        if not self.visible:
            return
        
        theme = Theme.get()
        r = self.get_abs_rect()
        
        def _c(c):
            return c.as_tuple() if hasattr(c, 'as_tuple') else c
        
        if not self.enabled:
            bg = _c(theme.bg_disabled)
            border = _c(theme.border_disabled)
            icon_c = _c(theme.text_disabled)
        elif self._pressed:
            bg = _c(theme.accent_active)
            border = _c(theme.accent_active)
            icon_c = (255, 255, 255, 255)
        elif self.toggled:
            bg = _c(theme.accent)
            border = _c(theme.accent)
            icon_c = (255, 255, 255, 255)
        elif self._hover:
            bg = _c(theme.bg_hover)
            border = _c(theme.border_focus)
            icon_c = _c(theme.text)
        else:
            if self.variant == self.VARIANT_PRIMARY:
                bg = _c(theme.accent)
                border = _c(theme.accent)
                icon_c = (255, 255, 255, 255)
            elif self.variant == self.VARIANT_DANGER:
                bg = _c(theme.danger)
                border = _c(theme.danger)
                icon_c = (255, 255, 255, 255)
            elif self.variant == self.VARIANT_GHOST:
                bg = (0, 0, 0, 0)
                border = _c(theme.border)
                icon_c = _c(theme.text)
            else:
                bg = _c(theme.surface)
                border = _c(theme.border)
                icon_c = _c(theme.text)
        
        if bg[3] < 255:
            bg_surf = pygame.Surface((r.w, r.h), pygame.SRCALPHA)
            bg_surf.fill(bg)
            surface.blit(bg_surf, r.topleft)
        else:
            pygame.draw.rect(surface, bg, r, border_radius=theme.radius)
        
        if self.variant != self.VARIANT_GHOST or self._hover or self.toggled:
            pygame.draw.rect(surface, border, r, 2, border_radius=theme.radius)
        
        if self._icon_surf:
            ix = r.x + (r.w - self._icon_surf.get_width()) // 2
            iy = r.y + (r.h - self._icon_surf.get_height()) // 2
            # Tint icon
            if icon_c != (255, 255, 255, 255):
                tinted = self._icon_surf.copy()
                tinted.fill(icon_c[:3] + (0,), special_flags=pygame.BLEND_RGB_MULT)
                surface.blit(tinted, (ix, iy))
            else:
                surface.blit(self._icon_surf, (ix, iy))


class ToolButton(IconButton):
    """Radio-style tool button with group support."""
    
    _groups = {}  # group_name -> active ToolButton
    
    def __init__(self, x, y, size, icon, callback=None, group=None,
                 variant=Button.VARIANT_DEFAULT, tooltip=None):
        super().__init__(x, y, size, icon, callback, toggle=True, variant=variant, tooltip=tooltip)
        self.group = group
        if group:
            if group not in ToolButton._groups:
                ToolButton._groups[group] = None
            ToolButton._groups[group] = self
    
    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        
        result = super().handle_event(event)
        
        if self.group and self.toggled:
            # Deactivate others in group
            other = ToolButton._groups.get(self.group)
            if other is not self and other and other.toggled:
                other.toggled = False
        
        return result
    
    @classmethod
    def clear_group(cls, group):
        if group in cls._groups:
            cls._groups[group] = None