"""Property editor widgets for element_tab.py.

Pure functions that create UI widgets for each property type (bool, choice,
int, str). No state — caller owns widgets and wires callbacks.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.text_input import TextInput
from editor.widgets.simple_dropdown import SimpleDropdown

PADDING = 6


def make_bool_toggle(
    pkey: str,
    val: bool,
    y: int,
    i18n_t: Callable[[str], str],
    on_change: Callable[[str, bool], None],
    parent: Any,
) -> Tuple[Label, Button]:
    """Create a boolean toggle button for a property."""
    lbl = Label(PADDING + 10, y, 140, 22,
                "", font_size=11, color=(180, 185, 195))
    btn = Button(155, y, 60, 22,
                 i18n_t("app.yes") if val else i18n_t("app.no"))
    btn.color = (50, 110, 50) if val else (100, 60, 60)
    btn.text_color = (230, 230, 230) if val else (180, 180, 180)
    btn._bool_val = val

    def _toggle():
        btn._bool_val = not btn._bool_val
        btn.text = i18n_t("app.yes") if btn._bool_val else i18n_t("app.no")
        btn.color = (50, 110, 50) if btn._bool_val else (100, 60, 60)
        btn.text_color = (230, 230, 230) if btn._bool_val else (180, 180, 180)
        on_change(pkey, btn._bool_val)

    btn.callback = _toggle
    btn.parent = parent
    lbl.parent = parent
    return lbl, btn


def make_choice_dropdown(
    pkey: str,
    val: Any,
    options: Sequence[str],
    y: int,
    on_select: Callable[[str, Any], None],
    parent: Any,
) -> Tuple[Label, SimpleDropdown]:
    """Create a choice dropdown for a property."""
    lbl = Label(PADDING + 10, y, 140, 22,
                "", font_size=11, color=(180, 185, 195))
    dd = SimpleDropdown(155, y, 140, 22, [(o, o) for o in options])
    dd.set_selected(val)
    dd._on_select = lambda v, k=pkey: on_select(k, v)
    dd.parent = parent
    lbl.parent = parent
    return lbl, dd


def make_int_input(
    pkey: str,
    val: Any,
    y: int,
    on_change: Callable[[str], None],
    parent: Any,
) -> Tuple[Label, TextInput]:
    """Create an integer input for a property."""
    lbl = Label(PADDING + 10, y, 140, 22,
                "", font_size=11, color=(180, 185, 195))
    inp = TextInput(155, y, 60, 22, default=str(val),
                    max_chars=5, numeric_only=True)
    inp._on_change = lambda k=pkey: on_change(k)
    inp.parent = parent
    lbl.parent = parent
    return lbl, inp


def make_str_input(
    pkey: str,
    val: Any,
    y: int,
    on_change: Callable[[str], None],
    parent: Any,
) -> Tuple[Label, TextInput]:
    """Create a string input for a property."""
    lbl = Label(PADDING + 10, y, 140, 22,
                "", font_size=11, color=(180, 185, 195))
    inp = TextInput(155, y, 200, 22, default=str(val),
                    max_chars=40, numeric_only=False)
    inp._on_change = lambda k=pkey: on_change(k)
    inp.parent = parent
    lbl.parent = parent
    return lbl, inp


def set_label_text(label: Label, text: str) -> None:
    """Set label text (convenience)."""
    label.text = text


def build_properties(
    schema: Dict[str, Any],
    current_props: Dict[str, Any],
    start_y: int,
    i18n_t: Callable[[str], str],
    on_bool_change: Callable[[str, bool], None],
    on_choice_select: Callable[[str, Any], None],
    on_int_change: Callable[[str], None],
    on_str_change: Callable[[str], None],
    parent: Any,
) -> Tuple[Dict[str, Any], int]:
    """Build property widgets from a behavior schema.

    Returns (widgets_dict, next_y) where widgets_dict maps pkey → widget.
    """
    widgets: Dict[str, Any] = {}
    y = start_y

    for pkey, pdata in schema.items():
        label_text = pdata.get("label", pkey) + ":"
        ptype = pdata.get("type", "bool")
        val = current_props.get(pkey, pdata.get("default"))

        if ptype == "bool":
            lbl, btn = make_bool_toggle(pkey, val, y, i18n_t, on_bool_change, parent)
            lbl.text = label_text
            widgets[f"lbl_{pkey}"] = lbl
            widgets[pkey] = btn
            y += 26

        elif ptype == "choice":
            opts = pdata.get("options", [])
            lbl, dd = make_choice_dropdown(pkey, val, opts, y, on_choice_select, parent)
            lbl.text = label_text
            widgets[f"lbl_{pkey}"] = lbl
            widgets[pkey] = dd
            y += 26

        elif ptype == "int":
            lbl, inp = make_int_input(pkey, val, y, on_int_change, parent)
            lbl.text = label_text
            widgets[f"lbl_{pkey}"] = lbl
            widgets[pkey] = inp
            y += 26

        elif ptype == "drop_list":
            widgets[f"lbl_{pkey}"] = None
            widgets[pkey] = list(val) if isinstance(val, list) else []
            y += 24
            continue

        else:
            lbl, inp = make_str_input(pkey, val, y, on_str_change, parent)
            lbl.text = label_text
            widgets[f"lbl_{pkey}"] = lbl
            widgets[pkey] = inp
            y += 26

    return widgets, y
