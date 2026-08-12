import pygame

SELECT_COLOR = (0, 200, 255)
MOVE_COLOR = (255, 200, 0)


class SelectTool:
    id = "select"
    name_key = "sprite.select"

    def __init__(self):
        self.selection = None
        self.clipboard = None
        self.pasting = False
        self._surface = None
        self._marquee = None
        self._marquee_start = None
        self._moving = False
        self._move_offset = (0, 0)
        self._moving_surf = None
        self._move_origin = None

    def set_surface(self, surface):
        self._surface = surface

    # ── Acciones del panel ────────────────────────────────

    def copy(self):
        if self.selection:
            self.clipboard = self._surface.subsurface(self.selection).copy()
            self.pasting = False

    def cut(self):
        if self.selection:
            self.clipboard = self._surface.subsurface(self.selection).copy()
            self._clear_selection_region()
            self.pasting = False

    def delete(self):
        if self.selection:
            self._clear_selection_region()
            self.pasting = False

    def paste(self, pos=None):
        if self.clipboard is None:
            return
        self.pasting = True
        self._move_offset = (0, 0)
        self._moving_surf = self.clipboard.copy()
        self._move_origin = pos
        if pos is not None:
            w, h = self.clipboard.get_size()
            self.selection = pygame.Rect(pos[0], pos[1], w, h)
        else:
            self.selection = None

    def cancel(self):
        self.pasting = False
        self._moving = False
        self._moving_surf = None

    def clear_selection(self):
        self.selection = None
        self._marquee = None
        self.pasting = False
        self._moving = False
        self._moving_surf = None

    # ── Mouse ─────────────────────────────────────────────

    def on_mouse_down(self, surface, pos, color):
        self._surface = surface
        w, h = surface.get_size()
        if self.pasting and self._moving_surf is not None:
            cw, ch = self._moving_surf.get_size()
            px = pos[0] - (cw // 2)
            py = pos[1] - (ch // 2)
            surface.blit(self._moving_surf, (px, py))
            self.pasting = False
            self._moving_surf = None
            return
        if self.selection and self.selection.collidepoint(pos):
            self._moving = True
            self._move_origin = pos
            self._moving_surf = self._surface.subsurface(self.selection).copy()
            self._clear_rect(surface, self.selection)
            self._move_offset = (self.selection.x, self.selection.y)
            return
        self._marquee_start = pos
        self._marquee = pygame.Rect(pos[0], pos[1], 0, 0)

    def on_mouse_move(self, surface, pos, color):
        self._surface = surface
        w, h = surface.get_size()
        if self._moving and self._moving_surf is not None:
            cw, ch = self._moving_surf.get_size()
            ox = self._move_origin[0] if self._move_origin else 0
            oy = self._move_origin[1] if self._move_origin else 0
            dx = pos[0] - ox
            dy = pos[1] - oy
            sx = self._move_offset[0] + dx
            sy = self._move_offset[1] + dy
            self.selection = pygame.Rect(sx, sy, cw, ch)
            self.selection.clamp_ip(pygame.Rect(0, 0, w, h))
            return
        if self._marquee_start is not None:
            x1 = min(self._marquee_start[0], pos[0])
            y1 = min(self._marquee_start[1], pos[1])
            x2 = max(self._marquee_start[0], pos[0])
            y2 = max(self._marquee_start[1], pos[1])
            self._marquee = pygame.Rect(x1, y1, x2 - x1, y2 - y1)
            self._marquee.clamp_ip(pygame.Rect(0, 0, w, h))

    def on_mouse_up(self, surface, pos, color):
        w, h = surface.get_size()
        if self._moving and self._moving_surf is not None:
            if self.selection is not None:
                surface.blit(self._moving_surf, self.selection.topleft)
            self._moving = False
            self._moving_surf = None
            return
        if self._marquee is not None:
            if self._marquee.w >= 1 and self._marquee.h >= 1:
                self.selection = self._marquee.copy()
            else:
                self.selection = None
        self._marquee = None
        self._marquee_start = None

    def _clear_selection_region(self):
        if self.selection and self._surface is not None:
            self._clear_rect(self._surface, self.selection)

    @staticmethod
    def _clear_rect(surface, rect):
        x0 = max(0, rect.x)
        y0 = max(0, rect.y)
        x1 = min(surface.get_width(), rect.right)
        y1 = min(surface.get_height(), rect.bottom)
        clear = (0, 0, 0, 0)
        for yy in range(y0, y1):
            for xx in range(x0, x1):
                surface.set_at((xx, yy), clear)

    # ── Overlay ───────────────────────────────────────────

    def draw_overlay(self, surface, canvas):
        zoom = canvas.get_zoom()
        if self._marquee is not None:
            self._draw_marquee(surface, canvas, self._marquee, SELECT_COLOR)
        elif self.selection is not None and not self.pasting:
            self._draw_marquee(surface, canvas, self.selection, SELECT_COLOR)
        if self.pasting and self._moving_surf is not None:
            hover = canvas.get_hover_surface()
            cw, ch = self._moving_surf.get_size()
            if hover:
                px = hover[0] - (cw // 2)
                py = hover[1] - (ch // 2)
            else:
                px = py = 0
            sx, sy = canvas.surface_to_screen(px, py)
            overlay = self._moving_surf.copy()
            overlay.set_alpha(160)
            surface.blit(overlay, (sx, sy))
            pygame.draw.rect(surface, MOVE_COLOR,
                             (sx, sy, cw * zoom, ch * zoom), max(1, zoom // 8))
        elif self._moving and self.selection is not None and self._moving_surf is not None:
            sx, sy = canvas.surface_to_screen(self.selection.x, self.selection.y)
            overlay = self._moving_surf.copy()
            overlay.set_alpha(180)
            surface.blit(overlay, (sx, sy))
            pygame.draw.rect(surface, MOVE_COLOR,
                             (sx, sy, self.selection.w * zoom, self.selection.h * zoom),
                             max(1, zoom // 8))

    def _draw_marquee(self, surface, canvas, rect, color):
        zoom = canvas.get_zoom()
        sx, sy = canvas.surface_to_screen(rect.x, rect.y)
        sw = max(1, rect.w * zoom)
        sh = max(1, rect.h * zoom)
        width = max(1, zoom // 8)
        dash = max(2, zoom)
        x0, y0, x1, y1 = sx, sy, sx + sw, sy + sh
        for x in range(x0, x1 + 1, dash):
            pygame.draw.rect(surface, color, (x, y0, min(dash, x1 - x + 1), width))
        for x in range(x0, x1 + 1, dash):
            pygame.draw.rect(surface, color, (x, y1 - width + 1, min(dash, x1 - x + 1), width))
        for y in range(y0, y1 + 1, dash):
            pygame.draw.rect(surface, color, (x0, y, width, min(dash, y1 - y + 1)))
        for y in range(y0, y1 + 1, dash):
            pygame.draw.rect(surface, color, (x1 - width + 1, y, width, min(dash, y1 - y + 1)))
