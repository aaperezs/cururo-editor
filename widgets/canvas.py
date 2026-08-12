import pygame

from editor.translation import I18n
from editor.widgets.base import Widget


class Canvas(Widget):
    def __init__(self, x, y, w, h):

        super().__init__(x, y, w, h)
        self._surface = None
        self._zoom = 10
        self._offset_x = 0
        self._offset_y = 0
        self._pan_x = 0
        self._pan_y = 0
        self._panning = False
        self._pan_start = (0, 0)
        self._pan_start_pan = (0, 0)
        self._tool = None
        self._show_grid = True
        self._grid_color = (60, 60, 65)
        self._bg_color = (25, 25, 30)
        self._cut_lines = []
        self._show_cut_lines = True
        self._symmetry = "off"
        self._hover_surface = None
        self._cache_img = None
        self._cache_img_key = None
        self._cache_check = None
        self._cache_check_key = None

    def set_symmetry(self, mode):
        self._symmetry = mode

    def set_cut_lines(self, lines):
        self._cut_lines = list(lines)

    def set_show_cut_lines(self, show):
        self._show_cut_lines = show

    def set_surface(self, surface):
        self._surface = surface
        if self._tool and hasattr(self._tool, "set_surface"):
            self._tool.set_surface(surface)
        self._invalidate()

    def get_surface(self):
        return self._surface

    def set_tool(self, tool):
        self._tool = tool
        if self._tool and hasattr(self._tool, "set_surface") and self._surface is not None:
            self._tool.set_surface(self._surface)

    def set_zoom(self, zoom):
        self._zoom = max(2, min(40, zoom))
        self._invalidate()

    def get_zoom(self):
        return self._zoom

    def fit(self, margin=8):
        """Ajusta el zoom y el pan para que el sprite completo quepa"""
        if self._surface is None:
            return
        r = self._abs_rect()
        if r.w <= 0 or r.h <= 0:
            return
        w, h = self._surface.get_size()
        if w <= 0 or h <= 0:
            return
        zx = max(1, (r.w - margin * 2)) / w
        zy = max(1, (r.h - margin * 2)) / h
        self._zoom = max(2, min(40, int(min(zx, zy))))
        self._pan_x = 0
        self._pan_y = 0
        self._invalidate()

    def _invalidate(self):
        self._cache_img = None
        self._cache_img_key = None
        self._cache_check = None
        self._cache_check_key = None

    def _abs_rect(self):
        if self.parent:
            pr = self.parent.get_abs_rect() if hasattr(self.parent, 'get_abs_rect') else self.parent.rect
            return pygame.Rect(pr.x + self.rect.x, pr.y + self.rect.y, self.rect.w, self.rect.h)
        return self.rect.copy()

    def _update_offsets(self):
        """Calcula offset base centrado + pan del usuario, con límites"""
        if self._surface is None:
            self._offset_x = 0
            self._offset_y = 0
            return (self._offset_x, self._offset_y)
        r = self._abs_rect()
        w, h = self._surface.get_size()
        zoom = self._zoom
        dw = w * zoom
        dh = h * zoom
        base_x = (r.w - dw) // 2
        base_y = (r.h - dh) // 2

        ox = base_x + self._pan_x
        oy = base_y + self._pan_y
        if dw >= r.w:
            ox = max(r.w - dw, min(0, ox))
        else:
            ox = base_x
        if dh >= r.h:
            oy = max(r.h - dh, min(0, oy))
        else:
            oy = base_y
        self._offset_x = int(ox)
        self._offset_y = int(oy)
        return (self._offset_x, self._offset_y)

    def _canvas_to_surface(self, mx, my):
        r = self._abs_rect()
        if self._surface is None:
            return None
        self._update_offsets()
        px = (mx - r.x - self._offset_x) // self._zoom
        py = (my - r.y - self._offset_y) // self._zoom
        return (px, py)

    def get_hover_surface(self):
        return self._hover_surface

    def surface_to_screen(self, sx, sy):
        self._update_offsets()
        r = self._abs_rect()
        return (r.x + self._offset_x + int(sx) * self._zoom,
                r.y + self._offset_y + int(sy) * self._zoom)

    def handle_event(self, event):
        if not self.visible or not self.enabled or self._surface is None:
            return False
        r = self._abs_rect()

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 3:
                self._panning = True
                self._pan_start = event.pos
                self._pan_start_pan = (self._pan_x, self._pan_y)
                return True
            if event.button == 1:
                if r.collidepoint(event.pos):
                    pos = self._canvas_to_surface(*event.pos)
                    if pos and self._tool and hasattr(self._tool, 'on_mouse_down'):
                        self._tool.on_mouse_down(self._surface, pos, getattr(self._tool, 'color', (255, 255, 255)))
                        self._invalidate()
                        return True
            elif event.button == 4:
                self.set_zoom(self._zoom + 2)
                return True
            elif event.button == 5:
                self.set_zoom(self._zoom - 2)
                return True
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 3:
                self._panning = False
                return True
            if event.button == 1:
                if self._tool and hasattr(self._tool, 'on_mouse_up'):
                    self._tool.on_mouse_up(self._surface, (0, 0), (0, 0, 0))
                    self._invalidate()
                return False
        if event.type == pygame.MOUSEMOTION:
            if self._panning:
                dx = event.pos[0] - self._pan_start[0]
                dy = event.pos[1] - self._pan_start[1]
                self._pan_x = self._pan_start_pan[0] + dx
                self._pan_y = self._pan_start_pan[1] + dy
                return True
            pos = self._canvas_to_surface(*event.pos)
            if r.collidepoint(event.pos):
                self._hover_surface = pos
            else:
                self._hover_surface = None
            if pos and self._tool and hasattr(self._tool, 'on_mouse_move'):
                if r.collidepoint(event.pos) and pygame.mouse.get_pressed()[0]:
                    self._tool.on_mouse_move(self._surface, pos, getattr(self._tool, 'color', (255, 255, 255)))
                    self._invalidate()
                    return True
            return False
        return False

    def _scaled_sprite(self):
        if not self._surface:
            return None
        w, h = self._surface.get_size()
        zoom = self._zoom
        key = (w, h, zoom)
        if self._cache_img_key == key and self._cache_img is not None:
            return self._cache_img
        dw = max(1, int(w * zoom))
        dh = max(1, int(h * zoom))
        if dw == w and dh == h:
            img = self._surface
        else:
            img = pygame.transform.scale(self._surface, (dw, dh))
        self._cache_img = img
        self._cache_img_key = key
        return img

    def _scaled_checker(self, dw, dh):
        key = (int(dw), int(dh))
        if self._cache_check_key == key and self._cache_check is not None:
            return self._cache_check
        pat = pygame.Surface((8, 8))
        for py in range(8):
            for px in range(8):
                pat.set_at((px, py), (45, 45, 50) if ((px // 4) + (py // 4)) % 2 == 0 else (35, 35, 40))
        scaled = pygame.transform.scale(pat, (max(1, int(dw)), max(1, int(dh))))
        self._cache_check = scaled
        self._cache_check_key = key
        return scaled

    def draw(self, surface):
        if not self.visible:
            return
        r = self._abs_rect()
        pygame.draw.rect(surface, self._bg_color, r)
        pygame.draw.rect(surface, (50, 55, 60), r, 1)

        if self._surface is None:
            i18n = I18n.instancia()
            fuente = i18n.fuente(16) if i18n else pygame.font.SysFont("Arial", 16)
            txt = fuente.render(i18n.t("sprite.no_file") if i18n else "No sprite loaded", True, (120, 120, 120))
            surface.blit(txt, (r.x + (r.w - txt.get_width()) // 2, r.y + (r.h - txt.get_height()) // 2))
            return

        self._update_offsets()
        ox = r.x + self._offset_x
        oy = r.y + self._offset_y
        zoom = self._zoom
        surf_w = self._surface.get_width()
        surf_h = self._surface.get_height()
        dw = surf_w * zoom
        dh = surf_h * zoom

        # Checker + sprite escalados (cache)
        surface.blit(self._scaled_checker(dw, dh), (ox, oy))
        surface.blit(self._scaled_sprite(), (ox, oy))

        # Grid por píxel (líneas, eficiente: (w+1)+(h+1) trazos sin importar el tamaño)
        if self._show_grid and zoom >= 6:
            for px in range(surf_w + 1):
                x = ox + px * zoom
                pygame.draw.line(surface, self._grid_color, (x, oy), (x, oy + dh))
            for py in range(surf_h + 1):
                y = oy + py * zoom
                pygame.draw.line(surface, self._grid_color, (ox, y), (ox + dw, y))

        if self._show_cut_lines and self._cut_lines:
            for (x1, y1), (x2, y2) in self._cut_lines:
                sx1 = ox + x1 * zoom
                sy1 = oy + y1 * zoom
                sx2 = ox + x2 * zoom
                sy2 = oy + y2 * zoom
                pygame.draw.line(surface, (0, 200, 255), (int(sx1), int(sy1)), (int(sx2), int(sy2)), max(1, zoom // 8))

        # Symmetry axis overlay
        if self._symmetry != "off" and zoom >= 4:
            axis_color = (200, 80, 80)
            if self._symmetry in ("horizontal", "both"):
                mid_x = ox + (surf_w // 2) * zoom
                for ly in range(int(oy), int(oy + dh), max(2, zoom)):
                    pygame.draw.rect(surface, axis_color, (int(mid_x) - 1, ly, 2, max(1, zoom // 2)))
            if self._symmetry in ("vertical", "both"):
                mid_y = oy + (surf_h // 2) * zoom
                for lx in range(int(ox), int(ox + dw), max(2, zoom)):
                    pygame.draw.rect(surface, axis_color, (lx, int(mid_y) - 1, max(1, zoom // 2), 2))

        # Tool overlay (marquesina, preview de forma, pegado flotante)
        if self._tool and hasattr(self._tool, "draw_overlay"):
            self._tool.draw_overlay(surface, self)

    def _draw_checker(self, surface, x, y, w, h):
        c1 = (45, 45, 50)
        c2 = (35, 35, 40)
        s = 4
        for py in range(0, h, s):
            for px in range(0, w, s):
                color = c1 if ((x + px) // s + (y + py) // s) % 2 == 0 else c2
                pygame.draw.rect(surface, color, (x + px, y + py, s, s))

    def _draw_checker_blended(self, surface, x, y, w, h, pixel_color):
        a = pixel_color.a
        c1 = (45, 45, 50)
        c2 = (35, 35, 40)
        s = 4
        for py in range(0, h, s):
            for px in range(0, w, s):
                checker = c1 if ((x + px) // s + (y + py) // s) % 2 == 0 else c2
                r = (pixel_color.r * a + checker[0] * (255 - a)) // 255
                g = (pixel_color.g * a + checker[1] * (255 - a)) // 255
                b = (pixel_color.b * a + checker[2] * (255 - a)) // 255
                pygame.draw.rect(surface, (r, g, b), (x + px, y + py, s, s))
