"""File I/O operations for SpriteEditorPanel.

New, open, save, save-as sprite operations.
Extracted from SpriteEditorPanel (sprite_editor.py) for testability.
"""

from __future__ import annotations

import os
from typing import Any, TYPE_CHECKING

import pygame

if TYPE_CHECKING:
    from editor.widgets.canvas import Canvas
    from editor.ui.widgets import StatusBar


def new_sprite(
    surface: pygame.Surface | None,
    canvas: Any,
    sprite_w: int,
    sprite_h: int,
    status_bar: Any,
    undo_stack: list,
    redo_stack: list,
) -> pygame.Surface:
    """Create a new blank sprite surface."""
    surf = pygame.Surface((sprite_w, sprite_h), pygame.SRCALPHA)
    surf.fill((0, 0, 0, 0))
    canvas.set_surface(surf)
    canvas.fit()
    undo_stack.clear()
    redo_stack.clear()
    status_bar.set_text("nuevo.png")
    return surf


def load_sprite(
    fname: str,
    full_path: str | None,
    canvas: Any,
    status_bar: Any,
    undo_stack: list,
    redo_stack: list,
    assets_path_fn: Any,
    set_size_fn: Any,
    update_header_fn: Any,
) -> tuple[pygame.Surface | None, str | None]:
    """Load a sprite from disk. Returns (surface, path) or (None, None) on failure."""
    from editor.project import get_current_project
    path = full_path or os.path.join(get_current_project().assets_path(), fname)
    if not os.path.exists(path):
        return None, None
    try:
        img = pygame.image.load(path).convert_alpha()
        surf = pygame.Surface(img.get_size(), pygame.SRCALPHA)
        surf.blit(img, (0, 0))
        canvas.set_surface(surf)
        canvas.fit()
        undo_stack.clear()
        redo_stack.clear()
        status_bar.set_text(fname)
        set_size_fn(img.get_width(), img.get_height())
        update_header_fn()
        return surf, path
    except pygame.error:
        return None, None


def save_sprite(
    surface: pygame.Surface,
    current_path: str | None,
    tileset_mode: bool,
    save_tileset_fn: Any,
    do_save_fn: Any,
    status_bar: Any,
    i18n: Any,
    assets_path_fn: Any,
    update_header_fn: Any,
) -> str | None:
    """Save sprite to disk. Returns the saved path or None if cancelled."""
    from editor.project import get_current_project
    if tileset_mode:
        save_tileset_fn()
        status_bar.set_text("Tile guardado en tileset")
        return current_path
    if current_path:
        do_save_fn(current_path)
        return current_path
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    path = filedialog.asksaveasfilename(
        initialdir=get_current_project().assets_path(),
        title=i18n.t("sprite.save"),
        defaultextension=".png",
        filetypes=[("PNG files", "*.png")]
    )
    root.destroy()
    if path:
        do_save_fn(path)
        status_bar.set_text(os.path.basename(path))
        update_header_fn()
        return path
    return None


def do_save(
    surface: pygame.Surface,
    path: str,
    tile_rows: int,
    tile_cols: int,
    cut_cell_w: int,
    cut_cell_h: int,
    i18n: Any,
    status_bar: Any,
    update_header_fn: Any,
) -> None:
    """Write surface to PNG. If multi-tile grid, also saves sub-tiles."""
    pygame.image.save(surface, path)
    if tile_rows > 1 or tile_cols > 1:
        _save_multi_tiles(surface, path, tile_rows, tile_cols, cut_cell_w, cut_cell_h)
    status_bar.set_text(i18n.t("sprite.saved"))
    update_header_fn()


def _save_multi_tiles(
    surface: pygame.Surface,
    full_path: str,
    rows: int,
    cols: int,
    cut_cell_w: int,
    cut_cell_h: int,
) -> None:
    """Split multi-tile image and save each sub-tile PNG."""
    from editor.sprite_registry import _BUILT_KEYS, _DYNAMIC_ENTRIES, _MERGED_NEEDS_REBUILD
    stem = os.path.splitext(os.path.basename(full_path))[0]
    assets_dir = os.path.dirname(full_path)
    tiles = []
    for r in range(rows):
        for c in range(cols):
            sub = surface.subsurface((c * cut_cell_w, r * cut_cell_h, cut_cell_w, cut_cell_h))
            sub_stem = f"{stem}_r{r}_c{c}"
            sub_path = os.path.join(assets_dir, f"{sub_stem}.png")
            pygame.image.save(sub, sub_path)
            tiles.append({"col": c, "row": r, "file": sub_stem, "z": 0, "behavior": "decorative"})
    _DYNAMIC_ENTRIES[stem] = {
        "file": stem,
        "display": stem.replace("_", " ").title(),
        "char": None,
        "multi": True,
        "tiles": tiles,
    }
    for t in tiles:
        if t["file"] not in _BUILT_KEYS:
            _DYNAMIC_ENTRIES[t["file"]] = {
                "file": t["file"],
                "display": t["file"].replace("_", " ").title(),
                "char": None,
            }


def save_as_sprite(
    surface: pygame.Surface,
    i18n: Any,
    assets_path_fn: Any,
    do_save_fn: Any,
    status_bar: Any,
) -> str | None:
    """Show save-as dialog and save. Returns path or None."""
    from editor.project import get_current_project
    import tkinter as tk
    from tkinter import filedialog
    root = tk.Tk()
    root.withdraw()
    path = filedialog.asksaveasfilename(
        initialdir=get_current_project().assets_path(),
        title=i18n.t("sprite.save_as"),
        defaultextension=".png",
        filetypes=[("PNG files", "*.png")]
    )
    root.destroy()
    if path:
        do_save_fn(path)
        status_bar.set_text(os.path.basename(path))
        return path
    return None
