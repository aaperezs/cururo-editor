"""Commit and persist logic for menus and controls.

Pure data manipulation + data I/O — no pygame_gui dependency.
Extracted from MenuTab (menu_panel.py) for testability.
"""

from __future__ import annotations

from typing import Any, Callable

from editor.actions_data import NONE_ACTION, schema
from editor.menu.data import set_menu, validar_menu
from editor.controls_data import set_controles, validar_controles
from editor.menu.forms import CONFIG_FIELDS


# ── Type aliases ───────────────────────────────────────────

Menu = dict[str, Any]
Apartado = dict[str, Any]
ConfigItem = dict[str, Any]
Control = dict[str, Any]
StatusFn = Callable[[str, bool], None]


def sel_option(widget: Any) -> str:
    """Extract selected_option from pygame_gui widget (str or (str, str))."""
    opt = widget.selected_option
    return opt[0] if isinstance(opt, tuple) else opt


def commit_config(
    ap: Apartado,
    config_key: str | None,
    config_items: list[ConfigItem],
    item_idx: int | None,
    it_inps: dict[str, Any] | None,
    it_accion_dd: Any | None,
    it_params: dict[str, Any],
) -> None:
    """Commit config form values (items/flags/stats) to apartado in memory."""
    if config_key is None or item_idx is None:
        return
    if not (0 <= item_idx < len(config_items)):
        return
    it = config_items[item_idx]
    if it_inps:
        for fname in CONFIG_FIELDS.get(config_key, ("id", "nombre")):
            inp = it_inps.get(fname)
            if inp:
                it[fname] = inp.get_text().strip()
        if config_key == "items" and it_accion_dd is not None:
            acc_tipo = sel_option(it_accion_dd).split("|")[0]
            if acc_tipo == NONE_ACTION:
                it.pop("accion", None)
            else:
                params: dict[str, Any] = {}
                for pname, _plabel, ptype, pdefault in schema(acc_tipo):
                    w = it_params.get(pname)
                    if w is None:
                        continue
                    if ptype == "bool":
                        params[pname] = sel_option(w).split("|")[0] == "true"
                    elif ptype == "int":
                        try:
                            params[pname] = int(w.get_text().strip())
                        except (ValueError, TypeError):
                            params[pname] = pdefault
                    elif ptype == "float":
                        try:
                            params[pname] = float(w.get_text().strip())
                        except (ValueError, TypeError):
                            params[pname] = pdefault
                    else:
                        params[pname] = w.get_text().strip()
                it["accion"] = {"tipo": acc_tipo, "params": params}
    ap[config_key] = config_items


def commit_controles(
    controles: list[Control] | None,
    control_idx: int | None,
    ctrl_inps: dict[str, Any] | None,
) -> None:
    """Commit controls form values to binding in memory."""
    if controles is None or control_idx is None:
        return
    if not (0 <= control_idx < len(controles)):
        return
    c = controles[control_idx]
    if not ctrl_inps:
        return
    for fname in ("accion", "tecla"):
        inp = ctrl_inps.get(fname)
        if inp:
            c[fname] = inp.get_text().strip()


def commit_current(
    menu: Menu | None,
    selected_id: str | None,
    apartado_idx: int | None,
    config_key: str | None,
    config_items: list[ConfigItem],
    item_idx: int | None,
    controles: list[Control] | None,
    control_idx: int | None,
    tecla_inp: Any | None = None,
    titulo_inp: Any | None = None,
    ap_name_inp: Any | None = None,
    ap_tipo_dd: Any | None = None,
    it_inps: dict[str, Any] | None = None,
    it_accion_dd: Any | None = None,
    it_params: dict[str, Any] | None = None,
    ctrl_inps: dict[str, Any] | None = None,
) -> None:
    """Commit all form inputs to menu/controls in memory (no disk save)."""
    if not selected_id or menu is None:
        return
    if tecla_inp is not None:
        menu["tecla"] = tecla_inp.get_text().strip()
    if titulo_inp is not None:
        menu["titulo"] = titulo_inp.get_text().strip()
    if apartado_idx is not None and 0 <= apartado_idx < len(menu.get("apartados", [])):
        ap = menu["apartados"][apartado_idx]
        if ap_name_inp is not None:
            ap["nombre"] = ap_name_inp.get_text().strip() or ap.get("id", "")
        if ap_tipo_dd is not None:
            raw = sel_option(ap_tipo_dd)
            if "|" in raw:
                ap["tipo"] = raw.split("|")[0]
        if config_key:
            commit_config(
                ap, config_key, config_items, item_idx,
                it_inps, it_accion_dd, it_params or {},
            )
    if controles is not None:
        commit_controles(controles, control_idx, ctrl_inps)


def persist(
    menu: Menu | None,
    selected_id: str | None,
    controles: list[Control] | None,
    set_status: StatusFn,
) -> bool:
    """Persist menu and controls to disk. Returns True on success."""
    adv: list[str] = []
    if selected_id and menu is not None:
        bloq, adv = validar_menu(menu)
        if bloq:
            set_status("⚠ " + " · ".join(bloq), True)
            return False
        set_menu(selected_id, menu)
    if controles is not None:
        cbloq, _cadv = validar_controles(controles)
        if cbloq:
            set_status("⚠ " + " · ".join(cbloq), True)
            return False
        set_controles(controles)
    if selected_id and menu is not None:
        if adv:
            set_status("⚠ " + " · ".join(adv), False)
        else:
            set_status("✓ Guardado", False)
    return True


def persist_controles(
    controles: list[Control] | None,
    set_status: StatusFn,
) -> bool:
    """Persist controls to disk. Returns True on success."""
    if controles is None:
        return True
    bloq, adv = validar_controles(controles)
    if bloq:
        set_status("⚠ " + " · ".join(bloq), True)
        return False
    set_controles(controles)
    if adv:
        set_status("⚠ " + " · ".join(adv), False)
    else:
        set_status("✓ Guardado", False)
    return True
