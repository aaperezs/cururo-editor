"""Editor sub-sections for MenuTab: config editor, controls section, preview.

Pure pygame_gui construction + preview rendering — no MenuTab state dependency.
Extracted from MenuTab (menu_panel.py) for testability.
"""

from __future__ import annotations

import json
from typing import Any, Sequence

import pygame
import pygame_gui

from editor.menu.forms import (
    build_item_form,
    build_flag_form,
    build_stat_form,
    build_controls_form,
)


# ── Constants ──────────────────────────────────────────────

PADDING = 6

TIPO_OPTIONS = [
    ("lista_habilidades", "Habilidades"),
    ("lista_consumibles", "Consumibles"),
    ("objetos_clave", "Objetos Clave"),
    ("equipo", "Equipo"),
    ("lista", "Lista"),
    ("opciones", "Opciones"),
    ("controles", "Controles"),
    ("stats_flags", "Stats/Flags"),
    ("stats", "Stats"),
    ("shop_comprar", "Tienda: Comprar"),
    ("shop_vender", "Tienda: Vender"),
]

CONFIG_LABELS = {
    "lista": "items",
    "opciones": "items",
    "stats_flags": "flags",
    "stats": "stats",
    "shop_comprar": "shop_id",
    "shop_vender": "shop_id",
}


# ── Config editor ──────────────────────────────────────────

def build_config_editor(
    y: int,
    ew_avail: int,
    gui: Any,
    container: Any,
    ap: dict[str, Any],
    key: str,
    item_idx: int | None,
    i18n: Any,
) -> tuple[int, str, list, int | None, dict[str, Any] | None, Any | None, dict[str, Any], Any, Any, Any, Any]:
    """Build config editor (items/flags/stats list + buttons + form).

    Returns (y, config_key, config_items, item_idx, it_inps, it_accion_dd, it_params,
             cfg_list, cfg_add_btn, cfg_del_btn, cfg_dup_btn).
    """
    items = ap.get(key) or []
    if not isinstance(items, list):
        items = []

    if key == "items":
        lbl = i18n.t("menu.config_items")
    elif key == "flags":
        lbl = i18n.t("menu.config_flags")
    else:
        lbl = i18n.t("menu.config_stats")
    pygame_gui.elements.UILabel(
        pygame.Rect(PADDING, y, ew_avail, 18), lbl, gui, container=container
    )
    y += 22

    cfg_h = 84
    cfg_rect = pygame.Rect(PADDING, y, ew_avail - 60, cfg_h)
    labels = []
    for idx, it in enumerate(items):
        nombre = it.get("nombre") or it.get("id", "")
        labels.append(f"{idx + 1}. {nombre}")
    sel_label = None
    if item_idx is not None and 0 <= item_idx < len(labels):
        sel_label = labels[item_idx]
    cfg_list = pygame_gui.elements.UISelectionList(
        cfg_rect, item_list=labels, manager=gui,
        default_selection=sel_label, container=container
    )
    cfg_add_btn = pygame_gui.elements.UIButton(
        pygame.Rect(cfg_rect.right + 4, cfg_rect.y, 54, 24), "+",
        gui, container=container
    )
    cfg_del_btn = pygame_gui.elements.UIButton(
        pygame.Rect(cfg_rect.right + 4, cfg_rect.y + 28, 54, 24), "X",
        gui, container=container
    )
    cfg_dup_btn = pygame_gui.elements.UIButton(
        pygame.Rect(cfg_rect.right + 4, cfg_rect.y + 56, 54, 24), "Dup",
        gui, container=container
    )
    y = cfg_rect.bottom + 8

    it_inps = None
    it_accion_dd = None
    it_params: dict[str, Any] = {}

    if item_idx is not None and 0 <= item_idx < len(items):
        it = items[item_idx]
        if key == "items":
            y, it_inps, it_accion_dd, it_params = build_item_form(
                y, ew_avail, gui, container, it
            )
        elif key == "flags":
            y, it_inps = build_flag_form(y, ew_avail, gui, container, it)
        elif key == "shop_id":
            from editor.shops_data import get_all_shops
            shops = get_all_shops()
            y, it_inps, _, _ = build_shop_id_form(
                y, ew_avail, gui, container, it, shops
            )
        else:
            y, it_inps = build_stat_form(y, ew_avail, gui, container, it)

    return y, key, items, item_idx, it_inps, it_accion_dd, it_params, cfg_list, cfg_add_btn, cfg_del_btn, cfg_dup_btn


# ── Controls section ───────────────────────────────────────

def build_controls_section(
    y: int,
    ew_avail: int,
    gui: Any,
    container: Any,
    controls: list[dict[str, Any]],
    control_idx: int | None,
    i18n: Any,
) -> tuple[int, Any, Any, Any, dict[str, Any] | None]:
    """Build controls section (list + buttons + form).

    Returns (y, ctrl_list, ctrl_add_btn, (ctrl_del_btn, ctrl_dup_btn), ctrl_inps).
    """
    return build_controls_form(y, ew_avail, gui, container, controls, control_idx, i18n)


# ── Preview ────────────────────────────────────────────────

def build_preview(
    ex: int,
    ey: int,
    eh: int,
    y: int,
    ew_avail: int,
    container: Any,
    apartados: list[dict[str, Any]],
    gui: Any,
    apartado_idx: int | None,
    apartado_labels: list[str],
    preview: Any,
    i18n: Any,
) -> tuple[int, list[str], Any, Any, Any, pygame.Rect | None]:
    """Build preview mode UI (apartados list + preview rect).

    Returns (y, apartado_labels, ap_list, ap_add_btn, (ap_up_btn, ap_down_btn), preview_rect).
    """
    pygame_gui.elements.UILabel(
        pygame.Rect(PADDING, y, ew_avail, 18), i18n.t("menu.preview_hint"),
        gui, container=container
    )
    y += 22

    ap_h = 72
    ap_rect = pygame.Rect(PADDING, y, ew_avail - 60, ap_h)
    labels = []
    for idx, ap in enumerate(apartados):
        nombre = ap.get("nombre", ap.get("id", ""))
        tipo = ap.get("tipo", "lista")
        labels.append(f"{idx + 1}. {nombre} ({tipo})")
    sel_label = None
    if apartado_idx is not None and 0 <= apartado_idx < len(labels):
        sel_label = labels[apartado_idx]
    ap_list = pygame_gui.elements.UISelectionList(
        ap_rect, item_list=labels, manager=gui,
        default_selection=sel_label, container=container
    )
    bx = ap_rect.right + 4
    ap_add_btn = pygame_gui.elements.UIButton(
        pygame.Rect(bx, ap_rect.y, 26, 24), "+",
        gui, container=container
    )
    ap_del_btn = pygame_gui.elements.UIButton(
        pygame.Rect(bx, ap_rect.y + 28, 26, 24), "X",
        gui, container=container
    )
    bx2 = ap_rect.right + 32
    ap_up_btn = pygame_gui.elements.UIButton(
        pygame.Rect(bx2, ap_rect.y, 26, 24), "↑",
        gui, container=container
    )
    ap_down_btn = pygame_gui.elements.UIButton(
        pygame.Rect(bx2, ap_rect.y + 28, 26, 24), "↓",
        gui, container=container
    )

    pv_y = ap_rect.bottom + 10
    pv_h = eh - (pv_y - ey) - PADDING
    avail = pygame.Rect(ex + PADDING, ey + pv_y, ew_avail - PADDING, pv_h)
    gw, gh = preview.tamanio()
    scale = min(avail.w / gw, avail.h / gh)
    tw, th = max(1, int(gw * scale)), max(1, int(gh * scale))
    preview_rect = pygame.Rect(
        avail.x + (avail.w - tw) // 2, avail.y, tw, th
    )

    return y, labels, ap_list, ap_add_btn, (ap_del_btn, ap_up_btn, ap_down_btn), preview_rect


def render_preview(
    menu: dict[str, Any] | None,
    selected_id: str | None,
    apartado_idx: int | None,
    preview: Any,
    preview_sig: tuple | None,
) -> tuple[pygame.Surface | None, tuple | None]:
    """Render preview surface. Returns (surface, signature) or (None, sig) if unchanged."""
    if not menu or not menu.get("apartados"):
        return None, None
    try:
        sig = (selected_id, apartado_idx,
               json.dumps(menu, ensure_ascii=False, sort_keys=True))
    except Exception:
        sig = None
    if sig == preview_sig:
        return None, preview_sig
    gw, gh = preview.tamanio()
    surf = pygame.Surface((gw, gh))
    preview.dibujar(surf, menu, apartado_idx or 0, 0)
    return surf, sig
