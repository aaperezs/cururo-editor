import json
from typing import Sequence

import pygame
import pygame_gui

from editor.panels.base_panel import BasePanel
from editor.pygame_gui_theme import create_gui
from editor.menu_preview import MenuPreview
from editor.menu_data import (
    _load_menus,
    get_all_menus,
    get_menu,
)
from editor.menu_crud import (
    create_new_menu,
    clone_menu,
    delete_menu_by_id,
    rename_menu_by_id,
    move_apartado,
    add_apartado,
    delete_apartado,
    add_config_item,
    delete_config_item,
    duplicate_config_item,
    add_control,
    delete_control,
    duplicate_control,
)
from editor.controls_data import (
    _load_controles,
    get_controles,
)
from editor.menu_dialogs import prompt_template, prompt_new_id
from editor.menu_file_io import (
    commit_current,
    commit_controles,
    persist,
    persist_controles,
)
from editor.menu_forms import (
    build_item_form,
    build_flag_form,
    build_stat_form,
    build_controls_form,
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
        self._it_inps = None
        self._ctrl_inps = None
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
        if menu is None:
            return
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
            tipo_items: Sequence[str | tuple[str, str]] = [f"{k}|{v}" for k, v in TIPO_OPTIONS]
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
                y, self._it_inps, self._it_accion_dd, self._it_params = build_item_form(
                    y, ew_avail, self._gui, container, it
                )
            elif key == "flags":
                y, self._it_inps = build_flag_form(y, ew_avail, self._gui, container, it)
            else:
                y, self._it_inps = build_stat_form(y, ew_avail, self._gui, container, it)
        return y

    def _build_controls_editor(self, y, ew_avail, container):
        i = self.i18n
        if self._controles is None:
            self._controles = get_controles()
        controls = self._controles
        self._config_key = None
        self._config_items = []
        self._item_idx = None

        y, self._ctrl_list, self._ctrl_add_btn, (self._ctrl_del_btn, self._ctrl_dup_btn), self._ctrl_inps = build_controls_form(
            y, ew_avail, self._gui, container, controls, self._control_idx, i
        )
        return y

    # ── Persistencia ─────────────────────────────────────────

    def _commit_current(self):
        """Vuelca los inputs actuales al menú en memoria (no guarda en disco)."""
        commit_current(
            self._menu, self._selected_id, self._apartado_idx,
            self._config_key, self._config_items, self._item_idx,
            self._controles, self._control_idx,
            tecla_inp=getattr(self, "_tecla_inp", None),
            titulo_inp=getattr(self, "_titulo_inp", None),
            ap_name_inp=getattr(self, "_ap_name_inp", None),
            ap_tipo_dd=getattr(self, "_ap_tipo_dd", None),
            it_inps=getattr(self, "_it_inps", None),
            it_accion_dd=getattr(self, "_it_accion_dd", None),
            it_params=getattr(self, "_it_params", None),
            ctrl_inps=getattr(self, "_ctrl_inps", None),
        )

    def _persist_controles(self):
        return persist_controles(self._controles, self._set_status)

    def _save_controles(self):
        self._commit_current()
        return self._persist_controles()

    def _persist(self):
        return persist(self._menu, self._selected_id, self._controles, self._set_status)

    def _save_menu(self):
        self._commit_current()
        return self._persist()

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
        mid = create_new_menu(tpl)
        if mid:
            self._select_menu(mid)

    def _on_clone(self):
        if not self._selected_id:
            return
        self._save_menu()
        mid = clone_menu(self._selected_id)
        if mid:
            self._select_menu(mid)

    def _on_delete(self):
        if not self._selected_id:
            return
        delete_menu_by_id(self._selected_id)
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
        if not rename_menu_by_id(self._selected_id, new_id):
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
        new_idx = move_apartado(self._menu, self._apartado_idx, direccion)
        if new_idx is not None:
            self._apartado_idx = new_idx
        self._persist()
        self._build_ui()

    def _on_add_apartado(self):
        if not self._selected_id or self._menu is None:
            return
        self._commit_current()
        self._apartado_idx = add_apartado(self._menu)
        self._persist()
        self._build_ui()

    def _on_del_apartado(self):
        if not self._selected_id or self._menu is None:
            return
        if self._apartado_idx is None:
            return
        self._apartado_idx = delete_apartado(self._menu, self._apartado_idx)
        self._persist()
        self._build_ui()

    # ── Items / Flags ────────────────────────────────────────

    def _on_add_item(self):
        if not self._config_key:
            return
        self._commit_current()
        self._item_idx = add_config_item(self._config_items, self._config_key)
        self._build_ui()
        self._save_menu()

    def _on_del_item(self):
        if not self._config_key:
            return
        if self._item_idx is None:
            return
        self._commit_current()
        self._item_idx = delete_config_item(self._config_items, self._item_idx)
        self._build_ui()
        self._save_menu()

    def _on_dup_item(self):
        if not self._config_key:
            return
        if self._item_idx is None:
            return
        self._commit_current()
        new_idx = duplicate_config_item(self._config_items, self._item_idx)
        if new_idx is not None:
            self._item_idx = new_idx
            self._build_ui()
            self._save_menu()

    # ── Controles ────────────────────────────────────────────

    def _on_add_control(self):
        if self._controles is None:
            self._controles = get_controles()
        commit_controles(self._controles, self._control_idx, getattr(self, "_ctrl_inps", None))
        self._control_idx = add_control(self._controles)
        self._build_ui()
        self._save_controles()

    def _on_del_control(self):
        if self._controles is None or self._control_idx is None:
            return
        commit_controles(self._controles, self._control_idx, getattr(self, "_ctrl_inps", None))
        self._control_idx = delete_control(self._controles, self._control_idx)
        self._build_ui()
        self._save_controles()

    def _on_dup_control(self):
        if self._controles is None or self._control_idx is None:
            return
        commit_controles(self._controles, self._control_idx, getattr(self, "_ctrl_inps", None))
        new_idx = duplicate_control(self._controles, self._control_idx)
        if new_idx is not None:
            self._control_idx = new_idx
            self._build_ui()
            self._save_controles()

    def _prompt_template(self):
        return prompt_template(self.i18n)

    def _prompt_new_id(self, current_id):
        return prompt_new_id(self.i18n, current_id)

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
                self._persist()
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
                self._persist()
                self._build_ui()
                return True
            if hasattr(self, '_ctrl_list') and e.ui_element == self._ctrl_list:
                commit_controles(self._controles, self._control_idx, getattr(self, "_ctrl_inps", None))
                text = e.text
                idx = 0
                try:
                    idx = int(text.split(".")[0]) - 1
                except (ValueError, AttributeError):
                    idx = 0
                self._control_idx = idx
                self._persist_controles()
                self._build_ui()
                return True
        elif e.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if hasattr(self, '_ap_tipo_dd') and e.ui_element == self._ap_tipo_dd:
                self._commit_current()
                self._item_idx = None
                self._persist()
                self._build_ui()
                return True
            if hasattr(self, '_it_accion_dd') and e.ui_element == self._it_accion_dd:
                self._commit_current()
                self._persist()
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