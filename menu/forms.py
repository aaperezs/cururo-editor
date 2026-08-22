"""Form-building functions for items, flags, stats, and controls.

Pure pygame_gui construction — no MenuTab state dependency.
Extracted from MenuTab (menu_panel.py) for testability.
"""

from __future__ import annotations

from typing import Any, Sequence

import pygame
import pygame_gui

from editor.actions_data import ACCIONES, NONE_ACTION, acciones_disponibles, label_accion, schema


# ── Constants ──────────────────────────────────────────────

PADDING = 6

CONFIG_FIELDS = {
    "items": ("id", "nombre", "descripcion"),
    "flags": ("id", "nombre", "default"),
    "stats": ("id", "nombre", "valor"),
}


# ── Item form ──────────────────────────────────────────────

def build_item_form(
    y: int,
    ew_avail: int,
    gui: Any,
    container: Any,
    it: dict[str, Any],
) -> tuple[int, dict[str, Any], Any, dict[str, Any]]:
    """Build item config form. Returns (y, inputs, accion_dd, params)."""
    pygame_gui.elements.UILabel(
        pygame.Rect(PADDING, y, ew_avail, 18), "Item", gui, container=container
    )
    y += 20

    inputs: dict[str, Any] = {}
    for fname, flabel in (("id", "ID"), ("nombre", "Nombre"), ("descripcion", "Descripción")):
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 90, 22), flabel, gui, container=container
        )
        inputs[fname] = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(94, y, ew_avail - 94, 22),
            initial_text=str(it.get(fname, "")),
            manager=gui, container=container
        )
        y += 26

    pygame_gui.elements.UILabel(
        pygame.Rect(PADDING, y, 75, 20), "Acción", gui, container=container
    )
    acc = it.get("accion") or {}
    acc_tipo = acc.get("tipo", "") if isinstance(acc, dict) else ""
    if acc_tipo not in ACCIONES:
        acc_tipo = ""
    opt_none = f"{NONE_ACTION}|Ninguna"
    opt_items = [opt_none] + [f"{t}|{lbl}" for t, lbl in acciones_disponibles()]
    sel = f"{acc_tipo}|{label_accion(acc_tipo)}" if acc_tipo else opt_none
    accion_dd = pygame_gui.elements.UIDropDownMenu(
        opt_items, sel,
        pygame.Rect(79, y, ew_avail - 79, 22), gui, container=container
    )
    y += 30

    params: dict[str, Any] = {}
    if acc_tipo:
        acc_params = acc.get("params", {}) or {}
        for pname, plabel, ptype, pdefault in schema(acc_tipo):
            pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 100, 20), plabel, gui, container=container
            )
            if ptype == "bool":
                val = acc_params.get(pname, pdefault)
                sval = "true" if val else "false"
                slabel = "Verdadero" if sval == "true" else "Falso"
                bool_opts: Sequence[str | tuple[str, str]] = ["true|Verdadero", "false|Falso"]
                params[pname] = pygame_gui.elements.UIDropDownMenu(
                    bool_opts, f"{sval}|{slabel}",
                    pygame.Rect(104, y, 130, 22), gui, container=container
                )
            else:
                params[pname] = pygame_gui.elements.UITextEntryLine(
                    pygame.Rect(104, y, ew_avail - 104, 22),
                    initial_text=str(acc_params.get(pname, pdefault)),
                    manager=gui, container=container
                )
            y += 26
    return y, inputs, accion_dd, params


# ── Flag form ──────────────────────────────────────────────

def build_flag_form(
    y: int,
    ew_avail: int,
    gui: Any,
    container: Any,
    it: dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    """Build flag config form. Returns (y, inputs)."""
    pygame_gui.elements.UILabel(
        pygame.Rect(PADDING, y, ew_avail, 18), "Flag", gui, container=container
    )
    y += 20

    inputs: dict[str, Any] = {}
    for fname, flabel in (("id", "ID"), ("nombre", "Nombre"), ("default", "Default")):
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 75, 22), flabel, gui, container=container
        )
        inputs[fname] = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(79, y, ew_avail - 79, 22),
            initial_text=str(it.get(fname, "")),
            manager=gui, container=container
        )
        y += 26
    return y, inputs


# ── Stat form ──────────────────────────────────────────────

def build_stat_form(
    y: int,
    ew_avail: int,
    gui: Any,
    container: Any,
    it: dict[str, Any],
) -> tuple[int, dict[str, Any]]:
    """Build stat config form. Returns (y, inputs)."""
    pygame_gui.elements.UILabel(
        pygame.Rect(PADDING, y, ew_avail, 18), "Stat", gui, container=container
    )
    y += 20

    inputs: dict[str, Any] = {}
    for fname, flabel in (("id", "ID"), ("nombre", "Nombre"), ("valor", "Valor")):
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 75, 22), flabel, gui, container=container
        )
        inputs[fname] = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(79, y, ew_avail - 79, 22),
            initial_text=str(it.get(fname, "")),
            manager=gui, container=container
        )
        y += 26
    return y, inputs


# ── Controls form ──────────────────────────────────────────

def build_controls_form(
    y: int,
    ew_avail: int,
    gui: Any,
    container: Any,
    controls: list[dict[str, Any]],
    control_idx: int | None,
    i18n: Any,
) -> tuple[int, Any, Any, Any, dict[str, Any] | None]:
    """Build controls list + selected form. Returns (y, list, add_btn, del/dup_btns, inputs)."""
    pygame_gui.elements.UILabel(
        pygame.Rect(PADDING, y, ew_avail, 18), i18n.t("menu.controls"),
        gui, container=container
    )
    y += 22

    cfg_h = 84
    cfg_rect = pygame.Rect(PADDING, y, ew_avail - 60, cfg_h)
    labels = []
    for idx, c in enumerate(controls):
        labels.append(f"{idx + 1}. {c.get('accion', '')}")
    sel_label = None
    if control_idx is not None and 0 <= control_idx < len(labels):
        sel_label = labels[control_idx]
    ctrl_list = pygame_gui.elements.UISelectionList(
        cfg_rect, item_list=labels, manager=gui,
        default_selection=sel_label, container=container
    )
    ctrl_add_btn = pygame_gui.elements.UIButton(
        pygame.Rect(cfg_rect.right + 4, cfg_rect.y, 54, 24), "+",
        gui, container=container
    )
    ctrl_del_btn = pygame_gui.elements.UIButton(
        pygame.Rect(cfg_rect.right + 4, cfg_rect.y + 28, 54, 24), "X",
        gui, container=container
    )
    ctrl_dup_btn = pygame_gui.elements.UIButton(
        pygame.Rect(cfg_rect.right + 4, cfg_rect.y + 56, 54, 24), "Dup",
        gui, container=container
    )
    y = cfg_rect.bottom + 8

    ctrl_inps = None
    if control_idx is not None and 0 <= control_idx < len(controls):
        c = controls[control_idx]
        ctrl_inps = {}
        for fname, flabel in (("accion", i18n.t("menu.control_accion")),
                              ("tecla", i18n.t("menu.control_tecla"))):
            pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 75, 22), flabel, gui, container=container
            )
            ctrl_inps[fname] = pygame_gui.elements.UITextEntryLine(
                pygame.Rect(79, y, ew_avail - 79, 22),
                initial_text=str(c.get(fname, "")),
                manager=gui, container=container
            )
            y += 26
    return y, ctrl_list, ctrl_add_btn, (ctrl_del_btn, ctrl_dup_btn), ctrl_inps
