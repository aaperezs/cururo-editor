import pygame
from editor.widgets.base import Widget
from editor.translation import I18n


class Canvas(Widget):
    def __init__(self, x, y, w, h):

        super().__init__(x, y, w, h)
        self._surface = None
        self._zoom = 10
        self._offset_x = 0
        self._offset_y = 0
        self._tool = None
        self._show_grid = True
        self._grid_color = (60, 60, 65)
        self._bg_color = (25, 25, 30)
        self._cut_lines = []
        self._show_cut_lines = True
        self._symmetry = "off"

    def set_symmetry(self, mode):
        self._symmetry = mode

    def set_cut_lines(self, lines):
        self._cut_lines = list(lines)

    def set_show_cut_lines(self, show):
        self._show_cut_lines = show

    def set_surface(self, surface):
        self._surface = surface

    def get_surface(self):
        return self._surface

    def set_tool(self, tool):
        self._tool = tool

    def set_zoom(self, zoom):
        self._zoom = max(2, min(40, zoom))

    def get_zoom(self):
        return self._zoom

    def _abs_rect(self):
        if self.parent:
            pr = self.parent.get_abs_rect() if hasattr(self.parent, 'get_abs_rect') else self.parent.rect
            return pygame.Rect(pr.x + self.rect.x, pr.y + self.rect.y, self.rect.w, self.rect.h)
        return self.rect.copy()

    def _canvas_to_surface(self, mx, my):
        r = self._abs_rect()
        if self._surface is None:
            return None
        px = (mx - r.x - self._offset_x) // self._zoom
        py = (my - r.y - self._offset_y) // self._zoom
        return (px, py)

    def handle_event(self, event):
        if not self.visible or not self.enabled or self._surface is None:
            return False
        r = self._abs_rect()
        if event.type == pygame.MOUSEMOTION:
            pos = self._canvas_to_surface(*event.pos)
            if pos and self._tool and hasattr(self._tool, 'on_mouse_move'):
                if r.collidepoint(event.pos) and pygame.mouse.get_pressed()[0]:
                    self._tool.on_mouse_move(self._surface, pos, getattr(self._tool, 'color', (255, 255, 255)))
                    return True
            return False
        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                if r.collidepoint(event.pos):
                    pos = self._canvas_to_surface(*event.pos)
                    if pos and self._tool and hasattr(self._tool, 'on_mouse_down'):
                        self._tool.on_mouse_down(self._surface, pos, getattr(self._tool, 'color', (255, 255, 255)))
                        return True
            elif event.button == 4:
                self.set_zoom(self._zoom + 2)
                return True
            elif event.button == 5:
                self.set_zoom(self._zoom - 2)
                return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._tool and hasattr(self._tool, 'on_mouse_up'):
                self._tool.on_mouse_up(self._surface, (0, 0), (0, 0, 0))
            return False
        return False

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

        surf_w = self._surface.get_width()
        surf_h = self._surface.get_height()
        zoom = self._zoom
        self._offset_x = (r.w - surf_w * zoom) // 2
        self._offset_y = (r.h - surf_h * zoom) // 2

        for py in range(surf_h):
            for px in range(surf_w):
                color = self._surface.get_at((px, py))
                dx = r.x + self._offset_x + px * zoom
                dy = r.y + self._offset_y + py * zoom
                if color.a == 0:
                    self._draw_checker(surface, dx, dy, zoom, zoom)
                elif color.a == 255:
                    pygame.draw.rect(surface, (color.r, color.g, color.b), (dx, dy, zoom, zoom))
                else:
                    self._draw_checker_blended(surface, dx, dy, zoom, zoom, color)
                if self._show_grid and zoom >= 6:
                    pygame.draw.rect(surface, self._grid_color, (dx, dy, zoom, zoom), 1)

        if self._show_cut_lines and self._cut_lines and zoom >= 4:
            ox = r.x + self._offset_x
            oy = r.y + self._offset_y
            for (x1, y1), (x2, y2) in self._cut_lines:
                sx1 = ox + x1 * zoom
                sy1 = oy + y1 * zoom
                sx2 = ox + x2 * zoom
                sy2 = oy + y2 * zoom
                pygame.draw.line(surface, (0, 200, 255), (sx1, sy1), (sx2, sy2), max(1, zoom // 8))

        # Symmetry axis overlay
        if self._symmetry != "off" and self._surface and zoom >= 4:
            ox = r.x + self._offset_x
            oy = r.y + self._offset_y
            sw = self._surface.get_width()
            sh = self._surface.get_height()
            axis_color = (200, 80, 80)
            if self._symmetry in ("horizontal", "both"):
                mid_x = ox + (sw // 2) * zoom
                start_y = oy
                end_y = oy + sh * zoom
                for ly in range(start_y, end_y, max(2, zoom)):
                    pygame.draw.rect(surface, axis_color, (mid_x - 1, ly, 2, max(1, zoom // 2)))
            if self._symmetry in ("vertical", "both"):
                mid_y = oy + (sh // 2) * zoom
                start_x = ox
                end_x = ox + sw * zoom
                for lx in range(start_x, end_x, max(2, zoom)):
                    pygame.draw.rect(surface, axis_color, (lx, mid_y - 1, max(1, zoom // 2), 2))

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
