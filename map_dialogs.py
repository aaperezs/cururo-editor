"""Map dialogs — new map and resize map dialogs.

Extracted from MapEditorPanel to separate dialog construction from the main panel.
"""

from __future__ import annotations

import os
import tkinter as tk
from tkinter import filedialog
from typing import TYPE_CHECKING

from editor.widgets.dialog import Dialog
from editor.project import get_current_project

if TYPE_CHECKING:
    from editor.map_editor import MapEditorPanel
    from editor.widgets.text_input import TextInput


def build_new_dialog(panel: MapEditorPanel) -> Dialog:
    """Create the 'new map' dialog."""
    dw, dh = 300, 220
    dlg = Dialog(
        (panel.rect.w - dw) // 2, (panel.rect.h - dh) // 2, dw, dh,
        title=panel.i18n.t("map.new_title"),
    )
    dlg.build(
        fields=[
            (panel.i18n.t("map.width"), "40", 4, True),
            (panel.i18n.t("map.height"), "30", 4, True),
        ],
        accept_text=panel.i18n.t("dialog.accept"),
        cancel_text=panel.i18n.t("dialog.cancel"),
        accept_callback=panel._new_map_confirm,
    )
    return dlg


def build_resize_dialog(panel: MapEditorPanel) -> Dialog:
    """Create the 'resize map' dialog."""
    dw, dh = 300, 220
    dlg = Dialog(
        (panel.rect.w - dw) // 2, (panel.rect.h - dh) // 2, dw, dh,
        title=panel.i18n.t("map.resize_title"),
    )
    dlg.build(
        fields=[
            (panel.i18n.t("map.width"), "", 4, True),
            (panel.i18n.t("map.height"), "", 4, True),
        ],
        accept_text=panel.i18n.t("dialog.accept"),
        cancel_text=panel.i18n.t("dialog.cancel"),
        accept_callback=panel._resize_map_confirm,
    )
    return dlg


def open_map_dialog(maps_dir: str, i18n_label: str) -> str | None:
    """Open a tkinter file dialog to select a map file.

    Returns the map_id (filename without extension) or None.
    """
    root = tk.Tk()
    root.withdraw()
    path = filedialog.askopenfilename(
        initialdir=maps_dir,
        title=i18n_label,
        filetypes=[("Map files", "*.txt *.json"), ("Text maps", "*.txt"), ("JSON maps", "*.json")]
    )
    root.destroy()
    if path:
        return os.path.splitext(os.path.basename(path))[0]
    return None


def open_save_dialog(maps_dir: str, i18n_label: str) -> str | None:
    """Open a tkinter save-as dialog for maps.

    Returns the full path or None.
    """
    root = tk.Tk()
    root.withdraw()
    path = filedialog.asksaveasfilename(
        initialdir=maps_dir,
        title=i18n_label,
        defaultextension=".json",
        filetypes=[("JSON maps", "*.json"), ("Text maps", "*.txt")]
    )
    root.destroy()
    return path
