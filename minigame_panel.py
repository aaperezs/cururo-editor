import json
import pygame
import pygame_gui

from editor.panels.base_panel import BasePanel
from editor.pygame_gui_theme import create_gui
from editor.minigame_data import (
    get_minigames, get_minigame, set_minigame,
    add_minigame, delete_minigame, TIPOS_MINIJUEGO,
    _load_minigames,
)

PADDING = 6
TOOLBAR_H = 36


class MiniGamePanel(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(0, 0, w, h, i18n)
        self.bg_color = (30, 32, 36)
        self._gui = create_gui((w, h), offset_getter=lambda: (
            self.get_abs_rect().x, self.get_abs_rect().y
        ))
        _load_minigames()
        self._selected_id = None
        self._editor_widgets = {}
        self._build_ui()

    def _build_ui(self):
        self._gui.clear_and_reset()
        self._editor_widgets.clear()
        w, h = self.rect.w, self.rect.h
        i = self.i18n

        self._save_btn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING, 4, 80, 28), i.t("app.save"), self._gui
        )
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING + 88, 8, 300, 20),
            i.t("minigame.title"), self._gui
        )

        minigames = get_minigames()
        mid_list = sorted(minigames.keys())
        cy = TOOLBAR_H + PADDING

        # ── List ──
        list_h = 160
        list_rect = pygame.Rect(PADDING, cy, 220, list_h)
        sel = self._selected_id if self._selected_id in mid_list else None
        self._list = pygame_gui.elements.UISelectionList(
            list_rect, item_list=mid_list, manager=self._gui,
            default_selection=sel,
        )
        cy = list_rect.bottom + 4

        self._new_btn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING, cy, 60, 24), i.t("minigame.new"), self._gui
        )
        self._del_btn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING + 64, cy, 60, 24), i.t("minigame.delete"), self._gui
        )

        # ── Editor ──
        if self._selected_id and self._selected_id in minigames:
            mg = minigames[self._selected_id]
            ex = 240
            ew = w - ex - PADDING
            self._build_editor(mg, ex, TOOLBAR_H + PADDING, ew, h - TOOLBAR_H - PADDING)

    def _build_editor(self, mg, ex, ey, ew, eh):
        tipo = mg.get("tipo", "recoleccion")
        y = ey + PADDING
        ew_avail = ew - PADDING * 2
        container = pygame_gui.core.UIContainer(
            pygame.Rect(ex, ey, ew, eh), manager=self._gui
        )

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew_avail, 20),
            f"ID: {self._selected_id}", self._gui, container=container
        )
        y += 24

        # ── Name ──
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 60, 20),
            self.i18n.t("minigame.name"), self._gui, container=container
        )
        name_inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(64, y, ew_avail - 68, 22),
            initial_text=mg.get("nombre", ""),
            manager=self._gui, container=container
        )
        self._editor_widgets["nombre"] = name_inp
        y += 28

        # ── Type ──
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 60, 20),
            self.i18n.t("minigame.type"), self._gui, container=container
        )
        tipo_items = [f"{k}|{v}" for k, v in TIPOS_MINIJUEGO.items()]
        tipo_dd = pygame_gui.elements.UIDropDownMenu(
            tipo_items, f"{tipo}|{TIPOS_MINIJUEGO.get(tipo, tipo)}",
            pygame.Rect(64, y, ew_avail - 68, 22), self._gui, container=container
        )
        self._editor_widgets["tipo"] = tipo_dd
        y += 28

        # ── Tipo-specific fields ──
        if tipo == "recoleccion":
            y = self._build_recoleccion_editor(mg, container, y, ew_avail)
        elif tipo == "timing":
            y = self._build_timing_editor(mg, container, y, ew_avail)
        elif tipo == "puzzle":
            y = self._build_puzzle_editor(mg, container, y, ew_avail)

        # ── Flags resultado ──
        y += 6
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew_avail, 18),
            self.i18n.t("minigame.flags_result"), self._gui, container=container
        )
        y += 22
        flags = mg.get("flags_resultado", {})
        flags_str = json.dumps(flags, ensure_ascii=False)
        flags_inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(PADDING, y, ew_avail - PADDING, 22),
            initial_text=flags_str, manager=self._gui, container=container
        )
        self._editor_widgets["flags_resultado"] = flags_inp

    def _build_recoleccion_editor(self, mg, container, y, ew):
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 120, 20),
            self.i18n.t("minigame.time_limit"), self._gui, container=container
        )
        tl_inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(124, y, 60, 22),
            initial_text=str(mg.get("tiempo_limite", 30)),
            manager=self._gui, container=container
        )
        self._editor_widgets["tiempo_limite"] = tl_inp
        y += 28

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 100, 20),
            self.i18n.t("minigame.objective"), self._gui, container=container
        )
        obj_inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(104, y, 60, 22),
            initial_text=str(mg.get("objetivo", 10)),
            manager=self._gui, container=container
        )
        self._editor_widgets["objetivo"] = obj_inp
        y += 28

        items = mg.get("items", [])
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew, 18),
            self.i18n.t("minigame.items"), self._gui, container=container
        )
        y += 22
        items_str = json.dumps(items, ensure_ascii=False)
        items_inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(PADDING, y, ew - PADDING, 22),
            initial_text=items_str, manager=self._gui, container=container
        )
        self._editor_widgets["items"] = items_inp
        y += 28
        return y

    def _build_timing_editor(self, mg, container, y, ew):
        seq = mg.get("secuencia", [])
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew, 18),
            self.i18n.t("minigame.sequence"), self._gui, container=container
        )
        y += 22
        seq_str = json.dumps(seq, ensure_ascii=False)
        seq_inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(PADDING, y, ew - PADDING, 22),
            initial_text=seq_str, manager=self._gui, container=container
        )
        self._editor_widgets["secuencia"] = seq_inp
        y += 28
        return y

    def _build_puzzle_editor(self, mg, container, y, ew):
        grid = mg.get("grid", [3, 3])
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 60, 20),
            self.i18n.t("minigame.grid"), self._gui, container=container
        )
        grid_str = json.dumps(grid)
        grid_inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(64, y, 80, 22),
            initial_text=grid_str, manager=self._gui, container=container
        )
        self._editor_widgets["grid"] = grid_inp
        y += 28

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 120, 20),
            self.i18n.t("minigame.tile_size"), self._gui, container=container
        )
        ts_inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(124, y, 60, 22),
            initial_text=str(mg.get("tile_size", 80)),
            manager=self._gui, container=container
        )
        self._editor_widgets["tile_size"] = ts_inp
        y += 28
        return y

    def _save_editor(self):
        mid = self._selected_id
        if not mid:
            return
        mg = get_minigame(mid)
        if not mg:
            return
        if "nombre" in self._editor_widgets:
            mg["nombre"] = self._editor_widgets["nombre"].get_text()
        if "tipo" in self._editor_widgets:
            raw = self._editor_widgets["tipo"].selected_option
            if "|" in raw:
                mg["tipo"] = raw.split("|")[0]
        tipo = mg.get("tipo", "")
        if tipo == "recoleccion":
            for k in ("tiempo_limite", "objetivo"):
                if k in self._editor_widgets:
                    try:
                        mg[k] = int(self._editor_widgets[k].get_text())
                    except ValueError:
                        pass
            if "items" in self._editor_widgets:
                try:
                    mg["items"] = json.loads(self._editor_widgets["items"].get_text())
                except (json.JSONDecodeError, TypeError):
                    pass
        elif tipo == "timing":
            if "secuencia" in self._editor_widgets:
                try:
                    mg["secuencia"] = json.loads(self._editor_widgets["secuencia"].get_text())
                except (json.JSONDecodeError, TypeError):
                    pass
        elif tipo == "puzzle":
            if "grid" in self._editor_widgets:
                try:
                    mg["grid"] = json.loads(self._editor_widgets["grid"].get_text())
                except (json.JSONDecodeError, TypeError):
                    pass
            if "tile_size" in self._editor_widgets:
                try:
                    mg["tile_size"] = int(self._editor_widgets["tile_size"].get_text())
                except ValueError:
                    pass
        if "flags_resultado" in self._editor_widgets:
            try:
                mg["flags_resultado"] = json.loads(
                    self._editor_widgets["flags_resultado"].get_text()
                )
            except (json.JSONDecodeError, TypeError):
                pass
        set_minigame(mid, mg)

    def _on_new(self):
        add_minigame()
        minigames = get_minigames()
        keys = sorted(minigames.keys())
        self._selected_id = keys[-1] if keys else None
        self._build_ui()

    def _on_delete(self):
        if self._selected_id:
            delete_minigame(self._selected_id)
            self._selected_id = None
            self._build_ui()

    # ── Integration ──

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
                self._save_editor()
                return True
            if el == self._new_btn:
                self._save_editor()
                self._on_new()
                return True
            if el == self._del_btn:
                self._on_delete()
                return True
        elif e.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if hasattr(self, '_list') and e.ui_element == self._list:
                self._save_editor()
                self._selected_id = e.text
                self._build_ui()
                return True
        elif e.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if hasattr(self, '_editor_widgets') and e.ui_element == self._editor_widgets.get("tipo"):
                self._save_editor()
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
