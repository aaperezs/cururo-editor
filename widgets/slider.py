import pygame
from editor.widgets.base import Widget


class Slider(Widget):
    def __init__(self, x, y, w, h, min_val=0, max_val=255, default=255, label=""):
        super().__init__(x, y, w, h)
        self.min = min_val
        self.max = max_val
        self.value = default
        self.label = label
        self._dragging = False
        self._hover = False
        self.callback = None

    def _abs_rect(self):
        if self.parent:
            pr = self.parent.get_abs_rect() if hasattr(self.parent, 'get_abs_rect') else self.parent.rect
            return pygame.Rect(pr.x + self.rect.x, pr.y + self.rect.y, self.rect.w, self.rect.h)
        return self.rect.copy()

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        r = self._abs_rect()
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if r.collidepoint(event.pos):
                self._dragging = True
                self._update_from_pos(event.pos, r)
                return True
        if event.type == pygame.MOUSEMOTION:
            self._hover = r.collidepoint(event.pos)
            if self._dragging:
                self._update_from_pos(event.pos, r)
                return True
        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            if self._dragging:
                self._dragging = False
                return True
        return False

    def _update_from_pos(self, pos, r):
        track_x = r.x + 14
        track_w = r.w - 28
        if track_w <= 0:
            return
        rel = max(0.0, min(1.0, (pos[0] - track_x) / track_w))
        old = self.value
        self.value = int(self.min + (self.max - self.min) * rel)
        if self.value != old and self.callback:
            self.callback(self.value)

    def draw(self, surface):
        if not self.visible:
            return
        r = self._abs_rect()
        pygame.draw.rect(surface, (45, 50, 55), r)

        if self.label:
            from editor.translation import I18n
            i18n = I18n.instancia()
            f = i18n.fuente(11) if i18n else pygame.font.Font(None, 11)
            txt = f.render(self.label + ":", True, (200, 200, 200))
            surface.blit(txt, (r.x + 3, r.y + (r.h - txt.get_height()) // 2))

        pct = ((self.value - self.min) / (self.max - self.min)) if self.max > self.min else 0
        track_x = r.x + 14
        track_w = r.w - 42
        track_y = r.y + r.h // 2 - 2

        pygame.draw.rect(surface, (70, 75, 85), (track_x, track_y, track_w, 4))
        if pct > 0:
            fill_w = int(track_w * pct)
            pygame.draw.rect(surface, (100, 140, 200), (track_x, track_y, fill_w, 4))

        thumb_x = track_x + int(track_w * pct) - 4
        thumb_rect = (thumb_x, r.y + 2, 8, r.h - 4)
        thumb_color = (160, 190, 220) if self._hover or self._dragging else (130, 160, 190)
        pygame.draw.rect(surface, thumb_color, thumb_rect)

        from editor.translation import I18n
        i18n = I18n.instancia()
        f = i18n.fuente(11) if i18n else pygame.font.Font(None, 11)
        pct_str = f"{pct * 100:.0f}%"
        vt = f.render(pct_str, True, (200, 200, 200))
        surface.blit(vt, (r.x + r.w - vt.get_width() - 4, r.y + (r.h - vt.get_height()) // 2))
