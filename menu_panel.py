import copy
import json

import pygame
import pygame_gui

from editor.panels.base_panel import BasePanel
from editor.pygame_gui_theme import create_gui
from editor.menu_preview import MenuPreview
from editor.actions_data import (
    ACCIONES,
    NONE_ACTION,
    acciones_disponibles,
    label_accion,
    schema,
)
from editor.menu_data import (
    _load_menus,
    create_menu,
    delete_menu,
    get_all_menus,
    get_menu,
    menu_exists,
    rename_menu,
    set_menu,
    validar_menu,
)
from editor.controls_data import (
    _load_controles,
    get_controles,
    set_controles,
    validar_controles,
)

PADDING = 6
TOOLBAR_H = 36

TIPO_OPTIONS = [
    ("lista_habilidades", "Habilidades"),
    ("lista_consumibles", "Consumibles"),
    ("equipo", "Equipo"),
    ("lista", "Lista"),
    ("opciones", "Opciones"),
    ("controles", "Controles"),
    ("stats_flags", "Stats/Flags"),
    ("stats", "Stats"),
]

# Para estos tipos el apartado admite config JSON (items/flags).
CONFIG_LABELS = {
    "lista": "items",
    "opciones": "items",
    "stats_flags": "flags",
    "stats": "stats",
}

# Campos editables por tipo de config.
CONFIG_FIELDS = {
    "items": ("id", "nombre", "descripcion"),
    "flags": ("id", "nombre", "default"),
    "stats": ("id", "nombre", "valor"),
}


class MenuTab(BasePanel):
    """Editor de menús editables (data/menus.json).

    Estructura: menus -> apartados (tipo + config).
    """

    def __init__(self, x, y, w, h, i18n):
        super().__init__(0, 0, w, h, i18n)
        self.bg_color = (30, 32, 36)
        self._gui = create_gui((w, h), offset_getter=lambda: (
            self.get_abs_rect().x, self.get_abs_rect().y
        ))
        _load_menus()
        _load_controles()
        self._selected_id = None
        self._menu = None
        self._apartado_idx = None
        self._apartado_labels = []
        self._config_key = None
        self._config_items = []
        self._item_idx = None
        self._controles = get_controles()
        self._control_idx = None
        self._status_text = ""
        self._status_error = False
        self._preview_mode = False
        self._preview = MenuPreview()
        self._preview_surface = None
        self._preview_rect = None
        self._preview_sig = None
        self._build_ui()

    # ── Construcción ─────────────────────────────────────────

    def _build_ui(self):
        self._gui.clear_and_reset()
        w, h = self.rect.w, self.rect.h
        i = self.i18n

        menus = get_all_menus()
        self.mostrar_descripcion(i.t("tab.menus.desc") if not menus else "")

        # Toolbar
        self._new_btn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING, 4, 72, 28), i.t("menu.new"), self._gui
        )
        self._clone_btn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING + 78, 4, 72, 28), i.t("menu.clone"), self._gui
        )
        self._del_btn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING + 156, 4, 72, 28), i.t("menu.delete"), self._gui
        )
        self._rename_btn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING + 234, 4, 90, 28), i.t("menu.rename"), self._gui
        )
        self._save_btn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING + 330, 4, 72, 28), i.t("menu.save"), self._gui
        )
        self._preview_btn = pygame_gui.elements.UIButton(
            pygame.Rect(PADDING + 408, 4, 78, 28),
            i.t("menu.edit" if self._preview_mode else "menu.preview"), self._gui
        )
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING + 492, 8, 160, 20),
            f"{i.t('menu.title_panel')} ({len(menus)})", self._gui
        )
        self._status_lbl = pygame_gui.elements.UILabel(
            pygame.Rect(PADDING + 658, 8, w - (PADDING + 664), 20),
            self._status_text, self._gui
        )

        cy = TOOLBAR_H + PADDING
        lw = 240
        lh = h - cy - PADDING
        list_rect = pygame.Rect(PADDING, cy, lw, lh)
        sel = self._selected_id if self._selected_id in menus else None
        self._list = pygame_gui.elements.UISelectionList(
            list_rect, item_list=menus, manager=self._gui,
            default_selection=sel,
        )

        # Editor del menú seleccionado
        if self._selected_id and self._menu is not None:
            self._build_editor(240 + PADDING * 2, cy, w - (240 + PADDING * 3), lh)

    def _build_editor(self, ex, ey, ew, eh):
        i = self.i18n
        menu = self._menu
        apartados = menu.get("apartados", [])
        y = ey + PADDING
        ew_avail = ew - PADDING * 2
        container = pygame_gui.core.UIContainer(
            pygame.Rect(ex, ey, ew, eh), manager=self._gui
        )

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew_avail, 18),
            f"ID: {self._selected_id}", self._gui, container=container
        )
        y += 22

        if self._preview_mode:
            self._build_preview(ex, ey, eh, y, ew_avail, container, apartados)
            return

        # ── Tecla ──
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 70, 20), i.t("menu.key"), self._gui, container=container
        )
        self._tecla_inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(74, y, 50, 22), initial_text=menu.get("tecla", ""),
            manager=self._gui, container=container
        )
        y += 26

        # ── Título ──
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 70, 20), i.t("menu.title"), self._gui, container=container
        )
        self._titulo_inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(74, y, ew_avail - 74, 22), initial_text=menu.get("titulo", ""),
            manager=self._gui, container=container
        )
        y += 30

        # ── Apartados ──
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew_avail, 18), i.t("menu.apartados"),
            self._gui, container=container
        )
        y += 22

        ap_h = 72
        ap_rect = pygame.Rect(PADDING, y, ew_avail - 60, ap_h)
        ap_labels = []
        for idx, ap in enumerate(apartados):
            nombre = ap.get("nombre", ap.get("id", ""))
            tipo = ap.get("tipo", "lista")
            ap_labels.append(f"{idx + 1}. {nombre} ({tipo})")
        self._apartado_labels = ap_labels
        sel_label = None
        if self._apartado_idx is not None and 0 <= self._apartado_idx < len(ap_labels):
            sel_label = ap_labels[self._apartado_idx]
        self._ap_list = pygame_gui.elements.UISelectionList(
            ap_rect, item_list=ap_labels, manager=self._gui,
            default_selection=sel_label, container=container
        )
        bx = ap_rect.right + 4
        self._ap_add_btn = pygame_gui.elements.UIButton(
            pygame.Rect(bx, ap_rect.y, 26, 24), "+",
            self._gui, container=container
        )
        self._ap_del_btn = pygame_gui.elements.UIButton(
            pygame.Rect(bx, ap_rect.y + 28, 26, 24), "X",
            self._gui, container=container
        )
        bx2 = ap_rect.right + 32
        self._ap_up_btn = pygame_gui.elements.UIButton(
            pygame.Rect(bx2, ap_rect.y, 26, 24), "↑",
            self._gui, container=container
        )
        self._ap_down_btn = pygame_gui.elements.UIButton(
            pygame.Rect(bx2, ap_rect.y + 28, 26, 24), "↓",
            self._gui, container=container
        )
        y = ap_rect.bottom + 8

        # ── Editor de apartado ──
        if self._apartado_idx is not None and 0 <= self._apartado_idx < len(apartados):
            ap = apartados[self._apartado_idx]
            tipo = ap.get("tipo", "lista")

            pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, ew_avail, 18), i.t("menu.apartado_edit"),
                self._gui, container=container
            )
            y += 22

            pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 75, 22), i.t("menu.apartado_name"),
                self._gui, container=container
            )
            self._ap_name_inp = pygame_gui.elements.UITextEntryLine(
                pygame.Rect(79, y, ew_avail - 79, 22),
                initial_text=ap.get("nombre", ""),
                manager=self._gui, container=container
            )
            y += 26

            pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 75, 22), i.t("menu.apartado_type"),
                self._gui, container=container
            )
            tipo_items = [f"{k}|{v}" for k, v in TIPO_OPTIONS]
            tipo_label = dict(TIPO_OPTIONS).get(tipo, tipo)
            self._ap_tipo_dd = pygame_gui.elements.UIDropDownMenu(
                tipo_items, f"{tipo}|{tipo_label}",
                pygame.Rect(79, y, ew_avail - 79, 22), self._gui, container=container
            )
            y += 30

            key = CONFIG_LABELS.get(tipo)
            if key:
                y = self._build_config_editor(y, ew_avail, container, ap, key)
            elif tipo == "controles":
                y = self._build_controls_editor(y, ew_avail, container)
            else:
                self._config_key = None
                self._config_items = []
                self._item_idx = None
                pygame_gui.elements.UILabel(
                    pygame.Rect(PADDING, y, ew_avail, 18), i.t("menu.config_none"),
                    self._gui, container=container
                )
        else:
            self._config_key = None
            self._config_items = []
            self._item_idx = None

    # ── Vista previa en vivo ─────────────────────────────────

    def _build_preview(self, ex, ey, eh, y, ew_avail, container, apartados):
        i = self.i18n
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew_avail, 18), i.t("menu.preview_hint"),
            self._gui, container=container
        )
        y += 22

        ap_h = 72
        ap_rect = pygame.Rect(PADDING, y, ew_avail - 60, ap_h)
        ap_labels = []
        for idx, ap in enumerate(apartados):
            nombre = ap.get("nombre", ap.get("id", ""))
            tipo = ap.get("tipo", "lista")
            ap_labels.append(f"{idx + 1}. {nombre} ({tipo})")
        self._apartado_labels = ap_labels
        sel_label = None
        if self._apartado_idx is not None and 0 <= self._apartado_idx < len(ap_labels):
            sel_label = ap_labels[self._apartado_idx]
        self._ap_list = pygame_gui.elements.UISelectionList(
            ap_rect, item_list=ap_labels, manager=self._gui,
            default_selection=sel_label, container=container
        )
        bx = ap_rect.right + 4
        self._ap_add_btn = pygame_gui.elements.UIButton(
            pygame.Rect(bx, ap_rect.y, 26, 24), "+",
            self._gui, container=container
        )
        self._ap_del_btn = pygame_gui.elements.UIButton(
            pygame.Rect(bx, ap_rect.y + 28, 26, 24), "X",
            self._gui, container=container
        )
        bx2 = ap_rect.right + 32
        self._ap_up_btn = pygame_gui.elements.UIButton(
            pygame.Rect(bx2, ap_rect.y, 26, 24), "↑",
            self._gui, container=container
        )
        self._ap_down_btn = pygame_gui.elements.UIButton(
            pygame.Rect(bx2, ap_rect.y + 28, 26, 24), "↓",
            self._gui, container=container
        )

        pv_y = ap_rect.bottom + 10
        pv_h = eh - (pv_y - ey) - PADDING
        avail = pygame.Rect(ex + PADDING, ey + pv_y, ew_avail - PADDING, pv_h)
        gw, gh = self._preview.tamanio()
        scale = min(avail.w / gw, avail.h / gh)
        tw, th = max(1, int(gw * scale)), max(1, int(gh * scale))
        self._preview_rect = pygame.Rect(
            avail.x + (avail.w - tw) // 2, avail.y, tw, th
        )
        self._preview_surface = None
        self._preview_sig = None

    def _render_preview(self):
        if not self._menu or not self._menu.get("apartados"):
            self._preview_surface = None
            self._preview_sig = None
            return
        try:
            sig = (self._selected_id, self._apartado_idx,
                   json.dumps(self._menu, ensure_ascii=False, sort_keys=True))
        except Exception:
            sig = None
        if sig == self._preview_sig:
            return
        self._preview_sig = sig
        gw, gh = self._preview.tamanio()
        surf = pygame.Surface((gw, gh))
        self._preview.dibujar(surf, self._menu, self._apartado_idx or 0, 0)
        self._preview_surface = surf

    # ── Editor visual de config (items/flags) ────────────────

    def _build_config_editor(self, y, ew_avail, container, ap, key):
        i = self.i18n
        items = ap.get(key) or []
        if not isinstance(items, list):
            items = []
        self._config_key = key
        self._config_items = items

        if key == "items":
            lbl = i.t("menu.config_items")
        elif key == "flags":
            lbl = i.t("menu.config_flags")
        else:
            lbl = i.t("menu.config_stats")
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew_avail, 18), lbl, self._gui, container=container
        )
        y += 22

        cfg_h = 84
        cfg_rect = pygame.Rect(PADDING, y, ew_avail - 60, cfg_h)
        labels = []
        for idx, it in enumerate(items):
            nombre = it.get("nombre") or it.get("id", "")
            labels.append(f"{idx + 1}. {nombre}")
        sel_label = None
        if self._item_idx is not None and 0 <= self._item_idx < len(labels):
            sel_label = labels[self._item_idx]
        self._cfg_list = pygame_gui.elements.UISelectionList(
            cfg_rect, item_list=labels, manager=self._gui,
            default_selection=sel_label, container=container
        )
        self._cfg_add_btn = pygame_gui.elements.UIButton(
            pygame.Rect(cfg_rect.right + 4, cfg_rect.y, 54, 24), "+",
            self._gui, container=container
        )
        self._cfg_del_btn = pygame_gui.elements.UIButton(
            pygame.Rect(cfg_rect.right + 4, cfg_rect.y + 28, 54, 24), "X",
            self._gui, container=container
        )
        self._cfg_dup_btn = pygame_gui.elements.UIButton(
            pygame.Rect(cfg_rect.right + 4, cfg_rect.y + 56, 54, 24), "Dup",
            self._gui, container=container
        )
        y = cfg_rect.bottom + 8

        if self._item_idx is not None and 0 <= self._item_idx < len(items):
            it = items[self._item_idx]
            if key == "items":
                y = self._build_item_form(y, ew_avail, container, it)
            elif key == "flags":
                y = self._build_flag_form(y, ew_avail, container, it)
            else:
                y = self._build_stat_form(y, ew_avail, container, it)
        return y

    def _build_item_form(self, y, ew_avail, container, it):
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew_avail, 18), "Item", self._gui, container=container
        )
        y += 20

        self._it_inps = {}
        for fname, flabel in (("id", "ID"), ("nombre", "Nombre"), ("descripcion", "Descripción")):
            pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 90, 22), flabel, self._gui, container=container
            )
            self._it_inps[fname] = pygame_gui.elements.UITextEntryLine(
                pygame.Rect(94, y, ew_avail - 94, 22),
                initial_text=str(it.get(fname, "")),
                manager=self._gui, container=container
            )
            y += 26

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 75, 20), "Acción", self._gui, container=container
        )
        acc = it.get("accion") or {}
        acc_tipo = acc.get("tipo", "") if isinstance(acc, dict) else ""
        if acc_tipo not in ACCIONES:
            acc_tipo = ""
        opt_none = f"{NONE_ACTION}|Ninguna"
        opt_items = [opt_none] + [f"{t}|{lbl}" for t, lbl in acciones_disponibles()]
        sel = f"{acc_tipo}|{label_accion(acc_tipo)}" if acc_tipo else opt_none
        self._it_accion_dd = pygame_gui.elements.UIDropDownMenu(
            opt_items, sel,
            pygame.Rect(79, y, ew_avail - 79, 22), self._gui, container=container
        )
        y += 30

        self._it_params = {}
        if acc_tipo:
            params = acc.get("params", {}) or {}
            for pname, plabel, ptype, pdefault in schema(acc_tipo):
                pygame_gui.elements.UILabel(
                    pygame.Rect(PADDING, y, 100, 20), plabel, self._gui, container=container
                )
                if ptype == "bool":
                    val = params.get(pname, pdefault)
                    sval = "true" if val else "false"
                    slabel = "Verdadero" if sval == "true" else "Falso"
                    self._it_params[pname] = pygame_gui.elements.UIDropDownMenu(
                        ["true|Verdadero", "false|Falso"], f"{sval}|{slabel}",
                        pygame.Rect(104, y, 130, 22), self._gui, container=container
                    )
                else:
                    self._it_params[pname] = pygame_gui.elements.UITextEntryLine(
                        pygame.Rect(104, y, ew_avail - 104, 22),
                        initial_text=str(params.get(pname, pdefault)),
                        manager=self._gui, container=container
                    )
                y += 26
        return y

    def _build_flag_form(self, y, ew_avail, container, it):
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew_avail, 18), "Flag", self._gui, container=container
        )
        y += 20

        self._it_inps = {}
        for fname, flabel in (("id", "ID"), ("nombre", "Nombre"), ("default", "Default")):
            pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 75, 22), flabel, self._gui, container=container
            )
            self._it_inps[fname] = pygame_gui.elements.UITextEntryLine(
                pygame.Rect(79, y, ew_avail - 79, 22),
                initial_text=str(it.get(fname, "")),
                manager=self._gui, container=container
            )
            y += 26
        return y

    def _build_stat_form(self, y, ew_avail, container, it):
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew_avail, 18), "Stat", self._gui, container=container
        )
        y += 20

        self._it_inps = {}
        for fname, flabel in (("id", "ID"), ("nombre", "Nombre"), ("valor", "Valor")):
            pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 75, 22), flabel, self._gui, container=container
            )
            self._it_inps[fname] = pygame_gui.elements.UITextEntryLine(
                pygame.Rect(79, y, ew_avail - 79, 22),
                initial_text=str(it.get(fname, "")),
                manager=self._gui, container=container
            )
            y += 26
        return y

    def _build_controls_editor(self, y, ew_avail, container):
        i = self.i18n
        if self._controles is None:
            self._controles = get_controles()
        controls = self._controles
        self._config_key = None
        self._config_items = []
        self._item_idx = None

        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew_avail, 18), i.t("menu.controls"),
            self._gui, container=container
        )
        y += 22

        cfg_h = 84
        cfg_rect = pygame.Rect(PADDING, y, ew_avail - 60, cfg_h)
        labels = []
        for idx, c in enumerate(controls):
            labels.append(f"{idx + 1}. {c.get('accion', '')}")
        sel_label = None
        if self._control_idx is not None and 0 <= self._control_idx < len(labels):
            sel_label = labels[self._control_idx]
        self._ctrl_list = pygame_gui.elements.UISelectionList(
            cfg_rect, item_list=labels, manager=self._gui,
            default_selection=sel_label, container=container
        )
        self._ctrl_add_btn = pygame_gui.elements.UIButton(
            pygame.Rect(cfg_rect.right + 4, cfg_rect.y, 54, 24), "+",
            self._gui, container=container
        )
        self._ctrl_del_btn = pygame_gui.elements.UIButton(
            pygame.Rect(cfg_rect.right + 4, cfg_rect.y + 28, 54, 24), "X",
            self._gui, container=container
        )
        self._ctrl_dup_btn = pygame_gui.elements.UIButton(
            pygame.Rect(cfg_rect.right + 4, cfg_rect.y + 56, 54, 24), "Dup",
            self._gui, container=container
        )
        y = cfg_rect.bottom + 8

        if self._control_idx is not None and 0 <= self._control_idx < len(controls):
            c = controls[self._control_idx]
            self._ctrl_inps = {}
            for fname, flabel in (("accion", i.t("menu.control_accion")),
                                  ("tecla", i.t("menu.control_tecla"))):
                pygame_gui.elements.UILabel(
                    pygame.Rect(PADDING, y, 75, 22), flabel, self._gui, container=container
                )
                self._ctrl_inps[fname] = pygame_gui.elements.UITextEntryLine(
                    pygame.Rect(79, y, ew_avail - 79, 22),
                    initial_text=str(c.get(fname, "")),
                    manager=self._gui, container=container
                )
                y += 26
        return y

    # ── Persistencia ─────────────────────────────────────────

    def _commit_current(self):
        """Vuelca los inputs actuales al menú en memoria (no guarda en disco)."""
        if not self._selected_id or self._menu is None:
            return
        menu = self._menu
        if hasattr(self, "_tecla_inp"):
            menu["tecla"] = self._tecla_inp.get_text().strip()
        if hasattr(self, "_titulo_inp"):
            menu["titulo"] = self._titulo_inp.get_text().strip()
        if self._apartado_idx is not None and 0 <= self._apartado_idx < len(menu["apartados"]):
            ap = menu["apartados"][self._apartado_idx]
            if hasattr(self, "_ap_name_inp"):
                ap["nombre"] = self._ap_name_inp.get_text().strip() or ap.get("id", "")
            if hasattr(self, "_ap_tipo_dd"):
                raw = self._sel_option(self._ap_tipo_dd)
                if "|" in raw:
                    ap["tipo"] = raw.split("|")[0]
            if self._config_key:
                self._commit_config(ap)
        if self._controles is not None:
            self._commit_controles()

    @staticmethod
    def _sel_option(widget):
        """selected_option de pygame_gui puede ser str o (str, str)."""
        opt = widget.selected_option
        return opt[0] if isinstance(opt, tuple) else opt

    def _commit_config(self, ap):
        """Vuelca el formulario de items/flags/stats al apartado en memoria."""
        key = self._config_key
        items = self._config_items
        if self._item_idx is not None and 0 <= self._item_idx < len(items):
            it = items[self._item_idx]
            inps = getattr(self, "_it_inps", None)
            if inps:
                for fname in CONFIG_FIELDS.get(key, ("id", "nombre")):
                    inp = inps.get(fname)
                    if inp:
                        it[fname] = inp.get_text().strip()
                if key == "items":
                    acc_dd = getattr(self, "_it_accion_dd", None)
                    if acc_dd:
                        acc_tipo = self._sel_option(acc_dd).split("|")[0]
                        if acc_tipo == NONE_ACTION:
                            it.pop("accion", None)
                        else:
                            params = {}
                            for pname, _plabel, ptype, pdefault in schema(acc_tipo):
                                w = self._it_params.get(pname)
                                if w is None:
                                    continue
                                if ptype == "bool":
                                    params[pname] = self._sel_option(w).split("|")[0] == "true"
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
        ap[key] = items

    def _commit_controles(self):
        """Vuelca el formulario de controles al binding seleccionado (en memoria)."""
        if self._controles is None or self._control_idx is None:
            return
        if not (0 <= self._control_idx < len(self._controles)):
            return
        c = self._controles[self._control_idx]
        inps = getattr(self, "_ctrl_inps", None)
        if not inps:
            return
        for fname in ("accion", "tecla"):
            inp = inps.get(fname)
            if inp:
                c[fname] = inp.get_text().strip()

    def _save_controles(self):
        self._commit_controles()
        if self._controles is None:
            return True
        bloq, adv = validar_controles(self._controles)
        if bloq:
            self._set_status("⚠ " + " · ".join(bloq), error=True)
            return False
        set_controles(self._controles)
        if adv:
            self._set_status("⚠ " + " · ".join(adv), error=False)
        else:
            self._set_status("✓ Guardado", error=False)
        return True

    def _save_menu(self):
        self._commit_current()
        if self._selected_id and self._menu is not None:
            bloq, adv = validar_menu(self._menu)
            if bloq:
                self._set_status("⚠ " + " · ".join(bloq), error=True)
                return False
            set_menu(self._selected_id, self._menu)
        if self._controles is not None:
            cbloq, _cadv = validar_controles(self._controles)
            if cbloq:
                self._set_status("⚠ " + " · ".join(cbloq), error=True)
                return False
            set_controles(self._controles)
        if self._selected_id and self._menu is not None:
            if adv:
                self._set_status("⚠ " + " · ".join(adv), error=False)
            else:
                self._set_status("✓ Guardado", error=False)
        else:
            self._save_controles()
        return True

    def _set_status(self, text, error=False):
        self._status_text = text
        self._status_error = error
        lbl = getattr(self, "_status_lbl", None)
        if lbl:
            lbl.set_text(text)

    def _select_menu(self, mid):
        self._selected_id = mid
        self._menu = get_menu(mid)
        if self._menu and self._menu.get("apartados"):
            self._apartado_idx = 0
        else:
            self._apartado_idx = None
        self._item_idx = None
        self._build_ui()

    # ── Acciones ─────────────────────────────────────────────

    def _on_new(self):
        self._save_menu()
        tpl = self._prompt_template()
        if tpl is None:
            return
        base = "menu_nuevo"
        mid = base
        n = 1
        while menu_exists(mid):
            mid = f"{base}_{n}"
            n += 1
        create_menu(mid, plantilla=tpl)
        self._select_menu(mid)

    def _on_clone(self):
        if not self._selected_id:
            return
        self._save_menu()
        data = get_menu(self._selected_id)
        if not data:
            return
        base = self._selected_id + "_copia"
        mid = base
        n = 1
        while menu_exists(mid):
            mid = f"{base}_{n}"
            n += 1
        set_menu(mid, data)
        self._select_menu(mid)

    def _on_delete(self):
        if not self._selected_id:
            return
        delete_menu(self._selected_id)
        self._selected_id = None
        self._menu = None
        self._apartado_idx = None
        self._build_ui()

    def _on_rename(self):
        if not self._selected_id:
            return
        new_id = self._prompt_new_id(self._selected_id)
        if not new_id or new_id == self._selected_id:
            return
        if menu_exists(new_id):
            return
        if not rename_menu(self._selected_id, new_id):
            return
        if self._menu is not None:
            self._menu["id"] = new_id
        self._selected_id = new_id
        self._build_ui()

    def _on_ap_move(self, direccion):
        if not self._selected_id or self._menu is None:
            return
        if self._apartado_idx is None:
            return
        self._commit_current()
        apartados = self._menu.get("apartados", [])
        idx = self._apartado_idx
        nuevo = idx + direccion
        if not (0 <= idx < len(apartados)) or not (0 <= nuevo < len(apartados)):
            return
        apartados[idx], apartados[nuevo] = apartados[nuevo], apartados[idx]
        self._apartado_idx = nuevo
        self._save_menu()
        self._build_ui()

    def _on_add_apartado(self):
        if not self._selected_id or self._menu is None:
            return
        self._commit_current()
        apartados = self._menu.setdefault("apartados", [])
        n = len(apartados) + 1
        apartados.append({
            "id": f"apartado_{n}",
            "nombre": f"Apartado {n}",
            "tipo": "lista",
        })
        self._apartado_idx = len(apartados) - 1
        self._save_menu()
        self._build_ui()

    def _on_del_apartado(self):
        if not self._selected_id or self._menu is None:
            return
        if self._apartado_idx is None:
            return
        apartados = self._menu.get("apartados", [])
        if 0 <= self._apartado_idx < len(apartados):
            del apartados[self._apartado_idx]
        self._apartado_idx = max(0, min(self._apartado_idx - 1, len(apartados) - 1))
        if not apartados:
            self._apartado_idx = None
        self._save_menu()
        self._build_ui()

    # ── Items / Flags ────────────────────────────────────────

    def _on_add_item(self):
        if not self._config_key:
            return
        self._commit_current()
        n = len(self._config_items) + 1
        if self._config_key == "items":
            self._config_items.append({
                "id": f"item_{n}", "nombre": f"Item {n}", "descripcion": "",
            })
        elif self._config_key == "flags":
            self._config_items.append({
                "id": f"flag_{n}", "nombre": f"Flag {n}", "default": "0",
            })
        else:
            self._config_items.append({
                "id": f"stat_{n}", "nombre": f"Stat {n}", "valor": "",
            })
        self._item_idx = len(self._config_items) - 1
        self._build_ui()
        self._save_menu()

    def _on_del_item(self):
        if not self._config_key:
            return
        if self._item_idx is None:
            return
        self._commit_current()
        items = self._config_items
        if 0 <= self._item_idx < len(items):
            del items[self._item_idx]
        self._item_idx = max(0, min(self._item_idx - 1, len(items) - 1))
        if not items:
            self._item_idx = None
        self._build_ui()
        self._save_menu()

    def _on_dup_item(self):
        if not self._config_key:
            return
        if self._item_idx is None:
            return
        self._commit_current()
        items = self._config_items
        if 0 <= self._item_idx < len(items):
            dup = copy.deepcopy(items[self._item_idx])
            dup["id"] = (dup.get("id", "") or "item") + "_copia"
            items.append(dup)
            self._item_idx = len(items) - 1
            self._build_ui()
            self._save_menu()

    # ── Controles ────────────────────────────────────────────

    def _on_add_control(self):
        if self._controles is None:
            self._controles = get_controles()
        self._commit_controles()
        n = len(self._controles) + 1
        self._controles.append({"accion": f"Acción {n}", "tecla": ""})
        self._control_idx = len(self._controles) - 1
        self._build_ui()
        self._save_controles()

    def _on_del_control(self):
        if self._controles is None or self._control_idx is None:
            return
        self._commit_controles()
        controles = self._controles
        if 0 <= self._control_idx < len(controles):
            del controles[self._control_idx]
        self._control_idx = max(0, min(self._control_idx - 1, len(controles) - 1))
        if not controles:
            self._control_idx = None
        self._build_ui()
        self._save_controles()

    def _on_dup_control(self):
        if self._controles is None or self._control_idx is None:
            return
        self._commit_controles()
        controles = self._controles
        if 0 <= self._control_idx < len(controles):
            dup = copy.deepcopy(controles[self._control_idx])
            dup["accion"] = (dup.get("accion", "") or "Acción") + "_copia"
            controles.append(dup)
            self._control_idx = len(controles) - 1
            self._build_ui()
            self._save_controles()

    def _prompt_template(self):
        i = self.i18n
        font = i.fuente(14) if i else pygame.font.SysFont("Arial", 14)
        font_b = i.fuente(14, bold=True) if i else pygame.font.SysFont("Arial", 14, bold=True)
        screen = pygame.display.get_surface()
        W, H = screen.get_width(), screen.get_height()
        dw, dh = 460, 220
        dx, dy = (W - dw) // 2, (H - dh) // 2
        tpls = [
            ("vacio", i.t("menu.tpl_vacio")),
            ("inventario", i.t("menu.tpl_inventario")),
            ("opciones", i.t("menu.tpl_opciones")),
            ("relaciones", i.t("menu.tpl_relaciones")),
        ]
        bw, bh, gap = 200, 34, 12
        x0 = dx + (dw - (bw * 2 + gap)) // 2
        y0 = dy + 60
        btn_rects = []
        for n, (key, label) in enumerate(tpls):
            col = n % 2
            row = n // 2
            btn_rects.append(
                (pygame.Rect(x0 + col * (bw + gap), y0 + row * (bh + 10), bw, bh), key, label)
            )
        clock = pygame.time.Clock()
        result = None
        done = False
        bg = pygame.Surface((W, H), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))
        while not done:
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    done = True
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for rect, key, _label in btn_rects:
                        if rect.collidepoint(event.pos):
                            result = key
                            done = True
                            break
            screen.blit(bg, (0, 0))
            pygame.draw.rect(screen, (45, 50, 58), (dx, dy, dw, dh))
            pygame.draw.rect(screen, (70, 80, 95), (dx, dy, dw, dh), 2)
            title = font_b.render(i.t("menu.template_title"), True, (220, 190, 120))
            screen.blit(title, (dx + (dw - title.get_width()) // 2, dy + 16))
            for rect, _key, label in btn_rects:
                pygame.draw.rect(screen, (70, 78, 90), rect)
                pygame.draw.rect(screen, (110, 120, 135), rect, 1)
                txt = font.render(label, True, (210, 210, 210))
                screen.blit(txt, (rect.centerx - txt.get_width() // 2, rect.centery - txt.get_height() // 2))
            pygame.display.flip()
        return result

    def _prompt_new_id(self, current_id):
        i = self.i18n
        font = i.fuente(14) if i else pygame.font.SysFont("Arial", 14)
        font_b = i.fuente(14, bold=True) if i else pygame.font.SysFont("Arial", 14, bold=True)
        screen = pygame.display.get_surface()
        W, H = screen.get_width(), screen.get_height()
        dw, dh = 400, 160
        dx, dy = (W - dw) // 2, (H - dh) // 2
        input_text = current_id
        cursor_pos = len(input_text)
        clock = pygame.time.Clock()
        result = None
        done = False
        bg = pygame.Surface((W, H), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))
        while not done:
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return None
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        done = True
                        result = None
                    elif event.key == pygame.K_RETURN:
                        result = input_text.strip()
                        done = True
                    elif event.key == pygame.K_BACKSPACE:
                        if cursor_pos > 0:
                            input_text = input_text[:cursor_pos - 1] + input_text[cursor_pos:]
                            cursor_pos -= 1
                    elif event.key == pygame.K_DELETE:
                        if cursor_pos < len(input_text):
                            input_text = input_text[:cursor_pos] + input_text[cursor_pos + 1:]
                    elif event.key == pygame.K_LEFT:
                        cursor_pos = max(0, cursor_pos - 1)
                    elif event.key == pygame.K_RIGHT:
                        cursor_pos = min(len(input_text), cursor_pos + 1)
                    elif event.key == pygame.K_HOME:
                        cursor_pos = 0
                    elif event.key == pygame.K_END:
                        cursor_pos = len(input_text)
                    elif event.unicode and event.unicode.isprintable():
                        input_text = input_text[:cursor_pos] + event.unicode + input_text[cursor_pos:]
                        cursor_pos += 1
            screen.blit(bg, (0, 0))
            pygame.draw.rect(screen, (45, 50, 58), (dx, dy, dw, dh))
            pygame.draw.rect(screen, (70, 80, 95), (dx, dy, dw, dh), 2)
            title = font_b.render(i.t("menu.rename"), True, (220, 190, 120))
            screen.blit(title, (dx + (dw - title.get_width()) // 2, dy + 14))
            lbl = font.render("Nuevo ID:", True, (180, 190, 200))
            screen.blit(lbl, (dx + 20, dy + 50))
            inp_r = pygame.Rect(dx + 20, dy + 74, dw - 40, 28)
            pygame.draw.rect(screen, (55, 60, 70), inp_r)
            pygame.draw.rect(screen, (80, 90, 105), inp_r, 1)
            txt = font.render(input_text, True, (220, 220, 220))
            screen.blit(txt, (inp_r.x + 4, inp_r.y + (inp_r.h - txt.get_height()) // 2))
            if (pygame.time.get_ticks() // 500) % 2 == 0:
                cx = inp_r.x + 4 + font.size(input_text[:cursor_pos])[0]
                pygame.draw.line(screen, (200, 200, 200), (cx, inp_r.y + 3), (cx, inp_r.y + inp_r.h - 3))
            pygame.display.flip()
        return result

    # ── Integración ──────────────────────────────────────────

    def update(self, dt):
        self._gui.update(dt)

    def handle_event(self, event):
        if not self.visible:
            return False
        r = self.get_abs_rect()
        if hasattr(event, 'pos'):
            e = pygame.event.Event(event.type, {
                "pos": (event.pos[0] - r.x, event.pos[1] - r.y),
                "button": getattr(event, "button", 0),
                "buttons": getattr(event, "buttons", (0, 0, 0)),
                "rel": getattr(event, "rel", (0, 0)),
            })
        else:
            e = event
        self._gui.process_events(e)

        if e.type == pygame_gui.UI_BUTTON_PRESSED:
            el = e.ui_element
            if el == getattr(self, "_save_btn", None):
                self._save_menu()
                return True
            if el == getattr(self, "_preview_btn", None):
                self._save_menu()
                self._preview_mode = not self._preview_mode
                self._preview_sig = None
                self._build_ui()
                return True
            if el == getattr(self, "_new_btn", None):
                self._on_new()
                return True
            if el == getattr(self, "_clone_btn", None):
                self._on_clone()
                return True
            if el == getattr(self, "_del_btn", None):
                self._on_delete()
                return True
            if el == getattr(self, "_rename_btn", None):
                self._on_rename()
                return True
            if el == getattr(self, "_ap_add_btn", None):
                self._on_add_apartado()
                return True
            if el == getattr(self, "_ap_del_btn", None):
                self._on_del_apartado()
                return True
            if el == getattr(self, "_ap_up_btn", None):
                self._on_ap_move(-1)
                return True
            if el == getattr(self, "_ap_down_btn", None):
                self._on_ap_move(1)
                return True
            if el == getattr(self, "_cfg_add_btn", None):
                self._on_add_item()
                return True
            if el == getattr(self, "_cfg_del_btn", None):
                self._on_del_item()
                return True
            if el == getattr(self, "_cfg_dup_btn", None):
                self._on_dup_item()
                return True
            if el == getattr(self, "_ctrl_add_btn", None):
                self._on_add_control()
                return True
            if el == getattr(self, "_ctrl_del_btn", None):
                self._on_del_control()
                return True
            if el == getattr(self, "_ctrl_dup_btn", None):
                self._on_dup_control()
                return True
            return True
        elif e.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            if hasattr(self, '_list') and e.ui_element == self._list:
                self._save_menu()
                self._select_menu(e.text)
                return True
            if hasattr(self, '_ap_list') and e.ui_element == self._ap_list:
                self._commit_current()
                text = e.text
                idx = 0
                try:
                    idx = int(text.split(".")[0]) - 1
                except (ValueError, AttributeError):
                    idx = 0
                self._apartado_idx = idx
                self._item_idx = None
                self._save_menu()
                self._build_ui()
                return True
            if hasattr(self, '_cfg_list') and e.ui_element == self._cfg_list:
                self._commit_current()
                text = e.text
                idx = 0
                try:
                    idx = int(text.split(".")[0]) - 1
                except (ValueError, AttributeError):
                    idx = 0
                self._item_idx = idx
                self._save_menu()
                self._build_ui()
                return True
            if hasattr(self, '_ctrl_list') and e.ui_element == self._ctrl_list:
                self._commit_controles()
                text = e.text
                idx = 0
                try:
                    idx = int(text.split(".")[0]) - 1
                except (ValueError, AttributeError):
                    idx = 0
                self._control_idx = idx
                self._save_controles()
                self._build_ui()
                return True
        elif e.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if hasattr(self, '_ap_tipo_dd') and e.ui_element == self._ap_tipo_dd:
                self._commit_current()
                self._item_idx = None
                self._save_menu()
                self._build_ui()
                return True
            if hasattr(self, '_it_accion_dd') and e.ui_element == self._it_accion_dd:
                self._commit_current()
                self._save_menu()
                self._build_ui()
                return True

        return True

    def draw(self, surface):
        if not self.visible:
            return
        r = self.get_abs_rect()
        pygame.draw.rect(surface, self.bg_color, r)
        self._gui.draw_ui(surface.subsurface(r))
        if self._preview_mode:
            self._render_preview()
            if self._preview_surface and self._preview_rect:
                surf = surface.subsurface(r)
                target = self._preview_rect
                scaled = pygame.transform.smoothscale(
                    self._preview_surface, (target.w, target.h)
                )
                surf.blit(scaled, (target.x, target.y))
        if self._descripcion:
            self.draw_descripcion(surface)

    def set_size(self, w, h):
        if self.rect.w != w or self.rect.h != h:
            self.rect.w = w
            self.rect.h = h
            self._gui.set_window_resolution((w, h))
            self._build_ui()