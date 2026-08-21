"""Sub-tile editor for multi-tile elements.

Builds the sub-tile list UI (z-index input + behavior dropdown per tile).
Pure functions — no state.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from editor.behaviors import BEHAVIORS
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.text_input import TextInput
from editor.widgets.simple_dropdown import SimpleDropdown

PADDING = 6


def build_subtile_widgets(
    tiles: List[Dict[str, Any]],
    existing_subtiles: List[Dict[str, Any]],
    start_y: int,
    on_z_change: Callable[[int, int, TextInput], None],
    on_behavior_select: Callable[[int, int, str], None],
    parent: Any,
) -> Tuple[List[Any], int]:
    """Build sub-tile editor widgets.

    Args:
        tiles: List of tile defs from sprite registry ({col, row}).
        existing_subtiles: Current subtile data for the element.
        start_y: Y position to start drawing.
        on_z_change: Callback(col, row, text_input).
        on_behavior_select: Callback(col, row, behavior_id).
        parent: Parent widget for positioning.

    Returns (widgets_list, next_y).
    """
    widgets: List[Any] = []
    existing_map = {(st["col"], st["row"]): st for st in existing_subtiles}

    y = start_y + 4
    sep = Panel(PADDING, y, 400, 2, bg_color=(55, 60, 70))
    sep.parent = parent
    widgets.append(sep)
    y += 10

    title = Label(PADDING, y, 300, 18, "Sub-tiles:",
                  font_size=12, bold=True, color=(200, 210, 220))
    title.parent = parent
    widgets.append(title)
    y += 24

    beh_opts = [(bid, bdata["label"]) for bid, bdata in BEHAVIORS.items()]

    for t in tiles:
        col, row = t.get("col", 0), t.get("row", 0)
        st_data = existing_map.get((col, row), t)

        lbl = Label(PADDING + 10, y, 100, 20,
                    f"  ({col},{row})", font_size=11, color=(180, 185, 195))
        lbl.parent = parent
        widgets.append(lbl)

        z_inp = TextInput(PADDING + 80, y, 30, 20,
                          default=str(st_data.get("z", 0)),
                          max_chars=2, numeric_only=True)
        z_inp._on_change = lambda cc=col, rr=row, inp=z_inp: on_z_change(cc, rr, inp)
        z_inp.parent = parent
        widgets.append(z_inp)

        beh_dd = SimpleDropdown(PADDING + 115, y, 120, 20, beh_opts)
        beh_dd.set_selected(st_data.get("behavior", "decorative"))
        beh_dd._on_select = lambda v, cc=col, rr=row: on_behavior_select(cc, rr, v)
        beh_dd.parent = parent
        widgets.append(beh_dd)

        y += 24

    return widgets, y


def update_subtile_z(
    element_id: str,
    col: int,
    row: int,
    text: str,
    set_element_subtile_fn: Callable[[str, int, int, Dict[str, Any]], None],
) -> bool:
    """Parse z value and save to subtile. Returns True on success."""
    try:
        z = int(text) if text else 0
        set_element_subtile_fn(element_id, col, row, {"z": z})
        return True
    except ValueError:
        return False


def update_subtile_behavior(
    element_id: str,
    col: int,
    row: int,
    behavior: str,
    set_element_subtile_fn: Callable[[str, int, int, Dict[str, Any]], None],
) -> None:
    """Save behavior to subtile."""
    set_element_subtile_fn(element_id, col, row, {"behavior": behavior})
