import pygame
from editor.widgets.base import Widget
from editor.translation import I18n

MAX_VISIBLE = 10
ITEM_H = 20
SCROLL_W = 18


class Dropdown(Widget):
    """Dropdown con filtro, scrollbar arrastrable y navegacion por teclado.

    Modo de uso:
        dd = Dropdown(x, y, w, options, callback)
        dd.open()  # muestra el dropdown
        dd.handle_event(event)  # procesa eventos
        dd.draw(surface)  # dibuja
        dd.selected  # valor seleccionado (None si no)
        dd.is_open  # bool
    """

    def __init__(self, x, y, w, options, callback):

        super().__init__(x, y, w)
        self.options = list(options)
        self._all_options = list(options)
        self.callback = callback
        self.is_open = False
        self.selected = None
        self.highlight = 0
        self.scroll = 0
        self.filtro = ""
        self._filter_active = False
        self._filter_text = ""
        self._cursor_timer = 0
        self._cursor_visible = True

        # Scrollbar dragging
        self._dragging = False
        self._drag_start = (0, 0)
        self._drag_start_scroll = 0

        # Visual
        self.bg_color = (45, 50, 58)
        self.border_color = (70, 75, 85)
        self.highlight_color = (60, 80, 120)
        self.text_color = (220, 220, 220)
        self.dim_color = (160, 165, 175)
        self.scroll_track = (40, 43, 50)
        self.scroll_thumb = (75, 80, 90)
        self.scroll_thumb_hover = (95, 100, 110)
        self.filter_bg = (50, 55, 65)

    def get_abs_rect(self):
        if self.parent:
            pr = self.parent.get_abs_rect()
            return pygame.Rect(pr.x + self.rect.x, pr.y + self.rect.y,
                               self.rect.w, self.rect.h)
        return self.rect.copy()

    def _abs_rect(self):
        return self.get_abs_rect()

    def contains(self, point):
        return self.get_abs_rect().collidepoint(point)

    def set_pos(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def set_size(self, w, h):
        self.rect.w = w
        self.rect.h = h

    def _filtrados(self):
        if not self.filtro:
            return self._all_options
        f = self.filtro.lower()
        return [o for o in self._all_options
                if self._opt_label(o).lower().startswith(f) or f in self._opt_label(o).lower()]

    def _opt_label(self, opt):
        if isinstance(opt, tuple):
            return str(opt[1])
        return str(opt)

    def _opt_value(self, opt):
        if isinstance(opt, tuple):
            return opt[0]
        return opt

    def open(self, x=None, y=None):
        if x is not None:
            self.rect.x = x
        if y is not None:
            self.rect.y = y
        self.is_open = True
        self.filtro = ""
        self.options = list(self._all_options)
        self.scroll = 0
        self.highlight = 0
        self._filter_active = True
        self._filter_text = ""

    def close(self):
        self.is_open = False
        self._filter_active = False

    def _calc_h(self):
        vis = min(len(self.options), MAX_VISIBLE)
        return vis * ITEM_H + (ITEM_H if self._filter_active else 0)

    def handle_event(self, event):
        if not self.visible or not self.enabled or not self.is_open:
            return False
        r = self.get_abs_rect()
        mx, my = pygame.mouse.get_pos() if event.type in (pygame.MOUSEMOTION, pygame.MOUSEBUTTONDOWN) else (0, 0)

        # Scroll con rueda
        if event.type == pygame.MOUSEWHEEL:
            if r.collidepoint(pygame.mouse.get_pos()):
                self.scroll -= event.y
                self._clamp_scroll()
                return True

        # Click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if not r.collidepoint(mx, my):
                self.close()
                return True

            # Scrollbar zone (right edge)
            scroll_zone = pygame.Rect(r.right - SCROLL_W, r.y, SCROLL_W, r.h)
            if scroll_zone.collidepoint(mx, my):
                self._handle_scroll_click(mx, my, r)
                return True

            # Item seleccion
            list_y = r.y + (ITEM_H if self._filter_active else 0)
            rel_y = my - list_y
            if rel_y >= 0:
                idx = rel_y // ITEM_H + self.scroll
                if 0 <= idx < len(self.options):
                    self.selected = self._opt_value(self.options[idx])
                    if self.callback:
                        self.callback(self.options[idx])
                    self.close()
                    return True

            return True

        # Arrastre de scrollbar
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False
        if event.type == pygame.MOUSEMOTION and self._dragging:
            r = self.get_abs_rect()
            list_h = r.h - (ITEM_H if self._filter_active else 0)
            if list_h > 0 and len(self.options) > MAX_VISIBLE:
                track_h = list_h - max(16, list_h * MAX_VISIBLE // len(self.options))
                if track_h > 0:
                    dy = my - self._drag_start[1]
                    max_scroll = len(self.options) - MAX_VISIBLE
                    self.scroll = int(self._drag_start_scroll + dy / track_h * max_scroll)
                    self._clamp_scroll()
            return True

        # Teclas
        if event.type == pygame.KEYDOWN and self.is_open:
            if event.key == pygame.K_ESCAPE:
                self.close()
                return True
            if event.key == pygame.K_RETURN:
                if 0 <= self.highlight < len(self.options):
                    self.selected = self._opt_value(self.options[self.highlight])
                    if self.callback:
                        self.callback(self.options[self.highlight])
                    self.close()
                    return True
            if event.key == pygame.K_UP:
                self.highlight = max(0, self.highlight - 1)
                if self.highlight < self.scroll:
                    self.scroll = self.highlight
                return True
            if event.key == pygame.K_DOWN:
                self.highlight = min(len(self.options) - 1, self.highlight + 1)
                if self.highlight >= self.scroll + MAX_VISIBLE:
                    self.scroll = self.highlight - MAX_VISIBLE + 1
                return True
            if event.key == pygame.K_BACKSPACE and self._filter_active:
                self.filtro = self.filtro[:-1]
                self._apply_filtro()
                return True
            if event.unicode and self._filter_active and event.unicode.isprintable():
                self.filtro += event.unicode
                self._apply_filtro()
                return True

        return False

    def _apply_filtro(self):
        self.options = self._filtrados()
        self.scroll = 0
        self.highlight = 0

    def _clamp_scroll(self):
        max_scroll = max(0, len(self.options) - MAX_VISIBLE)
        self.scroll = max(0, min(self.scroll, max_scroll))
        self.highlight = max(0, min(self.highlight, len(self.options) - 1))

    def _handle_scroll_click(self, mx, my, r):
        list_h = r.h - (ITEM_H if self._filter_active else 0)
        if list_h <= 0:
            return
        thumb_h = max(16, list_h * MAX_VISIBLE // max(1, len(self.options)))
        # Check arrows
        if my - r.y < 16:
            self.scroll = max(0, self.scroll - 1)
            return
        if r.y + r.h - my < 16:
            self.scroll = min(len(self.options) - MAX_VISIBLE, self.scroll + 1)
            return
        # Click en track — iniciar drag
        self._dragging = True
        self._drag_start = (mx, my)
        self._drag_start_scroll = self.scroll
        # Tambien mover al clic
        track_h = list_h - thumb_h
        if track_h > 0:
            rel_y = my - r.y - (ITEM_H if self._filter_active else 0) - thumb_h // 2
            if rel_y < 0:
                rel_y = 0
            max_scroll = len(self.options) - MAX_VISIBLE
            self.scroll = int(rel_y / track_h * max_scroll)
            self._clamp_scroll()

    def draw(self, surface):
        if not self.visible or not self.is_open:
            return
        r = self.get_abs_rect()
        i = I18n.instancia()
        fpeq = i.fuente(11) if i else pygame.font.SysFont("Arial", 11)
        fonte = i.fuente(13) if i else pygame.font.SysFont("Arial", 13)

        vis_h = min(len(self.options), MAX_VISIBLE) * ITEM_H
        total_h = vis_h + (ITEM_H if self._filter_active else 0)
        self.rect.h = total_h

        # Fondo
        pygame.draw.rect(surface, self.bg_color, (r.x, r.y, r.w, total_h))
        pygame.draw.rect(surface, self.border_color, (r.x, r.y, r.w, total_h), 1)

        cy = r.y
        # Input de filtro
        if self._filter_active:
            self._cursor_timer += 1
            if self._cursor_timer >= 30:
                self._cursor_timer = 0
                self._cursor_visible = not self._cursor_visible
            pygame.draw.rect(surface, self.filter_bg, (r.x, cy, r.w, ITEM_H))
            display = self.filtro + ("|" if self._cursor_visible else "")
            txt = fpeq.render(display, True, self.text_color)
            surface.blit(txt, (r.x + 4, cy + 2))
            cy += ITEM_H

        # Opciones
        for vi in range(vis_h // ITEM_H):
            oi = self.scroll + vi
            if oi >= len(self.options):
                break
            opt = self.options[oi]
            oy = cy + vi * ITEM_H

            if oi == self.highlight:
                pygame.draw.rect(surface, self.highlight_color, (r.x, oy, r.w - SCROLL_W, ITEM_H))

            lbl = self._opt_label(opt)
            txt = fpeq.render(lbl, True, self.text_color)
            surface.blit(txt, (r.x + 4, oy + 2))

            if vi < vis_h // ITEM_H - 1 and vi + self.scroll < len(self.options) - 1:
                pygame.draw.line(surface, self.border_color,
                                 (r.x, oy + ITEM_H), (r.x + r.w - SCROLL_W, oy + ITEM_H))

        # Scrollbar
        sb_x = r.x + r.w - SCROLL_W
        sb_h = vis_h
        pygame.draw.rect(surface, self.scroll_track, (sb_x, cy, SCROLL_W, sb_h))
        if len(self.options) > MAX_VISIBLE:
            thumb_h = max(16, int(sb_h * MAX_VISIBLE / len(self.options)))
            max_scroll = len(self.options) - MAX_VISIBLE
            thumb_y = cy + int((sb_h - thumb_h) * self.scroll / max_scroll) if max_scroll > 0 else cy
            color = self.scroll_thumb_hover if self._dragging else self.scroll_thumb
            pygame.draw.rect(surface, color, (sb_x + 2, thumb_y, SCROLL_W - 4, thumb_h))
            # Flechas
            if self.scroll > 0:
                surface.blit(fpeq.render("▲", True, self.dim_color), (sb_x + 3, cy + 2))
            if self.scroll + MAX_VISIBLE < len(self.options):
                surface.blit(fpeq.render("▼", True, self.dim_color), (sb_x + 3, cy + sb_h - 16))
