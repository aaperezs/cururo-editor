"""Map toolbar construction and launcher helpers.

Extracted from MapEditorPanel to separate toolbar UI creation
and game launch logic from the main panel.
"""

from __future__ import annotations

import os
import sys
import subprocess

from editor.widgets.button import Button, make_icon
from editor.widgets.label import Label
from editor.project import get_current_project


def build_toolbar(editor_panel, toolbar) -> dict:
    """Build toolbar buttons on the given toolbar panel.

    Args:
        editor_panel: The MapEditorPanel (for callbacks and i18n).
        toolbar: The toolbar Panel widget (as parent for buttons).

    Returns a dict of button references for external access.
    """
    btns = {}

    def _add(x, y, w, h, **kwargs):
        b = Button(x, y, w, h, **kwargs)
        b.parent = toolbar
        toolbar.children.append(b)
        return b

    btns["new_btn"] = _add(6, 4, 60, 28, text=editor_panel.i18n.t("map.new"), callback=editor_panel._new_map)
    btns["open_btn"] = _add(72, 4, 90, 28, text=editor_panel.i18n.t("map.open"), callback=editor_panel._open_map)
    btns["save_btn"] = _add(168, 4, 90, 28, text=editor_panel.i18n.t("map.save"), callback=editor_panel._save_map)

    ico_grid = make_icon("grid", 18)
    grid_text = "" if ico_grid else "Grid"
    _add(268, 4, 32, 28, text=grid_text, icon=ico_grid, callback=editor_panel._toggle_grid)

    _add(304, 4, 24, 28, text="+", callback=editor_panel._zoom_in)
    _add(332, 4, 24, 28, text="-", callback=editor_panel._zoom_out)

    zoom_label = Label(360, 4, 50, 28, "100%", font_size=12)
    zoom_label.parent = toolbar
    toolbar.children.append(zoom_label)
    btns["zoom_label"] = zoom_label

    ico_play = make_icon("play", 18)
    play_text = "\u25b6 Test" if not ico_play else ""
    btns["test_btn"] = _add(420, 4, 32, 28, text=play_text, icon=ico_play, callback=editor_panel._launch_game)
    btns["folder_btn"] = _add(456, 4, 70, 28, text="Carpeta", callback=editor_panel._select_project_folder)

    resize_x = 610
    btns["resize_btn"] = _add(resize_x, 4, 60, 28, text=editor_panel.i18n.t("map.resize"), callback=editor_panel._resize_map)

    ico_tileset = make_icon("grid", 18)
    tileset_text = "Tileset" if not ico_tileset else ""
    btns["tileset_btn"] = _add(resize_x + 66, 4, 32, 28, text=tileset_text, icon=ico_tileset, callback=editor_panel._toggle_tileset_mode)

    ico_sel = make_icon("select", 18)
    ico_era = make_icon("eraser", 18)
    ico_buc = make_icon("bucket", 18)
    ico_drag = make_icon("drag", 18)
    tx = resize_x + 102
    btns["tool_sel_btn"] = _add(tx, 4, 32, 28, icon=ico_sel, callback=editor_panel._set_tool_select)
    btns["tool_era_btn"] = _add(tx + 36, 4, 32, 28, icon=ico_era, callback=editor_panel._set_tool_eraser)
    btns["tool_buc_btn"] = _add(tx + 72, 4, 32, 28, icon=ico_buc, callback=editor_panel._set_tool_bucket)
    drag_text = "" if ico_drag else "\u2195"
    btns["tool_drag_btn"] = _add(tx + 108, 4, 32, 28, text=drag_text, icon=ico_drag, callback=editor_panel._set_tool_drag)

    return btns


def launch_game() -> None:
    """Launch the runtime for the current project in a separate process."""
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


def select_project_folder(folder_btn) -> None:
    """Open a tkinter folder dialog to select the project root."""
    import tkinter as tk
    from tkinter import filedialog
    p = get_current_project()
    if not p:
        return
    root = tk.Tk()
    root.withdraw()
    folder = filedialog.askdirectory(
        title="Seleccionar carpeta del proyecto Orm",
        initialdir=p.root
    )
    root.destroy()
    if folder:
        if os.path.exists(os.path.join(folder, "main.py")):
            p.root = folder
            folder_btn.text = os.path.basename(folder)
            print(f"[EDITOR] Carpeta del proyecto: {folder}")
        else:
            print(f"[EDITOR] No se encuentra main.py en {folder}")
