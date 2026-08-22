"""Dropdown widget for the editor UI."""

import pygame

from editor.widgets.base import Widget
from editor.ui.theme import Theme
from editor.ui.fonts import get_font_manager
from editor.ui.icons import get_icon_factory


class Dropdown(Widget):
    """Themed dropdown with filtering and keyboard navigation."""
    
    MAX_VISIBLE = 8
    
    def __init__(self, x, y, w, h, options, callback=None):
        super().__init__(x, y, w, h)
        self._all_options = list(options)  # [(value, label), ...]
        self._selected = self._all_options[0][0] if self._all_options else None
        self._open = False
        self._filter_text = ""
        self._filtered = list(self._all_options)
        self._scroll_offset = 0
        self._focus = False
        self._callback = callback
        self._chevron = get_icon_factory().get("chevron_down", 12)
    
    def set_options(self, options):
        self._all_options = list(options)
        self._apply_filter()
        if self._selected not in [v for v, _ in self._all_options]:
            self._selected = self._all_options[0][0] if self._all_options else None
    
    def set_selected(self, value):
        self._selected = value
    
    def get_selected(self):
        return self._selected
    
    def open(self, x=None, y=None):
        self._open = True
        self._filter_text = ""
        self._apply_filter()
        self._scroll_offset = 0
    
    def close(self):
        self._open = False
        self._filter_text = ""
        self._filtered = list(self._all_options)
        self._scroll_offset = 0
    
    @property
    def is_open(self):
        return self._open
    
    def _apply_filter(self):
        ft = self._filter_text.lower()
        if not ft:
            self._filtered = list(self._all_options)
        else:
            self._filtered = [(v, l) for v, l in self._all_options
                              if ft in v.lower() or ft in l.lower()]
        self._scroll_offset = 0
    
    def _get_selected_label(self):
        for v, l in self._all_options:
            if v == self._selected:
                return l
        return str(self._selected) if self._selected else ""
    
    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        
        r = self.get_abs_rect()
        
        if self._open:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.close()
                    return True
                elif event.key == pygame.K_RETURN:
                    if self._filtered:
                        self._selected = self._filtered[0][0]
                        self.close()
                        if self._callback:
                            self._callback(self._selected)
                    return True
                elif event.key == pygame.K_UP:
                    if self._filtered:
                        idx = self._get_selected_filtered_idx()
                        new_idx = max(0, idx - 1)
                        if new_idx < self._scroll_offset:
                            self._scroll_offset = new_idx
                        self._selected = self._filtered[new_idx][0]
                    return True
                elif event.key == pygame.K_DOWN:
                    if self._filtered:
                        idx = self._get_selected_filtered_idx()
                        new_idx = min(len(self._filtered) - 1, idx + 1)
                        if new_idx >= self._scroll_offset + self.MAX_VISIBLE:
                            self._scroll_offset = new_idx - self.MAX_VISIBLE + 1
                        self._selected = self._filtered[new_idx][0]
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self._filter_text = self._filter_text[:-1]
                    self._apply_filter()
                    return True
                elif event.unicode and event.unicode.isprintable():
                    self._filter_text += event.unicode
                    self._apply_filter()
                    return True
            
            if event.type == pygame.MOUSEWHEEL:
                max_scroll = max(0, len(self._filtered) - self.MAX_VISIBLE)
                self._scroll_offset = max(0, min(max_scroll, self._scroll_offset - event.y))
                return True
        
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            r = self.rect
            if r.collidepoint(mx, my):
                if not self._open:
                    self._open = True
                    self._filter_text = ""
                    self._filtered = list(self._all_options)
                    self._scroll_offset = 0
                return True
            if self._open:
                ih = 24
                vis = min(len(self._filtered), self.MAX_VISIBLE)
                total_h = vis * ih + 2
                scr_h = pygame.display.get_surface().get_height() if pygame.display.get_surface() else 600
                space_below = scr_h - (r.y + r.h)
                open_up = total_h > space_below and r.y > total_h
                dy = r.y - total_h if open_up else r.y + r.h
                dd_rect = pygame.Rect(r.x, dy, r.w, total_h)
                if dd_rect.y < 0:
                    dd_rect.y = 0
                if scr_h and dd_rect.y + dd_rect.h > scr_h:
                    dd_rect.y = scr_h - dd_rect.h
                has_scroll = len(self._filtered) > self.MAX_VISIBLE
                sb_w = 10 if has_scroll else 0
                if has_scroll:
                    sb_rect = pygame.Rect(r.x + r.w - sb_w, dy, sb_w, total_h)
                    if sb_rect.collidepoint(mx, my):
                        total = len(self._filtered)
                        max_scroll = total - vis
                        if max_scroll > 0:
                            thumb_h = max(12, int(sb_rect.h * vis / total))
                            thumb_y = sb_rect.y + int((self._scroll_offset / max_scroll) * (sb_rect.h - thumb_h))
                            thumb = pygame.Rect(sb_rect.x, thumb_y, sb_rect.w, thumb_h)
                            if thumb.collidepoint(mx, my):
                                return True
                            elif my < thumb_y:
                                self._scroll_offset = max(0, self._scroll_offset - vis)
                                return True
                            else:
                                self._scroll_offset = min(max_scroll, self._scroll_offset + vis)
                                return True
                item_rect = pygame.Rect(r.x, dy, r.w - sb_w, vis * ih)
                if item_rect.collidepoint(mx, my):
                    click_idx = (my - dy) // ih
                    idx = self._scroll_offset + click_idx
                    if 0 <= idx < len(self._filtered):
                        self._selected = self._filtered[idx][0]
                        self.close()
                        if self._callback:
                            self._callback(self._selected)
                        return True
                self.close()
                return True
        
        if event.type == pygame.MOUSEBUTTONDOWN and self._open:
            self.close()
            return True
        
        return False
    
    def _get_selected_filtered_idx(self):
        for i, (v, l) in enumerate(self._filtered):
            if v == self._selected:
                return i
        return 0
    
    def draw(self, surface):
        if not self.visible:
            return
        
        theme = Theme.get()
        r = self.get_abs_rect()
        font = get_font_manager().get(theme.font_sizes["body"])
        
        def _c(c):
            return c.as_tuple() if hasattr(c, 'as_tuple') else c
        
        # Main button
        label = self._get_selected_label()
        bg = _c(theme.surface if not self._focus else theme.bg_hover)
        pygame.draw.rect(surface, bg, r, border_radius=theme.radius)
        pygame.draw.rect(surface, _c(theme.border_focus if self._focus else theme.border), r, 1, border_radius=theme.radius)
        
        txt = font.render(label, True, _c(theme.text))
        surface.blit(txt, (r.x + 8, r.y + (r.h - txt.get_height()) // 2))
        
        # Chevron
        if self._chevron:
            cx = r.x + r.w - 24
            cy = r.y + (r.h - self._chevron.get_height()) // 2
            surface.blit(self._chevron, (cx, cy))
        
        if self._open:
            ih = 24
            vis = min(len(self._filtered), self.MAX_VISIBLE)
            total_h = vis * ih + 2
            scr_h = pygame.display.get_surface().get_height() if pygame.display.get_surface() else 600
            space_below = scr_h - (r.y + r.h)
            open_up = total_h > space_below and r.y > total_h
            dy = r.y - total_h if open_up else r.y + r.h
            dd_rect = pygame.Rect(r.x, dy, r.w, total_h)
            if dd_rect.y < 0:
                dd_rect.y = 0
            if scr_h and dd_rect.y + dd_rect.h > scr_h:
                dd_rect.y = scr_h - dd_rect.h
            has_scroll = len(self._filtered) > self.MAX_VISIBLE
            sb_w = 10 if has_scroll else 0
            item_w = r.w - sb_w
            
            pygame.draw.rect(surface, _c(theme.surface_elevated), dd_rect, border_radius=theme.radius)
            pygame.draw.rect(surface, _c(theme.border), dd_rect, 1, border_radius=theme.radius)
            
            clip = surface.get_clip()
            surface.set_clip(dd_rect)
            
            for i in range(vis):
                idx = self._scroll_offset + i
                if idx >= len(self._filtered):
                    break
                v, l = self._filtered[idx]
                ir = pygame.Rect(r.x, dy + i * ih, item_w, ih)
                sel = v == self._selected
                bg = _c(theme.accent if sel else (theme.bg_hover if ir.collidepoint(pygame.mouse.get_pos()) else theme.surface_elevated))
                pygame.draw.rect(surface, bg, ir)
                if i < vis - 1:
                    pygame.draw.line(surface, _c(theme.border), (ir.x, ir.y + ih), (ir.x + ir.w, ir.y + ih))
                txt = font.render(l, True, _c(theme.text))
                surface.blit(txt, (ir.x + 8, ir.y + (ih - txt.get_height()) // 2))
            
            if has_scroll:
                sb_x = r.x + r.w - sb_w
                track = pygame.Rect(sb_x, dy, sb_w, total_h)
                pygame.draw.rect(surface, _c(theme.bg_disabled), track, border_radius=2)
                total = len(self._filtered)
                thumb_h = max(12, int(track.h * vis / total))
                max_scroll = total - vis
                thumb_y = track.y + int((self._scroll_offset / max_scroll) * (track.h - thumb_h)) if max_scroll > 0 else track.y
                thumb = pygame.Rect(sb_x + 1, thumb_y, sb_w - 2, thumb_h)
                pygame.draw.rect(surface, _c(theme.accent), thumb, border_radius=2)
            
            if self._filter_text:
                hint_font = get_font_manager().get(theme.font_sizes["caption"])
                hint = hint_font.render(f'"{self._filter_text}" ({len(self._filtered)})', True, _c(theme.text_dim))
                surface.blit(hint, (dd_rect.x + 4, dd_rect.y + dd_rect.h - 16))