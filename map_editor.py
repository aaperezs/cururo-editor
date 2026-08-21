import pygame
import os
import sys
import subprocess
from editor.translation import I18n
from editor.panels.base_panel import BasePanel
from editor.widgets.button import Button, make_icon
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.palette import EntityPalette
from editor.widgets.event_editor_widget import EventEditorWidget
from editor.widgets.scrollable import ScrollableArea
from editor.widgets.tab_bar import TabBar
from editor.widgets.layer_panel import LayerPanel
from editor.widgets.dialog import Dialog
from editor.sprite_map import get_sprite_file
from editor.sprite_registry import get_sprite_registry
from editor.elements import get_element, get_element_sprite_id, is_multi_tile_element
from editor.map_tab import MapTab
from editor.project import get_current_project
from editor.tileset import Tileset, clear_cache as clear_tileset_cache
from editor import workspace
from editor.common.parser import parsear_mapa
from editor.common.sprite_loader import obtener as obtener_sprite
from editor.map_model import (
    load_layer, save_layer, load_stacks, save_stacks,
    load_multi_tiles, save_multi_tiles, load_meta, save_meta,
    scan_spawn_from_grid,
)
from editor.map_viewport import MapViewport
from editor.map_tools import MapTools



def _maps_dir():
    p = get_current_project()
    return p.maps_path() if p else ""


def _stacks_dir():
    p = get_current_project()
    return p.stacks_path() if p else ""


class MapEditorPanel(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(x, y, w, h, i18n)
        self.bg_color = (30, 32, 36)

        self._tabs = {}
        self._tab_order = []
        self.viewport = MapViewport()
        self.tools = MapTools(get_element_fn=get_element)
        self._build_ui()

        p = get_current_project()
        if p and p.tileset:
            self._palette.set_mode("tileset")
        else:
            self._palette.set_mode("elements")

    @property
    def _current_tab(self):
        tid = self._map_tab_bar.get_active() if hasattr(self, "_map_tab_bar") else None
        return self._tabs.get(tid) if tid else None

    def _build_ui(self):
        self.clear()

        toolbar = Panel(0, 0, self.rect.w, 36)
        self.add(toolbar)

        self._new_btn = Button(6, 4, 60, 28, self.i18n.t("map.new"), callback=self._new_map)
        self._new_btn.parent = toolbar
        toolbar.children.append(self._new_btn)

        self._open_btn = Button(72, 4, 90, 28, self.i18n.t("map.open"), callback=self._open_map)
        self._open_btn.parent = toolbar
        toolbar.children.append(self._open_btn)

        self._save_btn = Button(168, 4, 90, 28, self.i18n.t("map.save"), callback=self._save_map)
        self._save_btn.parent = toolbar
        toolbar.children.append(self._save_btn)

        _ico_grid = make_icon("grid", 18)
        _grid_text = "" if _ico_grid else "Grid"
        gbtn = Button(268, 4, 32, 28, text=_grid_text, icon=_ico_grid, callback=self._toggle_grid)
        gbtn.parent = toolbar
        toolbar.children.append(gbtn)

        pbtn = Button(304, 4, 24, 28, "+", callback=self._zoom_in)
        pbtn.parent = toolbar
        toolbar.children.append(pbtn)

        mbtn = Button(332, 4, 24, 28, "-", callback=self._zoom_out)
        mbtn.parent = toolbar
        toolbar.children.append(mbtn)

        self._zoom_label = Label(360, 4, 50, 28, "100%", font_size=12)
        self._zoom_label.parent = toolbar
        toolbar.children.append(self._zoom_label)

        _ico_play = make_icon("play", 18)
        _play_text = "▶ Test" if not _ico_play else ""
        self._test_btn = Button(420, 4, 32, 28, text=_play_text, icon=_ico_play, callback=self._launch_game)
        self._test_btn.parent = toolbar
        toolbar.children.append(self._test_btn)

        self._folder_btn = Button(456, 4, 70, 28, "Carpeta", callback=self._select_project_folder)
        self._folder_btn.parent = toolbar
        toolbar.children.append(self._folder_btn)

        resize_x = 610
        self._resize_btn = Button(resize_x, 4, 60, 28, self.i18n.t("map.resize"), callback=self._resize_map)
        self._resize_btn.parent = toolbar
        toolbar.children.append(self._resize_btn)

        _ico_tileset = make_icon("grid", 18)
        _tileset_text = "Tileset" if not _ico_tileset else ""
        self._tileset_btn = Button(resize_x + 66, 4, 32, 28, text=_tileset_text, icon=_ico_tileset, callback=self._toggle_tileset_mode)
        self._tileset_btn.parent = toolbar
        toolbar.children.append(self._tileset_btn)

        # Tool selector buttons with icons
        _ico_sel = make_icon("select", 18)
        _ico_era = make_icon("eraser", 18)
        _ico_buc = make_icon("bucket", 18)
        _ico_drag = make_icon("drag", 18)
        tx = resize_x + 102  # After tileset button (66 + 36)
        self._tool_sel_btn = Button(tx, 4, 32, 28, icon=_ico_sel, callback=self._set_tool_select)
        self._tool_sel_btn.parent = toolbar
        toolbar.children.append(self._tool_sel_btn)
        self._tool_era_btn = Button(tx + 36, 4, 32, 28, icon=_ico_era, callback=self._set_tool_eraser)
        self._tool_era_btn.parent = toolbar
        toolbar.children.append(self._tool_era_btn)
        self._tool_buc_btn = Button(tx + 72, 4, 32, 28, icon=_ico_buc, callback=self._set_tool_bucket)
        self._tool_buc_btn.parent = toolbar
        toolbar.children.append(self._tool_buc_btn)
        _drag_text = "" if _ico_drag else "↕"
        self._tool_drag_btn = Button(tx + 108, 4, 32, 28, text=_drag_text, icon=_ico_drag, callback=self._set_tool_drag)
        self._tool_drag_btn.parent = toolbar
        toolbar.children.append(self._tool_drag_btn)

        dw, dh = 300, 220
        self._new_dialog = Dialog(
            (self.rect.w - dw) // 2, (self.rect.h - dh) // 2, dw, dh,
            title=self.i18n.t("map.new_title"),
        )
        self._new_dialog.build(
            fields=[
                (self.i18n.t("map.width"), "40", 4, True),
                (self.i18n.t("map.height"), "30", 4, True),
            ],
            accept_text=self.i18n.t("dialog.accept"),
            cancel_text=self.i18n.t("dialog.cancel"),
            accept_callback=self._new_map_confirm,
        )

        self._resize_dialog = Dialog(
            (self.rect.w - dw) // 2, (self.rect.h - dh) // 2, dw, dh,
            title=self.i18n.t("map.resize_title"),
        )
        self._resize_dialog.build(
            fields=[
                (self.i18n.t("map.width"), "", 4, True),
                (self.i18n.t("map.height"), "", 4, True),
            ],
            accept_text=self.i18n.t("dialog.accept"),
            cancel_text=self.i18n.t("dialog.cancel"),
            accept_callback=self._resize_map_confirm,
        )

        tb_y = 36
        tb_h = 26
        self._map_tab_bar = TabBar(0, tb_y, self.rect.w, tb_h, on_close_tab=self._close_tab)
        self.add(self._map_tab_bar)

        left_w = 130
        palette_h = 170  # Reduced to fit tool buttons inside palette
        content_y = tb_y + tb_h

        self._palette = EntityPalette(0, content_y, left_w, palette_h)
        self.add(self._palette)

        lpnl_y = content_y + palette_h
        lpnl_h = self.rect.h - lpnl_y
        self._layer_panel = LayerPanel(0, lpnl_y, left_w, lpnl_h)
        self._layer_panel.set_callbacks(
            on_change_active=self._on_layer_change_active,
            on_toggle=self._on_layer_toggle,
            on_opacity=self._on_layer_opacity,
            on_add_layer=self._on_add_layer,
            on_remove_layer=self._on_remove_layer,
        )
        self.add(self._layer_panel)

        ew = 280
        self._event_widget = EventEditorWidget(
            self.rect.w - ew, content_y, ew, self.rect.h - content_y,
            on_set_spawn=self._on_set_spawn,
            on_clear_spawn=self._on_clear_spawn,
            on_change=self._on_event_change,
        )
        self.add(self._event_widget)

        sx = left_w
        sy = content_y
        sw = self.rect.w - sx - ew
        sh = self.rect.h - content_y
        self._scroll_area = ScrollableArea(sx, sy, sw, sh, draw_callback=self._draw_grid)
        self.add(self._scroll_area)
        self._update_tool_buttons()

        # Restore existing tabs in the new tab bar after rebuild (resize, etc.)
        if self._tab_order:
            first = self._tab_order[0]
            for tid in self._tab_order:
                tab = self._tabs.get(tid)
                if tab:
                    self._map_tab_bar.add_tab(tid, tab.label(), dirty=tab.dirty, closeable=True)
            self._map_tab_bar.set_active_by_id(first)
            self._sync_ui()
            self._update_content_size()

    def _tile_size(self):
        return self.viewport.tile_size

    def _update_content_size(self):
        tab = self._current_tab
        if not tab:
            self._scroll_area.set_content(0, 0)
            return
        self.viewport.update_content_size(tab, self._scroll_area)

    def _get_multi_tile_dims(self, element_id):
        el = get_element(element_id)
        if not el or not el.get("multi_tile"):
            return 1, 1
        props = el.get("properties", {})
        return props.get("tile_rows", 1), props.get("tile_cols", 1)

    def _paint_multi_tile(self, tab, ls, gx, gy, element_id):
        from editor.map_model import paint_multi_tile
        return paint_multi_tile(tab, ls, gx, gy, element_id, get_element)

    def _is_multi_tile_anchor(self, tab, gx, gy, z):
        from editor.map_model import is_multi_tile_anchor
        return is_multi_tile_anchor(tab, gx, gy, z, get_element)

    def _erase_multi_tile(self, tab, ls, anchor_key):
        from editor.map_model import erase_multi_tile
        erase_multi_tile(tab, ls, anchor_key, get_element)

    def _zoom_in(self):
        self.viewport.zoom_in()
        self._zoom_label.text = self.viewport.zoom_label()
        self._update_content_size()

    def _zoom_out(self):
        self.viewport.zoom_out()
        self._zoom_label.text = self.viewport.zoom_label()
        self._update_content_size()

    def _toggle_grid(self):
        self.viewport.show_grid = not self.viewport.show_grid

    def _launch_game(self):
        """Lanza el runtime del proyecto actual en un proceso separado"""
        tab = self._current_tab
        if tab and tab.map_id and not tab.map_id.startswith("_new_"):
            self._save_map()
        p = get_current_project()
        if not p:
            print("[EDITOR] No hay proyecto seleccionado")
            return
        if getattr(sys, "frozen", False):
            meipass = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
            runtime = os.path.join(meipass, "orm", "main.py")
            cwd = os.path.dirname(sys.executable)
            cmd = [sys.executable, "--runtime", "--project", p.root]
        else:
            src = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            runtime = os.path.join(src, "orm", "main.py")
            cwd = src
            cmd = [sys.executable, runtime, "--project", p.root]
        if not os.path.exists(runtime):
            print(f"[EDITOR] No se encuentra el runtime en {runtime}")
            return
        try:
            subprocess.Popen(
                cmd,
                cwd=cwd,
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0
            )
            print(f"[EDITOR] Juego lanzado para {p.root}")
        except Exception as e:
            print(f"[EDITOR] Error lanzando juego: {e}")

    def _select_project_folder(self):
        """Abre un diálogo para seleccionar la carpeta del proyecto"""
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        folder = filedialog.askdirectory(
            title="Seleccionar carpeta del proyecto Orm",
            initialdir=get_current_project().root
        )
        root.destroy()
        if folder:
            if os.path.exists(os.path.join(folder, "main.py")):
                get_current_project().root = folder
                self._folder_btn.text = os.path.basename(folder)
                print(f"[EDITOR] Carpeta del proyecto: {folder}")
            else:
                print(f"[EDITOR] No se encuentra main.py en {folder}")

    def _new_map(self):
        self._new_dialog.rect.x = (self.rect.w - 300) // 2
        self._new_dialog.rect.y = (self.rect.h - 220) // 2
        self._new_dialog.show()

    def _new_map_confirm(self):
        fields = self._new_dialog._fields
        if len(fields) >= 2:
            w = fields[0]["input"].get_value()
            h = fields[1]["input"].get_value()
            w = max(5, min(200, w if w > 0 else 40))
            h = max(5, min(200, h if h > 0 else 30))

            tab = MapTab(map_id=None)
            tab.layers[0].ancho = w
            tab.layers[0].alto = h
            tab.layers[0].visible = True
            tab.layers[0].opacity = 100

            uid = f"_new_{id(tab)}"
            tab.map_id = uid
            self._tabs[uid] = tab
            self._tab_order.append(uid)
            self._map_tab_bar.add_tab(uid, tab.label(), dirty=False, closeable=True)
            self._map_tab_bar.set_active_by_id(uid)
            self.viewport.zoom = 1.0
            self._zoom_label.text = self.viewport.zoom_label()
            self._layer_panel.sync_layers(tab.layer_order)
            self._sync_ui()
            self._update_content_size()
            self._event_widget.set_selection(None, 0, None)

        self._new_dialog.visible = False

    def _resize_map(self):
        """Abre el diálogo para redimensionar el mapa actual"""
        tab = self._current_tab
        if not tab:
            return
        w = max((ls.ancho for ls in tab.layers.values()), default=40)
        h = max((ls.alto for ls in tab.layers.values()), default=30)
        fields = self._resize_dialog._fields
        if len(fields) >= 2:
            fields[0]["input"].set_value(str(w))
            fields[1]["input"].set_value(str(h))
        self._resize_dialog.rect.x = (self.rect.w - 300) // 2
        self._resize_dialog.rect.y = (self.rect.h - 220) // 2
        self._resize_dialog.show()

    def _resize_map_confirm(self):
        """Redimensiona el mapa con las nuevas dimensiones"""
        fields = self._resize_dialog._fields
        if len(fields) >= 2:
            nuevo_w = fields[0]["input"].get_value()
            nuevo_h = fields[1]["input"].get_value()
            nuevo_w = max(5, min(200, nuevo_w if nuevo_w > 0 else 40))
            nuevo_h = max(5, min(200, nuevo_h if nuevo_h > 0 else 30))

            tab = self._current_tab
            if not tab:
                self._resize_dialog.visible = False
                return

            tab.push_undo()

            for z, ls in tab.layers.items():
                old_w = ls.ancho
                old_h = ls.alto
                # Crop tiles that fall outside the new bounds
                if nuevo_w < old_w or nuevo_h < old_h:
                    ls.grid = {
                        (gx, gy): sid
                        for (gx, gy), sid in ls.grid.items()
                        if gx < nuevo_w and gy < nuevo_h
                    }
                ls.ancho = nuevo_w
                ls.alto = nuevo_h
            # Clean up multi_tiles outside new bounds
            for key in list(tab.multi_tiles.keys()):
                gx, gy, z = key
                if gx >= nuevo_w or gy >= nuevo_h:
                    del tab.multi_tiles[key]

            self._sync_ui()
            self._update_content_size()
            self._map_tab_bar.set_tab_label(tab.map_id, tab.label(), dirty=tab.dirty)

        self._resize_dialog.visible = False

    def _open_map(self):
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            initialdir=_maps_dir(),
            title=self.i18n.t("map.open"),
            filetypes=[("Map files", "*.txt *.json"), ("Text maps", "*.txt"), ("JSON maps", "*.json")]
        )
        root.destroy()
        if path:
            map_id = os.path.splitext(os.path.basename(path))[0]
            self._load_map_into_tab(map_id)

    def _load_map_into_tab(self, map_id):
        if map_id in self._tabs:
            self._map_tab_bar.set_active_by_id(map_id)
            self._sync_ui()
            self._update_content_size()
            return

        tab = MapTab(map_id=map_id)

        def _try_load_layer(z):
            result = load_layer(map_id, z, _maps_dir())
            if result is None:
                return False
            grid, ancho, alto = result
            if z not in tab.layers:
                tab.layers[z] = tab.layers[0].__class__()
            tab.layers[z].grid = grid
            tab.layers[z].ancho = ancho
            tab.layers[z].alto = alto
            return True

        # Load Z=0 first to get base dimensions
        if _try_load_layer(0):
            tab.layers[0].visible = True
            tab.layers[0].opacity = 100
        else:
            tab.layers[0].ancho = 40
            tab.layers[0].alto = 30
            tab.layers[0].visible = True
            tab.layers[0].opacity = 100

        # Scan and load any existing z-layer files (z1..z4)
        for z in range(1, 5):
            if _try_load_layer(z):
                tab.layers[z].visible = True
                tab.layers[z].opacity = 100

        # Load stacks
        tab.stacks = load_stacks(map_id, _stacks_dir())

        # Load multi_tiles
        tab.multi_tiles = load_multi_tiles(map_id, _maps_dir())

        # Load meta (spawn point, etc.)
        meta = load_meta(map_id, _maps_dir())
        if meta:
            tab.spawn_pos = meta.get("spawn_pos")
            tab.spawn_z = meta.get("spawn_z", 0)

        # If no spawn from meta, scan grid for 'inicio' sprite (legacy maps)
        if not tab.spawn_pos:
            spawn_pos, spawn_z = scan_spawn_from_grid(tab)
            if spawn_pos:
                tab.spawn_pos = spawn_pos
                tab.spawn_z = spawn_z

        self._tabs[map_id] = tab
        self._tab_order.append(map_id)
        self._map_tab_bar.add_tab(map_id, tab.label(), dirty=False, closeable=True)
        self._map_tab_bar.set_active_by_id(map_id)
        self.viewport.zoom = 1.0
        self._zoom_label.text = self.viewport.zoom_label()
        self._layer_panel.sync_layers(tab.layer_order)
        self._sync_ui()
        self._update_content_size()
        self._event_widget.set_selection(None, 0, None)
        self._save_workspace()

    def get_workspace_data(self):
        data = {
            "open_tabs": list(self._tab_order),
            "active_tab": self._map_tab_bar.get_active(),
        }
        tabs_data = {}
        for tid, tab in self._tabs.items():
            tabs_data[tid] = {
                "active_z": tab.active_z,
                "spawn_pos": list(tab.spawn_pos) if tab.spawn_pos else None,
                "spawn_z": tab.spawn_z,
                "zoom": self.viewport.zoom,
                "scroll_x": getattr(self._scroll_area, "scroll_x", 0),
                "scroll_y": getattr(self._scroll_area, "scroll_y", 0),
            }
        data["tabs"] = tabs_data
        return data

    def restore_workspace(self, maps_data):
        if not maps_data:
            return
        for tab_id in maps_data.get("open_tabs", []):
            if tab_id not in self._tabs:
                self._load_map_into_tab(tab_id)
        # Restore per-tab state
        for tid, tdata in maps_data.get("tabs", {}).items():
            tab = self._tabs.get(tid)
            if tab:
                tab.active_z = tdata.get("active_z", 0)
                sp = tdata.get("spawn_pos")
                tab.spawn_pos = tuple(sp) if sp else None
                tab.spawn_z = tdata.get("spawn_z", 0)
        # Restore active tab
        active = maps_data.get("active_tab")
        if active and active in self._tabs:
            self._map_tab_bar.set_active_by_id(active)
            # Restore zoom/scroll for active tab
            tdata = maps_data.get("tabs", {}).get(active, {})
            self.viewport.zoom = tdata.get("zoom", 1)
            self._scroll_area.scroll_x = tdata.get("scroll_x", 0)
            self._scroll_area.scroll_y = tdata.get("scroll_y", 0)
        self._sync_ui()
        self._update_content_size()

    def _save_workspace(self):
        from editor import workspace as ws
        data = {"maps": self.get_workspace_data()}
        ws.save_workspace(data)

    def _close_tab(self, tab_id):
        if tab_id in self._tabs:
            del self._tabs[tab_id]
            self._map_tab_bar.remove_tab(tab_id)
            if tab_id in self._tab_order:
                self._tab_order.remove(tab_id)
            self._sync_ui()
            self._update_content_size()
            self._save_workspace()

    def _sync_ui(self):
        self._update_tool_buttons()
        self._sprite_cache = {}
        tab = self._current_tab
        if tab:
            self._layer_panel.sync_state(tab)
            self._layer_panel.set_active_z(tab.active_z)
            self._layer_panel.sync_layers(tab.layer_order)
            self._layer_panel.sync_layers(tab.layer_order)
            self._event_widget.set_spawn(tab.spawn_pos, tab.spawn_z)
            # Sync event widget with current selection (filter by active z)
            pos = self._event_widget.selected_pos
            if pos:
                key = (pos[0], pos[1], tab.active_z)
                data = tab.stacks.get(key)
                evs = data.get("eventos", []) if data else []
                self._event_widget.set_eventos(evs)

    def _grid_to_json(self, grid, ancho, alto):
        from editor.map_model import grid_to_json
        return grid_to_json(grid, ancho, alto)

    def _json_to_grid(self, text):
        from editor.map_model import json_to_grid
        return json_to_grid(text)

    def _save_map(self):
        tab = self._current_tab
        if not tab:
            return

        map_id = tab.map_id
        if not map_id or map_id.startswith("_new_"):
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            path = filedialog.asksaveasfilename(
                initialdir=_maps_dir(),
                title=self.i18n.t("app.save_as"),
                defaultextension=".json",
                filetypes=[("JSON maps", "*.json"), ("Text maps", "*.txt")]
            )
            root.destroy()
            if not path:
                return
            new_id = os.path.splitext(os.path.basename(path))[0]
            old_id = tab.map_id
            tab.map_id = new_id
            self._tabs[new_id] = self._tabs.pop(old_id)
            if old_id in self._tab_order:
                self._tab_order.remove(old_id)
            self._tab_order.append(new_id)
            self._map_tab_bar.remove_tab(old_id)
            self._map_tab_bar.add_tab(new_id, tab.label(), dirty=False, closeable=True)
            self._map_tab_bar.set_active_by_id(new_id)
            map_id = new_id

        # Save widget eventos back to tab.stacks before writing
        sel = self._event_widget.selected_pos
        if sel:
            z = self._event_widget.selected_z
            key = (sel[0], sel[1], z)
            if key in tab.stacks:
                tab.stacks[key]["eventos"] = self._event_widget.get_eventos()
            else:
                tab.stacks[key] = {"pos": list(sel), "z": z, "eventos": self._event_widget.get_eventos()}

        # Save each layer
        for z, ls in tab.layers.items():
            save_layer(map_id, z, ls, _maps_dir())

        # Save stacks
        save_stacks(map_id, tab.stacks, _stacks_dir())

        # Save multi_tiles
        save_multi_tiles(map_id, tab.multi_tiles, _maps_dir())

        # Scan spawn from grid and save meta
        spawn_pos, spawn_z = scan_spawn_from_grid(tab)
        if spawn_pos:
            tab.spawn_pos = spawn_pos
            tab.spawn_z = spawn_z
        elif tab.spawn_pos:
            ls = tab.layers.get(tab.spawn_z)
            if not ls or ls.grid.get(tab.spawn_pos) != "inicio":
                tab.spawn_pos = None
                tab.spawn_z = 0
        save_meta(map_id, tab.spawn_pos, tab.spawn_z, _maps_dir())

        tab.dirty = False
        self._map_tab_bar.set_tab_label(map_id, tab.label(), dirty=False)

    def _on_layer_change_active(self, z):
        tab = self._current_tab
        if tab:
            tab.active_z = z
            self._layer_panel.set_active_z(z)
            # Reselect event widget with new active z and reload events
            pos = self._event_widget.selected_pos
            self._event_widget.set_selection(pos, z, None)
            if pos:
                key = (pos[0], pos[1], z)
                data = tab.stacks.get(key)
                evs = data.get("eventos", []) if data else []
                self._event_widget.set_eventos(evs)

    def _on_layer_toggle(self, z):
        tab = self._current_tab
        if tab and z in tab.layers:
            tab.push_undo()
            tab.layers[z].visible = not tab.layers[z].visible
            self._layer_panel.sync_state(tab)
            self._map_tab_bar.set_tab_label(tab.map_id, tab.label(), dirty=tab.dirty)

    def _on_layer_opacity(self, z, value):
        tab = self._current_tab
        if tab and z in tab.layers:
            tab.layers[z].opacity = value
            self._layer_panel.sync_state(tab)

    def _on_add_layer(self):
        tab = self._current_tab
        if not tab:
            return
        tab.push_undo()
        new_z = tab.add_layer()
        if new_z is None:
            return
        tab.active_z = new_z
        self._layer_panel.set_active_z(new_z)
        self._layer_panel.sync_state(tab)
        self._map_tab_bar.set_tab_label(tab.map_id, tab.label(), dirty=tab.dirty)

    def _on_remove_layer(self, z):
        tab = self._current_tab
        if not tab:
            return
        tab.push_undo()
        if tab.remove_layer(z):
            self._layer_panel.set_active_z(tab.active_z)
            self._layer_panel.sync_state(tab)
            self._sync_ui()
            self._map_tab_bar.set_tab_label(tab.map_id, tab.label(), dirty=tab.dirty)

    def _on_set_spawn(self, pos, z):
        tab = self._current_tab
        if tab:
            tab.push_undo()
            tab.spawn_pos = pos
            tab.spawn_z = z
            self._event_widget.set_spawn(pos, z)
            self._map_tab_bar.set_tab_label(tab.map_id, tab.label(), dirty=tab.dirty)

    def _on_clear_spawn(self):
        tab = self._current_tab
        if tab and tab.spawn_pos:
            tab.push_undo()
            tab.spawn_pos = None
            tab.spawn_z = 0
            self._event_widget.set_spawn(None, 0)
            self._map_tab_bar.set_tab_label(tab.map_id, tab.label(), dirty=tab.dirty)

    def _on_event_change(self):
        tab = self._current_tab
        if not tab:
            return
        tab.dirty = True
        self._map_tab_bar.set_tab_label(tab.map_id, tab.label(), dirty=True)
        sel = self._event_widget.selected_pos
        if sel:
            z = self._event_widget.selected_z
            key = (sel[0], sel[1], z)
            if key in tab.stacks:
                tab.stacks[key]["eventos"] = self._event_widget.get_eventos()
            else:
                tab.stacks[key] = {"pos": list(sel), "z": z, "eventos": self._event_widget.get_eventos()}

    def _set_tool_select(self):
        self._palette.tool = "select"
        self._update_tool_buttons()

    def _set_tool_eraser(self):
        self._palette.tool = "eraser"
        self._palette.selected_sprite_id = None
        self._update_tool_buttons()

    def _set_tool_bucket(self):
        self._palette.tool = "bucket"
        self._update_tool_buttons()

    def _set_tool_drag(self):
        self._palette.tool = "drag"
        self._palette.selected_sprite_id = None
        self._drag_source = None
        self._update_tool_buttons()

    def _toggle_tileset_mode(self):
        """Toggle palette between elements and tileset mode."""
        if self._palette.mode == "elements":
            p = get_current_project()
            if p and p.tileset:
                self._palette.set_mode("tileset")
            else:
                return
        else:
            self._palette.set_mode("elements")
        self._update_tileset_button()

    def _update_tileset_button(self):
        """Update the tileset mode button appearance."""
        self._tileset_btn.toggled = (self._palette.mode == "tileset")

    def _update_tool_buttons(self):
        tool = getattr(self._palette, 'tool', 'select')
        self._tool_sel_btn.toggle = True
        self._tool_era_btn.toggle = True
        self._tool_buc_btn.toggle = True
        self._tool_drag_btn.toggle = True
        self._tool_sel_btn.toggled = (tool == 'select')
        self._tool_era_btn.toggled = (tool == 'eraser')
        self._tool_buc_btn.toggled = (tool == 'bucket')
        self._tool_drag_btn.toggled = (tool == 'drag')
        self._update_tileset_button()

    def _screen_to_grid(self, mx, my):
        sa = self._scroll_area
        vp = sa.viewport_rect()
        return self.viewport.screen_to_grid(mx, my, vp)

    def _start_paint_drag(self, mx, my, button):
        tab = self._current_tab
        if not tab:
            return False
        vp = self._scroll_area.viewport_rect()
        if not vp.collidepoint(mx, my):
            return False
        gx, gy = self._screen_to_grid(mx, my)
        ls = tab.layers.get(tab.active_z)
        if not ls or gx < 0 or gx >= ls.ancho or gy < 0 or gy >= ls.alto:
            return False

        tool = getattr(self._palette, 'tool', 'select')

        # Tool: BUCKET (single click, no drag)
        if button == 1 and tool == 'bucket':
            tab.push_undo()
            self._flood_fill(tab, ls, gx, gy)
            tab.dirty = True
            self._map_tab_bar.set_tab_label(tab.map_id, tab.label(), dirty=True)
            return True

        tab.push_undo()
        self._paint_dragging = True
        self._drag_button = button
        self._last_paint_pos = (gx, gy)

        # Tool: ERASER (left click = erase, drag continues erasing)
        if button == 1 and tool == 'eraser':
            anchor = self._is_multi_tile_anchor(tab, gx, gy, tab.active_z)
            if anchor:
                self._erase_multi_tile(tab, ls, anchor)
            else:
                self._erase_tile(tab, ls, gx, gy)

        if button == 1 and self._palette.selected_sprite_id is not None:
            selected = self._palette.selected_sprite_id
            if is_multi_tile_element(selected):
                self._paint_multi_tile(tab, ls, gx, gy, selected)
            else:
                ls.grid[(gx, gy)] = selected
            self._event_widget.set_selection((gx, gy), tab.active_z, selected)
            if selected == "inicio":
                tab.spawn_pos = (gx, gy)
                tab.spawn_z = tab.active_z
                self._event_widget.set_spawn((gx, gy), tab.active_z)
        elif button == 3:
            anchor = self._is_multi_tile_anchor(tab, gx, gy, tab.active_z)
            if anchor:
                self._erase_multi_tile(tab, ls, anchor)
            else:
                self._erase_tile(tab, ls, gx, gy)
        elif button == 1:
            # Click without sprite selected: just select
            self._event_widget.set_selection((gx, gy), tab.active_z, ls.grid.get((gx, gy)))

        tab.dirty = True
        self._map_tab_bar.set_tab_label(tab.map_id, tab.label(), dirty=True)
        return True

    def _erase_tile(self, tab, ls, gx, gy):
        from editor.map_model import erase_tile
        if erase_tile(tab, ls, gx, gy):
            self._event_widget.set_spawn(tab.spawn_pos, tab.spawn_z)
            self._event_widget.set_selection(None, tab.active_z, None)

    def _flood_fill(self, tab, ls, gx, gy):
        from editor.map_model import flood_fill
        replacement = self._palette.selected_sprite_id
        if replacement is None:
            return
        modified = flood_fill(ls, gx, gy, replacement)
        for cx, cy in modified:
            if replacement == "inicio":
                tab.spawn_pos = (cx, cy)
                tab.spawn_z = tab.active_z
                self._event_widget.set_spawn((cx, cy), tab.active_z)

    def _paint_drag_to(self, mx, my):
        tab = self._current_tab
        if not tab:
            return
        vp = self._scroll_area.viewport_rect()
        if not vp.collidepoint(mx, my):
            return
        gx, gy = self._screen_to_grid(mx, my)
        ls = tab.layers.get(tab.active_z)
        if not ls or gx < 0 or gx >= ls.ancho or gy < 0 or gy >= ls.alto:
            return
        if self._last_paint_pos == (gx, gy):
            return

        # Interpolate tiles between last pos and current pos
        lx, ly = self._last_paint_pos
        dx = gx - lx
        dy = gy - ly
        steps = max(abs(dx), abs(dy))
        tool = getattr(self._palette, 'tool', 'select')
        if steps > 0:
            for i in range(1, steps + 1):
                ix = lx + int(dx * i / steps)
                iy = ly + int(dy * i / steps)
                if 0 <= ix < ls.ancho and 0 <= iy < ls.alto:
                    # Eraser tool drag
                    if self._drag_button == 1 and tool == 'eraser':
                        anchor = self._is_multi_tile_anchor(tab, ix, iy, tab.active_z)
                        if anchor:
                            self._erase_multi_tile(tab, ls, anchor)
                        else:
                            self._erase_tile(tab, ls, ix, iy)
                        tab.dirty = True
                    # Normal paint drag
                    elif self._drag_button == 1 and self._palette.selected_sprite_id is not None:
                        selected = self._palette.selected_sprite_id
                        if is_multi_tile_element(selected):
                            self._paint_multi_tile(tab, ls, ix, iy, selected)
                        else:
                            ls.grid[(ix, iy)] = selected
                        if selected == "inicio":
                            tab.spawn_pos = (ix, iy)
                            tab.spawn_z = tab.active_z
                            self._event_widget.set_spawn((ix, iy), tab.active_z)
                        tab.dirty = True
                    elif self._drag_button == 3:
                        anchor = self._is_multi_tile_anchor(tab, ix, iy, tab.active_z)
                        if anchor:
                            self._erase_multi_tile(tab, ls, anchor)
                        elif (ix, iy) in ls.grid:
                            if ls.grid[(ix, iy)] == "inicio" and tab.spawn_pos == (ix, iy):
                                tab.spawn_pos = None
                                tab.spawn_z = 0
                                self._event_widget.set_spawn(None, 0)
                            del ls.grid[(ix, iy)]
                            tab.dirty = True

        self._last_paint_pos = (gx, gy)

    def _stop_paint_drag(self):
        self._paint_dragging = False
        self._last_paint_pos = None
        tab = self._current_tab
        if tab:
            self._map_tab_bar.set_tab_label(tab.map_id, tab.label(), dirty=tab.dirty)

    def handle_event(self, event):
        if not self.visible:
            return False

        if self._new_dialog.visible:
            return self._new_dialog.handle_event(event)

        if self._resize_dialog.visible:
            return self._resize_dialog.handle_event(event)

        # Paint/erase dragging — handle before anything else
        if self._paint_dragging:
            if event.type == pygame.MOUSEMOTION:
                self._paint_drag_to(*event.pos)
                return True
            if event.type == pygame.MOUSEBUTTONUP and event.button == self._drag_button:
                self._stop_paint_drag()
                return True

        # Undo/redo
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z and pygame.key.get_mods() & pygame.KMOD_CTRL:
                tab = self._current_tab
                if tab and tab.undo():
                    self._map_tab_bar.set_tab_label(tab.map_id, tab.label(), dirty=True)
                    self._sync_ui()
                return True
            if event.key == pygame.K_y and pygame.key.get_mods() & pygame.KMOD_CTRL:
                tab = self._current_tab
                if tab and tab.redo():
                    self._map_tab_bar.set_tab_label(tab.map_id, tab.label(), dirty=True)
                    self._sync_ui()
                return True

        if self._map_tab_bar.handle_event(event):
            self._sync_ui()
            self._update_content_size()
            self._scroll_area.scroll_x = 0
            self._scroll_area.scroll_y = 0
            return True

        if self._layer_panel.handle_event(event):
            return True

        if self._palette.handle_event(event):
            return True

        if self._event_widget.handle_event(event):
            return True

        if self._scroll_area.handle_event(event):
            return True

        # Start paint/erase drag
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            tool = getattr(self._palette, 'tool', 'select')
            if tool == 'drag':
                if self._handle_drag_click(mx, my):
                    return True
            elif self._palette.selected_sprite_id is not None or tool in ('eraser', 'bucket'):
                if self._start_paint_drag(mx, my, 1):
                    return True
            if self._handle_map_click(mx, my):
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            mx, my = event.pos
            if self._drag_source is not None:
                self._drag_source = None
                self._event_widget.set_selection(None, 0, None)
                return True
            if self._start_paint_drag(mx, my, 3):
                return True
            if self._handle_map_right_click(mx, my):
                return True

        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_PLUS, pygame.K_EQUALS):
                self._zoom_in()
                return True
            elif event.key == pygame.K_MINUS:
                self._zoom_out()
                return True

        return super().handle_event(event)

    def _handle_map_click(self, mx, my):
        tab = self._current_tab
        if not tab:
            return False

        vp = self._scroll_area.viewport_rect()
        if not vp.collidepoint(mx, my):
            return False

        gx, gy = self._screen_to_grid(mx, my)
        if gx is None:
            return False

        ls = tab.layers.get(tab.active_z)
        if not ls:
            return False

        if gx < 0 or gx >= ls.ancho or gy < 0 or gy >= ls.alto:
            return False

        if self._palette.selected_sprite_id is not None:
            tab.push_undo()
            selected = self._palette.selected_sprite_id
            if is_multi_tile_element(selected):
                self._paint_multi_tile(tab, ls, gx, gy, selected)
            else:
                ls.grid[(gx, gy)] = selected
            self._event_widget.set_selection((gx, gy), tab.active_z, selected)
            # Auto-set spawn when placing inicio sprite
            if selected == "inicio":
                tab.spawn_pos = (gx, gy)
                tab.spawn_z = tab.active_z
                self._event_widget.set_spawn((gx, gy), tab.active_z)
        else:
            self._event_widget.set_selection((gx, gy), tab.active_z, ls.grid.get((gx, gy)))
        # Sync eventos (filter by active z)
        evs = tab.stacks.get((gx, gy, tab.active_z), {}).get("eventos", [])
        self._event_widget.set_eventos(evs)

        self._map_tab_bar.set_tab_label(tab.map_id, tab.label(), dirty=tab.dirty)
        return True

    def _handle_drag_click(self, mx, my):
        """Arrastrar: click origen -> pick up, click destino -> place (mismo Z)"""
        tab = self._current_tab
        if not tab:
            return False
        vp = self._scroll_area.viewport_rect()
        if not vp.collidepoint(mx, my):
            return False
        gx, gy = self._screen_to_grid(mx, my)
        if gx is None:
            return False
        ls = tab.layers.get(tab.active_z)
        if not ls or gx < 0 or gx >= ls.ancho or gy < 0 or gy >= ls.alto:
            return False

        if self._drag_source is None:
            # Pick up: guardar origen
            sid = ls.grid.get((gx, gy))
            if sid is None:
                return False
            # Block drag for multi-tile cells
            if self._is_multi_tile_anchor(tab, gx, gy, tab.active_z):
                return False
            self._drag_source = (gx, gy, sid, tab.active_z)
            self._event_widget.set_selection((gx, gy), tab.active_z, sid)
            evs = tab.stacks.get((gx, gy, tab.active_z), {}).get("eventos", [])
            self._event_widget.set_eventos(evs)
            return True

        # Place: mover sprite + eventos de origen a destino
        sx, sy, sid, sz = self._drag_source
        if sz != tab.active_z:
            # Solo se permite mover en la misma capa
            return False
        if sx == gx and sy == gy:
            # Click en el mismo tile -> cancelar seleccion
            self._drag_source = None
            return True

        tab.push_undo()

        # Mover sprite en el grid
        ls.grid[(gx, gy)] = sid
        del ls.grid[(sx, sy)]

        # Limpiar spawn si se movio el inicio
        if sid == "inicio" and tab.spawn_pos == (sx, sy):
            tab.spawn_pos = (gx, gy)
            tab.spawn_z = tab.active_z

        # Mover eventos en tab.stacks
        src_key = (sx, sy, tab.active_z)
        dst_key = (gx, gy, tab.active_z)
        if src_key in tab.stacks:
            tab.stacks[dst_key] = tab.stacks.pop(src_key)
            tab.stacks[dst_key]["pos"] = [gx, gy]

        self._drag_source = None
        self._event_widget.set_selection((gx, gy), tab.active_z, sid)
        evs = tab.stacks.get(dst_key, {}).get("eventos", [])
        self._event_widget.set_eventos(evs)
        tab.dirty = True
        self._map_tab_bar.set_tab_label(tab.map_id, tab.label(), dirty=True)
        return True

    def _handle_map_right_click(self, mx, my):
        tab = self._current_tab
        if not tab:
            return False

        vp = self._scroll_area.viewport_rect()
        if not vp.collidepoint(mx, my):
            return False

        gx, gy = self._screen_to_grid(mx, my)
        if gx is None:
            return False

        ls = tab.layers.get(tab.active_z)
        if not ls:
            return False

        if gx < 0 or gx >= ls.ancho or gy < 0 or gy >= ls.alto:
            return False

        anchor = self._is_multi_tile_anchor(tab, gx, gy, tab.active_z)
        if anchor:
            tab.push_undo()
            self._erase_multi_tile(tab, ls, anchor)
            self._event_widget.set_selection(None, tab.active_z, None)
            self._map_tab_bar.set_tab_label(tab.map_id, tab.label(), dirty=tab.dirty)
        elif (gx, gy) in ls.grid:
            erased_sid = ls.grid[(gx, gy)]
            tab.push_undo()
            del ls.grid[(gx, gy)]
            # Clear spawn if the erased tile was the spawn point
            if erased_sid == "inicio" and tab.spawn_pos == (gx, gy):
                tab.spawn_pos = None
                tab.spawn_z = 0
                self._event_widget.set_spawn(None, 0)
            self._event_widget.set_selection(None, tab.active_z, None)
            self._map_tab_bar.set_tab_label(tab.map_id, tab.label(), dirty=tab.dirty)
        return True

    def _draw_grid(self, surface, vp_x, vp_y, scroll_x, scroll_y):
        tab = self._current_tab
        if not tab:
            return

        ts = self._tile_size()
        gr = pygame.Rect(vp_x, vp_y, self._scroll_area.viewport_rect().w, self._scroll_area.viewport_rect().h)

        # Cache for sprite resolution: sprite_id -> surface
        if not hasattr(self, '_sprite_cache') or not hasattr(self, '_sprite_cache_zoom') or self._sprite_cache_zoom != self.viewport.zoom:
            self._sprite_cache = {}
            self._sprite_cache_zoom = self.viewport.zoom

        # Cache for tileset: tileset index -> surface
        if not hasattr(self, '_tileset_cache') or not hasattr(self, '_tileset_cache_zoom') or self._tileset_cache_zoom != self.viewport.zoom:
            self._tileset_cache = {}
            self._tileset_cache_zoom = self.viewport.zoom

        # Get tileset if available
        tileset = None
        p = get_current_project()
        if p and p.tileset:
            tileset = Tileset.load_from_project(p)

        # Render visible layers bottom-up (lowest Z first)
        for z in tab.layer_order:
            ls = tab.layers.get(z)
            if not ls or not ls.visible or ls.opacity <= 0:
                continue

            alpha = max(1, int(ls.opacity * 2.55))

            for (gx, gy), sprite_id in ls.grid.items():
                sx = vp_x + gx * ts - scroll_x
                sy = vp_y + gy * ts - scroll_y
                if sx + ts < gr.x or sx > gr.x + gr.w or sy + ts < gr.y or sy > gr.y + gr.h:
                    continue

                # Handle tileset tiles
                if sprite_id.startswith("tileset:") and tileset:
                    try:
                        tile_index = int(sprite_id.split(":", 1)[1])
                        if tile_index not in self._tileset_cache:
                            tile_surf = tileset.get_tile(tile_index)
                            if tile_surf:
                                scaled = pygame.transform.scale(tile_surf, (ts, ts))
                                if alpha < 255:
                                    scaled.set_alpha(alpha)
                                self._tileset_cache[tile_index] = scaled
                            else:
                                self._tileset_cache[tile_index] = None
                        cached = self._tileset_cache.get(tile_index)
                        if isinstance(cached, pygame.Surface):
                            surface.blit(cached, (sx, sy))
                        continue
                    except (ValueError, IndexError):
                        pass

                # Resolve sprite_id: element_id → sprite_id → file (cached)
                if sprite_id not in self._sprite_cache:
                    actual_sprite_id = sprite_id
                    from editor.elements import _ELEMENTOS_DATA
                    el = _ELEMENTOS_DATA.get(sprite_id)
                    if el:
                        esp_id = el.get("sprite_id")
                        if esp_id:
                            actual_sprite_id = esp_id
                    info = get_sprite_registry().get(actual_sprite_id)
                    if not info:
                        info = get_sprite_registry().get(sprite_id)
                    sprite_file = info["file"] if info else None
                    sprite = obtener_sprite(sprite_file) if sprite_file else None
                    if sprite:
                        scaled = pygame.transform.scale(sprite, (ts, ts))
                        if alpha < 255:
                            scaled.set_alpha(alpha)
                        self._sprite_cache[sprite_id] = scaled
                    else:
                        col = (80, 80, 90) if info else (50, 55, 60)
                        self._sprite_cache[sprite_id] = col

                cached = self._sprite_cache.get(sprite_id)
                if isinstance(cached, pygame.Surface):
                    surface.blit(cached, (sx, sy))
                elif cached is not None:
                    if alpha < 255:
                        s = pygame.Surface((ts, ts), pygame.SRCALPHA)
                        s.fill((*cached, alpha))
                        surface.blit(s, (sx, sy))
                    else:
                        pygame.draw.rect(surface, cached, (sx, sy, ts, ts))

                if self._show_grid and ts >= 8:
                    pygame.draw.rect(surface, (45, 48, 52), (sx, sy, ts, ts), 1)

        # Selection overlay (on active layer)
        sel = self._event_widget.selected_pos
        if sel:
            sx = vp_x + sel[0] * ts - scroll_x
            sy = vp_y + sel[1] * ts - scroll_y
            pygame.draw.rect(surface, (255, 200, 50), (sx, sy, ts, ts), 3)

        # Ghost preview for multi-tile placement
        if self._palette.selected_sprite_id and is_multi_tile_element(self._palette.selected_sprite_id):
            mx, my = pygame.mouse.get_pos()
            if gr.collidepoint(mx, my):
                rows, cols = self._get_multi_tile_dims(self._palette.selected_sprite_id)
                ghost_gx = (mx - vp_x + scroll_x) // ts
                ghost_gy = (my - vp_y + scroll_y) // ts
                for r in range(rows):
                    for c in range(cols):
                        gsx = vp_x + (ghost_gx + c) * ts - scroll_x
                        gsy = vp_y + (ghost_gy + r) * ts - scroll_y
                        pygame.draw.rect(surface, (100, 200, 255, 80), (gsx, gsy, ts, ts), 2)

# Ghost sprite while dragging (follows cursor)
        if self._drag_source is not None:
            mx, my = pygame.mouse.get_pos()
            gr = pygame.Rect(vp_x, vp_y, self._scroll_area.viewport_rect().w,
                             self._scroll_area.viewport_rect().h)
            if gr.collidepoint(mx, my):
                ghost_gx = (mx - vp_x + scroll_x) // ts
                ghost_gy = (my - vp_y + scroll_y) // ts
                gsx = vp_x + ghost_gx * ts - scroll_x
                gsy = vp_y + ghost_gy * ts - scroll_y
                ghost_sid = self._drag_source[2]
                ghost_surf = None
                if ghost_sid.startswith("tileset:") and tileset:
                    try:
                        tile_index = int(ghost_sid.split(":", 1)[1])
                        if tile_index in self._tileset_cache:
                            ghost_surf = self._tileset_cache[tile_index]
                        else:
                            tile_surf = tileset.get_tile(tile_index)
                            if tile_surf:
                                ghost_surf = pygame.transform.scale(tile_surf, (ts, ts))
                                self._tileset_cache[tile_index] = ghost_surf
                    except (ValueError, IndexError):
                        pass
                elif ghost_sid in self._sprite_cache:
                    ghost_surf = self._sprite_cache[ghost_sid]
                if isinstance(ghost_surf, pygame.Surface):
                    ghost_surf.set_alpha(100)
                    surface.blit(ghost_surf, (gsx, gsy))
                    ghost_surf.set_alpha(255)
                pygame.draw.rect(surface, (100, 200, 255), (gsx, gsy, ts, ts), 2)

    def draw(self, surface):
        if not self.visible:
            return
        super().draw(surface)

        tab = self._current_tab
        if not tab:
            vp = self._scroll_area.viewport_rect()
            i18n = I18n.instancia()
            fuente = i18n.fuente(16) if i18n else pygame.font.SysFont("Arial", 16)
            txt = fuente.render(i18n.t("map.no_file"), True, (100, 100, 100))
            surface.blit(txt, (vp.x + (vp.w - txt.get_width()) // 2, vp.y + (vp.h - txt.get_height()) // 2))
        else:
            sel = self._event_widget.selected_pos
            if sel:
                key = (sel[0], sel[1], tab.active_z)
                stack = tab.stacks.get(key)
                if stack:
                    vp = self._scroll_area.viewport_rect()
                    i18n = I18n.instancia()
                    fuente = i18n.fuente(11) if i18n else pygame.font.SysFont("Arial", 11)
                    evs = stack.get("eventos", [])
                    txt = fuente.render(f"Z={tab.active_z} Stack: {len(evs)} eventos", True, (255, 200, 80))
                    surface.blit(txt, (vp.x + 6, vp.y + vp.h - 18))

        if self._new_dialog.visible:
            self._new_dialog.draw(surface)

        if self._resize_dialog.visible:
            self._resize_dialog.draw(surface)
