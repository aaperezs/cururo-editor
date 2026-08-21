"""Drop list editor for element_tab.py.

Handles the UI for element drop tables: item selector, probability input,
ability selector, add/remove buttons. Pure functions — no state.
"""

from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple

from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.text_input import TextInput
from editor.widgets.simple_dropdown import SimpleDropdown

PADDING = 6


def build_drop_widgets(
    drops_data: List[Dict[str, Any]],
    item_opts: List[Tuple[str, str]],
    ability_opts: List[Tuple[str, str]],
    start_y: int,
    i18n_t: Callable[[str], str],
    on_item_select: Callable[[Dict[str, Any], str], None],
    on_prob_change: Callable[[Dict[str, Any], TextInput], None],
    on_ability_select: Callable[[Dict[str, Any], str], None],
    on_remove: Callable[[int], None],
    on_add: Callable[[], None],
    parent: Any,
) -> Tuple[List[Any], int]:
    """Build drop list widgets.

    Returns (widgets_list, next_y).
    """
    widgets: List[Any] = []
    y = start_y

    if not item_opts:
        lbl = Label(PADDING + 20, y, 200, 18, i18n_t("element.no_items"),
                    font_size=11, color=(140, 140, 150))
        lbl.parent = parent
        widgets.append(lbl)
        return widgets, y

    for di, drop in enumerate(drops_data):
        dd = SimpleDropdown(PADDING + 20, y, 130, 20, item_opts)
        dd.set_selected(drop.get("item", ""))
        dd._on_select = lambda v, d=drop: on_item_select(d, v)
        dd.parent = parent
        widgets.append(dd)

        inp = TextInput(155, y, 40, 20, default=str(drop.get("prob", 50)),
                        max_chars=3, numeric_only=True)
        inp._on_change = lambda d=drop, i=inp: on_prob_change(d, i)
        inp.parent = parent
        widgets.append(inp)

        ab = SimpleDropdown(200, y, 120, 20, ability_opts)
        ab.set_selected(drop.get("ability", ""))
        ab._on_select = lambda v, d=drop: on_ability_select(d, v)
        ab.parent = parent
        widgets.append(ab)

        rm = Button(325, y, 20, 20, "X",
                    callback=lambda di=di: on_remove(di))
        rm.color = (180, 60, 60)
        rm.text_color = (255, 255, 255)
        rm.parent = parent
        widgets.append(rm)
        y += 26

    add_btn = Button(PADDING + 20, y, 100, 22, i18n_t("element.add_drop"),
                     callback=on_add)
    add_btn.color = (50, 90, 50)
    add_btn.text_color = (220, 220, 220)
    add_btn.parent = parent
    widgets.append(add_btn)

    return widgets, y


def add_drop(drops_data: List[Dict[str, Any]]) -> None:
    """Append an empty drop entry."""
    drops_data.append({"item": "", "prob": 50})


def remove_drop(drops_data: List[Dict[str, Any]], idx: int) -> bool:
    """Remove a drop at idx. Returns True if removed."""
    if 0 <= idx < len(drops_data):
        drops_data.pop(idx)
        return True
    return False


def update_drop_prob(drop: Dict[str, Any], text: str) -> bool:
    """Parse and set probability from text input. Returns True on success."""
    try:
        drop["prob"] = int(text) if text else 0
        return True
    except ValueError:
        return False


def update_drop_item(drop: Dict[str, Any], item_id: str) -> None:
    """Set the item for a drop."""
    drop["item"] = item_id


def update_drop_ability(drop: Dict[str, Any], ability_id: str) -> None:
    """Set or clear the ability for a drop."""
    if ability_id:
        drop["ability"] = ability_id
    else:
        drop.pop("ability", None)
