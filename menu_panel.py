import json

import pygame
import pygame_gui

from editor.panels.base_panel import BasePanel
from editor.pygame_gui_theme import create_gui
from editor.menu_data import (
    _load_menus,
    create_menu,
    delete_menu,
    get_all_menus,
    get_menu,
    menu_exists,
    rename_menu,
    set_menu,
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
]

# Para estos tipos el apartado admite config JSON (items/flags).
CONFIG_LABELS = {
    "lista": "items",
    "opciones": "items",
    "stats_flags": "flags",
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
        self._selected_id = None
        self._menu = None
        self._apartado_idx = None
        self._apartado_labels = []
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
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING + 420, 8, 300, 20),
            f"{i.t('menu.title_panel')} ({len(menus)})", self._gui
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
            pygame.Rect(PADDING, y, ew_avail, 20),
            f"ID: {self._selected_id}", self._gui, container=container
        )
        y += 26

        # ── Tecla ──
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 70, 20), i.t("menu.key"), self._gui, container=container
        )
        self._tecla_inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(74, y, 50, 22), initial_text=menu.get("tecla", ""),
            manager=self._gui, container=container
        )
        y += 28

        # ── Título ──
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 70, 20), i.t("menu.title"), self._gui, container=container
        )
        self._titulo_inp = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(74, y, ew_avail - 74, 22), initial_text=menu.get("titulo", ""),
            manager=self._gui, container=container
        )
        y += 34

        # ── Apartados ──
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew_avail, 20), i.t("menu.apartados"),
            self._gui, container=container
        )
        y += 24

        ap_h = 120
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
        self._ap_add_btn = pygame_gui.elements.UIButton(
            pygame.Rect(ap_rect.right + 4, ap_rect.y, 54, 26), "+",
            self._gui, container=container
        )
        self._ap_del_btn = pygame_gui.elements.UIButton(
            pygame.Rect(ap_rect.right + 4, ap_rect.y + 30, 54, 26), "X",
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
            y += 24

            pygame_gui.elements.UILabel(
                pygame.Rect(PADDING, y, 75, 22), i.t("menu.apartado_name"),
                self._gui, container=container
            )
            self._ap_name_inp = pygame_gui.elements.UITextEntryLine(
                pygame.Rect(79, y, ew_avail - 79, 22),
                initial_text=ap.get("nombre", ""),
                manager=self._gui, container=container
            )
            y += 28

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
            y += 28

            key = CONFIG_LABELS.get(tipo)
            if key:
                lbl = i.t("menu.config_items") if key == "items" else i.t("menu.config_flags")
                pygame_gui.elements.UILabel(
                    pygame.Rect(PADDING, y, ew_avail, 18), lbl, self._gui, container=container
                )
                y += 22
                config_str = json.dumps(ap.get(key, {}), ensure_ascii=False)
                self._ap_config_inp = pygame_gui.elements.UITextEntryLine(
                    pygame.Rect(PADDING, y, ew_avail - PADDING, 22),
                    initial_text=config_str, manager=self._gui, container=container
                )
            else:
                self._ap_config_inp = None
                pygame_gui.elements.UILabel(
                    pygame.Rect(PADDING, y, ew_avail, 18), i.t("menu.config_none"),
                    self._gui, container=container
                )

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
                raw = self._ap_tipo_dd.selected_option
                if "|" in raw:
                    ap["tipo"] = raw.split("|")[0]
            key = CONFIG_LABELS.get(ap.get("tipo", ""))
            if key and hasattr(self, "_ap_config_inp") and self._ap_config_inp:
                text = self._ap_config_inp.get_text().strip()
                try:
                    parsed = json.loads(text) if text else {}
                except (json.JSONDecodeError, TypeError):
                    parsed = None
                if isinstance(parsed, dict) and parsed:
                    ap[key] = parsed
                elif isinstance(parsed, dict):
                    ap.pop(key, None)

    def _save_menu(self):
        self._commit_current()
        if self._selected_id and self._menu is not None:
            set_menu(self._selected_id, self._menu)

    def _select_menu(self, mid):
        self._selected_id = mid
        self._menu = get_menu(mid)
        if self._menu and self._menu.get("apartados"):
            self._apartado_idx = 0
        else:
            self._apartado_idx = None
        self._build_ui()

    # ── Acciones ─────────────────────────────────────────────

    def _on_new(self):
        self._save_menu()
        base = "menu_nuevo"
        mid = base
        n = 1
        while menu_exists(mid):
            mid = f"{base}_{n}"
            n += 1
        create_menu(mid)
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
                self._save_menu()
                self._build_ui()
                return True
        elif e.type == pygame_gui.UI_DROP_DOWN_MENU_CHANGED:
            if hasattr(self, '_ap_tipo_dd') and e.ui_element == self._ap_tipo_dd:
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
        if self._descripcion:
            self.draw_descripcion(surface)

    def set_size(self, w, h):
        if self.rect.w != w or self.rect.h != h:
            self.rect.w = w
            self.rect.h = h
            self._gui.set_window_resolution((w, h))
            self._build_ui()