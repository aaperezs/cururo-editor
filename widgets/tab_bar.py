import pygame
from editor.widgets.base import Widget
from editor.translation import I18n


class TabBar(Widget):
    BORDER_RADIUS = 5

    def __init__(self, x, y, w, h, on_close_tab=None):
        super().__init__(x, y, w, h)
        self.tabs = []
        self.active_index = 0
        self._on_close_tab = on_close_tab
        self._hover_index = -1
        self._close_hover = set()

    def add_tab(self, tab_id, label, dirty=False, closeable=True):
        self.tabs.append({"id": tab_id, "label": label, "dirty": dirty, "closeable": closeable})

    def remove_tab(self, tab_id):
        for i, t in enumerate(self.tabs):
            if t["id"] == tab_id:
                self.tabs.pop(i)
                self._close_hover.discard(i)
                if self.active_index >= len(self.tabs):
                    self.active_index = max(0, len(self.tabs) - 1)
                return

    def set_tab_label(self, tab_id, label, dirty=False):
        for t in self.tabs:
            if t["id"] == tab_id:
                t["label"] = label
                t["dirty"] = dirty
                return

    def get_active(self):
        if self.tabs and self.active_index < len(self.tabs):
            return self.tabs[self.active_index]["id"]
        return None

    def set_size(self, w, h):
        self.rect.w = w
        self.rect.h = h

    def set_active_by_id(self, tab_id):
        for i, t in enumerate(self.tabs):
            if t["id"] == tab_id:
                self.active_index = i
                return

    def _abs_rect(self):
        if self.parent:
            pr = self.parent.get_abs_rect() if hasattr(self.parent, 'get_abs_rect') else self.parent.rect
            return pygame.Rect(pr.x + self.rect.x, pr.y + self.rect.y, self.rect.w, self.rect.h)
        return self.rect.copy()

    def handle_event(self, event):
        if not self.visible:
            return False
        r = self._abs_rect()
        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            n = max(len(self.tabs), 1)
            tab_w = max(100, r.w // n)
            self._hover_index = -1
            self._close_hover.clear()
            for i, tab in enumerate(self.tabs):
                tx = r.x + i * tab_w
                tab_rect = pygame.Rect(tx, r.y, tab_w, r.h)
                if tab_rect.collidepoint(mx, my):
                    self._hover_index = i
                    if tab.get("closeable"):
                        cx = tx + tab_w - 18
                        cy = r.y + (r.h - 12) // 2
                        close_rect = pygame.Rect(cx, cy, 12, 12)
                        if close_rect.collidepoint(mx, my):
                            self._close_hover.add(i)
                    break
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if r.collidepoint(mx, my):
                n = max(len(self.tabs), 1)
                tab_w = max(100, r.w // n)
                for i, tab in enumerate(self.tabs):
                    tx = r.x + i * tab_w
                    if tx <= mx < tx + tab_w:
                        if tab.get("closeable"):
                            cx = tx + tab_w - 18
                            cy = r.y + (r.h - 12) // 2
                            close_rect = pygame.Rect(cx, cy, 12, 12)
                            if close_rect.collidepoint(mx, my):
                                if self._on_close_tab:
                                    self._on_close_tab(tab["id"])
                                return True
                        self.active_index = i
                        return True
        return False

    def _get_font(self):
        i18n = I18n.instancia()
        return i18n.fuente(13) if i18n else pygame.font.SysFont("Arial", 13)

    def _get_font_small(self):
        i18n = I18n.instancia()
        return i18n.fuente(10) if i18n else pygame.font.SysFont("Arial", 10)

    def draw(self, surface):
        if not self.visible:
            return
        r = self._abs_rect()
        fuente = self._get_font()
        fuente_x = self._get_font_small()

        n = max(len(self.tabs), 1)
        tab_w = max(100, r.w // n)

        # Tab bar background strip
        pygame.draw.rect(surface, (28, 31, 36), r)
        pygame.draw.line(surface, (45, 50, 58), (r.x, r.y + r.h - 1),
                         (r.x + r.w - 1, r.y + r.h - 1))

        for i, tab in enumerate(self.tabs):
            tx = r.x + i * tab_w
            is_active = i == self.active_index
            is_hover = i == self._hover_index
            tab_rect = pygame.Rect(tx, r.y, tab_w, r.h)

            # --- Fill ---
            if is_active:
                color = (40, 44, 55)
            elif is_hover:
                color = (38, 42, 50)
            else:
                color = (34, 37, 44)

            pygame.draw.rect(surface, color, tab_rect,
                             border_bottom_left_radius=self.BORDER_RADIUS,
                             border_bottom_right_radius=self.BORDER_RADIUS)

            if is_active:
                # Accent top line
                pygame.draw.rect(surface, (70, 130, 200), (tx, r.y, tab_w, 2))
            else:
                # Border for inactive tabs
                pygame.draw.rect(surface, (45, 50, 58), tab_rect, 1,
                                 border_bottom_left_radius=self.BORDER_RADIUS,
                                 border_bottom_right_radius=self.BORDER_RADIUS)

            # --- Text ---
            label = tab["label"]
            tc = (235, 235, 240) if is_active else (150, 155, 165)
            txt = fuente.render(label, True, tc)
            sx = tx + 8
            sy = r.y + (r.h - txt.get_height()) // 2
            surface.blit(txt, (sx, sy))

            # --- Close button ---
            if tab.get("closeable"):
                cx = tx + tab_w - 18
                cy = r.y + (r.h - 12) // 2
                close_rect = pygame.Rect(cx, cy, 12, 12)
                if i in self._close_hover:
                    pygame.draw.rect(surface, (180, 60, 60), close_rect,
                                     border_radius=3)
                    x1, y1 = cx + 3, cy + 3
                    x2, y2 = cx + 9, cy + 9
                    pygame.draw.line(surface, (255, 255, 255), (x1, y1), (x2, y2), 2)
                    pygame.draw.line(surface, (255, 255, 255), (x2, y1), (x1, y2), 2)
                else:
                    pygame.draw.rect(surface, (80, 85, 95), close_rect,
                                     border_radius=3)
                    pygame.draw.rect(surface, (120, 125, 135), close_rect, 1,
                                     border_radius=3)
                    x1, y1 = cx + 3, cy + 3
                    x2, y2 = cx + 9, cy + 9
                    pygame.draw.line(surface, (160, 165, 175), (x1, y1), (x2, y2), 1)
                    pygame.draw.line(surface, (160, 165, 175), (x2, y1), (x1, y2), 1)

            # --- Dirty indicator dot ---
            if tab.get("dirty"):
                dot_x = tx + 6
                dot_y = r.y + r.h - 8
                pygame.draw.circle(surface, (200, 180, 60), (dot_x, dot_y), 3)
