import pygame
from editor.widgets.base import Widget
from editor.translation import I18n


class TextInput(Widget):
    def __init__(self, x, y, w, h, default="", max_chars=5, numeric_only=True, font_size=16, on_confirm=None):
        super().__init__(x, y, w, h)
        self.text = str(default)
        self.max_chars = max_chars
        self.numeric_only = numeric_only
        self.font_size = font_size
        self.focused = False
        self.on_confirm = on_confirm
        self._on_change = None
        self._cursor_pos = len(self.text)
        self._sel_start = 0
        self._sel_end = 0
        self._cursor_timer = 0
        self._cursor_visible = True
        self._undo_stack = []
        self._undo_limit = 50
        self._bg_color = (45, 50, 58)
        self._focus_color = (60, 80, 120)
        self._border_color = (65, 70, 80)
        self._text_color = (220, 220, 220)
        self._sel_color = (80, 100, 140)

    def _push_undo(self):
        self._undo_stack.append(self.text)
        if len(self._undo_stack) > self._undo_limit:
            self._undo_stack.pop(0)

    def _undo(self):
        if self._undo_stack:
            self.text = self._undo_stack.pop()
            self._cursor_pos = len(self.text)
            self._sel_start = self._sel_end = 0
            if self._on_change:
                self._on_change()

    def _has_selection(self):
        return self._sel_start != self._sel_end

    def _sel_range(self):
        return min(self._sel_start, self._sel_end), max(self._sel_start, self._sel_end)

    def _selected_text(self):
        if not self._has_selection():
            return ""
        a, b = self._sel_range()
        return self.text[a:b]

    def _delete_selection(self):
        if not self._has_selection():
            return False
        a, b = self._sel_range()
        self._push_undo()
        self.text = self.text[:a] + self.text[b:]
        self._cursor_pos = a
        self._sel_start = self._sel_end = a
        if self._on_change:
            self._on_change()
        return True

    def _insert_at_cursor(self, chars):
        if self._has_selection():
            self._delete_selection()
        remaining = self.max_chars - len(self.text)
        if remaining <= 0:
            return
        insert = chars[:remaining]
        self._push_undo()
        self.text = self.text[:self._cursor_pos] + insert + self.text[self._cursor_pos:]
        self._cursor_pos += len(insert)
        self._sel_start = self._sel_end = self._cursor_pos
        if self._on_change:
            self._on_change()

    def _is_word_char(self, ch):
        return ch.isalnum() or ch == "_"

    def _prev_word_start(self, pos):
        if pos <= 0:
            return 0
        i = pos - 1
        while i >= 0 and not self._is_word_char(self.text[i]):
            i -= 1
        while i >= 0 and self._is_word_char(self.text[i]):
            i -= 1
        return i + 1

    def _next_word_end(self, pos):
        text = self.text
        n = len(text)
        if pos >= n:
            return n
        i = pos
        while i < n and self._is_word_char(text[i]):
            i += 1
        if i == pos:
            while i < n and not self._is_word_char(text[i]):
                i += 1
            while i < n and self._is_word_char(text[i]):
                i += 1
        return i

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        r = self._abs_rect()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            was_focused = self.focused
            self.focused = r.collidepoint(event.pos)
            if self.focused:
                self._cursor_timer = 0
                self._cursor_visible = True
                # Set cursor position based on click
                click_x = event.pos[0] - r.x - 8
                self._cursor_pos = self._char_index_at_x(click_x)
                if not was_focused:
                    self._sel_start = self._sel_end = self._cursor_pos
                elif pygame.key.get_mods() & pygame.KMOD_SHIFT:
                    self._sel_start = self._sel_start if self._has_selection() else self._cursor_pos
                    self._sel_end = self._cursor_pos
                else:
                    self._sel_start = self._sel_end = self._cursor_pos
            return self.focused

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3 and self.focused:
            r = self._abs_rect()
            if r.collidepoint(event.pos):
                self._sel_start = 0
                self._sel_end = len(self.text)
                return True

        if event.type == pygame.KEYDOWN and self.focused:
            mods = pygame.key.get_mods()
            ctrl = mods & pygame.KMOD_CTRL
            shift = mods & pygame.KMOD_SHIFT

            # Ctrl+Z undo
            if ctrl and event.key == pygame.K_z:
                self._undo()
                return True

            # Ctrl+A select all
            if ctrl and event.key == pygame.K_a:
                self._sel_start = 0
                self._sel_end = len(self.text)
                self._cursor_pos = len(self.text)
                return True

            # Ctrl+C copy
            if ctrl and event.key == pygame.K_c:
                s = self._selected_text()
                if s:
                    self._copy_to_clipboard(s)
                return True

            # Ctrl+X cut
            if ctrl and event.key == pygame.K_x:
                s = self._selected_text()
                if s:
                    self._copy_to_clipboard(s)
                    self._delete_selection()
                return True

            # Ctrl+V paste
            if ctrl and event.key == pygame.K_v:
                pasted = self._get_clipboard()
                pasted = self._filter_input(pasted)
                self._insert_at_cursor(pasted)
                return True

            # Ctrl+U clear
            if ctrl and event.key == pygame.K_u:
                self._push_undo()
                self.text = ""
                self._cursor_pos = 0
                self._sel_start = self._sel_end = 0
                if self._on_change:
                    self._on_change()
                return True

            # Tab: skip confirm
            if event.key == pygame.K_TAB:
                return True

            # Confirm
            if event.key in (pygame.K_RETURN, pygame.K_INSERT):
                if self.on_confirm:
                    self.on_confirm()
                return True

            # Ctrl+Left: previous word
            if ctrl and event.key == pygame.K_LEFT:
                self._cursor_pos = self._prev_word_start(self._cursor_pos)
                if not shift:
                    self._sel_start = self._sel_end = self._cursor_pos
                else:
                    self._sel_end = self._cursor_pos
                self._cursor_timer = 0
                self._cursor_visible = True
                return True

            # Ctrl+Right: next word end
            if ctrl and event.key == pygame.K_RIGHT:
                self._cursor_pos = self._next_word_end(self._cursor_pos)
                if not shift:
                    self._sel_start = self._sel_end = self._cursor_pos
                else:
                    self._sel_end = self._cursor_pos
                self._cursor_timer = 0
                self._cursor_visible = True
                return True

            # Left arrow
            if event.key == pygame.K_LEFT:
                if self._cursor_pos > 0:
                    self._cursor_pos -= 1
                if not shift:
                    self._sel_start = self._sel_end = self._cursor_pos
                else:
                    self._sel_end = self._cursor_pos
                self._cursor_timer = 0
                self._cursor_visible = True
                return True

            # Right arrow
            if event.key == pygame.K_RIGHT:
                if self._cursor_pos < len(self.text):
                    self._cursor_pos += 1
                if not shift:
                    self._sel_start = self._sel_end = self._cursor_pos
                else:
                    self._sel_end = self._cursor_pos
                self._cursor_timer = 0
                self._cursor_visible = True
                return True

            # Home
            if event.key == pygame.K_HOME:
                self._cursor_pos = 0
                if not shift:
                    self._sel_start = self._sel_end = 0
                else:
                    self._sel_end = 0
                self._cursor_timer = 0
                self._cursor_visible = True
                return True

            # End
            if event.key == pygame.K_END:
                self._cursor_pos = len(self.text)
                if not shift:
                    self._sel_start = self._sel_end = self._cursor_pos
                else:
                    self._sel_end = self._cursor_pos
                self._cursor_timer = 0
                self._cursor_visible = True
                return True

            # Delete
            if event.key == pygame.K_DELETE:
                if self._has_selection():
                    self._delete_selection()
                elif self._cursor_pos < len(self.text):
                    self._push_undo()
                    self.text = self.text[:self._cursor_pos] + self.text[self._cursor_pos + 1:]
                    if self._on_change:
                        self._on_change()
                self._cursor_timer = 0
                self._cursor_visible = True
                return True

            # Backspace
            if event.key == pygame.K_BACKSPACE:
                if self._has_selection():
                    self._delete_selection()
                elif self._cursor_pos > 0:
                    self._push_undo()
                    self.text = self.text[:self._cursor_pos - 1] + self.text[self._cursor_pos:]
                    self._cursor_pos -= 1
                    if self._on_change:
                        self._on_change()
                self._cursor_timer = 0
                self._cursor_visible = True
                return True

            # Character input
            if event.unicode:
                filtered = self._filter_input(event.unicode)
                if filtered:
                    self._insert_at_cursor(filtered)
                    self._cursor_timer = 0
                    self._cursor_visible = True
                return True

        return False

    def _filter_input(self, s):
        if self.numeric_only:
            return "".join(c for c in s if c.isdigit())
        return s

    def get_value(self):
        try:
            return int(self.text) if self.text else 0
        except ValueError:
            return 0

    def get_text(self):
        return self.text

    def set_value(self, v):
        self.text = str(v)
        self._cursor_pos = len(self.text)
        self._sel_start = self._sel_end = 0
        self._undo_stack.clear()

    def _char_index_at_x(self, local_x):
        i = I18n.instancia()
        font = i.fuente(self.font_size) if i else pygame.font.SysFont("Arial", self.font_size)
        if local_x <= 0 or not self.text:
            return 0
        for idx in range(1, len(self.text) + 1):
            w = font.size(self.text[:idx])[0]
            if local_x < w:
                return idx - 1 if local_x < w - font.size(self.text[:idx - 1])[0] // 2 else idx
        return len(self.text)

    def _copy_to_clipboard(self, s):
        try:
            import pyperclip
            pyperclip.copy(s)
        except ImportError:
            pass

    def _get_clipboard(self):
        try:
            import pyperclip
            return pyperclip.paste()
        except ImportError:
            return ""

    def draw(self, surface):
        if not self.visible:
            return
        r = self._abs_rect()

        border = self._focus_color if self.focused else self._border_color
        pygame.draw.rect(surface, self._bg_color, r)
        pygame.draw.rect(surface, border, r, 2)

        i = I18n.instancia()
        fuente = i.fuente(self.font_size) if i else pygame.font.SysFont("Arial", self.font_size)

        text_x = r.x + 8
        text_y = r.y + (r.h - fuente.get_height()) // 2

        # Draw selection background
        if self._has_selection():
            a, b = self._sel_range()
            pre = fuente.size(self.text[:a])[0]
            sel = fuente.size(self.text[a:b])[0]
            sel_rect = pygame.Rect(text_x + pre, r.y + 2, sel, r.h - 4)
            pygame.draw.rect(surface, self._sel_color, sel_rect)

        # Draw text
        txt = fuente.render(self.text, True, self._text_color)
        surface.blit(txt, (text_x, text_y))

        # Draw cursor
        if self.focused:
            self._cursor_timer += 1
            if self._cursor_timer >= 30:
                self._cursor_timer = 0
                self._cursor_visible = not self._cursor_visible
            if self._cursor_visible:
                cx = text_x + fuente.size(self.text[:self._cursor_pos])[0]
                pygame.draw.line(surface, self._text_color,
                                 (cx, r.y + 4), (cx, r.y + r.h - 4), 1)
