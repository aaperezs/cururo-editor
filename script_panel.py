import pygame
from editor.translation import I18n
from editor.panels.base_panel import BasePanel
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.text_input import TextInput
from editor.widgets.script_editor import ScriptEditor
from editor.scripts import list_scripts, get_script, save_script, delete_script, create_script

PADDING = 6
TOOLBAR_H = 36
LEFT_W = 200
LIST_H = 24
SCROLLBAR_W = 10


class ScriptPanel(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(x, y, w, h, i18n)
        self.bg_color = (30, 32, 36)
        self._current_name = None
        self._list_scroll = 0
        self._scroll_dragging = False
        self._build_ui()

    def _build_ui(self):
        self.clear()

        tb = Panel(0, 0, self.rect.w, TOOLBAR_H, bg_color=(42, 46, 55), border_color=(60, 65, 75))
        self.add(tb)

        self._new_btn = Button(8, 4, 60, 28, self.i18n.t("script.new"), callback=self._on_new)
        self._new_btn.parent = tb; tb.children.append(self._new_btn)

        self._name_input = TextInput(76, 4, 180, 28, default="", numeric_only=False,
                                     font_size=13, on_confirm=None)
        self._name_input.parent = tb; tb.children.append(self._name_input)
        self._name_input.numeric_only = False

        self._save_btn = Button(264, 4, 60, 28, self.i18n.t("script.save"), callback=self._on_save)
        self._save_btn.parent = tb; tb.children.append(self._save_btn)

        self._del_btn = Button(330, 4, 60, 28, self.i18n.t("script.delete"), callback=self._on_delete)
        self._del_btn.parent = tb; tb.children.append(self._del_btn)

        rx = LEFT_W
        rw = self.rect.w - rx
        cy = TOOLBAR_H
        ch = self.rect.h - cy
        self._editor = ScriptEditor(rx, cy, rw, ch)
        self._editor.parent = self
        self._editor._on_change = self._on_text_change
        self._editor._on_save = self._on_save
        self.children.append(self._editor)

    def _on_text_change(self):
        pass

    def _refresh_list(self):
        pass

    def _on_new(self):
        names = list_scripts()
        base = "script"
        n = 1
        while f"{base}_{n}" in names:
            n += 1
        new_name = f"{base}_{n}"
        create_script(new_name, "# " + new_name + "\n\n")
        self._current_name = new_name
        self._name_input.text = new_name + ".py"
        self._name_input._cursor_pos = len(self._name_input.text)
        self._editor.text = get_script(new_name)
        self._editor._invalidate_tokens()
        self._editor._undo_stack.clear()

    def _on_save(self):
        name = self._name_input.text.strip()
        if name.endswith(".py"):
            name = name[:-3]
        if not name:
            return
        save_script(name, self._editor.text)
        self._current_name = name
        self._name_input.text = name + ".py"
        self._name_input._cursor_pos = len(self._name_input.text)

    def _on_delete(self):
        name = self._name_input.text.strip()
        if name.endswith(".py"):
            name = name[:-3]
        if not name:
            return
        delete_script(name)
        self._current_name = None
        self._name_input.text = ""
        self._editor.text = ""
        self._editor._invalidate_tokens()
        self._editor._undo_stack.clear()

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        r = self.get_abs_rect()
        mx, my = pygame.mouse.get_pos()

        in_list = r.collidepoint(mx, my) and mx < r.x + LEFT_W and my > r.y + TOOLBAR_H

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1 and in_list:
            ly = r.y + TOOLBAR_H
            rel_y = my - ly
            idx = (rel_y // LIST_H) + self._list_scroll
            names = list_scripts()
            if 0 <= idx < len(names):
                self._load_script(names[idx])
            return True

        if event.type == pygame.MOUSEWHEEL and in_list:
            self._list_scroll -= event.y
            names = list_scripts()
            max_scroll = max(0, len(names) - self._list_items_visible())
            self._list_scroll = max(0, min(self._list_scroll, max_scroll))
            return True

        if self._editor.handle_event(event):
            return True

        for child in list(self.children):
            if child is not self._editor and child.visible and child.handle_event(event):
                return True

        return False

    def _list_items_visible(self):
        return max(1, (self.rect.h - TOOLBAR_H) // LIST_H)

    def _load_script(self, name):
        self._current_name = name
        self._name_input.text = name + ".py"
        self._name_input._cursor_pos = len(self._name_input.text)
        self._editor.text = get_script(name)
        self._editor._invalidate_tokens()
        self._editor._undo_stack.clear()

    def draw(self, surface):
        if not self.visible:
            return
        r = self.get_abs_rect()
        pygame.draw.rect(surface, self.bg_color, r)

        list_x = r.x
        list_y = r.y + TOOLBAR_H
        list_w = LEFT_W
        list_h = r.h - TOOLBAR_H

        pygame.draw.rect(surface, (38, 42, 48), (list_x, list_y, list_w, list_h))
        pygame.draw.line(surface, (55, 60, 68), (list_x + list_w, list_y),
                         (list_x + list_w, list_y + list_h))

        i = I18n.instancia()
        font = i.fuente(13) if i else pygame.font.SysFont("Arial", 13)

        header = font.render(self.i18n.t("script.list"), True, (180, 185, 195))
        surface.blit(header, (list_x + PADDING, list_y + 4))

        names = list_scripts()
        for vi in range(self._list_items_visible()):
            li = self._list_scroll + vi
            if li >= len(names):
                break
            y = list_y + 26 + vi * LIST_H
            if names[li] == self._current_name:
                pygame.draw.rect(surface, (55, 80, 120), (list_x, y, list_w, LIST_H))
            elif vi % 2 == 0:
                pygame.draw.rect(surface, (42, 46, 55), (list_x, y, list_w, LIST_H))
            txt = font.render(names[li], True, (200, 205, 215))
            surface.blit(txt, (list_x + PADDING + 4, y + 4))

        if len(names) > self._list_items_visible():
            sb_x = list_x + list_w - SCROLLBAR_W
            sb_h = list_h
            pygame.draw.rect(surface, (40, 43, 50), (sb_x, list_y, SCROLLBAR_W, sb_h))
            thumb_h = max(16, int(sb_h * self._list_items_visible() / len(names)))
            max_s = len(names) - self._list_items_visible()
            thumb_y = list_y + int((sb_h - thumb_h) * self._list_scroll / max_s) if max_s > 0 else list_y
            pygame.draw.rect(surface, (75, 80, 90), (sb_x + 1, thumb_y, SCROLLBAR_W - 2, thumb_h))

        # Draw children (toolbar + editor)
        for child in self.children:
            if child.visible:
                child.draw(surface)
