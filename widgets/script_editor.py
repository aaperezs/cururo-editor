import pygame
from editor.widgets.base import Widget
from editor.translation import I18n
from editor.clipboard import clipboard_get, clipboard_set

KEYWORD_COLOR = (200, 120, 255)
BUILTIN_COLOR = (80, 180, 255)
STRING_COLOR = (150, 200, 80)
COMMENT_COLOR = (100, 130, 120)
NUMBER_COLOR = (255, 180, 80)
DECORATOR_COLOR = (255, 215, 0)
NORMAL_COLOR = (220, 220, 220)
GUTTER_COLOR = (120, 130, 140)
GUTTER_BG = (38, 42, 48)
CURRENT_LINE_COLOR = (40, 44, 52)
BG_COLOR = (30, 32, 36)
LINE_NUM_COLOR = (80, 90, 100)
SEL_COLOR = (55, 80, 120)
SCROLL_TRACK = (40, 43, 50)
SCROLL_THUMB = (75, 80, 90)

KEYWORDS = {
    "False", "None", "True", "and", "as", "assert", "async", "await",
    "break", "class", "continue", "def", "del", "elif", "else", "except",
    "finally", "for", "from", "global", "if", "import", "in", "is",
    "lambda", "nonlocal", "not", "or", "pass", "raise", "return",
    "try", "while", "with", "yield",
}

BUILTINS = {
    "print", "len", "range", "type", "int", "float", "str", "list",
    "dict", "set", "tuple", "bool", "object", "super", "self", "cls",
    "isinstance", "hasattr", "getattr", "setattr", "delattr", "open",
    "abs", "all", "any", "bin", "chr", "dir", "divmod", "enumerate",
    "eval", "exec", "filter", "format", "frozenset", "hash", "hex",
    "id", "input", "iter", "map", "max", "min", "next", "oct", "ord",
    "pow", "property", "repr", "reversed", "round", "slice",
    "sorted", "staticmethod", "sum", "vars", "zip",
    "Exception", "ValueError", "TypeError", "KeyError", "IndexError",
    "StopIteration", "RuntimeError", "FileNotFoundError", "IOError",
    "AttributeError", "ImportError", "NameError", "SyntaxError",
    "SystemExit", "KeyboardInterrupt", "MemoryError", "ZeroDivisionError",
    "enumerate", "staticmethod", "classmethod", "property",
}

GUTTER_W = 44
SCROLL_W = 14
LINE_H = 18
FONT_SIZE = 14


class ScriptEditor(Widget):
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
        self._on_change = None
        self._on_save = None

        self._undo_stack = []
        self._undo_limit = 200
        self._dirty_lines = set()

        self._dragging = False
        self._drag_start = 0
        self._drag_start_scroll = 0

        self._in_multiline_string = False
        self._multiline_quote = None
        self._token_cache = None
        self._token_lines = None

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
        self._clamp_scroll()

    def _lines(self):
        return self.text.split("\n") if self.text else [""]

    def _vis_lines(self):
        return max(1, (self.rect.h - 4) // LINE_H)

    def _text_rect(self):
        r = self.get_abs_rect()
        return pygame.Rect(r.x + GUTTER_W + 2, r.y + 2,
                           r.w - GUTTER_W - SCROLL_W - 4, r.h - 4)

    def _clamp_scroll(self):
        lines = self._lines()
        max_s = max(0, len(lines) - self._vis_lines())
        self.scroll = max(0, min(self.scroll, max_s))

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
        last = len(lines) - 1 if lines else 0
        return last, len(lines[last]) if lines else 0

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
        self._invalidate_tokens()
        self._on_change_text()
        return True

    def _push_undo(self):
        self._undo_stack.append(self.text)
        if len(self._undo_stack) > self._undo_limit:
            self._undo_stack.pop(0)

    def _on_change_text(self):
        if self._on_change:
            self._on_change()

    def _invalidate_tokens(self):
        self._token_cache = None
        self._token_lines = None

    def _get_tokens(self):
        if self._token_lines is not None:
            return self._token_lines
        self._token_lines = []
        in_multiline = False
        multiline_quote = None
        for line in self.text.split("\n") if self.text else [""]:
            tokens, in_multiline, multiline_quote = self._tokenize_line(line, in_multiline, multiline_quote)
            self._token_lines.append(tokens)
        return self._token_lines

    def _tokenize_line(self, line, in_multiline, multiline_quote):
        tokens = []
        i = 0
        n = len(line)

        if in_multiline:
            end = line.find(multiline_quote)
            if end != -1:
                tokens.append(("string", line[:end + 3]))
                i = end + 3
                in_multiline = False
                multiline_quote = None
            else:
                tokens.append(("string", line))
                return tokens, True, multiline_quote

        while i < n:
            ch = line[i]

            if ch == "#":
                tokens.append(("comment", line[i:]))
                break

            if ch in ("'", '"'):
                for qlen in (3, 1):
                    if i + qlen <= n and line[i:i + qlen] == ch * qlen:
                        if qlen == 3:
                            rest = line[i + 3:]
                            end = rest.find(ch * 3)
                            if end != -1:
                                tokens.append(("string", line[i:i + end + 6]))
                                i += end + 6
                            else:
                                tokens.append(("string", line[i:]))
                                return tokens, True, ch * 3
                        else:
                            end = line.find(ch, i + 1)
                            if end != -1:
                                tokens.append(("string", line[i:end + 1]))
                                i = end + 1
                            else:
                                tokens.append(("string", line[i:]))
                                return tokens, False, None
                        break
                continue

            if ch == "@":
                j = i + 1
                while j < n and (line[j].isalnum() or line[j] == "_"):
                    j += 1
                tokens.append(("decorator", line[i:j]))
                i = j
                continue

            if ch.isalpha() or ch == "_":
                j = i
                while j < n and (line[j].isalnum() or line[j] == "_"):
                    j += 1
                word = line[i:j]
                if word in KEYWORDS:
                    tokens.append(("keyword", word))
                elif word in BUILTINS:
                    tokens.append(("builtin", word))
                else:
                    tokens.append(("normal", word))
                i = j
                continue

            if ch.isdigit() or (ch == "." and i + 1 < n and line[i + 1].isdigit()):
                j = i
                while j < n and (line[j].isdigit() or line[j] in ".eExXoObB"):
                    j += 1
                tokens.append(("number", line[i:j]))
                i = j
                continue

            tokens.append(("normal", ch))
            i += 1

        return tokens, in_multiline, multiline_quote

    def _token_type_color(self, ttype):
        return {
            "keyword": KEYWORD_COLOR,
            "builtin": BUILTIN_COLOR,
            "string": STRING_COLOR,
            "comment": COMMENT_COLOR,
            "number": NUMBER_COLOR,
            "decorator": DECORATOR_COLOR,
            "normal": NORMAL_COLOR,
        }.get(ttype, NORMAL_COLOR)

    def _is_word_char(self, ch):
        return ch.isalnum() or ch == "_"

    def _prev_word_start(self, row, col):
        offset = self._pos_to_offset(row, col)
        if offset <= 0:
            return 0, 0
        text = self.text[:offset]
        i = len(text) - 1
        while i >= 0 and not self._is_word_char(text[i]):
            i -= 1
        while i >= 0 and self._is_word_char(text[i]):
            i -= 1
        return self._offset_to_pos(i + 1)

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

    def _get_selected_text(self):
        if not self._has_selection():
            return ""
        a, b = self._sel_range()
        return self.text[a:b]

    def _insert_text_at_cursor(self, insert_text):
        if self._has_selection():
            self._delete_selection()
        self._push_undo()
        lines_list = list(self._lines())
        row = lines_list[self.cursor_row]
        before = row[:self.cursor_col]
        after = row[self.cursor_col:]
        pasted_lines = insert_text.split("\n")
        if len(pasted_lines) == 1:
            lines_list[self.cursor_row] = before + insert_text + after
            self.cursor_col += len(insert_text)
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
        self._invalidate_tokens()
        self._on_change_text()

    def _get_indent(self, line):
        spaces = 0
        for ch in line:
            if ch == " ":
                spaces += 1
            elif ch == "\t":
                spaces += 4
            else:
                break
        return " " * spaces

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
                row = (rel_y // LINE_H) + self.scroll
                lines = self._lines()
                row = max(0, min(row, len(lines) - 1))
                rel_x = mx - tr.x
                col = self._col_at_x(row, rel_x)
                mods = pygame.key.get_mods()
                if mods & pygame.KMOD_SHIFT and self.sel_start is not None:
                    self.cursor_row = row
                    self.cursor_col = col
                    self.sel_end = self._pos_to_offset(row, col)
                else:
                    self.cursor_row = row
                    self.cursor_col = col
                    self.sel_start = self.sel_end = self._pos_to_offset(row, col)
            return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._dragging = False

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

            if ctrl and event.key == pygame.K_z and not shift:
                self._undo()
                return True
            if (ctrl and event.key == pygame.K_y) or (ctrl and shift and event.key == pygame.K_z):
                return True
            if ctrl and event.key == pygame.K_s:
                if self._on_save:
                    self._on_save()
                return True
            if ctrl and event.key == pygame.K_a:
                self._select_all()
                return True
            if ctrl and event.key == pygame.K_c:
                sel = self._get_selected_text()
                if sel:
                    clipboard_set(sel)
                return True
            if ctrl and event.key == pygame.K_x:
                sel = self._get_selected_text()
                if sel:
                    clipboard_set(sel)
                    self._delete_selection()
                return True
            if ctrl and event.key == pygame.K_v:
                pasted = clipboard_get()
                if pasted:
                    self._insert_text_at_cursor(pasted)
                return True
            if ctrl and event.key == pygame.K_u:
                self._push_undo()
                self.text = ""
                self.cursor_row = 0
                self.cursor_col = 0
                self.sel_start = self.sel_end = None
                self._invalidate_tokens()
                self._on_change_text()
                return True

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
                    self._delete_word_back()
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

            if event.key == pygame.K_HOME and not shift:
                self.cursor_col = 0
                self.sel_start = self.sel_end = self._pos_to_offset(self.cursor_row, self.cursor_col)
                self._cursor_timer = 0
                return True
            if event.key == pygame.K_END and not shift:
                self.cursor_col = len(lines[self.cursor_row])
                self.sel_start = self.sel_end = self._pos_to_offset(self.cursor_row, self.cursor_col)
                self._cursor_timer = 0
                return True

            if event.key == pygame.K_DELETE:
                if self._has_selection():
                    self._delete_selection()
                else:
                    offset = self._pos_to_offset(self.cursor_row, self.cursor_col)
                    if offset < len(self.text):
                        self._push_undo()
                        self.text = self.text[:offset] + self.text[offset + 1:]
                        self._invalidate_tokens()
                        self._on_change_text()
                self._cursor_timer = 0
                self._cursor_visible = True
                return True

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
                    self._invalidate_tokens()
                    self._on_change_text()
                return True

            if event.key == pygame.K_RETURN:
                self._push_undo()
                if self._has_selection():
                    self._delete_selection()
                lines_list = list(self._lines())
                row_text = lines_list[self.cursor_row]
                indent = self._get_indent(row_text)
                stripped = row_text.strip()
                if stripped.endswith(":") and not stripped.startswith("#"):
                    extra_indent = "    "
                else:
                    extra_indent = ""
                lines_list[self.cursor_row] = row_text[:self.cursor_col]
                lines_list.insert(self.cursor_row + 1, indent + extra_indent + row_text[self.cursor_col:])
                self.text = "\n".join(lines_list)
                self.cursor_row += 1
                self.cursor_col = len(indent) + len(extra_indent)
                self.sel_start = self.sel_end = None
                self._cursor_timer = 0
                self._invalidate_tokens()
                self._on_change_text()
                return True

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

            if event.key == pygame.K_TAB:
                self._insert_text_at_cursor("    ")
                return True

            if event.unicode and event.unicode.isprintable():
                char = event.unicode
                self._push_undo()
                if self._has_selection():
                    self._delete_selection()
                lines_list = list(self._lines())
                row = lines_list[self.cursor_row]
                lines_list[self.cursor_row] = row[:self.cursor_col] + char + row[self.cursor_col:]
                self.text = "\n".join(lines_list)
                self.cursor_col += 1
                self.sel_start = self.sel_end = None
                self._cursor_timer = 0
                self._invalidate_tokens()
                self._on_change_text()
                return True

        return False

    def _delete_word_back(self):
        offset = self._pos_to_offset(self.cursor_row, self.cursor_col)
        if offset <= 0:
            return
        if self._has_selection():
            self._delete_selection()
            return
        text = self.text[:offset]
        i = len(text) - 1
        while i >= 0 and not self._is_word_char(text[i]):
            i -= 1
        while i >= 0 and self._is_word_char(text[i]):
            i -= 1
        start = i + 1
        self._push_undo()
        self.text = self.text[:start] + self.text[offset:]
        self.cursor_row, self.cursor_col = self._offset_to_pos(start)
        self.sel_start = self.sel_end = None
        self._invalidate_tokens()
        self._on_change_text()

    def _undo(self):
        if self._undo_stack:
            self.text = self._undo_stack.pop()
            self._invalidate_tokens()
            self._clamp_scroll()
            self._on_change_text()

    def _col_at_x(self, row, local_x):
        i = I18n.instancia()
        font = i.fuente(FONT_SIZE) if i else pygame.font.SysFont("Arial", FONT_SIZE)
        lines = self._lines()
        if row >= len(lines):
            return 0
        line = lines[row]
        if local_x <= 0:
            return 0
        for idx in range(1, len(line) + 1):
            w = font.size(line[:idx])[0]
            if local_x < w:
                before_w = font.size(line[:idx - 1])[0] if idx > 0 else 0
                if local_x < w - (w - before_w) // 2:
                    return idx - 1
                return idx
        return len(line)

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

    def draw(self, surface):
        if not self.visible:
            return
        r = self.get_abs_rect()
        i = I18n.instancia()
        font = i.fuente(FONT_SIZE) if i else pygame.font.SysFont("Consolas", FONT_SIZE)
        font_num = i.fuente(FONT_SIZE - 1) if i else pygame.font.SysFont("Consolas", FONT_SIZE - 1)

        pygame.draw.rect(surface, BG_COLOR, r)

        gutter_rect = pygame.Rect(r.x, r.y, GUTTER_W, r.h)
        pygame.draw.rect(surface, GUTTER_BG, gutter_rect)
        pygame.draw.line(surface, (55, 60, 68), (r.x + GUTTER_W, r.y), (r.x + GUTTER_W, r.y + r.h))

        tr = self._text_rect()
        clip = surface.get_clip()
        surface.set_clip(tr)

        lines = self._lines()
        tokens = self._get_tokens()
        vis_lines = self._vis_lines()

        for vi in range(vis_lines):
            li = self.scroll + vi
            if li >= len(lines):
                break
            y = tr.y + vi * LINE_H

            if self.focused and li == self.cursor_row:
                pygame.draw.rect(surface, CURRENT_LINE_COLOR,
                                 (tr.x, y, tr.w, LINE_H))

            if self._has_selection():
                a, b = self._sel_range()
                line_start = sum(len(lines[j]) + 1 for j in range(li))
                line_end = line_start + len(lines[li])
                sel_a = max(a, line_start)
                sel_b = min(b, line_end)
                if sel_a < sel_b:
                    before_text = lines[li][:sel_a - line_start]
                    sel_text = lines[li][sel_a - line_start:sel_b - line_start]
                    sx = tr.x + font.size(before_text)[0]
                    sw = font.size(sel_text)[0]
                    pygame.draw.rect(surface, SEL_COLOR, (sx, y, sw, LINE_H))

            line_tokens = tokens[li] if li < len(tokens) else []
            tx = tr.x
            for ttype, ttext in line_tokens:
                color = self._token_type_color(ttype)
                rendered = font.render(ttext, True, color)
                surface.blit(rendered, (tx, y))
                tx += rendered.get_width()

            if self.focused and li == self.cursor_row:
                self._cursor_timer += 1
                if self._cursor_timer >= 30:
                    self._cursor_timer = 0
                    self._cursor_visible = not self._cursor_visible
                if self._cursor_visible:
                    cursor_x = tr.x + font.size(lines[li][:self.cursor_col])[0]
                    pygame.draw.line(surface, NORMAL_COLOR, (cursor_x, y),
                                     (cursor_x, y + LINE_H))

        surface.set_clip(clip)

        for vi in range(vis_lines):
            li = self.scroll + vi
            if li >= len(lines):
                break
            gy = r.y + 2 + vi * LINE_H
            num_text = str(li + 1)
            num_rendered = font_num.render(num_text, True, LINE_NUM_COLOR)
            surface.blit(num_rendered, (r.x + GUTTER_W - 8 - num_rendered.get_width(), gy))

        if len(lines) > vis_lines:
            sb_x = r.x + r.w - SCROLL_W
            sb_h = r.h
            pygame.draw.rect(surface, SCROLL_TRACK, (sb_x, r.y, SCROLL_W, sb_h))
            thumb_h = max(16, int(sb_h * vis_lines / len(lines)))
            max_s = len(lines) - vis_lines
            thumb_y = r.y + int((sb_h - thumb_h) * self.scroll / max_s) if max_s > 0 else r.y
            pygame.draw.rect(surface, SCROLL_THUMB, (sb_x + 2, thumb_y, SCROLL_W - 4, thumb_h))

            if self.scroll > 0:
                arrow = font.render("▲", True, (160, 165, 175))
                surface.blit(arrow, (sb_x + 2, r.y + 1))
            if self.scroll + vis_lines < len(lines):
                arrow = font.render("▼", True, (160, 165, 175))
                surface.blit(arrow, (sb_x + 2, r.y + sb_h - font.get_height() - 1))
