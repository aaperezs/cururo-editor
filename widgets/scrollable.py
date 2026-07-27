import pygame
from editor.widgets.base import Widget


class ScrollableArea(Widget):
    def __init__(self, x, y, w, h, draw_callback=None):
        super().__init__(x, y, w, h)
        self.draw_callback = draw_callback

        self.content_w = 0
        self.content_h = 0
        self.scroll_x = 0
        self.scroll_y = 0
        self.scrollbar_size = 16
        self._dragging_h = False
        self._dragging_v = False
        self._drag_start_mouse = (0, 0)
        self._drag_start_scroll = (0, 0)

        self._track_color = (45, 49, 55)
        self._thumb_color = (110, 120, 130)
        self._thumb_hover = (140, 150, 165)
        self._thumb_drag = (165, 175, 190)
        self._border_color = (55, 60, 68)
        self._corner_color = (38, 42, 48)

    def set_content(self, w, h):
        self.content_w = max(w, 1)
        self.content_h = max(h, 1)
        self._clamp_scroll()

    def viewport_rect(self):
        r = self.get_abs_rect()
        return pygame.Rect(r.x, r.y, r.w - self.scrollbar_size, r.h - self.scrollbar_size)

    def _need_h_scroll(self):
        return self.content_w > self.viewport_rect().w

    def _need_v_scroll(self):
        return self.content_h > self.viewport_rect().h

    def _clamp_scroll(self):
        vp = self.viewport_rect()
        max_x = max(0, self.content_w - vp.w)
        max_y = max(0, self.content_h - vp.h)
        self.scroll_x = max(0, min(self.scroll_x, max_x))
        self.scroll_y = max(0, min(self.scroll_y, max_y))

    def _thumb_h_rect(self):
        vp = self.viewport_rect()
        if self.content_w <= vp.w:
            return pygame.Rect(0, 0, 0, 0)
        r = self.get_abs_rect()
        track_w = r.w - self.scrollbar_size
        thumb_w = max(20, int(track_w * vp.w / self.content_w))
        thumb_x = r.x + int(self.scroll_x / (self.content_w - vp.w) * (track_w - thumb_w))
        return pygame.Rect(thumb_x, r.y + r.h - self.scrollbar_size, thumb_w, self.scrollbar_size)

    def _thumb_v_rect(self):
        vp = self.viewport_rect()
        if self.content_h <= vp.h:
            return pygame.Rect(0, 0, 0, 0)
        r = self.get_abs_rect()
        track_h = r.h - self.scrollbar_size
        thumb_h = max(20, int(track_h * vp.h / self.content_h))
        thumb_y = r.y + int(self.scroll_y / (self.content_h - vp.h) * (track_h - thumb_h))
        return pygame.Rect(r.x + r.w - self.scrollbar_size, thumb_y, self.scrollbar_size, thumb_h)

    def _track_h_rect(self):
        r = self.get_abs_rect()
        return pygame.Rect(r.x, r.y + r.h - self.scrollbar_size, r.w - self.scrollbar_size, self.scrollbar_size)

    def _track_v_rect(self):
        r = self.get_abs_rect()
        return pygame.Rect(r.x + r.w - self.scrollbar_size, r.y, self.scrollbar_size, r.h - self.scrollbar_size)

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        r = self.get_abs_rect()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if not r.collidepoint(mx, my):
                return False

            thumb_h = self._thumb_h_rect()
            thumb_v = self._thumb_v_rect()

            if thumb_h and thumb_h.collidepoint(mx, my):
                self._dragging_h = True
                self._drag_start_mouse = (mx, my)
                self._drag_start_scroll = (self.scroll_x, self.scroll_y)
                return True
            if thumb_v and thumb_v.collidepoint(mx, my):
                self._dragging_v = True
                self._drag_start_mouse = (mx, my)
                self._drag_start_scroll = (self.scroll_x, self.scroll_y)
                return True

            # Click on track
            vp = self.viewport_rect()
            track_h = self._track_h_rect()
            track_v = self._track_v_rect()
            if track_h and track_h.collidepoint(mx, my):
                thumb = thumb_h
                if thumb:
                    tpos = mx - track_h.x
                    self.scroll_x = int(tpos / track_h.w * self.content_w)
                    self._clamp_scroll()
                return True
            if track_v and track_v.collidepoint(mx, my):
                thumb = thumb_v
                if thumb:
                    tpos = my - track_v.y
                    self.scroll_y = int(tpos / track_v.h * self.content_h)
                    self._clamp_scroll()
                return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging_h = False
            self._dragging_v = False

        if event.type == pygame.MOUSEMOTION:
            mx, my = event.pos
            if self._dragging_h:
                dx = mx - self._drag_start_mouse[0]
                track_h = self._track_h_rect()
                if track_h and track_h.w > 0:
                    vp = self.viewport_rect()
                    px_per_scroll = (self.content_w - vp.w) / (track_h.w - self._thumb_h_rect().w) if track_h.w > self._thumb_h_rect().w else 1
                    self.scroll_x = self._drag_start_scroll[0] + int(dx * px_per_scroll)
                    self._clamp_scroll()
                return True
            if self._dragging_v:
                dy = my - self._drag_start_mouse[1]
                track_v = self._track_v_rect()
                if track_v and track_v.h > 0:
                    vp = self.viewport_rect()
                    px_per_scroll = (self.content_h - vp.h) / (track_v.h - self._thumb_v_rect().h) if track_v.h > self._thumb_v_rect().h else 1
                    self.scroll_y = self._drag_start_scroll[1] + int(dy * px_per_scroll)
                    self._clamp_scroll()
                return True

        if event.type == pygame.MOUSEWHEEL:
            if r.collidepoint(pygame.mouse.get_pos()):
                mods = pygame.key.get_mods()
                if mods & pygame.KMOD_SHIFT:
                    self.scroll_x -= event.y * 40
                else:
                    self.scroll_y -= event.y * 40
                self._clamp_scroll()
                return True

        return False

    def draw(self, surface):
        if not self.visible:
            return
        r = self.get_abs_rect()
        vp = self.viewport_rect()

        # Background
        pygame.draw.rect(surface, (25, 28, 32), r)
        pygame.draw.rect(surface, self._border_color, r, 1)

        # Content
        clip = surface.get_clip()
        surface.set_clip(vp)
        if self.draw_callback:
            self.draw_callback(surface, vp.x, vp.y, self.scroll_x, self.scroll_y)
        surface.set_clip(clip)

        # Scrollbars
        need_h = self._need_h_scroll()
        need_v = self._need_v_scroll()
        if need_h or need_v:
            self._draw_scrollbar_h(surface, need_h)
            self._draw_scrollbar_v(surface, need_v)
            if need_h and need_v:
                cr = self.get_abs_rect()
                pygame.draw.rect(surface, self._corner_color,
                    (cr.x + cr.w - self.scrollbar_size, cr.y + cr.h - self.scrollbar_size,
                     self.scrollbar_size, self.scrollbar_size))

    def _draw_scrollbar_h(self, surface, visible=True):
        if not visible:
            return
        track = self._track_h_rect()
        if track.w <= 0:
            return
        pygame.draw.rect(surface, self._track_color, track)
        pygame.draw.line(surface, self._border_color,
            (track.x, track.y), (track.x + track.w, track.y))
        thumb = self._thumb_h_rect()
        if thumb.w > 0:
            mx, my = pygame.mouse.get_pos()
            color = self._thumb_drag if self._dragging_h else (self._thumb_hover if thumb.collidepoint(mx, my) else self._thumb_color)
            pygame.draw.rect(surface, color, thumb, border_radius=3)
            pygame.draw.rect(surface, self._border_color, thumb, 1, border_radius=3)

    def _draw_scrollbar_v(self, surface, visible=True):
        if not visible:
            return
        track = self._track_v_rect()
        if track.h <= 0:
            return
        pygame.draw.rect(surface, self._track_color, track)
        pygame.draw.line(surface, self._border_color,
            (track.x, track.y), (track.x, track.y + track.h))
        thumb = self._thumb_v_rect()
        if thumb.h > 0:
            mx, my = pygame.mouse.get_pos()
            color = self._thumb_drag if self._dragging_v else (self._thumb_hover if thumb.collidepoint(mx, my) else self._thumb_color)
            pygame.draw.rect(surface, color, thumb, border_radius=3)
            pygame.draw.rect(surface, self._border_color, thumb, 1, border_radius=3)
