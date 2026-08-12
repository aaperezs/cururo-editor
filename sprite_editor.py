import math
import os

import pygame

from editor.panels.base_panel import BasePanel
from editor.project import get_current_project
from editor.tools import BucketTool, EraserTool, EyedropperTool, PencilTool
from editor.tools.select import SelectTool
from editor.tools.shapes import ShapeTool
from editor.translation import I18n
from editor.widgets.button import Button
from editor.widgets.canvas import Canvas
from editor.widgets.color_picker import ColorPicker
from editor.widgets.dropdown import Dropdown
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.slider import Slider

CHECK_C1 = (45, 45, 50)
CHECK_C2 = (35, 35, 40)

TILE_W = 20
TILE_H = 20

# Tamaños predefinidos en píxeles (el editor es herramienta de creación libre)
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
        self.bg_color = (30, 32, 36)
        self._current_path = None
        self._surface = None
        self._undo_stack = []
        self._redo_stack = []
        self._tile_rows = 1
        self._tile_cols = 1
        self._cut_cell_w = TILE_W
        self._cut_cell_h = TILE_H
        self._sprite_w = 20
        self._sprite_h = 20

        self._build_ui()

    def _build_ui(self):
        self.clear()

        # Tool buttons panel (left)
        tool_panel = Panel(6, 6, 110, self.rect.h - 12, title=self.i18n.t("sprite.tools"))
        self.add(tool_panel)

        self._pencil = PencilTool()
        self._eraser = EraserTool()
        self._bucket = BucketTool()
        self._eyedropper = EyedropperTool()
        self._eyedropper.on_pick = self._on_eyedropper_pick
        self._shapes = ShapeTool()
        self._select = SelectTool()
        self._current_tool = self._pencil

        tools_data = [
            (self._pencil, self.i18n.t("sprite.pencil")),
            (self._eraser, self.i18n.t("sprite.eraser")),
            (self._bucket, self.i18n.t("sprite.bucket")),
            (self._eyedropper, self.i18n.t("sprite.eyedropper")),
            (self._shapes, self.i18n.t("sprite.shapes")),
            (self._select, self.i18n.t("sprite.select")),
        ]
        self._tool_buttons = {}
        ty = 24
        for tool_obj, tname in tools_data:
            btn = Button(10, ty, 90, 28, tname, callback=lambda t=tool_obj: self._set_tool(t))
            if tool_obj == self._current_tool:
                btn.toggle = True
                btn.toggled = True
            btn.parent = tool_panel
            self._tool_buttons[tool_obj.id] = btn
            self._add_tool_listener(tool_panel, btn, tool_obj)
            tool_panel.children.append(btn)
            ty += 36

        # Color picker
        self._color_picker = ColorPicker(10, ty + 10, 90, 200)
        self._color_picker.parent = tool_panel
        tool_panel.children.append(self._color_picker)

        # Opacity slider
        slider_y = ty + 10 + 200 + 10
        self._opacity_label = Label(10, slider_y, 90, 14, "", font_size=10, align="center")
        self._opacity_label.parent = tool_panel
        tool_panel.children.append(self._opacity_label)

        self._opacity_slider = Slider(10, slider_y + 14, 90, 22, min_val=0, max_val=255, default=255, label=self.i18n.t("sprite.opacity_short"))
        self._opacity_slider.parent = tool_panel
        tool_panel.children.append(self._opacity_slider)

        self._update_opacity_label()

        # Symmetry toggle
        sym_y = slider_y + 14 + 22 + 8
        sym_lbl = Label(10, sym_y, 90, 14, "Simetría:", font_size=10, align="center")
        sym_lbl.parent = tool_panel
        tool_panel.children.append(sym_lbl)
        sym_y += 16
        self._sym_buttons = {}
        self._sym_mode = "off"
        sym_modes = [
            ("off", "Off"),
            ("horizontal", "H"),
            ("vertical", "V"),
            ("both", "H+V"),
        ]
        for i, (mode, label) in enumerate(sym_modes):
            bx = 10 + (i % 2) * 46
            by = sym_y + (i // 2) * 26
            btn = Button(bx, by, 42, 22, label,
                         callback=lambda m=mode: self._set_symmetry(m))
            btn.toggle = True
            btn.toggled = (mode == "off")
            btn.parent = tool_panel
            tool_panel.children.append(btn)
            self._sym_buttons[mode] = btn

        # Shape options (rect / ellipse / line / filled)
        shape_y = sym_y + 2 * 26 + 10
        shape_lbl = Label(10, shape_y, 90, 14, "Forma:", font_size=10, align="center")
        shape_lbl.parent = tool_panel
        tool_panel.children.append(shape_lbl)
        self._shape_widgets = [shape_lbl]
        self._shape_buttons = {}
        shape_ops = [
            ("rect", "Rect"),
            ("ellipse", "Elip"),
            ("line", "Line"),
        ]
        for shp, label in shape_ops:
            bx = 10 + shape_ops.index((shp, label)) * 30
            btn = Button(bx, shape_y, 26, 22, label,
                         callback=lambda s=shp: self._set_shape(s))
            btn.toggle = True
            btn.toggled = (shp == "rect")
            btn.parent = tool_panel
            tool_panel.children.append(btn)
            self._shape_buttons[shp] = btn
            self._shape_widgets.append(btn)
        shape_y += 26
        self._fill_btn = Button(10, shape_y, 90, 22, "Relleno",
                                callback=self._toggle_filled)
        self._fill_btn.toggle = True
        self._fill_btn.toggled = False
        self._fill_btn.parent = tool_panel
        tool_panel.children.append(self._fill_btn)
        self._shape_widgets.append(self._fill_btn)
        self._update_shape_options_visibility()

        # Canvas (center)
        canvas_x = 122
        canvas_w = self.rect.w - canvas_x - 150
        canvas_h = self.rect.h - 12
        self._canvas = Canvas(canvas_x, 6, canvas_w, canvas_h)
        self._canvas.set_tool(self._current_tool)
        self.add(self._canvas)

        # Right panel (preview + file ops)
        right_panel = Panel(self.rect.w - 144, 6, 138, self.rect.h - 12, title=self.i18n.t("sprite.preview"))
        self.add(right_panel)

        self._new_btn = Button(8, 24, 122, 28, self.i18n.t("sprite.new"), callback=self._new_sprite)
        self._new_btn.parent = right_panel
        right_panel.children.append(self._new_btn)

        self._open_btn = Button(8, 58, 122, 28, self.i18n.t("sprite.open"), callback=self._open_sprite)
        self._open_btn.parent = right_panel
        right_panel.children.append(self._open_btn)

        self._save_btn = Button(8, 92, 122, 28, self.i18n.t("sprite.save"), callback=self._save_sprite)
        self._save_btn.parent = right_panel
        right_panel.children.append(self._save_btn)

        self._save_as_btn = Button(8, 126, 122, 28, self.i18n.t("sprite.save_as"), callback=self._save_as_sprite)
        self._save_as_btn.parent = right_panel
        right_panel.children.append(self._save_as_btn)

        # Size selector (dropdown con tamaños en px)
        y_off = 164
        szlbl = Label(8, y_off, 122, 16, "Tamaño:", font_size=11, align="center", color=(180, 190, 200))
        szlbl.parent = right_panel
        right_panel.children.append(szlbl)
        y_off += 18
        self._size_btn = Button(8, y_off, 122, 26, "", callback=self._open_size_dropdown)
        self._size_btn.parent = right_panel
        right_panel.children.append(self._size_btn)
        self._size_dropdown = Dropdown(8, y_off, 122, self._size_options(), self._on_size_selected)
        self._size_dropdown.parent = right_panel
        right_panel.children.append(self._size_dropdown)
        y_off += 44

        self._preview_label = Label(8, y_off, 122, 20, "", font_size=11, align="center")
        self._preview_label.parent = right_panel
        right_panel.children.append(self._preview_label)

        cut_btn_y = y_off + 24
        self._cut_btn = Button(8, cut_btn_y, 122, 24, "Cortes: On", callback=self._toggle_cut_lines)
        self._cut_btn.toggle = True
        self._cut_btn.toggled = True
        self._cut_btn.parent = right_panel
        right_panel.children.append(self._cut_btn)

        self._size_btn.text = f"{self._sprite_w}x{self._sprite_h}"
        self._right_content_bottom = cut_btn_y + self._cut_btn.rect.h
        self._update_cut_lines()

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
        self._sprite_w = w
        self._sprite_h = h
        self._tile_rows = (h // TILE_H) if h % TILE_H == 0 else 0
        self._tile_cols = (w // TILE_W) if w % TILE_W == 0 else 0
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

    def _compute_cut_cell(self, w, h):
        """Celda de corte para mostrar los tiles.

        - Si las dimensiones son múltiplos de 20 -> celda 20x20 (mapa).
        - Si no, el mayor divisor común cuadrado para división regular
          (ej: 256x192 -> 64x64).
        """
        if w % TILE_W == 0 and h % TILE_H == 0:
            return TILE_W, TILE_H
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

    def _add_tool_listener(self, panel, btn, tool):
        orig = btn.callback
        def wrapper():
            self._set_tool(tool)
            for child in panel.children:
                if isinstance(child, Button) and hasattr(child, 'toggled') and child != btn:
                    child.toggled = False
            btn.toggled = True
        btn.callback = wrapper

    def _set_tool(self, tool):
        self._current_tool = tool
        if self._canvas:
            self._canvas.set_tool(tool)
        self._update_shape_options_visibility()
        if hasattr(tool, 'color') and self._color_picker:
            r, g, b = self._color_picker.selected_color
            tool.color = (r, g, b, self._opacity_slider.value)

    def _update_shape_options_visibility(self):
        show = self._current_tool is self._shapes
        for w in getattr(self, "_shape_widgets", []):
            w.visible = show

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
        self._color_picker.selected_color = (color.r, color.g, color.b)
        self._opacity_slider.value = color.a
        self._update_opacity_label()
        self._select_tool(self._pencil)

    def _new_sprite(self):
        w = self._sprite_w
        h = self._sprite_h
        self._surface = pygame.Surface((w, h), pygame.SRCALPHA)
        self._surface.fill((0, 0, 0, 0))
        self._canvas.set_surface(self._surface)
        self._canvas.fit()
        self._current_path = None
        self._preview_label.text = "nuevo.png"
        self._clear_history()

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
        path = full_path or os.path.join(get_current_project().assets_path(), fname)
        if os.path.exists(path):
            try:
                img = pygame.image.load(path).convert_alpha()
                self._surface = pygame.Surface(img.get_size(), pygame.SRCALPHA)
                self._surface.blit(img, (0, 0))
                self._canvas.set_surface(self._surface)
                self._canvas.fit()
                self._current_path = path
                self._preview_label.text = fname
                self._clear_history()
                iw = img.get_width()
                ih = img.get_height()
                self._set_size(iw, ih)
            except pygame.error:
                pass

    def _save_sprite(self):
        if self._surface is None:
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
                self._preview_label.text = os.path.basename(path)

    def _do_save(self, path):
        pygame.image.save(self._surface, path)
        rows = self._tile_rows
        cols = self._tile_cols
        if rows > 1 or cols > 1:
            self._save_multi_tiles(path, rows, cols)
        self._preview_label.text = self.i18n.t("sprite.saved")

    def _save_multi_tiles(self, full_path, rows, cols):
        stem = os.path.splitext(os.path.basename(full_path))[0]
        assets_dir = os.path.dirname(full_path)
        tiles = []
        for r in range(rows):
            for c in range(cols):
                sub = self._surface.subsurface((c * TILE_W, r * TILE_H, TILE_W, TILE_H))
                sub_stem = f"{stem}_r{r}_c{c}"
                sub_path = os.path.join(assets_dir, f"{sub_stem}.png")
                pygame.image.save(sub, sub_path)
                tiles.append({"col": c, "row": r, "file": sub_stem, "z": 0, "behavior": "decorative"})
        from editor.sprite_registry import _BUILT_KEYS, _DYNAMIC_ENTRIES, _MERGED_NEEDS_REBUILD
        _DYNAMIC_ENTRIES[stem] = {
            "file": stem,
            "display": stem.replace("_", " ").title(),
            "char": None,
            "multi": True,
            "tiles": tiles,
        }
        _MERGED_NEEDS_REBUILD = True
        for t in tiles:
            if t["file"] not in _BUILT_KEYS:
                _DYNAMIC_ENTRIES[t["file"]] = {
                    "file": t["file"],
                    "display": t["file"].replace("_", " ").title(),
                    "char": None,
                }
        _MERGED_NEEDS_REBUILD = True

    def _save_as_sprite(self):
        if self._surface is None:
            return
        import tkinter as tk
        from tkinter import filedialog
        root = tk.Tk()
        root.withdraw()
        path = filedialog.asksaveasfilename(
            initialdir=get_current_project().assets_path(),
            title=self.i18n.t("sprite.save_as"),
            defaultextension=".png",
            filetypes=[("PNG files", "*.png")]
        )
        root.destroy()
        if path:
            self._do_save(path)
            self._current_path = path
            self._preview_label.text = os.path.basename(path)

    def _clear_history(self):
        self._undo_stack.clear()
        self._redo_stack.clear()

    def draw(self, surface):
        super().draw(surface)
        if self._surface is not None:
            self._draw_preview(surface)

        # Dropdown encima de todo (lista de tamaños sobre botones y preview)
        if self._size_dropdown.is_open:
            self._size_dropdown.draw(surface)

    def _draw_preview(self, surface):
        rp_abs_x = self.rect.x + self.rect.w - 144
        rp_abs_y = self.rect.y + 6

        preview_x = rp_abs_x + 8
        preview_y = rp_abs_y + self._right_content_bottom + 10

        # En un tileset multi-celda el preview muestra el primer tile
        # (la forma real en que se verá en el juego)
        rows, cols = self._cut_grid()
        if cols > 1 or rows > 1:
            tile_surf = self._surface.subsurface(
                (0, 0, self._cut_cell_w, self._cut_cell_h))
            sw = tile_surf.get_width()
            sh = tile_surf.get_height()
        else:
            tile_surf = self._surface
            sw = tile_surf.get_width()
            sh = tile_surf.get_height()

        # Label (dentro del area del preview, debajo de todos los botones)
        i18n = I18n.instancia()
        font = i18n.fuente(11) if i18n else pygame.font.SysFont("Arial", 11)
        label = font.render(f"Game: {sw}x{sh}", True, (180, 190, 200))
        surface.blit(label, (preview_x, preview_y))

        img_y = preview_y + 16

        # Escala para que quepa (soporta sprites hasta 256x192)
        avail_w = 122
        panel_bottom = self.rect.y + self.rect.h - 6
        avail_h = max(1, panel_bottom - img_y - 4)
        scale = min(avail_w / sw, avail_h / sh, 8.0)
        nw = max(1, int(sw * scale))
        nh = max(1, int(sh * scale))

        preview_w = nw
        preview_h = nh

        # Checkerboard background (escalado con un solo blit)
        checker = pygame.Surface((nw, nh), pygame.SRCALPHA)
        for py in range(0, nh, 4):
            for px in range(0, nw, 4):
                ck = CHECK_C1 if ((preview_x + px) // 4 + (img_y + py) // 4) % 2 == 0 else CHECK_C2
                checker.fill(ck, (px, py, min(4, nw - px), min(4, nh - py)))
        surface.blit(checker, (preview_x, img_y))

        # Primer tile escalado
        if nw == sw and nh == sh:
            scaled = tile_surf
        else:
            scaled = pygame.transform.smoothscale(tile_surf, (nw, nh))
        surface.blit(scaled, (preview_x, img_y))

        # Border
        pygame.draw.rect(surface, (100, 110, 120), (preview_x - 1, img_y - 1, preview_w + 2, preview_h + 2), 1)

    def _save_snapshot(self):
        if self._surface is None:
            return
        self._undo_stack.append(self._surface.copy())
        self._redo_stack.clear()
        if len(self._undo_stack) > 50:
            self._undo_stack.pop(0)

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
                r, g, b = self._color_picker.selected_color
                self._current_tool.color = (r, g, b, self._opacity_slider.value)
        return super().handle_event(event)
