import pygame
import os
import json
from editor.translation import I18n
from editor.panels.base_panel import BasePanel
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.event_editor_widget import EventEditorWidget, COL_BORDER, COL_ACCENT, COL_FIELD_BG
from editor.sprite_map import get_sprite_file
from editor.project import get_current_project
from levels.level_parser import LevelParser
from levels.level_manager import RUTA_MAPAS
from configs.constants import TAMANO_CELDA


def _stacks_dir():
    p = get_current_project()
    return p.stacks_path() if p else ""
CHAR_MAP_REVERSE = {v: k for k, v in LevelParser.CHAR_MAP.items() if v is not None}


class EventEditorPanel(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(x, y, w, h, i18n)
        self.bg_color = (30, 32, 36)

        self._current_map_id = None
        self._grid_data = {}
        self._map_ancho = 0
        self._map_alto = 0
        self._stacks = {}
        self._scroll_x = 0
        self._scroll_y = 0
        self._zoom = 1

        self._build_ui()

    def _build_ui(self):
        self.clear()

        # Toolbar
        toolbar = Panel(0, 0, self.rect.w, 36)
        self.add(toolbar)

        self._open_btn = Button(6, 4, 90, 28, self.i18n.t("map.open"), callback=self._open_map)
        self._open_btn.parent = toolbar
        toolbar.children.append(self._open_btn)

        self._save_btn = Button(102, 4, 90, 28, self.i18n.t("event.saved"), callback=self._save_stacks)
        self._save_btn.parent = toolbar
        toolbar.children.append(self._save_btn)

        self._map_label = Label(200, 4, 200, 28, "", font_size=13)
        self._map_label.parent = toolbar
        toolbar.children.append(self._map_label)

        # Mini-grid (left)
        self._minimap_x = 0
        self._minimap_y = 36
        self._minimap_w = 300
        self._minimap_h = self.rect.h - 36

        # Event editor (center-right)
        ew = self.rect.w - 310
        self._event_widget = EventEditorWidget(310, 36, ew, self.rect.h - 36, on_change=self._on_event_change)
        self.add(self._event_widget)

    def _on_event_change(self):
        pass

    def _open_map(self):
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            initialdir=RUTA_MAPAS,
            title=self.i18n.t("map.open"),
            filetypes=[("Map files", "*.txt")]
        )
        root.destroy()
        if path:
            map_id = os.path.splitext(os.path.basename(path))[0]
            self._current_map_id = map_id
            self._map_label.text = f"Mapa: {map_id}"
            self._load_map(map_id)
            self._load_stacks(map_id)

    def _load_map(self, map_id):
        path = os.path.join(RUTA_MAPAS, f"{map_id}.txt")
        try:
            with open(path, "r", encoding="utf-8") as f:
                text = f.read()
            parsed = LevelParser.parsear_mapa(text)
            self._grid_data = {}
            lines = [l.rstrip() for l in text.split("\n") if l.strip() and not l.startswith("# ")]
            for y, line in enumerate(lines):
                for x, char in enumerate(line):
                    if char in LevelParser.CHAR_MAP and LevelParser.CHAR_MAP[char] is not None:
                        self._grid_data[(x, y)] = char
            self._map_ancho = parsed["ancho"] // TAMANO_CELDA
            self._map_alto = parsed["alto"] // TAMANO_CELDA
        except FileNotFoundError:
            self._grid_data = {}
            self._map_ancho = 0
            self._map_alto = 0

    def _load_stacks(self, map_id):
        path = os.path.join(_stacks_dir(), f"{map_id}_stacks.json")
        if os.path.exists(path):
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._stacks = {}
                for s in data.get("stacks", []):
                    pos = tuple(s["pos"])
                    z = s.get("z", s.get("z_layer", 0))
                    eventos = s.get("eventos", [])
                    if not eventos and "capas" in s:
                        capas = s.get("capas", [])
                        if capas and "eventos" in capas[0]:
                            eventos = capas[0]["eventos"]
                    s["eventos"] = eventos
                    key = (pos[0], pos[1], z)
                    self._stacks[key] = s
            except (json.JSONDecodeError, KeyError):
                self._stacks = {}
        else:
            self._stacks = {}

    def _save_stacks(self):
        if not self._current_map_id:
            return
        sel = self._event_widget.selected_pos
        if sel is not None:
            z = self._event_widget.selected_z
            key = (sel[0], sel[1], z)
            if key in self._stacks:
                self._stacks[key]["eventos"] = self._event_widget.get_eventos()
            else:
                self._stacks[key] = {"pos": list(sel), "z": z, "eventos": self._event_widget.get_eventos()}

        stacks_list = []
        for key, data in self._stacks.items():
            entry = {"pos": [key[0], key[1]], "z": key[2]}
            if "eventos" in data:
                entry["eventos"] = data["eventos"]
            stacks_list.append(entry)
        path = os.path.join(_stacks_dir(), f"{self._current_map_id}_stacks.json")
        os.makedirs(_stacks_dir(), exist_ok=True)
        with open(path, "w", encoding="utf-8") as f:
            json.dump({"stacks": stacks_list}, f, indent=2, ensure_ascii=False)

    def set_selection(self, pos, z, sprite_id):
        """Called by map editor when a tile is selected with a specific z-layer"""
        self._event_widget.set_selection(pos, z, sprite_id)
        if pos is not None:
            key = (pos[0], pos[1], z)
            stack = self._stacks.get(key)
            eventos = stack.get("eventos", []) if stack else []
            self._event_widget.set_eventos(eventos)

    def handle_event(self, event):
        if not self.visible:
            return False

        # If the widget handled it, stop here (prevents double-handling from super())
        if self._event_widget.handle_event(event):
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            ar = self.get_abs_rect()
            mm_abs_x = ar.x + self._minimap_x
            mm_abs_y = ar.y + self._minimap_y
            if mm_abs_x <= mx <= mm_abs_x + self._minimap_w and my >= mm_abs_y:
                tile_size = 12
                gx = (mx - mm_abs_x) // tile_size
                gy = (my - mm_abs_y) // tile_size
                if 0 <= gx < self._map_ancho and 0 <= gy < self._map_alto:
                    char = self._grid_data.get((gx, gy))
                    z = 0
                    self._event_widget.set_selection((gx, gy), z, char)
                    key = (gx, gy, z)
                    stack = self._stacks.get(key)
                    eventos = stack.get("eventos", []) if stack else []
                    self._event_widget.set_eventos(eventos)
                    return True

        if event.type == pygame.MOUSEWHEEL:
            self._scroll_x += event.x * 20
            self._scroll_y -= event.y * 20
            return True

        return super().handle_event(event)

    def draw(self, surface):
        if not self.visible:
            return
        super().draw(surface)

        ar = self.get_abs_rect()

        # Mini-map (absolute coordinates)
        mm_rect = pygame.Rect(ar.x + self._minimap_x, ar.y + self._minimap_y, self._minimap_w, self._minimap_h)
        pygame.draw.rect(surface, (25, 28, 32), mm_rect)
        pygame.draw.rect(surface, (45, 50, 55), mm_rect, 1)

        if not self._grid_data:
            i18n = I18n.instancia()
            fuente = i18n.fuente(14) if i18n else pygame.font.SysFont("Arial", 14)
            txt = fuente.render(self.i18n.t("map.no_file"), True, (100, 100, 100))
            surface.blit(txt, (mm_rect.x + (mm_rect.w - txt.get_width()) // 2, mm_rect.y + (mm_rect.h - txt.get_height()) // 2))
            return

        tile_size = 12
        clip = surface.get_clip()
        surface.set_clip(mm_rect)

        for (gx, gy), char in self._grid_data.items():
            sx = mm_rect.x + gx * tile_size
            sy = mm_rect.y + gy * tile_size
            tipo = LevelParser.CHAR_MAP.get(char)
            if tipo:
                sprite = None
                try:
                    from utils.sprite_manager import obtener as obtener_sprite
                    sprite_file = get_sprite_file(tipo)
                    sprite = obtener_sprite(sprite_file) if sprite_file else None
                except Exception:
                    pass
                if sprite:
                    scaled = pygame.transform.scale(sprite, (tile_size, tile_size))
                    surface.blit(scaled, (sx, sy))
                else:
                    pygame.draw.rect(surface, COL_FIELD_BG, (sx, sy, tile_size, tile_size))
            else:
                pygame.draw.rect(surface, (40, 45, 52), (sx, sy, tile_size, tile_size))
            pygame.draw.rect(surface, COL_BORDER, (sx, sy, tile_size, tile_size), 1)

        # Highlight tiles with stacks (show once per position regardless of z)
        seen = set()
        for key in self._stacks:
            px, py = key[0], key[1]
            if (px, py) not in seen:
                seen.add((px, py))
                sx = mm_rect.x + px * tile_size
                sy = mm_rect.y + py * tile_size
                pygame.draw.rect(surface, COL_ACCENT, (sx, sy, tile_size, tile_size), 2)

        # Highlight selected
        sel = self._event_widget.selected_pos
        if sel:
            sx = mm_rect.x + sel[0] * tile_size
            sy = mm_rect.y + sel[1] * tile_size
            pygame.draw.rect(surface, COL_ACCENT, (sx, sy, tile_size, tile_size), 3)

        surface.set_clip(clip)
