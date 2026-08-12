import pygame
import pygame_gui

from editor.panels.base_panel import BasePanel
from editor.pygame_gui_theme import create_gui
from editor.scene_data import (
    get_chapters, add_chapter, delete_chapter, move_chapter,
    get_scenes, add_scene, delete_scene, move_scene,
    get_scene, set_scene, get_title_data, set_title_data,
    get_chapter, set_chapter, ENUM_SCENE_TYPES, TIPO_ESCENA,
    _load_scenes, _save_scenes,
)

PADDING = 6
ROW_H = 28
TOOLBAR_H = 36
BTN_W = 22


class ScenePanel(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(0, 0, w, h, i18n)
        self.bg_color = (30, 32, 36)
        self._gui = create_gui((w, h), offset_getter=lambda: (
            self.get_abs_rect().x, self.get_abs_rect().y
        ))
        _load_scenes()
        self._selected_chapter = None
        self._selected_scene = None
        self._chapter_rows = []
        self._scene_rows = []
        self._title_widgets = {}
        self._scene_editor_widgets = {}
        self._build_ui()

    # ── UI ────────────────────────────────────────────────

    def _build_ui(self, focus_chapter=None, focus_scene=None):
        self._gui.clear_and_reset()
        self._chapter_rows.clear()
        self._scene_rows.clear()
        self._title_widgets.clear()
        self._scene_editor_widgets.clear()
        w, h = self.rect.w, self.rect.h

        # ── Toolbar ──
        self._save_btn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING, 4, 80, 28), self.i18n.t("app.save"), self._gui
        )
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING + 88, 8, 300, 20),
            self.i18n.t("scene.title"), self._gui
        )

        chapters = get_chapters()
        cy = TOOLBAR_H + PADDING

        # ── Chapters ──
        sec_w = w // 2 - PADDING
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, cy, sec_w, 20),
            "--- " + self.i18n.t("scene.chapters") + " ---", self._gui
        )
        cy += 22

        list_h = 180
        list_rect = pygame.Rect(PADDING, cy, sec_w, list_h)
        chapter_items = []
        for ch in chapters:
            label = f"{ch.get('id', '?')} — {ch.get('nombre', '?')}"
            chapter_items.append(label)
        sel_ch = None
        if focus_chapter is not None:
            fch = chapters[focus_chapter]
            sel_ch = f"{fch.get('id', '?')} — {fch.get('nombre', '?')}"
        elif self._selected_chapter is not None and self._selected_chapter < len(chapters):
            fch = chapters[self._selected_chapter]
            sel_ch = f"{fch.get('id', '?')} — {fch.get('nombre', '?')}"
        self._chapter_list = pygame_gui.elements.UISelectionList(
            list_rect, item_list=chapter_items, manager=self._gui,
            default_selection=sel_ch,
        )
        cy = list_rect.bottom + 4

        btn_y = cy
        self._ch_new = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING, btn_y, 60, 24), self.i18n.t("scene.ch_new"), self._gui
        )
        self._ch_del = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING + 64, btn_y, 60, 24), self.i18n.t("scene.ch_del"), self._gui
        )
        self._ch_up = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING + 128, btn_y, 30, 24), "\u25B2", self._gui
        )
        self._ch_dn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING + 162, btn_y, 30, 24), "\u25BC", self._gui
        )
        cy = btn_y + 28

        # ── Scenes (right side) ──
        sx = w // 2 + PADDING
        scene_w = w // 2 - PADDING * 2
        pygame_gui.elements.UILabel(
            pygame.Rect(sx, TOOLBAR_H + PADDING, scene_w, 20),
            "--- " + self.i18n.t("scene.scenes") + " ---", self._gui
        )
        sy = TOOLBAR_H + PADDING + 22

        cidx = self._get_selected_chapter_idx()
        scenes = get_scenes(cidx) if cidx is not None else []
        scene_items = []
        _scene_map = {}
        for si, sc in enumerate(scenes):
            tid = sc.get("tipo", "?")
            tlabel = TIPO_ESCENA.get(tid, tid)
            label = f"{si + 1}. [{tlabel}] {sc.get('id', '?')}"
            scene_items.append(label)
            _scene_map[label] = si

        sel_sc_label = None
        if focus_scene is not None and focus_scene < len(scene_items):
            sel_sc_label = scene_items[focus_scene]
        elif self._selected_scene is not None and self._selected_scene < len(scene_items):
            sel_sc_label = scene_items[self._selected_scene]

        scene_list_rect = pygame.Rect(sx, sy, scene_w, list_h)
        self._scene_list = pygame_gui.elements.UISelectionList(
            scene_list_rect, item_list=scene_items, manager=self._gui,
            default_selection=sel_sc_label,
        )
        sy = scene_list_rect.bottom + 4

        self._sc_new = pygame_gui.elements.UIButton(
            pygame.Rect(sx, sy, 60, 24), self.i18n.t("scene.sc_new"), self._gui
        )
        self._sc_del = pygame_gui.elements.UIButton(
            pygame.Rect(sx + 64, sy, 60, 24), self.i18n.t("scene.sc_del"), self._gui
        )
        self._sc_up = pygame_gui.elements.UIButton(
            pygame.Rect(sx + 128, sy, 30, 24), "\u25B2", self._gui
        )
        self._sc_dn = pygame_gui.elements.UIButton(
            pygame.Rect(sx + 162, sy, 30, 24), "\u25BC", self._gui
        )
        sy += 28

        # ── Scene editor ──
        if cidx is not None and self._selected_scene is not None:
            scene = get_scene(cidx, self._selected_scene)
            if scene:
                sy += 6
                self._build_scene_editor(scene, sx, sy, scene_w, h - sy)

        # ── Title screen ──
        ty = max(cy, h - 120)
        if cy < ty:
            self._build_title_section(ty, w, h)

    def _build_scene_editor(self, scene, sx, sy, ew, max_h):
        ew_avail = ew - PADDING * 2
        sec_h = min(max_h - PADDING, 240)
        panel_rect = pygame.Rect(sx, sy, ew, sec_h)
        container = pygame_gui.core.UIContainer(panel_rect, manager=self._gui)
        self._scene_editor_container = container
        y = PADDING

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 80, 20),
            self.i18n.t("scene.sc_id"), self._gui, container=container
        )
        sid_w = ew_avail - 84
        sid_input = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(84, y, sid_w, 22), initial_text=scene.get("id", ""),
            manager=self._gui, container=container
        )
        self._scene_editor_widgets["id"] = sid_input
        y += 28

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 80, 20),
            self.i18n.t("scene.sc_type"), self._gui, container=container
        )
        type_items = [f"{k}|{v}" for k, v in ENUM_SCENE_TYPES.items()]
        current_type = scene.get("tipo", "dialogo")
        type_dropdown = pygame_gui.elements.UIDropDownMenu(
            type_items, f"{current_type}|{TIPO_ESCENA.get(current_type, current_type)}",
            pygame.Rect(84, y, ew_avail - 84, 22), self._gui, container=container
        )
        self._scene_editor_widgets["tipo"] = type_dropdown
        y += 28

        tipo = scene.get("tipo", "dialogo")
        tipo_schema = ENUM_SCENE_TYPES.get(tipo, {"fields": []})
        for field in tipo_schema["fields"]:
            val = scene.get(field, "")
            label_key = f"scene.field.{field}"
            pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 120, 20),
                self.i18n.t(label_key), self._gui, container=container
            )
            inp = pygame_gui.elements.UITextEntryLine(
                pygame.Rect(124, y, ew_avail - 128, 22), initial_text=str(val),
                manager=self._gui, container=container
            )
            self._scene_editor_widgets[field] = inp
            y += 28

        # ── Entry condition ──
        cond = scene.get("condicion_entrada", {})
        cond_flag = cond.get("flag", "")
        cond_op = cond.get("operador", "==")
        cond_val = str(cond.get("valor", ""))

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew_avail, 18),
            self.i18n.t("scene.condition") + ":", self._gui, container=container
        )
        y += 20

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 40, 20),
            self.i18n.t("event.param.flag"), self._gui, container=container
        )
        cond_flag_inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(44, y, ew_avail - 140, 22), initial_text=cond_flag,
            manager=self._gui, container=container
        )
        self._scene_editor_widgets["cond_flag"] = cond_flag_inp

        op_items = ["==", "!=", ">", "<", ">=", "<="]
        op_dropdown = pygame_gui.elements.UIDropDownMenu(
            op_items, cond_op,
            pygame.Rect(ew_avail - 88, y, 40, 22), self._gui, container=container
        )
        self._scene_editor_widgets["cond_op"] = op_dropdown

        cond_val_inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(ew_avail - 44, y, 40, 22), initial_text=cond_val,
            manager=self._gui, container=container
        )
        self._scene_editor_widgets["cond_val"] = cond_val_inp
        y += 28

    def _build_title_section(self, ty, w, h):
        tw = w - PADDING * 2
        panel_rect = pygame.Rect(PADDING, ty, tw, h - ty - PADDING)
        container = pygame_gui.core.UIContainer(panel_rect, manager=self._gui)
        self._title_container = container
        y = PADDING

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, tw, 20),
            "--- " + self.i18n.t("scene.title_screen") + " ---",
            self._gui, container=container
        )
        y += 24

        title_data = get_title_data()

        toggle = title_data.get("enabled", False)
        self._title_widgets["enabled"] = pygame_gui.elements.UICheckBox(
            pygame.Rect(PADDING, y, 20, 20), self.i18n.t("scene.title_enabled"),
            self._gui, container=container, initial_state=toggle
        )
        y += 26

        fields = [
            ("fondo", "scene.title_bg"),
            ("titulo", "scene.title_text"),
            ("subtitulo", "scene.title_sub"),
        ]
        for key, label_key in fields:
            val = title_data.get(key, "")
            pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, tw - 120, 20),
                self.i18n.t(label_key), self._gui, container=container
            )
            inp = pygame_gui.elements.UITextEntryLine(
                pygame.Rect(tw - 120, y, 120, 22), initial_text=str(val),
                manager=self._gui, container=container
            )
            self._title_widgets[key] = inp
            y += 28

    # ── Helpers ────────────────────────────────────────────

    def _get_selected_chapter_idx(self):
        chapters = get_chapters()
        if self._chapter_list and self._chapter_list.get_single_selection():
            sel = self._chapter_list.get_single_selection()
            for i, ch in enumerate(chapters):
                label = f"{ch.get('id', '?')} — {ch.get('nombre', '?')}"
                if label == sel:
                    return i
        return self._selected_chapter

    def _get_selected_scene_idx(self):
        cidx = self._get_selected_chapter_idx()
        if cidx is None:
            return None
        scenes = get_scenes(cidx)
        if self._scene_list and self._scene_list.get_single_selection():
            sel = self._scene_list.get_single_selection()
            for si, sc in enumerate(scenes):
                tid = sc.get("tipo", "?")
                tlabel = TIPO_ESCENA.get(tid, tid)
                label = f"{si + 1}. [{tlabel}] {sc.get('id', '?')}"
                if label == sel:
                    return si
        return self._selected_scene

    def _save_scene_editor(self):
        cidx = self._get_selected_chapter_idx()
        sidx = self._get_selected_scene_idx()
        if cidx is None or sidx is None:
            return
        scene = get_scene(cidx, sidx)
        if not scene:
            return
        if "id" in self._scene_editor_widgets:
            scene["id"] = self._scene_editor_widgets["id"].get_text()
        if "tipo" in self._scene_editor_widgets:
            raw = self._scene_editor_widgets["tipo"].selected_option
            if "|" in raw:
                scene["tipo"] = raw.split("|")[0]
        tipo_schema = ENUM_SCENE_TYPES.get(scene.get("tipo", "dialogo"), {"fields": []})
        for field in tipo_schema["fields"]:
            if field in self._scene_editor_widgets:
                scene[field] = self._scene_editor_widgets[field].get_text()
        cond = {}
        if "cond_flag" in self._scene_editor_widgets:
            fv = self._scene_editor_widgets["cond_flag"].get_text().strip()
            if fv:
                cond["flag"] = fv
                raw_op = self._scene_editor_widgets["cond_op"].selected_option
                cond["operador"] = raw_op
                cond["valor"] = self._scene_editor_widgets["cond_val"].get_text().strip()
        scene["condicion_entrada"] = cond
        set_scene(cidx, sidx, scene)

    def _save_title(self):
        data = get_title_data()
        if "enabled" in self._title_widgets:
            data["enabled"] = self._title_widgets["enabled"].is_checked
        fields = ["fondo", "titulo", "subtitulo"]
        for f in fields:
            if f in self._title_widgets:
                data[f] = self._title_widgets[f].get_text()
        set_title_data(data)

    def _guardar_todo(self):
        if self._scene_editor_widgets:
            self._save_scene_editor()
        if self._title_widgets:
            self._save_title()

    # ── Chapter actions ────────────────────────────────────

    def _on_ch_new(self):
        add_chapter()
        self._selected_chapter = len(get_chapters()) - 1
        self._selected_scene = None
        self._build_ui()

    def _on_ch_del(self):
        cidx = self._get_selected_chapter_idx()
        if cidx is not None:
            delete_chapter(cidx)
            self._selected_chapter = None
            self._selected_scene = None
            self._build_ui()

    def _on_ch_move(self, direction):
        cidx = self._get_selected_chapter_idx()
        if cidx is not None:
            move_chapter(cidx, direction)
            self._selected_chapter = cidx + direction
            self._build_ui()

    # ── Scene actions ──────────────────────────────────────

    def _on_sc_new(self):
        cidx = self._get_selected_chapter_idx()
        if cidx is not None:
            add_scene(cidx)
            scenes = get_scenes(cidx)
            self._selected_scene = len(scenes) - 1
            self._build_ui()

    def _on_sc_del(self):
        cidx = self._get_selected_chapter_idx()
        sidx = self._get_selected_scene_idx()
        if cidx is not None and sidx is not None:
            delete_scene(cidx, sidx)
            self._selected_scene = None
            self._build_ui()

    def _on_sc_move(self, direction):
        cidx = self._get_selected_chapter_idx()
        sidx = self._get_selected_scene_idx()
        if cidx is not None and sidx is not None:
            move_scene(cidx, sidx, direction)
            self._selected_scene = sidx + direction
            self._build_ui()

    # ── Integration ────────────────────────────────────────

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
            if el == self._ch_new:
                self._on_ch_new()
                return True
            if el == self._ch_del:
                self._on_ch_del()
                return True
            if el == self._ch_up:
                self._on_ch_move(-1)
                return True
            if el == self._ch_dn:
                self._on_ch_move(1)
                return True
            if el == self._sc_new:
                self._save_scene_editor()
                self._on_sc_new()
                return True
            if el == self._sc_del:
                self._on_sc_del()
                return True
            if el == self._sc_up:
                self._save_scene_editor()
                self._on_sc_move(-1)
                return True
            if el == self._sc_dn:
                self._save_scene_editor()
                self._on_sc_move(1)
                return True
        elif e.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if hasattr(self, '_chapter_list') and e.ui_element == self._chapter_list:
                chapters = get_chapters()
                for i, ch in enumerate(chapters):
                    label = f"{ch.get('id', '?')} — {ch.get('nombre', '?')}"
                    if label == e.text:
                        self._save_scene_editor()
                        self._selected_chapter = i
                        self._selected_scene = None
                        self._build_ui()
                        return True
            if hasattr(self, '_scene_list') and e.ui_element == self._scene_list:
                cidx = self._get_selected_chapter_idx()
                if cidx is not None:
                    scenes = get_scenes(cidx)
                    for si, sc in enumerate(scenes):
                        tid = sc.get("tipo", "?")
                        tlabel = TIPO_ESCENA.get(tid, tid)
                        label = f"{si + 1}. [{tlabel}] {sc.get('id', '?')}"
                        if label == e.text:
                            self._save_scene_editor()
                            self._selected_scene = si
                            self._build_ui()
                            return True
        elif e.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if hasattr(self, '_scene_editor_widgets') and e.ui_element == self._scene_editor_widgets.get("tipo"):
                self._save_scene_editor()
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
