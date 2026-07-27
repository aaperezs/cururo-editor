import pygame
import os
from editor.translation import I18n
from editor.project import get_current_project
from editor.panels.base_panel import BasePanel
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.canvas import Canvas
from editor.widgets.color_picker import ColorPicker
from editor.widgets.slider import Slider
from editor.tools import PencilTool, EraserTool, BucketTool, EyedropperTool
from editor.sprite_registry import get_sprite_registry, sprite_registry_reload

CHECK_C1 = (45, 45, 50)
CHECK_C2 = (35, 35, 40)

TILE_W = 20
TILE_H = 20

MULTI_SIZES = [
    (1, 1, "1x1"),
    (1, 2, "1x2"),
    (2, 1, "2x1"),
    (2, 2, "2x2"),
]

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
        self._current_tool = self._pencil

        tools_data = [
            (self._pencil, self.i18n.t("sprite.pencil")),
            (self._eraser, self.i18n.t("sprite.eraser")),
            (self._bucket, self.i18n.t("sprite.bucket")),
            (self._eyedropper, self.i18n.t("sprite.eyedropper")),
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

        # Size selector
        y_off = 164
        szlbl = Label(8, y_off, 122, 16, "Tamaño:", font_size=11, align="center", color=(180, 190, 200))
        szlbl.parent = right_panel
        right_panel.children.append(szlbl)
        y_off += 18
        self._size_btns = {}
        for i, (r, c, label) in enumerate(MULTI_SIZES):
            bx = 8 + (i % 2) * 62
            by = y_off + (i // 2) * 30
            btn = Button(bx, by, 58, 26, label,
                         callback=lambda rr=r, cc=c: self._set_multi_size(rr, cc))
            btn.toggle = True
            btn.parent = right_panel
            right_panel.children.append(btn)
            self._size_btns[(r, c)] = btn
        # Default: 1x1 selected
        self._set_multi_size(1, 1)

        self._preview_label = Label(8, y_off + 64, 122, 20, "", font_size=11, align="center")
        self._preview_label.parent = right_panel
        right_panel.children.append(self._preview_label)

        # Cut-line toggle
        cut_btn_y = y_off + 88
        self._cut_btn = Button(8, cut_btn_y, 122, 24, "Cortes: On", callback=self._toggle_cut_lines)
        self._cut_btn.toggle = True
        self._cut_btn.toggled = True
        self._cut_btn.parent = right_panel
        right_panel.children.append(self._cut_btn)

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
        if self._tile_cols > 1:
            x = TILE_W * self._tile_cols
            lines.append(((TILE_W, 0), (TILE_W, TILE_H * self._tile_rows)))
        if self._tile_rows > 1:
            y = TILE_H * self._tile_rows
            lines.append(((0, TILE_H), (TILE_W * self._tile_cols, TILE_H)))
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
        if hasattr(tool, 'color') and self._color_picker:
            r, g, b = self._color_picker.selected_color
            tool.color = (r, g, b, self._opacity_slider.value)

    def _select_tool(self, tool):
        self._set_tool(tool)
        for tid, btn in self._tool_buttons.items():
            if hasattr(btn, 'toggled'):
                btn.toggled = (tid == tool.id)

    def _set_multi_size(self, rows, cols):
        self._tile_rows = rows
        self._tile_cols = cols
        self._update_cut_lines()
        for (r, c), btn in self._size_btns.items():
            btn.toggled = (r == rows and c == cols)
        if self._surface is not None:
            old_w = self._surface.get_width()
            old_h = self._surface.get_height()
            new_w = cols * TILE_W
            new_h = rows * TILE_H
            if old_w != new_w or old_h != new_h:
                surf = pygame.Surface((new_w, new_h), pygame.SRCALPHA)
                surf.fill((0, 0, 0, 0))
                surf.blit(self._surface, (0, 0))
                self._surface = surf
                self._canvas.set_surface(self._surface)

    def _on_eyedropper_pick(self, color):
        self._color_picker.selected_color = (color.r, color.g, color.b)
        self._opacity_slider.value = color.a
        self._update_opacity_label()
        self._select_tool(self._pencil)

    def _new_sprite(self):
        w = self._tile_cols * TILE_W
        h = self._tile_rows * TILE_H
        self._surface = pygame.Surface((w, h), pygame.SRCALPHA)
        self._surface.fill((0, 0, 0, 0))
        self._canvas.set_surface(self._surface)
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
                self._current_path = path
                self._preview_label.text = fname
                self._clear_history()
                # Detect multi-tile from registry or image size
                stem = os.path.splitext(fname)[0]
                reg = get_sprite_registry()
                info = reg.get(stem)
                if info and info.get("multi"):
                    tiles = info.get("tiles", [])
                    rows = max(t.get("row", 0) for t in tiles) + 1 if tiles else 1
                    cols = max(t.get("col", 0) for t in tiles) + 1 if tiles else 1
                    self._set_multi_size(rows, cols)
                else:
                    # Auto-detect from image dimensions
                    iw = img.get_width()
                    ih = img.get_height()
                    if iw % TILE_W == 0 and ih % TILE_H == 0:
                        auto_cols = iw // TILE_W
                        auto_rows = ih // TILE_H
                        if auto_cols > 1 or auto_rows > 1:
                            self._set_multi_size(auto_rows, auto_cols)
                            return
                    self._set_multi_size(1, 1)
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
        from editor.sprite_registry import _DYNAMIC_ENTRIES, _MERGED_NEEDS_REBUILD, _BUILT_KEYS
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
        if self._surface is None:
            return

        rp_abs_x = self.rect.x + self.rect.w - 144
        rp_abs_y = self.rect.y + 6

        preview_x = rp_abs_x + 8
        preview_y = rp_abs_y + 200

        sw = self._surface.get_width()
        sh = self._surface.get_height()

        # Label
        i18n = I18n.instancia()
        font = i18n.fuente(11) if i18n else pygame.font.SysFont("Arial", 11)
        label = font.render(f"Game: {sw}x{sh}", True, (180, 190, 200))
        surface.blit(label, (preview_x, preview_y - 14))

        # Checkerboard background
        for py in range(sh):
            for px in range(sw):
                ck = CHECK_C1 if ((preview_x + px) // 4 + (preview_y + py) // 4) % 2 == 0 else CHECK_C2
                pygame.draw.rect(surface, ck, (preview_x + px, preview_y + py, 1, 1))

        # Sprite pixels at 1:1
        for py in range(sh):
            for px in range(sw):
                color = self._surface.get_at((px, py))
                if color.a == 0:
                    continue
                dx = preview_x + px
                dy = preview_y + py
                if color.a == 255:
                    pygame.draw.rect(surface, (color.r, color.g, color.b), (dx, dy, 1, 1))
                else:
                    ck = CHECK_C1 if (px // 4 + py // 4) % 2 == 0 else CHECK_C2
                    r = (color.r * color.a + ck[0] * (255 - color.a)) // 255
                    g = (color.g * color.a + ck[1] * (255 - color.a)) // 255
                    b = (color.b * color.a + ck[2] * (255 - color.a)) // 255
                    pygame.draw.rect(surface, (r, g, b), (dx, dy, 1, 1))

        # Border
        pygame.draw.rect(surface, (100, 110, 120), (preview_x - 1, preview_y - 1, sw + 2, sh + 2), 1)

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

        # Keyboard shortcuts for undo/redo
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

        # Sync color from color picker to tool (with opacity)
        if self._current_tool and self._color_picker:
            if hasattr(self._current_tool, 'color'):
                r, g, b = self._color_picker.selected_color
                self._current_tool.color = (r, g, b, self._opacity_slider.value)
        return super().handle_event(event)
