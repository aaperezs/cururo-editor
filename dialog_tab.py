import pygame
import pygame_gui

from editor.translation import I18n
from editor.panels.base_panel import BasePanel
from editor.pygame_gui_theme import create_gui
from editor.dialog_data import (
    get_all_dialogo_keys, get_dialogo_by_key, set_dialogo_by_key,
    delete_dialogo_by_key, create_dialogo_by_key, rename_dialogo,
    _parse_key, _make_key
)

PADDING = 6
ROW_H = 28
TOOLBAR_H = 36
HEADER_H = 26
LINE_H = 24
LEFT_W = 220


class DialogTab(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(0, 0, w, h, i18n)
        self.bg_color = (30, 32, 36)
        self._gui = create_gui((w, h), offset_getter=lambda: (
            self.get_abs_rect().x, self.get_abs_rect().y
        ))
        self._selected_key = None
        self._dirty = False
        self._line_widgets = []
        self._build_ui()

    # ── UI ─────────────────────────────────────────────────

    def _build_ui(self):
        prev_key = self._selected_key
        self._gui.clear_and_reset()
        self._line_widgets.clear()
        w, h = self.rect.w, self.rect.h
        i = self.i18n

        # ── Toolbar ──
        self._new_btn = pygame_gui.elements.UIButton(
            pygame.Rect(8, 4, 72, 28), i.t("dialog.new"), self._gui
        )
        self._clone_btn = pygame_gui.elements.UIButton(
            pygame.Rect(86, 4, 72, 28), i.t("dialog.clone"), self._gui
        )
        self._del_btn = pygame_gui.elements.UIButton(
            pygame.Rect(164, 4, 72, 28), i.t("dialog.delete"), self._gui
        )
        self._save_btn = pygame_gui.elements.UIButton(
            pygame.Rect(240, 4, 72, 28), i.t("dialog.save"), self._gui
        )

        # ── Left list ──
        cy = TOOLBAR_H
        self._text_list = pygame_gui.elements.UISelectionList(
            pygame.Rect(0, cy, LEFT_W, h - cy),
            item_list=get_all_dialogo_keys(),
            manager=self._gui,
            default_selection=prev_key,
        )

        # ── Right editor panel ──
        rx, rw = LEFT_W, w - LEFT_W
        self._editor_panel = pygame_gui.elements.UIPanel(
            pygame.Rect(rx, cy, rw, h - cy), manager=self._gui
        )

        if prev_key:
            self._selected_key = prev_key
            self._build_editor_widgets()

    def _build_editor_widgets(self):
        ep = self._editor_panel
        y = PADDING
        ew = ep.rect.w

        self._eid_label = pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew - PADDING * 2, 20),
            f"ID: {self._selected_key}", self._gui, container=ep
        )
        y += 26

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 100, 22),
            self.i18n.t("dialog.character") + ":", self._gui, container=ep
        )
        p, c = _parse_key(self._selected_key) if self._selected_key else ("", "")
        self._char_input = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(110, y, 200, 22), initial_text=p,
            manager=self._gui, container=ep
        )
        y += 30

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 100, 22),
            self.i18n.t("dialog.context") + ":", self._gui, container=ep
        )
        self._ctx_input = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(110, y, 200, 22), initial_text=c,
            manager=self._gui, container=ep
        )
        y += 30

        y += 10

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 200, 18),
            self.i18n.t("dialog.lines"), self._gui, container=ep
        )
        y += 24

        lineas = get_dialogo_by_key(self._selected_key) if self._selected_key else None
        if lineas:
            for li, texto in enumerate(lineas):
                y = self._draw_line(li, texto, y, ew)

        self._add_line_btn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING + 10, y, 140, 22),
            self.i18n.t("dialog.add_line"), self._gui, container=ep
        )

    def _draw_line(self, li, texto, y, max_w):
        num_w = 24
        btn_w = 18
        inp_w = max_w - num_w - btn_w * 3 - 18 - PADDING * 2

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING + 6, y + 2, num_w, 20),
            f"{li + 1}:", self._gui, container=self._editor_panel
        )
        inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(PADDING + 6 + num_w + 2, y, inp_w, LINE_H),
            initial_text=texto, manager=self._gui,
            container=self._editor_panel
        )
        up = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING + 6 + num_w + 2 + inp_w + 2, y, btn_w, LINE_H),
            "\u25B2", self._gui, container=self._editor_panel
        )
        dn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING + 6 + num_w + 2 + inp_w + 2 + btn_w + 2, y, btn_w, LINE_H),
            "\u25BC", self._gui, container=self._editor_panel
        )
        rm = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING + 6 + num_w + 2 + inp_w + 2 + btn_w * 2 + 4, y, btn_w, LINE_H),
            "X", self._gui, container=self._editor_panel
        )
        self._line_widgets.append({
            "input": inp, "up": up, "down": dn, "delete": rm
        })
        return y + LINE_H + 2

    # ── Lineas ───────────────────────────────────────────

    def _get_line_texts(self):
        texts = []
        for lw in self._line_widgets:
            texts.append(lw["input"].get_text())
        return texts

    def _move_line(self, idx, direction):
        texts = self._get_line_texts()
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(texts):
            return
        texts[idx], texts[new_idx] = texts[new_idx], texts[idx]
        if self._selected_key:
            set_dialogo_by_key(self._selected_key, texts)
            self._dirty = True
            self._build_ui()

    def _remove_line(self, idx):
        texts = self._get_line_texts()
        if len(texts) <= 1:
            return
        texts.pop(idx)
        if self._selected_key:
            set_dialogo_by_key(self._selected_key, texts)
            self._dirty = True
            self._build_ui()

    def _on_add_line(self):
        texts = self._get_line_texts()
        texts.append("")
        if self._selected_key:
            set_dialogo_by_key(self._selected_key, texts)
            self._dirty = True
            self._build_ui()

    # ── Modal dialog (keep custom rendering) ─────────────────

    def _prompt_new_key(self, default_personaje="", default_contexto=""):
        font = I18n.instancia().fuente(14) if I18n.instancia() else pygame.font.SysFont("Arial", 14)
        font_b = I18n.instancia().fuente(14, bold=True) if I18n.instancia() else pygame.font.SysFont("Arial", 14, bold=True)
        screen = pygame.display.get_surface()
        W, H = screen.get_width(), screen.get_height()
        dw, dh = 420, 200
        dx, dy = (W - dw) // 2, (H - dh) // 2
        fields = [
            {"label": self.i18n.t("dialog.character"), "value": default_personaje},
            {"label": self.i18n.t("dialog.context"), "value": default_contexto},
        ]
        cursor_pos = [len(f["value"]) for f in fields]
        focus = 0
        clock = pygame.time.Clock()
        result = None
        done = False
        bg = pygame.Surface((W, H), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))
        while not done:
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        done = True
                        result = None
                    elif event.key == pygame.K_RETURN:
                        p = fields[0]["value"].strip()
                        c = fields[1]["value"].strip()
                        if p and c:
                            result = _make_key(p, c)
                            done = True
                        else:
                            focus = 0 if not p else 1
                    elif event.key == pygame.K_TAB:
                        focus = (focus + 1) % len(fields)
                    elif event.key == pygame.K_BACKSPACE:
                        if cursor_pos[focus] > 0:
                            fields[focus]["value"] = fields[focus]["value"][:cursor_pos[focus] - 1] + fields[focus]["value"][cursor_pos[focus]:]
                            cursor_pos[focus] -= 1
                    elif event.key == pygame.K_DELETE:
                        if cursor_pos[focus] < len(fields[focus]["value"]):
                            fields[focus]["value"] = fields[focus]["value"][:cursor_pos[focus]] + fields[focus]["value"][cursor_pos[focus] + 1:]
                    elif event.key == pygame.K_LEFT:
                        cursor_pos[focus] = max(0, cursor_pos[focus] - 1)
                    elif event.key == pygame.K_RIGHT:
                        cursor_pos[focus] = min(len(fields[focus]["value"]), cursor_pos[focus] + 1)
                    elif event.key == pygame.K_HOME:
                        cursor_pos[focus] = 0
                    elif event.key == pygame.K_END:
                        cursor_pos[focus] = len(fields[focus]["value"])
                    elif event.unicode and event.unicode.isprintable():
                        fields[focus]["value"] = fields[focus]["value"][:cursor_pos[focus]] + event.unicode + fields[focus]["value"][cursor_pos[focus]:]
                        cursor_pos[focus] += 1
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    for fi, f in enumerate(fields):
                        fx = dx + 20
                        fy = dy + 50 + fi * 50
                        fr = pygame.Rect(fx + 100, fy, dw - 120, 28)
                        if fr.collidepoint(mx, my):
                            focus = fi
                            rel_x = mx - fr.x - 4
                            txt = font.render(f["value"], True, (220, 220, 220))
                            char_pos = 0
                            for ci in range(len(f["value"]) + 1):
                                w_txt = font.render(f["value"][:ci], True, (220, 220, 220))
                                if w_txt.get_width() >= rel_x:
                                    char_pos = ci
                                    break
                            cursor_pos[fi] = char_pos
            screen.blit(bg, (0, 0))
            pygame.draw.rect(screen, (45, 50, 58), (dx, dy, dw, dh))
            pygame.draw.rect(screen, (70, 80, 95), (dx, dy, dw, dh), 2)
            title = font_b.render(self.i18n.t("dialog.new_title"), True, (220, 190, 120))
            screen.blit(title, (dx + (dw - title.get_width()) // 2, dy + 14))
            for fi, f in enumerate(fields):
                fy = dy + 50 + fi * 50
                lbl = font.render(f["label"] + ":", True, (180, 190, 200))
                screen.blit(lbl, (dx + 20, fy + 4))
                inp_r = pygame.Rect(dx + 120, fy, dw - 140, 28)
                bg_c = (70, 80, 100) if fi == focus else (55, 60, 70)
                pygame.draw.rect(screen, bg_c, inp_r)
                pygame.draw.rect(screen, (80, 90, 105), inp_r, 1)
                txt_surf = font.render(f["value"], True, (220, 220, 220))
                screen.blit(txt_surf, (inp_r.x + 4, inp_r.y + (inp_r.h - txt_surf.get_height()) // 2))
                if fi == focus and (pygame.time.get_ticks() // 500) % 2 == 0:
                    cx = inp_r.x + 4 + font.render(f["value"][:cursor_pos[fi]], True, (220, 220, 220)).get_width()
                    pygame.draw.line(screen, (200, 200, 200), (cx, inp_r.y + 3), (cx, inp_r.y + inp_r.h - 3))
            hint = font.render("TAB: cambiar campo  ENTER: aceptar  ESC: cancelar", True, (130, 140, 150))
            screen.blit(hint, (dx + (dw - hint.get_width()) // 2, dy + dh - 22))
            pygame.display.flip()
        return result

    # ── Acciones ─────────────────────────────────────────

    def _on_new(self):
        result = self._prompt_new_key("nuevo_personaje", "nuevo_contexto")
        if result is None:
            return
        if create_dialogo_by_key(result):
            self._selected_key = result
            self._dirty = True
            self._build_ui()

    def _on_clone(self):
        if not self._selected_key:
            return
        p, c = _parse_key(self._selected_key)
        result = self._prompt_new_key(p + "_copia", c)
        if result is None:
            return
        if result == self._selected_key:
            return
        lineas = get_dialogo_by_key(self._selected_key)
        if lineas is None:
            return
        if create_dialogo_by_key(result):
            set_dialogo_by_key(result, list(lineas))
            self._selected_key = result
            self._dirty = True
            self._build_ui()

    def _on_delete(self):
        if not self._selected_key:
            return
        delete_dialogo_by_key(self._selected_key)
        self._selected_key = None
        self._dirty = True
        self._build_ui()

    def _on_save(self):
        if not self._selected_key:
            return
        new_p = self._char_input.get_text().strip()
        new_c = self._ctx_input.get_text().strip()
        new_key = _make_key(new_p, new_c) if new_p and new_c else self._selected_key
        lineas = self._get_line_texts()
        if new_key != self._selected_key:
            if rename_dialogo(self._selected_key, new_key):
                set_dialogo_by_key(new_key, lineas)
                self._selected_key = new_key
            else:
                set_dialogo_by_key(self._selected_key, lineas)
        else:
            set_dialogo_by_key(self._selected_key, lineas)
        self._dirty = False
        self._build_ui()

    # ── Integración con el editor ────────────────────────

    def update(self, dt):
        self._gui.update(dt)

    def handle_event(self, event):
        if not self.visible:
            return False
        r = self.get_abs_rect()
        if hasattr(event, 'pos'):
            e = pygame.event.Event(event.type, {
                "pos": (event.pos[0] - r.x, event.pos[1] - r.y),
                "button": getattr(event, "button", 0),
                "buttons": getattr(event, "buttons", (0, 0, 0)),
                "rel": getattr(event, "rel", (0, 0)),
            })
        else:
            e = event
        self._gui.process_events(e)

        if e.type == pygame_gui.UI_BUTTON_PRESSED:
            el = e.ui_element
            if el == self._new_btn:
                self._on_new()
                return True
            if el == self._clone_btn:
                self._on_clone()
                return True
            if el == self._del_btn:
                self._on_delete()
                return True
            if el == self._save_btn:
                self._on_save()
                return True
            if hasattr(self, '_add_line_btn') and el == self._add_line_btn:
                self._on_add_line()
                return True
            for di, lw in enumerate(self._line_widgets):
                if el == lw["up"]:
                    self._move_line(di, -1)
                    return True
                if el == lw["down"]:
                    self._move_line(di, 1)
                    return True
                if el == lw["delete"]:
                    self._remove_line(di)
                    return True
        elif e.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            key = e.text
            if key in get_all_dialogo_keys():
                self._selected_key = key
                self._build_ui()
                return True

        return True

    def draw(self, surface):
        if not self.visible:
            return
        r = self.get_abs_rect()
        pygame.draw.rect(surface, self.bg_color, r)
        self._gui.draw_ui(surface.subsurface(r))

    def set_size(self, w, h):
        if self.rect.w != w or self.rect.h != h:
            self.rect.w = w
            self.rect.h = h
            self._gui.set_window_resolution((w, h))
            self._build_ui()
