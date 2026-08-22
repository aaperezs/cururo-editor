"""Color picker widget for the editor UI."""

import pygame

from editor.widgets.base import Widget
from editor.widgets.text_input import TextInput
from editor.ui.theme import Theme
from editor.ui import get_font_manager


class ColorPicker(Widget):
    """HSV color picker with RGB inputs."""
    
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        self.hue = 0
        self.saturation = 1
        self.value = 1
        self.alpha = 255  # Fixed — always 255; kept for compatibility
        self._dragging_hsv = False
        self._dragging_hue = False
        self._hue_rect = pygame.Rect(0, 0, 0, 0)
        self._hue_slider_rect = pygame.Rect(0, 0, 0, 0)
        self.selected_color = pygame.Color(255, 255, 255, 255)

        # RGB text inputs
        self._r_input = TextInput(0, 0, 26, 18, default="255", max_chars=3, numeric_only=True, font_size=10)
        self._g_input = TextInput(0, 0, 26, 18, default="255", max_chars=3, numeric_only=True, font_size=10)
        self._b_input = TextInput(0, 0, 26, 18, default="255", max_chars=3, numeric_only=True, font_size=10)
        self._rgb_inputs = [self._r_input, self._g_input, self._b_input]
    
    # ------------------------------------------------------------------ geometry helpers
    def _hsv_area(self):
        """Return (x, y, w, h) for the HSV gradient area."""
        r = self.get_abs_rect()
        hsv_x = r.x + 4
        hsv_y = r.y + 4
        hsv_w = int(r.w * 0.75)
        hsv_h = r.h - 58  # reserve bottom for labels + RGB row + preview
        return hsv_x, hsv_y, hsv_w, hsv_h

    def _hue_area(self):
        """Return (x, y, w, h) for the hue slider."""
        hsv_x, hsv_y, hsv_w, hsv_h = self._hsv_area()
        hue_x = hsv_x + hsv_w + 4
        return hue_x, hsv_y, 12, hsv_h

    # ------------------------------------------------------------------ events
    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        
        r = self.get_abs_rect()

        # Tab: move focus to next RGB input
        if event.type == pygame.KEYDOWN and event.key == pygame.K_TAB:
            if any(inp.focused for inp in self._rgb_inputs):
                idx = next(i for i, inp in enumerate(self._rgb_inputs) if inp.focused)
                next_idx = (idx + 1) % len(self._rgb_inputs)
                for i, inp in enumerate(self._rgb_inputs):
                    inp.focused = (i == next_idx)
                self._apply_rgb_inputs()
                return True

        # RGB input events
        for inp in self._rgb_inputs:
            if inp.handle_event(event):
                self._apply_rgb_inputs()
                return True
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_TAB):
            if any(inp.focused for inp in self._rgb_inputs):
                for inp in self._rgb_inputs:
                    inp.focused = False
                self._apply_rgb_inputs()
                return True
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos

            # Hue slider
            hx, hy, hw, hh = self._hue_area()
            hue_rect = pygame.Rect(hx, hy, hw, hh)
            if hue_rect.collidepoint(mx, my):
                self._dragging_hue = True
                self._update_hue(event.pos)
                return True

            # HSV area
            hsv_x, hsv_y, hsv_w, hsv_h = self._hsv_area()
            hsv_rect = pygame.Rect(hsv_x, hsv_y, hsv_w, hsv_h)
            if hsv_rect.collidepoint(mx, my):
                self._dragging_hsv = True
                self._update_hsv(event.pos)
                return True
        
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging_hsv = False
            self._dragging_hue = False
        
        if event.type == pygame.MOUSEMOTION:
            if self._dragging_hue:
                self._update_hue(event.pos)
                return True
            if self._dragging_hsv:
                self._update_hsv(event.pos)
                return True
        
        return False
    
    # ------------------------------------------------------------------ updates
    def _update_hue(self, pos):
        mx, my = pos
        _, hsv_y, _, hsv_h = self._hsv_area()
        rel = max(0.0, min(1.0, (my - hsv_y) / hsv_h))
        self.hue = rel
        self._update_color()
    
    def _update_hsv(self, pos):
        mx, my = pos
        hsv_x, hsv_y, hsv_w, hsv_h = self._hsv_area()
        rel_x = max(0.0, min(1.0, (mx - hsv_x) / hsv_w))
        rel_y = max(0.0, min(1.0, (my - hsv_y) / hsv_h))
        self.saturation = rel_x
        self.value = 1.0 - rel_y
        self._update_color()
    
    def _update_color(self):
        self.selected_color = pygame.Color(0, 0, 0, 255)
        self.selected_color.hsva = (self.hue * 360, self.saturation * 100, self.value * 100, 100)
        self._sync_rgb_inputs()
    
    def _sync_rgb_inputs(self):
        c = self.selected_color
        self._r_input.set_value(c.r)
        self._g_input.set_value(c.g)
        self._b_input.set_value(c.b)

    def _apply_rgb_inputs(self):
        try:
            rv = max(0, min(255, self._r_input.get_value()))
            gv = max(0, min(255, self._g_input.get_value()))
            bv = max(0, min(255, self._b_input.get_value()))
            self.selected_color = pygame.Color(rv, gv, bv, 255)
            h, s, v, _ = self.selected_color.hsva
            self.hue = h / 360.0
            self.saturation = s / 100.0
            self.value = v / 100.0
        except ValueError:
            pass
    
    # ------------------------------------------------------------------ draw
    def draw(self, surface):
        if not self.visible:
            return
        
        theme = Theme.get()
        r = self.get_abs_rect()
        
        def _c(c):
            return c.as_tuple() if hasattr(c, 'as_tuple') else c
        
        # Background
        pygame.draw.rect(surface, _c(theme.surface), r, border_radius=theme.radius)
        pygame.draw.rect(surface, _c(theme.border), r, 1, border_radius=theme.radius)

        # --- HSV area ---
        hsv_x, hsv_y, hsv_w, hsv_h = self._hsv_area()
        self._hue_rect = pygame.Rect(hsv_x, hsv_y, hsv_w, hsv_h)
        
        for x in range(max(hsv_w, 0)):
            s = x / hsv_w
            for y in range(max(hsv_h, 0)):
                v = 1.0 - y / hsv_h
                c = pygame.Color(0, 0, 0)
                c.hsva = (self.hue * 360, s * 100, v * 100, 100)
                surface.set_at((hsv_x + x, hsv_y + y), c)
        
        # --- Hue slider (full height, no alpha bar) ---
        hue_x, hue_y, hue_w, hue_h = self._hue_area()
        self._hue_slider_rect = pygame.Rect(hue_x, hue_y, hue_w, hue_h)
        
        for y in range(max(hue_h, 0)):
            h = y / hue_h if hue_h > 0 else 0
            c = pygame.Color(0, 0, 0)
            c.hsva = (h * 360, 100, 100, 100)
            pygame.draw.line(surface, c, (hue_x, hue_y + y), (hue_x + hue_w, hue_y + y))
        
        # Hue indicator arrows
        hy = hue_y + int(self.hue * hue_h)
        pygame.draw.polygon(surface, (255, 255, 255), [
            (hue_x - 6, hy), (hue_x - 2, hy - 4), (hue_x - 2, hy + 4)
        ])
        pygame.draw.polygon(surface, (255, 255, 255), [
            (hue_x + hue_w + 6, hy), (hue_x + hue_w + 2, hy - 4), (hue_x + hue_w + 2, hy + 4)
        ])
        
        # --- Color preview ---
        preview_x = r.x + 4
        preview_y = r.y + r.h - 24
        preview_w = 30
        preview_h = 20
        pygame.draw.rect(surface, self.selected_color, (preview_x, preview_y, preview_w, preview_h), border_radius=4)
        pygame.draw.rect(surface, _c(theme.border), (preview_x, preview_y, preview_w, preview_h), 1, border_radius=4)
        
        # --- RGB inputs row ---
        rgb_y = r.y + r.h - 44
        ix = r.x + 4
        font = get_font_manager().get(8)
        for i, (inp, label) in enumerate(zip(self._rgb_inputs, ["R", "G", "B"])):
            inp.rect.x = ix + i * 28
            inp.rect.y = rgb_y
            inp.rect.w = 26
            inp.rect.h = 18
            inp.draw(surface)
            lbl = font.render(label, True, _c(theme.text_dim))
            lbl_x = inp.rect.x + (inp.rect.w - lbl.get_width()) // 2
            surface.blit(lbl, (lbl_x, inp.rect.y - 10))
