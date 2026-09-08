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

ROW1_H = 30
ROW2_H = 28


def build_toolbar(editor_panel, toolbar_row1, toolbar_row2) -> dict:
    """Build toolbar buttons on two row panels.

    Args:
        editor_panel: The MapEditorPanel (for callbacks and i18n).
        toolbar_row1: Row 1 Panel (file / map / run).
        toolbar_row2: Row 2 Panel (view / tools).

    Returns a dict of button references for external access.
    """
    btns = {}

    def _add1(x, w, **kwargs):
        b = Button(x, 1, w, 28, **kwargs)
        b.parent = toolbar_row1
        toolbar_row1.children.append(b)
        return b

    def _add2(x, w, **kwargs):
        b = Button(x, 0, w, 26, **kwargs)
        b.parent = toolbar_row2
        toolbar_row2.children.append(b)
        return b

    # ── Row 1: Archivo | Mapa | Ejecutar ────────────────────
    btns["new_btn"] = _add1(6, 60, text=editor_panel.i18n.t("map.new"), callback=editor_panel._new_map)
    btns["open_btn"] = _add1(72, 90, text=editor_panel.i18n.t("map.open"), callback=editor_panel._open_map)
    btns["save_btn"] = _add1(168, 90, text=editor_panel.i18n.t("map.save"), callback=editor_panel._save_map)

    btns["props_btn"] = _add1(270, 80, text="Propiedades", callback=editor_panel._open_map_properties)
    btns["resize_btn"] = _add1(356, 60, text=editor_panel.i18n.t("map.resize"), callback=editor_panel._resize_map)

    ico_tileset = make_icon("grid", 18)
    tileset_text = "Tileset" if not ico_tileset else ""
    btns["tileset_btn"] = _add1(422, 32, text=tileset_text, icon=ico_tileset, callback=editor_panel._toggle_tileset_mode)

    ico_play = make_icon("play", 18)
    play_text = "\u25b6 Test" if not ico_play else ""
    btns["test_btn"] = _add1(490, 32, text=play_text, icon=ico_play, callback=editor_panel._launch_game)
    btns["folder_btn"] = _add1(526, 70, text="Carpeta", callback=editor_panel._select_project_folder)

    # ── Row 2: Vista | Herramientas ─────────────────────────
    ico_grid = make_icon("grid", 18)
    grid_text = "" if ico_grid else "Grid"
    _add2(6, 32, text=grid_text, icon=ico_grid, callback=editor_panel._toggle_grid)

    _add2(42, 24, text="+", callback=editor_panel._zoom_in)
    _add2(70, 24, text="-", callback=editor_panel._zoom_out)

    zoom_label = Label(98, 0, 50, 26, "100%", font_size=12)
    zoom_label.parent = toolbar_row2
    toolbar_row2.children.append(zoom_label)
    btns["zoom_label"] = zoom_label

    ico_sel = make_icon("select", 18)
    ico_era = make_icon("eraser", 18)
    ico_buc = make_icon("bucket", 18)
    ico_drag = make_icon("drag", 18)
    btns["tool_sel_btn"] = _add2(170, 32, icon=ico_sel, callback=editor_panel._set_tool_select)
    btns["tool_era_btn"] = _add2(206, 32, icon=ico_era, callback=editor_panel._set_tool_eraser)
    btns["tool_buc_btn"] = _add2(242, 32, icon=ico_buc, callback=editor_panel._set_tool_bucket)
    drag_text = "" if ico_drag else "\u2195"
    btns["tool_drag_btn"] = _add2(278, 32, text=drag_text, icon=ico_drag, callback=editor_panel._set_tool_drag)

    return btns


def launch_game() -> None:
    """Launch the runtime for the current project in a separate process."""
    p = get_current_project()
    if not p:
        print("[EDITOR] No hay proyecto seleccionado")
        return
    if getattr(sys, "frozen", False):
        meipass = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
        runtime = os.path.join(meipass, "engine", "main.py")
        cwd = os.path.dirname(sys.executable)
        cmd = [sys.executable, "--runtime", "--project", p.root]
    else:
        # El motor vive en editor/engine/ y corre desde ahí
        editor_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        runtime = os.path.join(editor_root, "engine", "main.py")
        cwd = editor_root
        cmd = [sys.executable, runtime, "--project", p.root]
    if not os.path.exists(runtime):
        print(f"[EDITOR] No se encuentra el motor en {runtime}")
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
