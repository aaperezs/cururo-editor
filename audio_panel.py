import json
import pygame
import pygame_gui

from editor.panels.base_panel import BasePanel
from editor.pygame_gui_theme import create_gui
from editor.audio_data import (
    get_audio_list, get_audio, set_audio,
    add_audio, delete_audio, get_audio_types,
    _load_audio,
)
from editor.asset_data import get_asset_list

PADDING = 6
TOOLBAR_H = 36


class AudioPanel(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(0, 0, w, h, i18n)
        self.bg_color = (30, 32, 36)
        self._gui = create_gui((w, h), offset_getter=lambda: (
            self.get_abs_rect().x, self.get_abs_rect().y
        ))
        _load_audio()
        self._selected_id = None
        self._editor_widgets = {}
        self._build_ui()

    def _build_ui(self):
        self._gui.clear_and_reset()
        self._editor_widgets.clear()
        w, h = self.rect.w, self.rect.h
        i = self.i18n

        audio_list = get_audio_list()
        self.mostrar_descripcion(
            i.t("tab.audio.desc") if not audio_list else ""
        )

        self._save_btn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING, 4, 80, 28), i.t("app.save"), self._gui
        )
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING + 88, 8, 300, 20),
            i.t("audio.title"), self._gui
        )

        audio_list = get_audio_list()
        ids = [a[0] for a in audio_list]
        cy = TOOLBAR_H + PADDING

        list_h = 160
        list_rect = pygame.Rect(PADDING, cy, 220, list_h)
        sel = self._selected_id if self._selected_id in ids else None
        self._list = pygame_gui.elements.UISelectionList(
            list_rect, item_list=ids, manager=self._gui,
            default_selection=sel,
        )
        cy = list_rect.bottom + 4

        self._new_btn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING, cy, 60, 24), i.t("audio.new"), self._gui
        )
        self._del_btn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING + 64, cy, 60, 24), i.t("audio.delete"), self._gui
        )

        if self._selected_id and self._selected_id in ids:
            info = get_audio(self._selected_id)
            ex = 240
            ew = w - ex - PADDING
            self._build_editor(info, ex, TOOLBAR_H + PADDING, ew, h - TOOLBAR_H - PADDING)

    def _build_editor(self, info, ex, ey, ew, eh):
        y = ey + PADDING
        ew_a = ew - PADDING * 2
        container = pygame_gui.core.UIContainer(
            pygame.Rect(ex, ey, ew, eh), manager=self._gui
        )
        i = self.i18n

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew_a, 20),
            f"ID: {self._selected_id}", self._gui, container=container
        )
        y += 24

        # Name
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 60, 20), i.t("audio.name"), self._gui, container=container
        )
        name_inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(64, y, ew_a - 68, 22),
            initial_text=info.get("nombre", ""),
            manager=self._gui, container=container
        )
        self._editor_widgets["nombre"] = name_inp
        y += 28

        # Type
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 60, 20), i.t("audio.type"), self._gui, container=container
        )
        tipo_items = [f"{k}|{v}" for k, v in get_audio_types()]
        current_tipo = info.get("tipo", "bgm")
        tipo_dd = pygame_gui.elements.UIDropDownMenu(
            tipo_items, f"{current_tipo}|{dict(get_audio_types()).get(current_tipo, current_tipo)}",
            pygame.Rect(64, y, ew_a - 68, 22), self._gui, container=container
        )
        self._editor_widgets["tipo"] = tipo_dd
        y += 28

        # Asset ID (file reference)
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 80, 20), i.t("audio.asset_id"), self._gui, container=container
        )
        assets = get_asset_list()
        asset_ids = [a[0] for a in assets]
        current_asset = info.get("asset_id", "")
        asset_dd = pygame_gui.elements.UIDropDownMenu(
            asset_ids if asset_ids else ["(sin assets)"],
            current_asset if current_asset in asset_ids else "(sin asset)",
            pygame.Rect(84, y, ew_a - 88, 22), self._gui, container=container
        )
        self._editor_widgets["asset_id"] = asset_dd
        y += 28

        # Volume
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 80, 20), i.t("audio.volume"), self._gui, container=container
        )
        vol = info.get("volumen", 0.7)
        vol_inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(84, y, 60, 22),
            initial_text=str(vol), manager=self._gui, container=container
        )
        self._editor_widgets["volumen"] = vol_inp
        y += 28

        # Loop toggle
        loop = info.get("loop", True)
        self._editor_widgets["loop"] = pygame_gui.elements.UICheckBox(
            pygame.Rect(PADDING, y, 20, 20), i.t("audio.loop"),
            self._gui, container=container, initial_state=loop
        )
        y += 28

        # Default scene
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 120, 20),
            i.t("audio.scene_default"), self._gui, container=container
        )
        scene_inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(124, y, ew_a - 128, 22),
            initial_text=info.get("scene_default", ""),
            manager=self._gui, container=container
        )
        self._editor_widgets["scene_default"] = scene_inp
        y += 28

    def _save_editor(self):
        mid = self._selected_id
        if not mid:
            return
        info = get_audio(mid)
        if not info:
            return
        if "nombre" in self._editor_widgets:
            info["nombre"] = self._editor_widgets["nombre"].get_text()
        if "tipo" in self._editor_widgets:
            raw = self._editor_widgets["tipo"].selected_option
            if "|" in raw:
                info["tipo"] = raw.split("|")[0]
        if "asset_id" in self._editor_widgets:
            sel = self._editor_widgets["asset_id"].selected_option
            if sel and sel != "(sin assets)" and sel != "(sin asset)":
                info["asset_id"] = sel
        if "volumen" in self._editor_widgets:
            try:
                info["volumen"] = float(self._editor_widgets["volumen"].get_text())
            except ValueError:
                pass
        if "loop" in self._editor_widgets:
            info["loop"] = self._editor_widgets["loop"].is_checked
        if "scene_default" in self._editor_widgets:
            info["scene_default"] = self._editor_widgets["scene_default"].get_text()
        set_audio(mid, info)

    def _on_new(self):
        from editor.asset_data import get_assets
        assets = get_assets()
        bgm_assets = [k for k, v in assets.items() if v.get("tipo") in ("bgm", "sfx")]
        if not bgm_assets:
            default_asset = next(iter(assets.keys()), "sin_asset")
        else:
            default_asset = bgm_assets[0]
        n = 1
        while True:
            aid = f"audio_{n}"
            if get_audio(aid) is None:
                break
            n += 1
        add_audio(aid, default_asset, "bgm")
        self._selected_id = aid
        self._build_ui()

    def _on_delete(self):
        if self._selected_id:
            delete_audio(self._selected_id)
            self._selected_id = None
            self._build_ui()

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

        return True

    def draw(self, surface):
        if not self.visible:
            return
        r = self.get_abs_rect()
        pygame.draw.rect(surface, self.bg_color, r)
        self._gui.draw_ui(surface.subsurface(r))
        if self._descripcion:
            self.draw_descripcion(surface)

    def set_size(self, w, h):
        if self.rect.w != w or self.rect.h != h:
            self.rect.w = w
            self.rect.h = h
            self._gui.set_window_resolution((w, h))
            self._build_ui()
