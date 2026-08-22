import math
import os

import pygame

from editor.panels.base_panel import BasePanel
from editor.project import get_current_project
from editor.tools import BucketTool, EraserTool, EyedropperTool, PencilTool
from editor.tools.select import SelectTool
from editor.tools.shapes import ShapeTool
from editor.translation import I18n
from editor.widgets.canvas import Canvas
from editor.tileset import Tileset, clear_cache as clear_tileset_cache
from editor.sprite_file_io import (
    new_sprite as _io_new_sprite,
    load_sprite as _io_load_sprite,
    save_sprite as _io_save_sprite,
    do_save as _io_do_save,
    save_as_sprite as _io_save_as_sprite,
)

from editor.ui import Theme, get_font_manager, get_icon_factory
from editor.ui.widgets import (
    Button, IconButton, ToolButton, Panel, CollapsibleSection,
    VBox, HBox, Label, Dropdown, Slider, ColorPicker,
    PreviewViewport, StatusBar, Tooltip
)
from editor.ui.layout import DockLayout, Grid

CHECK_C1 = (45, 45, 50)
CHECK_C2 = (35, 35, 40)

SIZE_PRESETS = [
    ("20x20", 20, 20),
    ("40x40", 40, 40),
    ("60x60", 60, 60),
    ("80x80", 80, 80),
    ("128x128", 128, 128),
    ("160x120", 160, 120),
    ("256x192", 256, 192),
]
MAX_W, MAX_H = 256, 192


class SpriteEditorPanel(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(x, y, w, h, i18n)
        self.bg_color = Theme.get().bg
        self._current_path = None
        self._surface = None
        self._undo_stack = []
        self._redo_stack = []
        self._tile_rows = 1
        self._tile_cols = 1
        self._tileset = None
        self._tileset_mode = False
        self._selected_tile_index = 0
        self._dirty = False
        p = get_current_project()
        base_ts = p.tile_size if p else 20
        self._cut_cell_w = base_ts
        self._cut_cell_h = base_ts
        self._sprite_w = 20
        self._sprite_h = 20

        self._dock = None
        self._canvas = None
        self._workspace_header = None
        self._status_bar = None
        self._preview_viewport = None
        self._color_picker = None
        self._opacity_slider = None
        self._opacity_label = None
        self._size_btn = None
        self._size_dropdown = None
        self._cut_btn = None
        self._tileset_mode_btn = None
        self._load_tileset_btn = None
        self._tile_dropdown = None
        self._save_tile_btn = None
        self._exit_tileset_btn = None

        self._pencil = PencilTool()
        self._eraser = EraserTool()
        self._bucket = BucketTool()
        self._eyedropper = EyedropperTool()
        self._eyedropper.on_pick = self._on_eyedropper_pick
        self._shapes = ShapeTool()
        self._select = SelectTool()
        self._current_tool = self._pencil
        self._tool_buttons = {}
        self._shape_buttons = {}
        self._sym_buttons = {}
        self._sym_mode = "off"
        self._fill_btn = None
        self._tooltip = None
        self._tooltip_widgets = []

        self._build_ui()
        self._tooltip = Tooltip()

    def _get_tile_size(self):
        p = get_current_project()
        return p.tile_size if p else 20

    def _build_ui(self):
        self.clear()

        # Root DockLayout
        self._dock = DockLayout(left_width=110, right_width=138)
        self._dock.rect = self.rect
        self.add(self._dock)

        # LEFT - Tools panel
        self._build_tools_panel()

        # CENTER - Workspace
        self._build_workspace()

        # RIGHT - Preview + Toolbar
        self._build_right_panel()

        self._dock.layout()

    def set_size(self, w, h):
        old_w, old_h = self.rect.w, self.rect.h
        self.rect.w = w
        self.rect.h = h
        if self.rect.w != old_w or self.rect.h != old_h:
            if self._dock is not None:
                self._dock.rect = self.rect
                self._dock.layout()
            else:
                self._build_ui()

    def _build_tools_panel(self):
        theme = Theme.get()
        icons = get_icon_factory()

        tools_panel = Panel(0, 0, 110, self.rect.h, title=self.i18n.t("sprite.tools"))
        tools_panel.rect = pygame.Rect(0, 0, 110, self.rect.h)
        self._dock.set_left(tools_panel)

        # VBox for tools content with align="left" so buttons keep natural width
        tools_content = VBox(padding=theme.gap, gap=theme.gap, align="stretch")
        tools_content.rect.w = 110
        tools_content.parent = tools_panel
        tools_panel.add(tools_content)

        # Tool buttons - 2 columns x 3 rows (declarative, like CSS grid)
        tools_data = [
            (self._pencil, "pencil", self.i18n.t("sprite.pencil")),
            (self._eraser, "eraser", self.i18n.t("sprite.eraser")),
            (self._bucket, "bucket", self.i18n.t("sprite.bucket")),
            (self._eyedropper, "gotero", self.i18n.t("sprite.eyedropper")),
            (self._shapes, "shapes_rect", self.i18n.t("sprite.shapes")),
            (self._select, "select", self.i18n.t("sprite.select")),
        ]

        tools_grid = Grid(cols=2, gap=theme.gap, padding=theme.gap)
        tools_grid.parent = tools_content
        tools_content.add(tools_grid)

        self._tool_buttons = {}
        for tool_obj, icon_name, tooltip in tools_data:
            btn = ToolButton(0, 0, theme.control_h, icon_name,
                           callback=lambda t=tool_obj: self._set_tool(t),
                           group="tools", tooltip=tooltip)
            btn.parent = tools_grid
            tools_grid.add(btn)
            self._tool_buttons[tool_obj.id] = btn

        # Set initial tool
        self._tool_buttons[self._pencil.id].toggled = True

        # Color picker
        self._color_picker = ColorPicker(0, 0, 90, 220)
        self._color_picker.parent = tools_content
        tools_content.add(self._color_picker)

        # Opacity
        self._opacity_label = Label(0, 0, 90, 14, "", font_size=10, align="center")
        self._opacity_label.parent = tools_content
        tools_content.add(self._opacity_label)

        self._opacity_slider = Slider(0, 0, 90, 22, min_val=0, max_val=255, default=255)
        self._opacity_slider.parent = tools_content
        tools_content.add(self._opacity_slider)

        self._update_opacity_label()

        # Symmetry
        sym_lbl = Label(0, 0, 90, 14, "Simetría:", font_size=10, align="center")
        sym_lbl.parent = tools_content
        tools_content.add(sym_lbl)

        self._sym_buttons = {}
        self._sym_mode = "off"
        sym_modes = [
            ("off", "symmetry_h", "Off", "Simetría: Off"),
            ("horizontal", "symmetry_h", "H", "Simetría horizontal"),
            ("vertical", "symmetry_v", "V", "Simetría vertical"),
            ("both", "symmetry_h", "H+V", "Simetría H+V"),
        ]
        for mode, icon, label, tip in sym_modes:
            btn = ToolButton(0, 0, 22, icon,
                           callback=lambda m=mode: self._set_symmetry(m),
                           group="symmetry", tooltip=tip)
            btn.parent = tools_content
            tools_content.add(btn)
            self._sym_buttons[mode] = btn

        # Shape options
        shape_lbl = Label(0, 0, 90, 14, "Forma:", font_size=10, align="center")
        shape_lbl.parent = tools_content
        tools_content.add(shape_lbl)

        self._shape_buttons = {}
        shape_ops = [
            ("rect", "shapes_rect", "Rect", "Rectángulo"),
            ("ellipse", "shapes_ellipse", "Elip", "Elipse"),
            ("line", "shapes_line", "Line", "Línea"),
        ]
        for shp, icon, label, tip in shape_ops:
            btn = ToolButton(0, 0, 22, icon,
                           callback=lambda s=shp: self._set_shape(s),
                           group="shapes", tooltip=tip)
            btn.parent = tools_content
            tools_content.add(btn)
            self._shape_buttons[shp] = btn

        self._fill_btn = Button(0, 0, 90, 22, "Relleno",
                              callback=self._toggle_filled,
                              toggle=True, tooltip="Relleno / Borde")
        self._fill_btn.parent = tools_content
        tools_content.add(self._fill_btn)

        self._update_shape_options_visibility()
        self._update_opacity_label()

        # Collect all widgets with tooltips for hover tracking
        self._tooltip_widgets = (
            list(self._tool_buttons.values())
            + list(self._sym_buttons.values())
            + list(self._shape_buttons.values())
            + [self._fill_btn]
        )

    def _build_workspace(self):
        theme = Theme.get()

        # Workspace header (24px)
        self._workspace_header = Label(0, 0, 0, 24,
                                      "", font_size=11, align="left",
                                      color=theme.text)

        # Canvas fills remaining space
        self._canvas = Canvas(0, 0, 0, 0)
        self._canvas.set_tool(self._current_tool)

        # VBox container: header (fixed 24px) + canvas (weight=1)
        workspace_container = VBox(padding=0, gap=0)
        workspace_container.add(self._workspace_header)
        workspace_container.add(self._canvas)
        workspace_container.set_weight(self._canvas, 1)

        self._dock.set_center(workspace_container)

        self._update_workspace_header()

    def _build_right_panel(self):
        theme = Theme.get()
        icons = get_icon_factory()

        # Right panel container
        right_panel = Panel(0, 0, 138, self.rect.h, title="")
        right_panel.rect = pygame.Rect(0, 0, 138, self.rect.h)
        self._dock.set_right(right_panel)

        inner_w = 122
        left = 8
        gap = theme.gap

        # Section: Preview (top, collapsible)
        preview_section = CollapsibleSection(0, 0, 138, 0,
                                           title="Vista previa", expanded=True,
                                           icon="chevron_down")
        right_panel.add(preview_section)

        # Preview viewport (170px, 1:1 scale, centered, clipped)
        self._preview_viewport = PreviewViewport(
            left, 0, inner_w, 170,
            get_surface=lambda: self._surface,
            get_cut_cell=lambda: (self._cut_cell_w, self._cut_cell_h)
        )
        self._preview_viewport.parent = preview_section._content
        preview_section._content.add(self._preview_viewport)

        # Status strip (16px)
        self._status_bar = StatusBar(left, 0, inner_w, 16)
        self._status_bar.parent = preview_section._content
        preview_section._content.add(self._status_bar)

        # Section: File
        file_section = CollapsibleSection(0, 0, 138, 0,
                                        title="Archivo", expanded=True,
                                        icon="chevron_down")
        right_panel.add(file_section)

        for name, cb in [
            (self.i18n.t("sprite.new"), self._new_sprite),
            (self.i18n.t("sprite.open"), self._open_sprite),
            (self.i18n.t("sprite.save"), self._save_sprite),
            (self.i18n.t("sprite.save_as"), self._save_as_sprite),
        ]:
            btn = Button(0, 0, inner_w, 28, name, callback=cb)
            btn.parent = file_section._content
            file_section._content.add(btn)

        # Section: Tileset
        tileset_section = CollapsibleSection(0, 0, 138, 0,
                                           title="Tileset", expanded=False,
                                           icon="chevron_down")
        right_panel.add(tileset_section)

        self._tileset_mode_btn = Button(0, 0, inner_w, 28, "Modo Tileset",
                                      callback=self._toggle_tileset_mode)
        self._tileset_mode_btn.parent = tileset_section._content
        tileset_section._content.add(self._tileset_mode_btn)

        self._load_tileset_btn = Button(0, 0, inner_w, 28, "Cargar Tileset",
                                      callback=self._load_tileset)
        self._load_tileset_btn.parent = tileset_section._content
        self._load_tileset_btn.enabled = False
        tileset_section._content.add(self._load_tileset_btn)

        self._tile_dropdown = Dropdown(0, 0, inner_w, 28, [], self._on_tile_selected)
        self._tile_dropdown.parent = tileset_section._content
        self._tile_dropdown.visible = False
        tileset_section._content.add(self._tile_dropdown)

        self._save_tile_btn = Button(0, 0, inner_w, 28, "Guardar Tile",
                                   callback=self._save_tileset)
        self._save_tile_btn.parent = tileset_section._content
        self._save_tile_btn.visible = False
        tileset_section._content.add(self._save_tile_btn)

        self._exit_tileset_btn = Button(0, 0, inner_w, 28, "Salir Tileset",
                                      callback=self._exit_tileset_mode)
        self._exit_tileset_btn.parent = tileset_section._content
        self._exit_tileset_btn.visible = False
        tileset_section._content.add(self._exit_tileset_btn)

        # Section: Size
        size_section = CollapsibleSection(0, 0, 138, 0,
                                        title="Tamaño", expanded=True,
                                        icon="chevron_down")
        right_panel.add(size_section)

        self._size_btn = Button(0, 0, inner_w, 26, "",
                              callback=self._open_size_dropdown)
        self._size_btn.parent = size_section._content
        size_section._content.add(self._size_btn)

        self._size_dropdown = Dropdown(0, 0, inner_w, 26, self._size_options(),
                                     self._on_size_selected)
        self._size_dropdown.parent = size_section._content
        size_section._content.add(self._size_dropdown)

        # Section: View
        view_section = CollapsibleSection(0, 0, 138, 0,
                                        title="Vista", expanded=True,
                                        icon="chevron_down")
        right_panel.add(view_section)

        self._cut_btn = Button(0, 0, inner_w, 24, "Cortes: On",
                             callback=self._toggle_cut_lines)
        self._cut_btn.toggle = True
        self._cut_btn.toggled = True
        self._cut_btn.parent = view_section._content
        view_section._content.add(self._cut_btn)

        # Initial layout
        self._dock.layout()

        # Check if project has tileset
        p = get_current_project()
        if p and p.tileset:
            self._load_tileset_btn.enabled = True

        self._size_btn.text = f"{self._sprite_w}x{self._sprite_h}"
        self._update_cut_lines()
        self._update_workspace_header()

    def _size_options(self):
        opts = [(f"{w}x{h}", f"{w}x{h}") for (label, w, h) in SIZE_PRESETS]
        opts.append(("custom", "Personalizado..."))
        return opts

    def _open_size_dropdown(self):
        self._size_dropdown.open(8, self._size_btn.rect.y + self._size_btn.rect.h)

    def _on_size_selected(self, value):
        label = value[0] if isinstance(value, tuple) else value
        if label == "custom":
            self._prompt_custom_size()
            return
        for (vlabel, w, h) in SIZE_PRESETS:
            if vlabel == label:
                self._set_size(w, h)
                return

    def _prompt_custom_size(self):
        import tkinter as tk
        from tkinter import simpledialog
        root = tk.Tk()
        root.withdraw()
        try:
            w = simpledialog.askinteger("Tamaño", "Ancho (px):", initialvalue=self._sprite_w,
                                        minvalue=1, maxvalue=MAX_W)
            h = simpledialog.askinteger("Tamaño", "Alto (px):", initialvalue=self._sprite_h,
                                        minvalue=1, maxvalue=MAX_H)
        finally:
            root.destroy()
        if w and h:
            self._set_size(w, h)

    def _set_size(self, w, h):
        w = max(1, min(MAX_W, int(w)))
        h = max(1, min(MAX_H, int(h)))
        if self._sprite_w != w or self._sprite_h != h:
            self._dirty = True
        self._sprite_w = w
        self._sprite_h = h
        ts = self._get_tile_size()
        self._tile_rows = (h // ts) if h % ts == 0 else 0
        self._tile_cols = (w // ts) if w % ts == 0 else 0
        self._cut_cell_w, self._cut_cell_h = self._compute_cut_cell(w, h)
        self._update_cut_lines()
        self._size_btn.text = f"{w}x{h}"
        if self._surface is not None:
            old_w = self._surface.get_width()
            old_h = self._surface.get_height()
            if old_w != w or old_h != h:
                surf = pygame.Surface((w, h), pygame.SRCALPHA)
                surf.fill((0, 0, 0, 0))
                surf.blit(self._surface, (0, 0))
                self._surface = surf
                self._canvas.set_surface(self._surface)
                self._canvas.fit()
        self._dock.layout()

    def _compute_cut_cell(self, w, h):
        """Celda de corte para mostrar los tiles.

        - Si las dimensiones son múltiplos de tile_size -> celda tile_sizex tile_size (mapa).
        - Si no, el mayor divisor común cuadrado para división regular
          (ej: 256x192 -> 64x64).
        """
        ts = self._get_tile_size()
        if w % ts == 0 and h % ts == 0:
            return ts, ts
        g = math.gcd(w, h)
        if g >= 2:
            return g, g
        return w, h

    def _cut_grid(self):
        if not self._cut_cell_w or not self._cut_cell_h:
            return 0, 0
        return (self._sprite_h // self._cut_cell_h,
                self._sprite_w // self._cut_cell_w)

    def _toggle_cut_lines(self):
        show = not self._canvas._show_cut_lines
        self._canvas.set_show_cut_lines(show)
        self._cut_btn.text = "Cortes: On" if show else "Cortes: Off"

    def _set_symmetry(self, mode):
        self._sym_mode = mode
        for m, btn in self._sym_buttons.items():
            btn.toggled = (m == mode)
        self._pencil.set_symmetry(mode)
        self._eraser.set_symmetry(mode)
        self._canvas.set_symmetry(mode)

    def _update_cut_lines(self):
        lines = []
        rows, cols = self._cut_grid()
        if cols > 1:
            for ci in range(1, cols):
                x = ci * self._cut_cell_w
                lines.append(((x, 0), (x, self._sprite_h)))
        if rows > 1:
            for ri in range(1, rows):
                y = ri * self._cut_cell_h
                lines.append(((0, y), (self._sprite_w, y)))
        self._canvas.set_cut_lines(lines)

    def _update_opacity_label(self):
        pct = self._opacity_slider.value * 100 // 255
        self._opacity_label.text = f"{self.i18n.t('sprite.opacity')}: {pct}%"

    def _set_tool(self, tool):
        self._current_tool = tool
        if self._canvas:
            self._canvas.set_tool(tool)
        self._update_shape_options_visibility()
        if hasattr(tool, 'color') and self._color_picker:
            r, g, b = self._color_picker.selected_color[:3]
            tool.color = (r, g, b, self._opacity_slider.value)

    def _update_shape_options_visibility(self):
        show = self._current_tool is self._shapes
        for btn in self._shape_buttons.values():
            btn.visible = show
        self._fill_btn.visible = show

    def _set_shape(self, shape):
        self._shapes.set_shape(shape)
        for s, btn in self._shape_buttons.items():
            btn.toggled = (s == shape)

    def _toggle_filled(self):
        filled = not self._shapes.filled
        self._shapes.set_filled(filled)
        self._fill_btn.toggled = filled
        self._fill_btn.text = "Relleno" if filled else "Borde"

    def _select_tool(self, tool):
        self._set_tool(tool)
        for tid, btn in self._tool_buttons.items():
            if hasattr(btn, 'toggled'):
                btn.toggled = (tid == tool.id)

    def _on_eyedropper_pick(self, color):
        self._color_picker.selected_color = pygame.Color(color.r, color.g, color.b, 255)
        self._opacity_slider.value = color.a
        self._update_opacity_label()
        self._select_tool(self._pencil)

    def _toggle_tileset_mode(self):
        """Toggle between normal sprite editing and tileset editing mode."""
        if self._tileset_mode:
            self._exit_tileset_mode()
        else:
            p = get_current_project()
            if p and p.tileset:
                self._load_tileset()
            else:
                self._status_bar.set_text("Proyecto sin tileset")

    def _exit_tileset_mode(self):
        """Exit tileset editing mode and return to normal sprite editing."""
        self._tileset_mode = False
        self._tileset = None
        self._selected_tile_index = 0
        p = get_current_project()
        self._load_tileset_btn.enabled = p is not None and p.tileset
        self._load_tileset_btn.visible = True
        self._tile_dropdown.visible = False
        self._save_tile_btn.visible = False
        self._exit_tileset_btn.visible = False
        self._tileset_mode_btn.text = "Modo Tileset"
        self._status_bar.set_text("")

    def _load_tileset(self):
        """Load the project's tileset for editing."""
        p = get_current_project()
        if p and p.tileset:
            self._tileset = Tileset.load_from_project(p)
            if self._tileset:
                self._tileset_mode = True
                self._selected_tile_index = 0
                self._set_size(self._tileset.tile_size, self._tileset.tile_size)
                self._surface = self._tileset._tiles[0].copy() if self._tileset._tiles else pygame.Surface((self._tileset.tile_size, self._tileset.tile_size), pygame.SRCALPHA)
                self._canvas.set_surface(self._surface)
                self._canvas.fit()
                self._update_tile_selector()
                self._load_tileset_btn.enabled = True
                self._load_tileset_btn.visible = False
                self._tile_dropdown.visible = True
                self._save_tile_btn.visible = True
                self._exit_tileset_btn.visible = True
                self._tileset_mode_btn.text = "Modo Normal"
                self._status_bar.set_text(f"Tileset: {self._tileset.tile_count} tiles")
                return True
        return False

    def _update_tile_selector(self):
        """Update the tile index dropdown with tileset tile count."""
        if self._tileset and hasattr(self, '_tile_dropdown'):
            self._tile_dropdown.options = [(f"Tile {i}", f"Tile {i}") for i in range(self._tileset.tile_count)]
            self._tile_dropdown.select(0)

    def _on_tile_selected(self, value):
        """Handle tile index selection."""
        label = value[0] if isinstance(value, tuple) else value
        if label.startswith("Tile "):
            idx = int(label.split(" ")[1])
            self._selected_tile_index = idx
            self._load_tile_into_canvas(idx)

    def _load_tile_into_canvas(self, index):
        """Load a specific tile from tileset into the canvas for editing."""
        if self._tileset and 0 <= index < self._tileset.tile_count:
            tile = self._tileset.get_tile(index)
            if tile:
                self._surface = tile.copy()
                self._canvas.set_surface(self._surface)
                self._canvas.fit()
                self._dirty = False

    def _save_tileset(self):
        """Save the current canvas back to the tileset at the selected index."""
        if self._tileset and self._surface:
            # Update the tile in the tileset's internal list
            if 0 <= self._selected_tile_index < len(self._tileset._tiles):
                self._tileset._tiles[self._selected_tile_index] = self._surface.copy()
                # Save the full tileset image
                self._save_tileset_image()
                self._dirty = False
                return True
        return False

    def _save_tileset_image(self):
        """Reconstruct and save the full tileset PNG."""
        if not self._tileset:
            return
        # Create a new surface with the full tileset dimensions
        w = self._tileset.cols * self._tileset.tile_size
        h = self._tileset.rows * self._tileset.tile_size
        full = pygame.Surface((w, h), pygame.SRCALPHA)
        for i, tile in enumerate(self._tileset._tiles):
            if tile:
                c = i % self._tileset.cols
                r = i // self._tileset.cols
                full.blit(tile, (c * self._tileset.tile_size, r * self._tileset.tile_size))
        pygame.image.save(full, self._tileset.tileset_path)
        clear_tileset_cache()

    def _new_sprite(self):
        self._surface = _io_new_sprite(
            self._surface, self._canvas, self._sprite_w, self._sprite_h,
            self._status_bar, self._undo_stack, self._redo_stack,
        )
        self._current_path = None
        self._dirty = False
        self._update_workspace_header()

    def _open_sprite(self):
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.askopenfilename(
            initialdir=get_current_project().assets_path(),
            title=self.i18n.t("sprite.open"),
            filetypes=[("PNG files", "*.png")]
        )
        root.destroy()
        if path:
            self._load_sprite(os.path.basename(path), path)

    def _load_sprite(self, fname, full_path=None):
        surf, path = _io_load_sprite(
            fname, full_path, self._canvas, self._status_bar,
            self._undo_stack, self._redo_stack,
            None, self._set_size, self._update_workspace_header,
        )
        if surf is not None:
            self._surface = surf
            self._current_path = path
            self._dirty = False

    def _save_sprite(self):
        if self._surface is None:
            return
        if self._tileset_mode:
            self._save_tileset()
            self._status_bar.set_text("Tile guardado en tileset")
            return
        if self._current_path:
            self._do_save(self._current_path)
        else:
            import tkinter as tk
            from tkinter import filedialog
            root = tk.Tk()
            root.withdraw()
            path = filedialog.asksaveasfilename(
                initialdir=get_current_project().assets_path(),
                title=self.i18n.t("sprite.save"),
                defaultextension=".png",
                filetypes=[("PNG files", "*.png")]
            )
            root.destroy()
            if path:
                self._do_save(path)
                self._current_path = path
                self._status_bar.set_text(os.path.basename(path))
                self._update_workspace_header()

    def _do_save(self, path):
        _io_do_save(
            self._surface, path, self._tile_rows, self._tile_cols,
            self._cut_cell_w, self._cut_cell_h,
            self.i18n, self._status_bar, self._update_workspace_header,
        )
        self._dirty = False

    def _save_as_sprite(self):
        if self._surface is None:
            return
        result = _io_save_as_sprite(
            self._surface, self.i18n,
            None,
            lambda p: _io_do_save(self._surface, p, self._tile_rows, self._tile_cols,
                                  self._cut_cell_w, self._cut_cell_h,
                                  self.i18n, self._status_bar, self._update_workspace_header),
            self._status_bar,
        )
        if result:
            self._current_path = result

    def _clear_history(self):
        self._undo_stack.clear()
        self._redo_stack.clear()

    def _update_tooltip(self, pos):
        """Find hovered widget with tooltip and show it."""
        target = None
        for w in self._tooltip_widgets:
            if w.visible and w.enabled and w.tooltip and w.get_abs_rect().collidepoint(pos):
                target = w
                break
        if target:
            self._tooltip.show(target.tooltip, pos)
        else:
            self._tooltip.hide()

    def draw(self, surface):
        super().draw(surface)
        # Dropdowns encima de todo (z-order)
        if self._size_dropdown.is_open:
            self._size_dropdown.draw(surface)
        if self._tile_dropdown.is_open:
            self._tile_dropdown.draw(surface)
        # Tooltip always on top
        self._tooltip.draw(surface)

    def _update_workspace_header(self):
        """Update center panel header: sprite name + dirty (*) + dimensions."""
        name = os.path.basename(self._current_path) if self._current_path else self.i18n.t("sprite.new_name")
        dirty = "*" if self._dirty else ""
        dims = f"{self._sprite_w}x{self._sprite_h}"
        if self._tileset_mode and self._tileset:
            name = f"Tile {self._selected_tile_index} ({dims})"
            dirty = ""
        self._workspace_header.text = f"{name}{dirty}  [{dims}]"

    def _save_snapshot(self):
        if self._surface is None:
            return
        self._undo_stack.append(self._surface.copy())
        self._redo_stack.clear()
        if len(self._undo_stack) > 50:
            self._undo_stack.pop(0)
        self._dirty = True

    def _undo(self):
        if not self._undo_stack or self._surface is None:
            return
        self._redo_stack.append(self._surface.copy())
        self._surface = self._undo_stack.pop()
        self._canvas.set_surface(self._surface)

    def _redo(self):
        if not self._redo_stack or self._surface is None:
            return
        self._undo_stack.append(self._surface.copy())
        self._surface = self._redo_stack.pop()
        self._canvas.set_surface(self._surface)

    def handle_event(self, event):
        if not self.visible:
            return False

        # Tooltip tracking
        if event.type == pygame.MOUSEMOTION:
            self._update_tooltip(event.pos)
        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._tooltip.hide()

        # Save snapshot before any left click (for undo)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            self._save_snapshot()

        # Keyboard shortcuts for undo/redo + selection ops
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_z and (event.mod & pygame.KMOD_CTRL):
                if event.mod & pygame.KMOD_SHIFT:
                    self._redo()
                else:
                    self._undo()
                return True
            if event.key == pygame.K_y and (event.mod & pygame.KMOD_CTRL):
                self._redo()
                return True
            if self._current_tool is self._select:
                if event.key == pygame.K_ESCAPE:
                    self._select.cancel()
                    return True
                if event.key == pygame.K_DELETE or event.key == pygame.K_BACKSPACE:
                    if self._select.selection:
                        self._save_snapshot()
                        self._select.delete()
                        self._canvas._invalidate()
                    return True
                if event.mod & pygame.KMOD_CTRL:
                    if event.key == pygame.K_c:
                        if self._select.selection:
                            self._select.copy()
                        return True
                    if event.key == pygame.K_x:
                        if self._select.selection:
                            self._save_snapshot()
                            self._select.cut()
                            self._canvas._invalidate()
                        return True
                    if event.key == pygame.K_v:
                        if self._select.clipboard is not None:
                            self._select.paste()
                        return True
                return False

        # Sync color from color picker to tool (with opacity)
        if self._current_tool and self._color_picker:
            if hasattr(self._current_tool, 'color'):
                r, g, b = self._color_picker.selected_color[:3]
                self._current_tool.color = (r, g, b, self._opacity_slider.value)
        return super().handle_event(event)