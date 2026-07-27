import pygame
from editor.widgets.base import Widget
from editor.translation import I18n
from editor.clipboard import clipboard_get, clipboard_set

SCROLL_W = 14


class TextArea(Widget):
    def __init__(self, x, y, w, h, text=""):
        super().__init__(x, y, w, h)
        self.text = str(text)
        self.focused = False
        self.cursor_row = 0
        self.cursor_col = 0
        self.sel_start = None
        self.sel_end = None
        self.scroll = 0
        self._cursor_timer = 0
        self._cursor_visible = True
        self._line_h = 16
        self._on_change = None

        self._undo_stack = []
        self._undo_limit = 50

        self._dragging = False
        self._drag_start = 0
        self._drag_start_scroll = 0

        self.bg_color = (45, 50, 58)
        self.focus_color = (60, 80, 120)
        self.border_color = (65, 70, 80)
        self.text_color = (220, 220, 220)
        self.sel_color = (55, 80, 120)
        self.scroll_track = (40, 43, 50)
        self.scroll_thumb = (75, 80, 90)

    def get_abs_rect(self):
        if self.parent:
            pr = self.parent.get_abs_rect()
            return pygame.Rect(pr.x + self.rect.x, pr.y + self.rect.y,
                               self.rect.w, self.rect.h)
        return self.rect.copy()

    def _abs_rect(self):
        return self.get_abs_rect()

    def set_pos(self, x, y):
        self.rect.x = x
        self.rect.y = y

    def set_size(self, w, h):
        self.rect.w = w
        self.rect.h = h

    def _lines(self):
        return self.text.split("\n") if self.text else [""]

    def _vis_lines(self):
        return max(1, (self.rect.h - 4) // self._line_h)

    def _text_rect(self):
        r = self.get_abs_rect()
        return pygame.Rect(r.x + 2, r.y + 2, r.w - SCROLL_W - 4, r.h - 4)

    def _clamp_scroll(self):
        lines = self._lines()
        max_s = max(0, len(lines) - self._vis_lines())
        self.scroll = max(0, min(self.scroll, max_s))
        self.cursor_row = max(0, min(self.cursor_row, len(lines) - 1))
        line = lines[self.cursor_row] if lines else ""
        self.cursor_col = max(0, min(self.cursor_col, len(line)))
        if self.sel_start is not None:
            total = self._total_chars()
            self.sel_start = max(0, min(self.sel_start, total))
            self.sel_end = max(0, min(self.sel_end, total))

    def _total_chars(self):
        return len(self.text)

    def _pos_to_offset(self, row, col):
        lines = self._lines()
        offset = 0
        for i in range(row):
            offset += len(lines[i]) + 1
        offset += col
        return offset

    def _offset_to_pos(self, offset):
        lines = self._lines()
        row = 0
        while row < len(lines):
            line_len = len(lines[row]) + 1
            if offset < line_len:
                return row, offset
            offset -= line_len
            row += 1
        return len(lines) - 1, len(lines[-1]) if lines else 0

    def _sel_range(self):
        if self.sel_start is None or self.sel_end is None:
            return None, None
        return min(self.sel_start, self.sel_end), max(self.sel_start, self.sel_end)

    def _has_selection(self):
        return self.sel_start is not None and self.sel_end is not None and self.sel_start != self.sel_end

    def _delete_selection(self):
        if not self._has_selection():
            return False
        a, b = self._sel_range()
        self._push_undo()
        self.text = self.text[:a] + self.text[b:]
        row, col = self._offset_to_pos(a)
        self.cursor_row = row
        self.cursor_col = col
        self.sel_start = self.sel_end = None
        self._on_change_text()
        return True

    def _push_undo(self):
        self._undo_stack.append(self.text)
        if len(self._undo_stack) > self._undo_limit:
            self._undo_stack.pop(0)

    def _on_change_text(self):
        if self._on_change:
            self._on_change()

    def _is_word_char(self, ch):
        return ch.isalnum() or ch == "_"

    def _prev_word_start(self, row, col):
        lines = self._lines()
        offset = self._pos_to_offset(row, col)
        if offset <= 0:
            return 0, 0
        text = self.text[:offset]
        i = len(text) - 1
        while i >= 0 and not self._is_word_char(text[i]):
            i -= 1
        while i >= 0 and self._is_word_char(text[i]):
            i -= 1
        result = i + 1
        return self._offset_to_pos(result)

    def _next_word_end(self, row, col):
        offset = self._pos_to_offset(row, col)
        text = self.text
        i = offset
        while i < len(text) and not self._is_word_char(text[i]):
            i += 1
        while i < len(text) and self._is_word_char(text[i]):
            i += 1
        return self._offset_to_pos(i)

    def _set_sel_end(self, row, col):
        self.cursor_row = row
        self.cursor_col = col
        self.sel_end = self._pos_to_offset(row, col)
        self._clamp_scroll()
        self._cursor_timer = 0
        self._cursor_visible = True

    def _select_all(self):
        lines = self._lines()
        if not lines:
            return
        self.sel_start = 0
        self.sel_end = self._total_chars()
        self.cursor_row = len(lines) - 1
        self.cursor_col = len(lines[-1])
        self._cursor_timer = 0
        self._cursor_visible = True

    def _get_selected_text(self):
        if not self._has_selection():
            return ""
        a, b = self._sel_range()
        return self.text[a:b]

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        r = self.get_abs_rect()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            self.focused = r.collidepoint(mx, my)
            if not self.focused:
                self.sel_start = self.sel_end = None
                return False
            scroll_zone = pygame.Rect(r.right - SCROLL_W, r.y, SCROLL_W, r.h)
            if scroll_zone.collidepoint(mx, my):
                self._handle_scroll_click(my, r)
                return True
            tr = self._text_rect()
            if tr.collidepoint(mx, my):
                rel_y = my - tr.y
                row = (rel_y // self._line_h) + self.scroll
                lines = self._lines()
                row = max(0, min(row, len(lines) - 1))
                col = len(lines[row]) if lines else 0
                self.cursor_row = row
                self.cursor_col = col
                offset = self._pos_to_offset(row, col)
                self.sel_start = offset
                self.sel_end = offset
            return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False

        if event.type == pygame.MOUSEMOTION and self._dragging:
            r = self.get_abs_rect()
            scroll_h = r.h
            lines = self._lines()
            if len(lines) > self._vis_lines():
                track_h = scroll_h - max(16, scroll_h * self._vis_lines() // len(lines))
                if track_h > 0:
                    dy = event.pos[1] - self._drag_start
                    max_scroll = len(lines) - self._vis_lines()
                    self.scroll = int(self._drag_start_scroll + dy / track_h * max_scroll)
                    self._clamp_scroll()
            return True

        if event.type == pygame.MOUSEWHEEL:
            if r.collidepoint(pygame.mouse.get_pos()):
                self.scroll -= event.y
                self._clamp_scroll()
                return True

        if event.type == pygame.KEYDOWN and self.focused:
            lines = self._lines()
            mods = pygame.key.get_mods()
            ctrl = mods & pygame.KMOD_CTRL
            shift = mods & pygame.KMOD_SHIFT

            # Ctrl+Z undo
            if ctrl and event.key == pygame.K_z and not shift:
                if self._undo_stack:
                    self.text = self._undo_stack.pop()
                    self._clamp_scroll()
                    self._on_change_text()
                return True
            # Ctrl+Y or Ctrl+Shift+Z redo (not implemented, but don't crash)
            if (ctrl and event.key == pygame.K_y) or (ctrl and shift and event.key == pygame.K_z):
                return True
            # Ctrl+A select all
            if ctrl and event.key == pygame.K_a:
                self._select_all()
                return True
            # Ctrl+C copy
            if ctrl and event.key == pygame.K_c:
                sel = self._get_selected_text()
                if sel:
                    clipboard_set(sel)
                return True
            # Ctrl+X cut
            if ctrl and event.key == pygame.K_x:
                sel = self._get_selected_text()
                if sel:
                    clipboard_set(sel)
                    self._delete_selection()
                return True
            # Ctrl+V paste
            if ctrl and event.key == pygame.K_v:
                pasted = clipboard_get()
                if pasted:
                    self._push_undo()
                    if self._has_selection():
                        self._delete_selection()
                    lines_list = list(self._lines())
                    row = lines_list[self.cursor_row]
                    before = row[:self.cursor_col]
                    after = row[self.cursor_col:]
                    pasted_lines = pasted.split("\n")
                    if len(pasted_lines) == 1:
                        lines_list[self.cursor_row] = before + pasted + after
                        self.cursor_col += len(pasted)
                    else:
                        lines_list[self.cursor_row] = before + pasted_lines[0]
                        for pl in pasted_lines[1:-1]:
                            lines_list.insert(self.cursor_row + 1, pl)
                            self.cursor_row += 1
                        lines_list.insert(self.cursor_row + 1, pasted_lines[-1] + after)
                        self.cursor_row += 1
                        self.cursor_col = len(pasted_lines[-1])
                    self.text = "\n".join(lines_list)
                    self.sel_start = self.sel_end = None
                    self._cursor_timer = 0
                    self._on_change_text()
                return True
            # Ctrl+U clear all
            if ctrl and event.key == pygame.K_u:
                self._push_undo()
                self.text = ""
                self.cursor_row = 0
                self.cursor_col = 0
                self.sel_start = self.sel_end = None
                self._cursor_timer = 0
                self._on_change_text()
                return True
            # Ctrl shortcut common block
            if ctrl:
                if event.key == pygame.K_LEFT:
                    row, col = self._prev_word_start(self.cursor_row, self.cursor_col)
                    if not shift:
                        self.sel_start = self.sel_end = self._pos_to_offset(row, col)
                    self._set_sel_end(row, col)
                    return True
                if event.key == pygame.K_RIGHT:
                    row, col = self._next_word_end(self.cursor_row, self.cursor_col)
                    if not shift:
                        self.sel_start = self.sel_end = self._pos_to_offset(row, col)
                    self._set_sel_end(row, col)
                    return True
                if event.key == pygame.K_BACKSPACE:
                    if self._has_selection():
                        self._delete_selection()
                    else:
                        offset = self._pos_to_offset(self.cursor_row, self.cursor_col)
                        if offset > 0:
                            self._push_undo()
                            # Delete previous word: find start of word
                            text = self.text[:offset]
                            i = len(text) - 1
                            while i >= 0 and not self._is_word_char(text[i]):
                                i -= 1
                            while i >= 0 and self._is_word_char(text[i]):
                                i -= 1
                            start = i + 1
                            self.text = self.text[:start] + self.text[offset:]
                            self.cursor_row, self.cursor_col = self._offset_to_pos(start)
                            self.sel_start = self.sel_end = None
                            self._on_change_text()
                    return True

            if shift and event.key == pygame.K_LEFT:
                if self.sel_start is None:
                    self.sel_start = self._pos_to_offset(self.cursor_row, self.cursor_col)
                if self.cursor_col > 0:
                    self.cursor_col -= 1
                elif self.cursor_row > 0:
                    self.cursor_row -= 1
                    self.cursor_col = len(lines[self.cursor_row])
                self.sel_end = self._pos_to_offset(self.cursor_row, self.cursor_col)
                self._cursor_timer = 0
                return True
            if shift and event.key == pygame.K_RIGHT:
                if self.sel_start is None:
                    self.sel_start = self._pos_to_offset(self.cursor_row, self.cursor_col)
                if self.cursor_col < len(lines[self.cursor_row]):
                    self.cursor_col += 1
                elif self.cursor_row < len(lines) - 1:
                    self.cursor_row += 1
                    self.cursor_col = 0
                self.sel_end = self._pos_to_offset(self.cursor_row, self.cursor_col)
                self._cursor_timer = 0
                return True
            if shift and event.key == pygame.K_UP:
                if self.sel_start is None:
                    self.sel_start = self._pos_to_offset(self.cursor_row, self.cursor_col)
                self.cursor_row = max(0, self.cursor_row - 1)
                self.sel_end = self._pos_to_offset(self.cursor_row, self.cursor_col)
                return True
            if shift and event.key == pygame.K_DOWN:
                if self.sel_start is None:
                    self.sel_start = self._pos_to_offset(self.cursor_row, self.cursor_col)
                self.cursor_row = min(len(lines) - 1, self.cursor_row + 1)
                self.sel_end = self._pos_to_offset(self.cursor_row, self.cursor_col)
                return True
            if shift and event.key == pygame.K_HOME:
                if self.sel_start is None:
                    self.sel_start = self._pos_to_offset(self.cursor_row, self.cursor_col)
                self.cursor_col = 0
                self.sel_end = self._pos_to_offset(self.cursor_row, self.cursor_col)
                return True
            if shift and event.key == pygame.K_END:
                if self.sel_start is None:
                    self.sel_start = self._pos_to_offset(self.cursor_row, self.cursor_col)
                self.cursor_col = len(lines[self.cursor_row])
                self.sel_end = self._pos_to_offset(self.cursor_row, self.cursor_col)
                return True
            # Ctrl+Shift+Left/Right word selection
            if ctrl and shift and event.key == pygame.K_LEFT:
                if self.sel_start is None:
                    self.sel_start = self._pos_to_offset(self.cursor_row, self.cursor_col)
                row, col = self._prev_word_start(self.cursor_row, self.cursor_col)
                self._set_sel_end(row, col)
                return True
            if ctrl and shift and event.key == pygame.K_RIGHT:
                if self.sel_start is None:
                    self.sel_start = self._pos_to_offset(self.cursor_row, self.cursor_col)
                row, col = self._next_word_end(self.cursor_row, self.cursor_col)
                self._set_sel_end(row, col)
                return True

            # Home without shift
            if event.key == pygame.K_HOME and not shift:
                self.cursor_col = 0
                self.sel_start = self.sel_end = self._pos_to_offset(self.cursor_row, self.cursor_col)
                self._cursor_timer = 0
                return True
            # End without shift
            if event.key == pygame.K_END and not shift:
                self.cursor_col = len(lines[self.cursor_row])
                self.sel_start = self.sel_end = self._pos_to_offset(self.cursor_row, self.cursor_col)
                self._cursor_timer = 0
                return True

            # Delete (forward)
            if event.key == pygame.K_DELETE:
                if self._has_selection():
                    self._delete_selection()
                else:
                    offset = self._pos_to_offset(self.cursor_row, self.cursor_col)
                    if offset < len(self.text):
                        self._push_undo()
                        self.text = self.text[:offset] + self.text[offset + 1:]
                        self._on_change_text()
                self._cursor_timer = 0
                self._cursor_visible = True
                return True

            # Backspace
            if event.key == pygame.K_BACKSPACE:
                if self._has_selection():
                    self._delete_selection()
                elif self.cursor_col > 0 or self.cursor_row > 0:
                    self._push_undo()
                    lines_list = list(self._lines())
                    if self.cursor_col > 0:
                        row = lines_list[self.cursor_row]
                        lines_list[self.cursor_row] = row[:self.cursor_col - 1] + row[self.cursor_col:]
                        self.cursor_col -= 1
                    else:
                        prev = lines_list.pop(self.cursor_row - 1)
                        self.cursor_col = len(prev)
                        lines_list[self.cursor_row - 1] = prev + lines_list[self.cursor_row - 1]
                        self.cursor_row -= 1
                    self.text = "\n".join(lines_list)
                    self.sel_start = self.sel_end = None
                    self._cursor_timer = 0
                    self._on_change_text()
                return True

            # Enter
            if event.key == pygame.K_RETURN:
                self._push_undo()
                if self._has_selection():
                    self._delete_selection()
                lines_list = list(self._lines())
                row = lines_list[self.cursor_row]
                lines_list[self.cursor_row] = row[:self.cursor_col]
                lines_list.insert(self.cursor_row + 1, row[self.cursor_col:])
                self.text = "\n".join(lines_list)
                self.cursor_row += 1
                self.cursor_col = 0
                self.sel_start = self.sel_end = None
                self._cursor_timer = 0
                self._on_change_text()
                return True

            # Arrow keys (without shift — clears selection)
            if not shift and event.key == pygame.K_UP:
                self.cursor_row = max(0, self.cursor_row - 1)
                self.sel_start = self.sel_end = self._pos_to_offset(self.cursor_row, self.cursor_col)
                return True
            if not shift and event.key == pygame.K_DOWN:
                self.cursor_row = min(len(lines) - 1, self.cursor_row + 1)
                self.sel_start = self.sel_end = self._pos_to_offset(self.cursor_row, self.cursor_col)
                return True
            if not shift and event.key == pygame.K_LEFT:
                if self.cursor_col > 0:
                    self.cursor_col -= 1
                elif self.cursor_row > 0:
                    self.cursor_row -= 1
                    self.cursor_col = len(lines[self.cursor_row])
                self.sel_start = self.sel_end = self._pos_to_offset(self.cursor_row, self.cursor_col)
                return True
            if not shift and event.key == pygame.K_RIGHT:
                if self.cursor_col < len(lines[self.cursor_row]):
                    self.cursor_col += 1
                elif self.cursor_row < len(lines) - 1:
                    self.cursor_row += 1
                    self.cursor_col = 0
                self.sel_start = self.sel_end = self._pos_to_offset(self.cursor_row, self.cursor_col)
                return True

            # Tab
            if event.key == pygame.K_TAB:
                self._push_undo()
                if self._has_selection():
                    self._delete_selection()
                lines_list = list(self._lines())
                row = lines_list[self.cursor_row]
                lines_list[self.cursor_row] = row[:self.cursor_col] + "    " + row[self.cursor_col:]
                self.text = "\n".join(lines_list)
                self.cursor_col += 4
                self.sel_start = self.sel_end = None
                self._cursor_timer = 0
                self._on_change_text()
                return True

            # Printable chars
            if event.unicode and event.unicode.isprintable():
                self._push_undo()
                if self._has_selection():
                    self._delete_selection()
                lines_list = list(self._lines())
                row = lines_list[self.cursor_row]
                lines_list[self.cursor_row] = row[:self.cursor_col] + event.unicode + row[self.cursor_col:]
                self.text = "\n".join(lines_list)
                self.cursor_col += 1
                self.sel_start = self.sel_end = None
                self._cursor_timer = 0
                self._on_change_text()
                return True

        return False

    def _handle_scroll_click(self, my, r):
        scroll_h = r.h
        lines = self._lines()
        if len(lines) <= self._vis_lines():
            return
        thumb_h = max(16, scroll_h * self._vis_lines() // max(1, len(lines)))
        if my - r.y < 16:
            self.scroll = max(0, self.scroll - 1)
            return
        if r.y + r.h - my < 16:
            self.scroll = min(len(lines) - self._vis_lines(), self.scroll + 1)
            return
        self._dragging = True
        self._drag_start = my
        self._drag_start_scroll = self.scroll

    def _clamp_scroll(self):
        lines = self._lines()
        max_s = max(0, len(lines) - self._vis_lines())
        self.scroll = max(0, min(self.scroll, max_s))

    def draw(self, surface):
        if not self.visible:
            return
        r = self.get_abs_rect()
        i = I18n.instancia()
        fpeq = i.fuente(13) if i else pygame.font.SysFont("Arial", 13)

        border = self.focus_color if self.focused else self.border_color
        pygame.draw.rect(surface, self.bg_color, r)
        pygame.draw.rect(surface, border, r, 2)

        tr = self._text_rect()
        clip = surface.get_clip()
        surface.set_clip(tr)

        lines = self._lines()
        for vi in range(self._vis_lines()):
            li = self.scroll + vi
            if li >= len(lines):
                break
            y = tr.y + vi * self._line_h

            # Draw selection highlight
            if self._has_selection():
                a, b = self._sel_range()
                line_start = sum(len(lines[j]) + 1 for j in range(li))
                line_end = line_start + len(lines[li])
                sel_a = max(a, line_start)
                sel_b = min(b, line_end)
                if sel_a < sel_b:
                    before = lines[li][:sel_a - line_start]
                    selected = lines[li][sel_a - line_start:sel_b - line_start]
                    sx = tr.x + fpeq.size(before)[0]
                    sw = fpeq.size(selected)[0]
                    pygame.draw.rect(surface, self.sel_color, (sx, y, sw, self._line_h))

            txt = fpeq.render(lines[li], True, self.text_color)
            surface.blit(txt, (tr.x, y))

            if self.focused and li == self.cursor_row:
                self._cursor_timer += 1
                if self._cursor_timer >= 30:
                    self._cursor_timer = 0
                    self._cursor_visible = not self._cursor_visible
                if self._cursor_visible:
                    cx = tr.x + fpeq.size(lines[li][:self.cursor_col])[0]
                    pygame.draw.line(surface, self.text_color, (cx, y), (cx, y + self._line_h))

        surface.set_clip(clip)

        # Scrollbar
        sb_x = r.x + r.w - SCROLL_W
        sb_h = r.h
        pygame.draw.rect(surface, self.scroll_track, (sb_x, r.y, SCROLL_W, sb_h))
        if len(lines) > self._vis_lines():
            thumb_h = max(16, int(sb_h * self._vis_lines() / len(lines)))
            max_s = len(lines) - self._vis_lines()
            thumb_y = r.y + int((sb_h - thumb_h) * self.scroll / max_s) if max_s > 0 else r.y
            pygame.draw.rect(surface, self.scroll_thumb, (sb_x + 2, thumb_y, SCROLL_W - 4, thumb_h))
            if self.scroll > 0:
                surface.blit(fpeq.render("▲", True, (160, 165, 175)), (sb_x + 2, r.y + 2))
            if self.scroll + self._vis_lines() < len(lines):
                surface.blit(fpeq.render("▼", True, (160, 165, 175)), (sb_x + 2, r.y + sb_h - 16))
