import json
import os
import pygame
import pygame_gui

from editor.panels.base_panel import BasePanel
from editor.pygame_gui_theme import create_gui

PADDING = 6
ROW_H = 28
TOOLBAR_H = 36
LINE_H = 24
TEXT_LEFT_W = 200


def _text_screens_path():
    from editor.project import get_current_project
    p = get_current_project()
    return os.path.join(p.root, "data", "text_screens.json") if p else None


def _load_text_screens():
    path = _text_screens_path()
    if path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {}


def _save_text_screens(data):
    path = _text_screens_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


class ScreensPanel(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(0, 0, w, h, i18n)
        self.bg_color = (30, 32, 36)
        self._gui = create_gui((w, h), offset_getter=lambda: (
            self.get_abs_rect().x, self.get_abs_rect().y
        ))
        self._manifest_path = None
        self._data = self._cargar_manifest()
        self._text_data = _load_text_screens()
        self._selected_text_id = None
        self._boot_rows = {}
        self._line_widgets = []
        self._build_ui()

    # ── Manifest (boot screens) ──────────────────────────────

    def _manifest_path_actual(self):
        from editor.project import get_current_project
        p = get_current_project()
        return os.path.join(p.root, "cururo.json") if p else None

    def _cargar_manifest(self):
        path = self._manifest_path_actual()
        if not path:
            return {"enabled": True, "items": [], "config": {}}
        try:
            with open(path, encoding="utf-8") as f:
                m = json.load(f)
            return m.get("screens", {"enabled": True, "items": [], "config": {}})
        except Exception:
            return {"enabled": True, "items": [], "config": {}}

    def _guardar_manifest(self):
        items = self._data.get("items", [])
        cfg = self._data.setdefault("config", {})
        for sid, row in self._boot_rows.items():
            if sid in items and "checkbox" in row:
                sc = cfg.setdefault(sid, {})
                sc["enabled"] = row["checkbox"].is_checked
                try:
                    sc["duration_ms"] = int(row["duration"].get_text())
                except ValueError:
                    sc["duration_ms"] = 0
        path = self._manifest_path_actual()
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as f:
                m = json.load(f)
        except Exception:
            m = {}
        m["screens"] = self._data
        with open(path, "w", encoding="utf-8") as f:
            json.dump(m, f, indent=2, ensure_ascii=False)

    # ── UI ─────────────────────────────────────────────────

    def _build_ui(self):
        prev_selection = self._selected_text_id
        self._gui.clear_and_reset()
        self._boot_rows.clear()
        self._line_widgets.clear()
        w, h = self.rect.w, self.rect.h
        i = self.i18n

        # ── Toolbar ──
        self._save_btn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING, 4, 80, 28), i.t("app.save"), self._gui
        )
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING + 88, 8, 300, 20), i.t("screens.title"), self._gui
        )

        # ── Boot screens ──
        cy = TOOLBAR_H + PADDING
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, cy, 200, 20), "--- Boot screens ---", self._gui
        )
        cy += 22

        items = self._data.get("items", [])
        cfg = self._data.get("config", {})
        for idx, sid in enumerate(items):
            sc = cfg.get(sid, {})
            enabled = sc.get("enabled", True)
            dur = sc.get("duration_ms", 0)
            obli = sid == "cururo_games"
            cx = PADDING + 4

            pygame_gui.elements.UILabel(
                pygame.Rect(cx, cy + 4, 20, 20), f"{idx + 1}.", self._gui
            )
            cx += 22
            pygame_gui.elements.UILabel(
                pygame.Rect(cx, cy + 4, 120, 20),
                sid.replace("_", " ").title(), self._gui
            )
            cx += 130

            row = {}
            if not obli:
                row["checkbox"] = pygame_gui.elements.UICheckBox(
                    pygame.Rect(cx, cy, 50, ROW_H), "", self._gui, initial_state=enabled
                )
                cx += 58
                row["duration"] = pygame_gui.elements.UITextEntryLine(
                    pygame.Rect(cx, cy, 50, ROW_H), initial_text=str(dur),
                    manager=self._gui
                )
                cx += 56

            pygame_gui.elements.UILabel(
                pygame.Rect(cx, cy + 4, 24, 20), "ms", self._gui
            )

            if not obli:
                cx += 30
                row["up"] = pygame_gui.elements.UIButton(
                    pygame.Rect(cx, cy + 1, 22, ROW_H - 2), "\u25B2", self._gui
                )
                cx += 26
                row["down"] = pygame_gui.elements.UIButton(
                    pygame.Rect(cx, cy + 1, 22, ROW_H - 2), "\u25BC", self._gui
                )
                cx += 28
                row["delete"] = pygame_gui.elements.UIButton(
                    pygame.Rect(cx, cy + 1, 22, ROW_H - 2), "X", self._gui
                )

            self._boot_rows[sid] = row
            cy += ROW_H

        self._add_boot_btn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING, cy + 4, 120, 28), i.t("screens.add"), self._gui
        )
        cy += 36

        # ── Text screens ──
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, cy, 400, 20),
            "--- " + i.t("screens.text_screens") + " ---", self._gui
        )
        cy += 22

        list_h = h - cy
        self._text_list = pygame_gui.elements.UISelectionList(
            pygame.Rect(0, cy, TEXT_LEFT_W, list_h - 28),
            item_list=sorted(self._text_data.keys()),
            manager=self._gui,
            default_selection=prev_selection,
        )
        self._new_text_btn = pygame_gui.elements.UIButton(
            pygame.Rect(0, h - 28, TEXT_LEFT_W, 28),
            "+ " + i.t("screens.new"), self._gui
        )

        # ── Text editor ──
        if prev_selection and prev_selection in self._text_data:
            self._build_text_editor(cy, w, h, prev_selection)
        self._selected_text_id = prev_selection

    def _build_text_editor(self, cy, w, h, sid):
        ex, ey = TEXT_LEFT_W, cy
        ew, eh = w - TEXT_LEFT_W, h - cy

        data = self._text_data.get(sid, {})
        title = data.get("title", "")
        lines = data.get("lineas", [])

        self._editor_panel = pygame_gui.elements.UIPanel(
            pygame.Rect(ex, ey, ew, eh), manager=self._gui
        )
        y = PADDING

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew, 20),
            f"ID: {sid}", self._gui, container=self._editor_panel
        )
        y += 22

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 155, 22),
            self.i18n.t("screens.title") + ":", self._gui,
            container=self._editor_panel
        )
        self._title_input = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(165, y, ew - 175, 22), initial_text=title,
            manager=self._gui, container=self._editor_panel
        )
        y += 28

        y += 10

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 200, 18),
            self.i18n.t("screens.lines") + ":", self._gui,
            container=self._editor_panel
        )
        y += 24

        for li, line_text in enumerate(lines):
            y = self._draw_line(li, line_text, y, ew)

        self._add_line_btn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING + 10, y, 140, 22),
            self.i18n.t("screens.add_line"), self._gui,
            container=self._editor_panel
        )

    def _draw_line(self, li, text, y, max_w):
        num_w = 24
        btn_w = 18
        inp_w = max_w - num_w - btn_w * 3 - 18 - PADDING * 2

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING + 6, y + 2, num_w, 20),
            f"{li + 1}:", self._gui, container=self._editor_panel
        )
        inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(PADDING + 6 + num_w + 2, y, inp_w, LINE_H),
            initial_text=text, manager=self._gui,
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
        self._line_widgets.append({"input": inp, "up": up, "down": dn, "delete": rm})
        return y + LINE_H + 2

    # ── Boot screen helpers ──────────────────────────────

    def _toggle(self, sid):
        cfg = self._data.setdefault("config", {})
        sc = cfg.setdefault(sid, {})
        sc["enabled"] = not sc.get("enabled", True)
        self._build_ui()

    def _mover(self, idx, delta):
        items = self._data.get("items", [])
        new_idx = idx + delta
        if new_idx < 0 or new_idx >= len(items):
            return
        items[idx], items[new_idx] = items[new_idx], items[idx]
        self._build_ui()

    def _eliminar(self, sid):
        items = self._data.get("items", [])
        if sid in items:
            items.remove(sid)
            self._data.get("config", {}).pop(sid, None)
        self._build_ui()

    def _on_add_boot(self):
        items = self._data.setdefault("items", [])
        base = "new_screen"
        sid = base
        n = 1
        while sid in items:
            n += 1
            sid = f"{base}_{n}"
        items.append(sid)
        self._data.setdefault("config", {})[sid] = {"enabled": True, "duration_ms": 2000}
        self._build_ui()

    # ── Text screen helpers ──────────────────────────────

    def _get_line_texts(self):
        texts = []
        for lw in self._line_widgets:
            texts.append(lw["input"].get_text())
        return texts

    def _on_new_text(self):
        base = "new_screen"
        sid = base
        n = 1
        while sid in self._text_data:
            n += 1
            sid = f"{base}_{n}"
        self._text_data[sid] = {"title": "", "lineas": [""]}
        self._selected_text_id = sid
        self._build_ui()

    def _select_text_id(self, text):
        if text in self._text_data:
            self._selected_text_id = text
            self._build_ui()

    def _on_add_line(self):
        if not self._selected_text_id:
            return
        lines = self._get_line_texts()
        lines.append("")
        self._text_data[self._selected_text_id]["lineas"] = lines
        self._build_ui()

    def _move_line(self, idx, direction):
        if not self._selected_text_id:
            return
        lines = self._get_line_texts()
        new_idx = idx + direction
        if new_idx < 0 or new_idx >= len(lines):
            return
        lines[idx], lines[new_idx] = lines[new_idx], lines[idx]
        self._text_data[self._selected_text_id]["lineas"] = lines
        self._build_ui()

    def _remove_line(self, idx):
        if not self._selected_text_id:
            return
        lines = self._get_line_texts()
        if len(lines) <= 1:
            return
        lines.pop(idx)
        self._text_data[self._selected_text_id]["lineas"] = lines
        self._build_ui()

    # ── Save ─────────────────────────────────────────────

    def _guardar_todo(self):
        if self._selected_text_id and self._title_input:
            data = self._text_data.setdefault(self._selected_text_id, {})
            data["title"] = self._title_input.get_text()
            data["lineas"] = self._get_line_texts()
        self._guardar_manifest()
        _save_text_screens(self._text_data)

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
            if el == self._save_btn:
                self._guardar_todo()
                return True
            if el == self._add_boot_btn:
                self._on_add_boot()
                return True
            if el == self._new_text_btn:
                self._on_new_text()
                return True
            if hasattr(self, '_add_line_btn') and el == self._add_line_btn:
                self._on_add_line()
                return True
            items = self._data.get("items", [])
            for sid, row in self._boot_rows.items():
                if sid not in items:
                    continue
                idx = items.index(sid)
                if el == row.get("up"):
                    self._mover(idx, -1)
                    return True
                if el == row.get("down"):
                    self._mover(idx, 1)
                    return True
                if el == row.get("delete"):
                    self._eliminar(sid)
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
            self._select_text_id(e.text)
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
