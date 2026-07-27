import pygame
from editor.widgets.base import Widget
from editor.translation import I18n

LAYER_COLORS = {
    0: (200, 200, 200),
    1: (80, 130, 200),
    2: (80, 180, 130),
    3: (200, 180, 80),
    4: (200, 120, 80),
}


HEADER_H = 22

class LayerPanel(Widget):
    def __init__(self, x, y, w, h):

        super().__init__(x, y, w, h)
        self._layers = [0]
        self._row_h = 34
        self._active_z = 0
        self._on_change_active = None
        self._on_toggle = None
        self._on_opacity = None
        self._on_add_layer = None
        self._on_remove_layer = None
        self._slider_dragging = None

    def _content_top(self):
        r = self._abs_rect()
        return r.y + HEADER_H + 4

    def set_callbacks(self, on_change_active=None, on_toggle=None, on_opacity=None,
                      on_add_layer=None, on_remove_layer=None):
        self._on_change_active = on_change_active
        self._on_toggle = on_toggle
        self._on_opacity = on_opacity
        self._on_add_layer = on_add_layer
        self._on_remove_layer = on_remove_layer

    def set_active_z(self, z):
        self._active_z = z

    def get_active_z(self):
        return self._active_z

    def sync_layers(self, layers_order):
        self._layers = list(layers_order)
        self._cleanup_opacity_attrs()

    def _cleanup_opacity_attrs(self):
        all_zs = set(self._layers)
        for attr_name in list(self.__dict__.keys()):
            if attr_name.startswith('_opacity_') and not attr_name.startswith('_opacity_ ') and all_zs.isdisjoint({int(attr_name.replace('_opacity_', ''))}):
                delattr(self, attr_name)

    def _abs_rect(self):
        if self.parent:
            pr = self.parent.get_abs_rect() if hasattr(self.parent, 'get_abs_rect') else self.parent.rect
            return pygame.Rect(pr.x + self.rect.x, pr.y + self.rect.y, self.rect.w, self.rect.h)
        return self.rect.copy()

    def get_row_rect(self, row_idx):
        r = self._abs_rect()
        return pygame.Rect(r.x + 2, self._content_top() + row_idx * self._row_h, r.w - 4, self._row_h - 2)

    def get_eye_rect(self, row_idx):
        r = self._abs_rect()
        y = self._content_top() + row_idx * self._row_h
        return pygame.Rect(r.x + 4, y + 6, 20, 20)

    def get_slider_rect(self, row_idx):
        r = self._abs_rect()
        y = self._content_top() + row_idx * self._row_h
        return pygame.Rect(r.x + 28, y + 6, r.w - 54, 14)

    def get_remove_rect(self, row_idx):
        r = self._abs_rect()
        y = self._content_top() + row_idx * self._row_h
        return pygame.Rect(r.x + r.w - 20, y + 5, 16, 16)

    def get_add_rect(self):
        r = self._abs_rect()
        last_y = self._content_top() + len(self._layers) * self._row_h + 2
        return pygame.Rect(r.x + 4, last_y, r.w - 8, 24)

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        r = self._abs_rect()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if not r.collidepoint(mx, my):
                return False

            # Add layer button
            add_rect = self.get_add_rect()
            if add_rect.collidepoint(mx, my):
                if self._on_add_layer:
                    self._on_add_layer()
                return True

            for i, z in enumerate(self._layers):
                eye = self.get_eye_rect(i)
                slider = self.get_slider_rect(i)
                remove = self.get_remove_rect(i)
                row = self.get_row_rect(i)

                if eye.collidepoint(mx, my):
                    if self._on_toggle:
                        self._on_toggle(z)
                    return True

                if slider.collidepoint(mx, my):
                    self._slider_dragging = z
                    self._update_slider(z, mx, slider)
                    return True

                if remove.collidepoint(mx, my) and z != 0:
                    if self._on_remove_layer:
                        self._on_remove_layer(z)
                    return True

                if row.collidepoint(mx, my):
                    if self._on_change_active:
                        self._on_change_active(z)
                    return True

        if event.type == pygame.MOUSEMOTION and self._slider_dragging is not None:
            mx, my = event.pos
            if self._slider_dragging in self._layers:
                slider = self.get_slider_rect(self._layers.index(self._slider_dragging))
                self._update_slider(self._slider_dragging, mx, slider)
                return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._slider_dragging = None

        return False

    def _update_slider(self, z, mx, slider_rect):
        pct = (mx - slider_rect.x) / slider_rect.w
        pct = max(0, min(1, pct))
        opacity = int(pct * 100)
        if self._on_opacity:
            self._on_opacity(z, opacity)

    def draw(self, surface):
        if not self.visible:
            return
        r = self._abs_rect()
        i18n = I18n.instancia()
        fuente = i18n.fuente(12) if i18n else pygame.font.SysFont("Arial", 12)
        fuente_peq = i18n.fuente(10) if i18n else pygame.font.SysFont("Arial", 10)

        pygame.draw.rect(surface, (35, 40, 48), r)
        pygame.draw.rect(surface, (55, 60, 68), r, 1)

        # Header
        hdr = pygame.Rect(r.x + 2, r.y + 2, r.w - 4, HEADER_H)
        pygame.draw.rect(surface, (42, 46, 55), hdr)
        pygame.draw.rect(surface, (55, 60, 68), hdr, 1)
        titulo = fuente.render(i18n.t("map.layers_panel") if i18n else "Capas", True, (180, 190, 200))
        surface.blit(titulo, (r.x + 6, r.y + 4))

        ct = self._content_top()

        for i, z in enumerate(self._layers):
            y = ct + i * self._row_h
            is_active = z == self._active_z
            bg = (50, 55, 65) if is_active else (38, 42, 50)
            pygame.draw.rect(surface, bg, (r.x + 2, y, r.w - 4, self._row_h - 2))

            # Eye toggle
            e_rect = self.get_eye_rect(i)
            visible = getattr(self, f'_visible_{z}', True)
            if visible:
                # Open eye: circle outline with dot
                pygame.draw.circle(surface, (180, 190, 200), e_rect.center, 7, 2)
                pygame.draw.circle(surface, (180, 190, 200), e_rect.center, 2)
            else:
                # Closed eye: circle with line
                pygame.draw.circle(surface, (120, 130, 140), e_rect.center, 7, 2)
                pygame.draw.line(surface, (200, 80, 80), (e_rect.x + 2, e_rect.y + 2),
                                 (e_rect.x + e_rect.w - 2, e_rect.y + e_rect.h - 2), 2)

            # Name (click to select)
            txt = fuente_peq.render(f"Z={z}", True, (200, 200, 200))
            surface.blit(txt, (r.x + 30, y + 2))

            # Remove button (X)
            if z != 0:
                rrect = self.get_remove_rect(i)
                pygame.draw.rect(surface, (180, 60, 60), rrect)
                x_txt = fuente_peq.render("X", True, (255, 255, 255))
                surface.blit(x_txt, (rrect.x + (rrect.w - x_txt.get_width()) // 2,
                                     rrect.y + (rrect.h - x_txt.get_height()) // 2))

            # Slider (opacity)
            srect = self.get_slider_rect(i)
            pygame.draw.rect(surface, (50, 55, 62), srect)
            pygame.draw.rect(surface, (65, 70, 78), srect, 1)
            fill_w = int(srect.w * getattr(self, f'_opacity_{z}', 100) / 100)
            if fill_w > 0:
                fill_r = pygame.Rect(srect.x, srect.y, fill_w, srect.h)
                c = LAYER_COLORS.get(z, (150, 150, 150))
                c_dim = (c[0] // 2, c[1] // 2, c[2] // 2)
                pygame.draw.rect(surface, c_dim, fill_r)

            thumb_x = srect.x + fill_w - 1
            pygame.draw.rect(surface, (180, 180, 190), (thumb_x, srect.y - 1, 4, srect.h + 2))
            op_txt = fuente_peq.render(str(getattr(self, f'_opacity_{z}', 100)), True, (180, 185, 195))
            surface.blit(op_txt, (srect.x + srect.w - op_txt.get_width() - 2, srect.y - 1))

            # Active indicator
            if is_active:
                pygame.draw.rect(surface, (255, 180, 50), (r.x + 1, y, 2, self._row_h - 2))

        # Add layer button
        if len(self._layers) < 5:
            add_rect = self.get_add_rect()
            pygame.draw.rect(surface, (60, 100, 60), add_rect)
            pygame.draw.rect(surface, (80, 130, 80), add_rect, 1)
            i18n_instance = I18n.instancia()
            lang = i18n_instance.lang if i18n_instance else "en"
            add_txt = fuente_peq.render("+ Capa" if lang == "es" else "+ Layer", True, (220, 255, 220))
            surface.blit(add_txt, (add_rect.x + (add_rect.w - add_txt.get_width()) // 2,
                                   add_rect.y + (add_rect.h - add_txt.get_height()) // 2))

    def sync_state(self, tab):
        self._active_z = tab.active_z
        self._layers = list(tab.layer_order)
        self._cleanup_opacity_attrs()
        for z in self._layers:
            ls = tab.layers.get(z)
            if ls:
                setattr(self, f'_opacity_{z}', ls.opacity)
                setattr(self, f'_visible_{z}', ls.visible)


def _delattr(obj, name):
    if hasattr(obj, name):
        delattr(obj, name)


def _getattr(obj, name, default=None):
    return getattr(obj, name, default)