import pygame
from editor.widgets.base import Widget
from editor.widgets.text_input import TextInput
from editor.translation import I18n


class ColorPicker(Widget):
    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        self.selected_color = (255, 255, 255)

        self._presets = [
            (255, 255, 255), (200, 200, 200), (150, 150, 150), (100, 100, 100), (50, 50, 50), (0, 0, 0),
            (255, 0, 0), (200, 50, 50), (150, 0, 0), (100, 0, 0),
            (255, 150, 0), (200, 120, 0), (150, 80, 0),
            (255, 255, 0), (200, 200, 0), (150, 150, 0),
            (0, 255, 0), (50, 200, 50), (0, 150, 0), (0, 100, 0),
            (0, 150, 255), (50, 100, 200), (0, 80, 150),
            (150, 0, 255), (100, 50, 200), (80, 0, 150),
            (255, 100, 150), (200, 80, 120), (150, 60, 90),
        ]
        self._swatch_size = 20
        self._cols = max(1, w // self._swatch_size)
        self._preset_rows = max(1, (len(self._presets) + self._cols - 1) // self._cols)

        self._r_input = TextInput(2, 0, 26, 16, default="255", max_chars=3, numeric_only=True, font_size=10)
        self._g_input = TextInput(32, 0, 26, 16, default="255", max_chars=3, numeric_only=True, font_size=10)
        self._b_input = TextInput(62, 0, 26, 16, default="255", max_chars=3, numeric_only=True, font_size=10)
        self._rgb_inputs = [self._r_input, self._g_input, self._b_input]

    def _abs_rect(self):
        if self.parent:
            pr = self.parent.get_abs_rect() if hasattr(self.parent, 'get_abs_rect') else self.parent.rect
            return pygame.Rect(pr.x + self.rect.x, pr.y + self.rect.y, self.rect.w, self.rect.h)
        return self.rect.copy()

    def _update_from_rgb(self):
        try:
            r = max(0, min(255, int(self._r_input.text))) if self._r_input.text else 0
            g = max(0, min(255, int(self._g_input.text))) if self._g_input.text else 0
            b = max(0, min(255, int(self._b_input.text))) if self._b_input.text else 0
            self.selected_color = (r, g, b)
        except ValueError:
            pass

    def _sync_rgb_inputs(self):
        self._r_input.text = str(self.selected_color[0])
        self._g_input.text = str(self.selected_color[1])
        self._b_input.text = str(self.selected_color[2])

    def _rgb_y(self, r):
        return r.y + self._preset_rows * self._swatch_size + 12

    def _preview_y(self, r):
        return self._rgb_y(r) + 18 + 4

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        r = self._abs_rect()

        # Handle RGB input events
        for inp in self._rgb_inputs:
            if inp.handle_event(event):
                self._update_from_rgb()
                return True

        # Force focus loss on enter/tab to trigger re-read
        if event.type == pygame.KEYDOWN and event.key in (pygame.K_RETURN, pygame.K_TAB):
            if any(inp.focused for inp in self._rgb_inputs):
                for inp in self._rgb_inputs:
                    inp.focused = False
                self._update_from_rgb()
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if r.collidepoint(mx, my):
                # Preset swatch click
                local_x = mx - r.x
                local_y = my - r.y
                col = local_x // self._swatch_size
                row = local_y // self._swatch_size
                idx = row * self._cols + col
                if 0 <= idx < len(self._presets):
                    self.selected_color = self._presets[idx]
                    self._sync_rgb_inputs()
                    return True
                # Click outside swatches but inside picker: deselect RGB focus
                for inp in self._rgb_inputs:
                    inp.focused = False
        return False

    def draw(self, surface):
        if not self.visible:
            return
        r = self._abs_rect()
        i18n = I18n.instancia()
        fuente = i18n.fuente(10) if i18n else pygame.font.SysFont("Arial", 10)
        fuente_b = i18n.fuente(10, bold=True) if i18n else pygame.font.SysFont("Arial", 10, bold=True)

        pygame.draw.rect(surface, (35, 40, 45), r)
        pygame.draw.rect(surface, (55, 60, 65), r, 1)

        # Preset swatches
        for i, color in enumerate(self._presets):
            col = i % self._cols
            row = i // self._cols
            sx = r.x + col * self._swatch_size + 1
            sy = r.y + row * self._swatch_size + 1
            sw = self._swatch_size - 2
            pygame.draw.rect(surface, color, (sx, sy, sw, sw))
            if color == self.selected_color:
                pygame.draw.rect(surface, (255, 255, 255), (sx - 1, sy - 1, sw + 2, sw + 2), 2)

        # RGB inputs row
        rgb_y = self._rgb_y(r)
        for i, (inp, label) in enumerate(zip(self._rgb_inputs, ["R", "G", "B"])):
            inp.rect.x = r.x + 2 + i * 30
            inp.rect.y = rgb_y
            inp.rect.w = 26
            inp.rect.h = 16
            inp.draw(surface)
            lbl = fuente_b.render(label, True, (180, 190, 200))
            surface.blit(lbl, (inp.rect.x + (inp.rect.w - lbl.get_width()) // 2, inp.rect.y - 11))

        # Color preview
        preview_y = self._preview_y(r)
        preview_rect = pygame.Rect(r.x + 4, preview_y, r.w - 8, 22)
        pygame.draw.rect(surface, self.selected_color, preview_rect)
        pygame.draw.rect(surface, (100, 100, 100), preview_rect, 1)

        # RGB text on preview
        rgb_text = f"RGB({self.selected_color[0]},{self.selected_color[1]},{self.selected_color[2]})"
        txt = fuente.render(rgb_text, True, (255, 255, 255) if sum(self.selected_color) < 384 else (0, 0, 0))
        surface.blit(txt, (preview_rect.x + (preview_rect.w - txt.get_width()) // 2,
                          preview_rect.y + (preview_rect.h - txt.get_height()) // 2 + 1))
