# editor/widgets/scroll_container.py
# Contenedor con barra de desplazamiento vertical para alojar sub-widgets.
import pygame
from editor.widgets.base import Container


class ScrollContainer(Container):
    """Area desplazable verticalmente que contiene widgets.

    Los widgets se agregan con add/remove/clear y se posicionan en coordenadas
    relativas al contenido (y desde 0 hacia abajo). Solo se muestra una barra
    vertical cuando el contenido excede el alto visible.
    """

    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        self.scrollbar_w = 16
        self.scroll_y = 0
        self.content_height = 0

        self._dragging_v = False
        self._drag_start_mouse = 0
        self._drag_start_scroll = 0
        self._scroll_step = 40

        self._track_color = (40, 43, 50)
        self._thumb_color = (75, 80, 90)
        self._thumb_hover = (95, 100, 110)
        self._thumb_drag = (120, 130, 145)
        self._border_color = (55, 60, 68)
        self._bg_color = (32, 35, 42)

        self._content = Container(0, 0, max(1, w - self.scrollbar_w), 1)
        self._content.parent = self

    # --- API de contenido ---

    def add(self, child):
        child.parent = self._content
        self._content.children.append(child)

    def remove(self, child):
        if child in self._content.children:
            child.parent = None
            self._content.children.remove(child)

    def clear(self):
        for c in self._content.children:
            c.parent = None
        self._content.children.clear()

    def set_content_height(self, h):
        self.content_height = max(0, int(h))
        self._content.rect.h = max(1, self.content_height)
        self._clamp_scroll()
        self._apply_scroll()

    def get_content_h(self):
        return self.content_height

    # --- Scroll ---

    def _need_v(self):
        return self.content_height > self.viewport_rect().h

    def viewport_rect(self):
        r = self.get_abs_rect()
        return pygame.Rect(r.x, r.y, r.w - self.scrollbar_w, r.h)

    def _clamp_scroll(self):
        max_y = max(0, self.content_height - self.viewport_rect().h)
        self.scroll_y = max(0, min(self.scroll_y, max_y))

    def _apply_scroll(self):
        self._content.rect.y = -self.scroll_y

    def _track_v_rect(self):
        r = self.get_abs_rect()
        return pygame.Rect(r.x + r.w - self.scrollbar_w, r.y, self.scrollbar_w, r.h)

    def _thumb_v_rect(self):
        vp = self.viewport_rect()
        if self.content_height <= vp.h:
            return pygame.Rect(0, 0, 0, 0)
        r = self.get_abs_rect()
        track = self._track_v_rect()
        thumb_h = max(20, int(track.h * vp.h / self.content_height))
        max_y = self.content_height - vp.h
        thumb_y = track.y + int(self.scroll_y / max_y * (track.h - thumb_h))
        return pygame.Rect(track.x, thumb_y, self.scrollbar_w, thumb_h)

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        r = self.get_abs_rect()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if not r.collidepoint(mx, my):
                return False
            thumb_v = self._thumb_v_rect()
            track_v = self._track_v_rect()
            if thumb_v and thumb_v.collidepoint(mx, my):
                self._dragging_v = True
                self._drag_start_mouse = my
                self._drag_start_scroll = self.scroll_y
                return True
            if track_v and track_v.collidepoint(mx, my) and self._need_v():
                max_y = max(0, self.content_height - self.viewport_rect().h)
                if track_v.h > 0:
                    self.scroll_y = int((my - track_v.y) / track_v.h * max_y)
                    self._clamp_scroll()
                    self._apply_scroll()
                return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging_v = False

        if event.type == pygame.MOUSEMOTION and self._dragging_v:
            dy = event.pos[1] - self._drag_start_mouse
            vp = self.viewport_rect()
            track_v = self._track_v_rect()
            thumb_v = self._thumb_v_rect()
            max_y = max(0, self.content_height - vp.h)
            denom = track_v.h - thumb_v.h
            if max_y > 0 and denom > 0:
                self.scroll_y = self._drag_start_scroll + int(dy * max_y / denom)
                self._clamp_scroll()
                self._apply_scroll()
            return True

        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            if r.collidepoint(mx, my):
                self.scroll_y -= event.y * self._scroll_step
                self._clamp_scroll()
                self._apply_scroll()
                return True

        return self._content.handle_event(event)

    def draw(self, surface):
        if not self.visible:
            return
        r = self.get_abs_rect()
        pygame.draw.rect(surface, self._bg_color, r)
        pygame.draw.rect(surface, self._border_color, r, 1)

        vp = self.viewport_rect()
        clip = surface.get_clip()
        surface.set_clip(vp)
        self._content.draw(surface)
        surface.set_clip(clip)

        if self._need_v():
            self._draw_scrollbar_v(surface)

    def _draw_scrollbar_v(self, surface):
        track = self._track_v_rect()
        if track.h <= 0:
            return
        pygame.draw.rect(surface, self._track_color, track)
        pygame.draw.line(surface, self._border_color,
                         (track.x, track.y), (track.x, track.y + track.h))
        thumb = self._thumb_v_rect()
        if thumb.h > 0:
            mx, my = pygame.mouse.get_pos()
            color = self._thumb_drag if self._dragging_v else (
                self._thumb_hover if thumb.collidepoint(mx, my) else self._thumb_color)
            pygame.draw.rect(surface, color, thumb, border_radius=3)
            pygame.draw.rect(surface, self._border_color, thumb, 1, border_radius=3)