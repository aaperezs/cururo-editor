"""Reusable dropdown widget with filter, keyboard navigation, and scroll.

Extracted from element_tab.py (_SimpleDropdown) and shared across
element_tab, boss_tab, item_tab, ability_tab, custom_behaviors.
"""

from __future__ import annotations

import pygame

from editor.translation import I18n


class SimpleDropdown:
    """Filterable dropdown selector with keyboard/mouse support."""

    MAX_VISIBLE = 8

    def __init__(
        self,
        x: int,
        y: int,
        w: int,
        h: int,
        options: list[tuple[str, str]],
        selected: str | None = None,
    ) -> None:
        self.rect = pygame.Rect(x, y, w, h)
        self.parent: object | None = None
        self.visible = True
        self.enabled = True
        self._all_options = list(options)
        self._selected = selected or (options[0][0] if options else None)
        self._open = False
        self._on_select: object | None = None
        self._filter_text = ""
        self._filtered = list(options)
        self._scroll_offset = 0
        self._focus = False

    def _abs_rect(self) -> pygame.Rect:
        if self.parent:
            pr = (
                self.parent.get_abs_rect()
                if hasattr(self.parent, "get_abs_rect")
                else self.parent.rect
            )
            return pygame.Rect(
                pr.x + self.rect.x, pr.y + self.rect.y, self.rect.w, self.rect.h
            )
        return self.rect.copy()

    def set_selected(self, value: str | None) -> None:
        self._selected = value

    def get_selected(self) -> str | None:
        return self._selected

    def _close_others(self) -> None:
        if not self.parent:
            return
        for child in list(self.parent.children):
            if isinstance(child, SimpleDropdown) and child is not self and child._open:
                child._open = False
                child._filter_text = ""
                child._filtered = list(child._all_options)
                child._scroll_offset = 0

    def _bring_to_front(self) -> None:
        p = self.parent.children
        if p and p[-1] is not self:
            p.remove(self)
            p.append(self)

    def handle_event(self, event: pygame.event.Event) -> bool:
        if not self.visible or not self.enabled:
            return False
        r = self._abs_rect()
        if self._open:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._open = False
                    self._filter_text = ""
                    self._filtered = list(self._all_options)
                    self._scroll_offset = 0
                    return True
                elif event.key == pygame.K_RETURN:
                    if self._filtered:
                        val = self._filtered[0][0]
                        self._selected = val
                        self._open = False
                        self._filter_text = ""
                        self._filtered = list(self._all_options)
                        self._scroll_offset = 0
                        if self._on_select:
                            self._on_select(val)
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
                self._scroll_offset = max(
                    0, min(max_scroll, self._scroll_offset - event.y)
                )
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if r.collidepoint(mx, my):
                if not self._open:
                    self._close_others()
                self._open = not self._open
                self._filter_text = ""
                self._filtered = list(self._all_options)
                self._scroll_offset = 0
                if self._open and self.parent:
                    self._bring_to_front()
                return True
            if self._open:
                ih = 20
                vis = min(len(self._filtered), self.MAX_VISIBLE)
                total_h = vis * ih + 2
                scr_h = (
                    pygame.display.get_surface().get_height()
                    if pygame.display.get_surface()
                    else 600
                )
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
                    sb_rect = pygame.Rect(r.x + r.w - sb_w, dd_rect.y, sb_w, dd_rect.h)
                    if sb_rect.collidepoint(mx, my):
                        total = len(self._filtered)
                        max_scroll = total - vis
                        if max_scroll > 0:
                            thumb_h = max(12, int(sb_rect.h * vis / total))
                            thumb_y = sb_rect.y + int(
                                (self._scroll_offset / max_scroll)
                                * (sb_rect.h - thumb_h)
                            )
                            thumb = pygame.Rect(sb_rect.x, thumb_y, sb_rect.w, thumb_h)
                            if thumb.collidepoint(mx, my):
                                ratio = (my - sb_rect.y) / sb_rect.h
                                self._scroll_offset = int(ratio * max_scroll)
                            elif my < thumb_y:
                                self._scroll_offset = max(
                                    0, self._scroll_offset - vis
                                )
                            else:
                                self._scroll_offset = min(
                                    max_scroll, self._scroll_offset + vis
                                )
                        return True
                item_rect = pygame.Rect(r.x, dd_rect.y, r.w - sb_w, vis * ih)
                if item_rect.collidepoint(mx, my):
                    click_idx = (my - dd_rect.y) // ih
                    idx = self._scroll_offset + click_idx
                    if 0 <= idx < len(self._filtered):
                        val, lbl = self._filtered[idx]
                        self._selected = val
                        self._open = False
                        self._filter_text = ""
                        self._filtered = list(self._all_options)
                        self._scroll_offset = 0
                        if self._on_select:
                            self._on_select(val)
                        return True
                self._open = False
                self._filter_text = ""
                self._filtered = list(self._all_options)
                self._scroll_offset = 0
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and self._open:
            self._open = False
            self._filter_text = ""
            self._filtered = list(self._all_options)
            self._scroll_offset = 0
            return True
        return False

    def _get_selected_filtered_idx(self) -> int:
        for i, (val, lbl) in enumerate(self._filtered):
            if val == self._selected:
                return i
        return 0

    def _apply_filter(self) -> None:
        ft = self._filter_text.lower()
        if not ft:
            self._filtered = list(self._all_options)
        else:
            self._filtered = [
                (v, l)
                for v, l in self._all_options
                if ft in v.lower() or ft in l.lower()
            ]
        self._scroll_offset = 0

    def draw(self, surface: pygame.Surface) -> None:
        if not self.visible:
            return
        r = self._abs_rect()
        i18n = I18n.instancia()
        fuente = i18n.fuente(12) if i18n else pygame.font.SysFont("Arial", 12)
        label = str(self._selected)
        for val, lbl in self._all_options:
            if val == self._selected:
                label = lbl
                break
        pygame.draw.rect(surface, (50, 55, 65), r)
        pygame.draw.rect(surface, (80, 90, 105), r, 1)
        txt = fuente.render(label, True, (220, 220, 220))
        surface.blit(txt, (r.x + 6, r.y + (r.h - txt.get_height()) // 2))
        pygame.draw.polygon(
            surface,
            (160, 170, 180),
            [
                (r.x + r.w - 12, r.y + r.h // 2 - 2),
                (r.x + r.w - 6, r.y + r.h // 2 - 2),
                (r.x + r.w - 9, r.y + r.h // 2 + 3),
            ],
        )
        if self._open:
            ih = 20
            vis = min(len(self._filtered), self.MAX_VISIBLE)
            total_h = vis * ih + 2
            space_below = surface.get_height() - (r.y + r.h)
            open_up = total_h > space_below and r.y > total_h
            dy = r.y - total_h if open_up else r.y + r.h
            dd_rect = pygame.Rect(r.x, dy, r.w, total_h)
            if dd_rect.y < 0:
                dd_rect.y = 0
            if dd_rect.y + dd_rect.h > surface.get_height():
                dd_rect.y = surface.get_height() - dd_rect.h
            has_scroll = len(self._filtered) > self.MAX_VISIBLE
            sb_w = 10 if has_scroll else 0
            item_w = r.w - sb_w
            pygame.draw.rect(surface, (45, 48, 56), dd_rect)
            pygame.draw.rect(surface, (70, 75, 85), dd_rect, 1)
            clip = surface.get_clip()
            surface.set_clip(dd_rect)
            for i in range(vis):
                idx = self._scroll_offset + i
                if idx >= len(self._filtered):
                    break
                val, lbl = self._filtered[idx]
                ir = pygame.Rect(r.x, dy + i * ih, item_w, ih)
                sel = val == self._selected
                bg = (60, 65, 78) if sel else (45, 48, 56)
                pygame.draw.rect(surface, bg, ir)
                if i < vis - 1:
                    pygame.draw.line(
                        surface,
                        (70, 75, 85),
                        (ir.x, ir.y + ih),
                        (ir.x + ir.w, ir.y + ih),
                    )
                txt = fuente.render(lbl, True, (200, 200, 200))
                surface.blit(txt, (ir.x + 6, ir.y + (ih - txt.get_height()) // 2))
            if has_scroll:
                sb_x = r.x + r.w - sb_w
                track = pygame.Rect(sb_x, dy, sb_w, total_h)
                pygame.draw.rect(surface, (35, 38, 44), track)
                total = len(self._filtered)
                thumb_h = max(12, int(total_h * vis / total))
                max_scroll = total - vis
                thumb_y = (
                    dy + int((self._scroll_offset / max_scroll) * (total_h - thumb_h))
                    if max_scroll > 0
                    else dy
                )
                thumb = pygame.Rect(sb_x + 1, thumb_y, sb_w - 2, thumb_h)
                pygame.draw.rect(surface, (100, 110, 125), thumb)
                pygame.draw.rect(surface, (130, 140, 155), thumb, 1)
            if self._filter_text:
                hint = fuente.render(
                    f'"{self._filter_text}" ({len(self._filtered)})',
                    True,
                    (120, 140, 160),
                )
                surface.blit(hint, (dd_rect.x + 4, dd_rect.y + dd_rect.h - 16))
            surface.set_clip(clip)
