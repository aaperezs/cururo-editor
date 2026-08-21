import pygame
import os
import copy
from editor.translation import I18n
from editor.panels.base_panel import BasePanel
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.text_input import TextInput
from editor.widgets.simple_dropdown import SimpleDropdown as _SimpleDropdown
from editor.behaviors import BEHAVIORS
from editor.elements import (
    get_all_elements, get_element, set_element, delete_element,
    create_element, get_element_name, get_element_subtiles, set_element_subtile,
    get_element_tileset_idx, set_element_tileset_idx, element_exists, rename_element,
)
from editor.sprite_registry import get_sprite_registry, get_sprite_options, get_multi_tile_tiles
from editor.common.sprite_loader import obtener as obtener_sprite
from editor.element_crud import generate_new_id, rename_element_maps
from editor.element_model import (
    apply_props_to_element, apply_multi_tile, build_drop_options,
)
from editor.property_editor import build_properties
from editor.drop_editor import (
    build_drop_widgets, add_drop as _drop_add, remove_drop as _drop_remove,
    update_drop_prob as _drop_update_prob, update_drop_item as _drop_update_item,
    update_drop_ability as _drop_update_ability,
)
from editor.subtile_editor import (
    build_subtile_widgets, update_subtile_z, update_subtile_behavior,
)


PADDING = 6
ROW_H = 28
TOOLBAR_H = 36
HEADER_H = 26
FILTER_GROUPS = [
    (None, "Todos"),
    ("terreno", "Terreno"),
    ("decoracion", "Decoracion"),
    ("obstaculos", "Obstaculos"),
    ("items", "Items"),
    ("enemigos", "Enemigos"),
]
SCROLLBAR_W = 10


class ElementTab(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(x, y, w, h, i18n)
        self.bg_color = (30, 32, 36)
        self._selected_id = None
        self._list_scroll = 0
        self._editing_props = {}
        self._dirty = False
        self._left_w = 240
        self._sprite_preview_surf = None
        self._filter_group = None
        self._scroll_dragging = False
        self._build_ui()

    def _build_ui(self):
        self.clear()

        # Toolbar as Panel (like other tabs do)
        tb_w = self.rect.w
        tb = Panel(0, 0, tb_w, TOOLBAR_H, bg_color=(42, 46, 55), border_color=(60, 65, 75))
        self.add(tb)

        self._new_btn = Button(8, 4, 72, 28, self.i18n.t("element.new"), callback=self._on_new)
        self._new_btn.parent = tb
        tb.children.append(self._new_btn)

        self._clone_btn = Button(86, 4, 72, 28, self.i18n.t("element.clone"), callback=self._on_clone)
        self._clone_btn.parent = tb
        tb.children.append(self._clone_btn)

        self._del_btn = Button(164, 4, 72, 28, self.i18n.t("element.delete"), callback=self._on_delete)
        self._del_btn.parent = tb
        tb.children.append(self._del_btn)

        self._save_btn = Button(240, 4, 72, 28, self.i18n.t("element.save"), callback=self._on_save)
        self._save_btn.parent = tb
        tb.children.append(self._save_btn)

        self._rename_btn = Button(318, 4, 80, 28, "Renombrar", callback=self._on_rename)
        self._rename_btn.parent = tb
        tb.children.append(self._rename_btn)

        # Editor panel
        rx = self._left_w
        rw = self.rect.w - rx
        cy = TOOLBAR_H
        ch = self.rect.h - cy
        self._editor_panel = Panel(rx, cy, rw, ch, bg_color=(35, 38, 46))
        self.add(self._editor_panel)

        self._build_editor_widgets()

    def _build_editor_widgets(self):
        ep = self._editor_panel
        ep.clear()
        y = PADDING

        self._eid_label = Label(PADDING, y, ep.rect.w - PADDING * 2, 20, "",
                                font_size=13, color=(200, 210, 220))
        self._eid_label.parent = ep
        ep.children.append(self._eid_label)
        y += 26

        lbl = Label(PADDING, y, 80, 22, self.i18n.t("element.name") + ":",
                    font_size=12, color=(180, 185, 195))
        lbl.parent = ep
        ep.children.append(lbl)
        self._name_input = TextInput(90, y, 200, 22, default="",
                                     max_chars=30, numeric_only=False)
        self._name_input.parent = ep
        ep.children.append(self._name_input)
        y += 30

        lbl = Label(PADDING, y, 80, 22, self.i18n.t("element.sprite") + ":",
                    font_size=12, color=(180, 185, 195))
        lbl.parent = ep
        ep.children.append(lbl)
        self._sprite_selector = _SimpleDropdown(90, y, 200, 22,
                                                   self._get_sprite_options())
        self._sprite_selector.parent = ep
        ep.children.append(self._sprite_selector)
        y += 30

        # Tileset index field (for tileset-based elements)
        lbl = Label(PADDING, y, 80, 22, "Tileset idx:",
                    font_size=12, color=(180, 185, 195))
        lbl.parent = ep
        ep.children.append(lbl)
        self._tileset_idx_input = TextInput(90, y, 60, 22, default="",
                                             max_chars=5, numeric_only=True)
        self._tileset_idx_input.parent = ep
        ep.children.append(self._tileset_idx_input)
        # Help text
        help_lbl = Label(155, y, 200, 22, "(vacío = usa sprite_id)",
                         font_size=10, color=(120, 130, 140))
        help_lbl.parent = ep
        ep.children.append(help_lbl)
        y += 30

        self._sprite_preview_surf = None
        y += 4

        lbl = Label(PADDING, y, 80, 22, self.i18n.t("element.behavior") + ":",
                    font_size=12, color=(180, 185, 195))
        lbl.parent = ep
        ep.children.append(lbl)
        self._behavior_selector = _SimpleDropdown(90, y, 200, 22,
                                                     self._get_behavior_options())
        self._behavior_selector.parent = ep
        ep.children.append(self._behavior_selector)
        y += 30

        sep = Panel(PADDING, y, ep.rect.w - PADDING * 2, 2,
                    bg_color=(55, 60, 70))
        sep.parent = ep
        ep.children.append(sep)
        y += 10

        self._props_title = Label(PADDING, y, 200, 18,
                                  self.i18n.t("element.properties"),
                                  font_size=12, bold=True, color=(200, 210, 220))
        self._props_title.parent = ep
        ep.children.append(self._props_title)
        y += 24

        self._prop_widgets = {}
        self._prop_y = y
        self._rebuild_properties()

    def _get_sprite_options(self):
        return get_sprite_options()

    def _get_behavior_options(self):
        return [(bid, bdata["label"]) for bid, bdata in BEHAVIORS.items()]

    def _rebuild_properties(self):
        ep = self._editor_panel
        for w in list(self._prop_widgets.values()):
            if w in ep.children:
                ep.children.remove(w)
        self._prop_widgets = {}
        if not self._selected_id:
            return
        el = get_element(self._selected_id)
        if not el:
            return
        behavior = el.get("behavior", "decorative")
        bdata = BEHAVIORS.get(behavior, {})
        props_schema = bdata.get("properties", {})
        current_props = el.get("properties", {})

        def _on_bool(key, val):
            self._editing_props[key] = val
            self._dirty = True

        def _on_choice(key, val):
            self._editing_props[key] = val
            self._dirty = True

        def _on_int(key):
            inp = self._prop_widgets.get(key)
            if inp:
                try:
                    self._editing_props[key] = int(inp.text) if inp.text else 0
                    self._dirty = True
                except ValueError:
                    pass

        def _on_str(key):
            inp = self._prop_widgets.get(key)
            if inp:
                self._editing_props[key] = inp.text
                self._dirty = True

        widgets, y = build_properties(
            props_schema, current_props, self._prop_y,
            self.i18n.t, _on_bool, _on_choice, _on_int, _on_str, ep,
        )
        for key, widget in widgets.items():
            if widget is not None:
                ep.children.append(widget)
        self._prop_widgets = widgets

        if behavior == "multi_tile":
            self._build_subtile_ui(y, el)

    def _rebuild_drops_ui(self, start_y, pkey):
        ep = self._editor_panel
        for w in list(getattr(self, "_drop_widgets", [])):
            if w in ep.children:
                ep.children.remove(w)
        self._drop_widgets = []
        item_opts, ability_opts = build_drop_options()

        def _on_item(d, v):
            _drop_update_item(d, v)
            self._dirty = True

        def _on_prob(d, i):
            _drop_update_prob(d, i.text)
            self._dirty = True

        def _on_ability(d, v):
            _drop_update_ability(d, v)
            self._dirty = True

        def _on_rm(di):
            _drop_remove(self._drops_data, di)
            self._dirty = True
            self._rebuild_properties()

        def _on_add():
            _drop_add(self._drops_data)
            self._dirty = True
            self._rebuild_properties()

        widgets, _ = build_drop_widgets(
            self._drops_data, item_opts, ability_opts, start_y,
            self.i18n.t, _on_item, _on_prob, _on_ability, _on_rm, _on_add, ep,
        )
        for w in widgets:
            ep.children.append(w)
        self._drop_widgets = widgets

    def _add_drop(self):
        _drop_add(self._drops_data)
        self._dirty = True
        self._rebuild_properties()

    def _remove_drop(self, idx):
        if _drop_remove(self._drops_data, idx):
            self._dirty = True
            self._rebuild_properties()

    def _on_drop_prob(self, drop, inp):
        if _drop_update_prob(drop, inp.text):
            self._dirty = True

    def _mark_dirty(self):
        self._dirty = True

    def _build_subtile_ui(self, start_y, el):
        ep = self._editor_panel
        for w in list(getattr(self, "_subtile_widgets", [])):
            if w in ep.children:
                ep.children.remove(w)
        self._subtile_widgets = []
        sprite_id = el.get("sprite_id")
        tiles = get_multi_tile_tiles(sprite_id)
        if not tiles:
            lbl = Label(PADDING + 10, start_y, 300, 20,
                        "Sin sub-tiles en registry", font_size=11, color=(140, 140, 150))
            lbl.parent = ep
            ep.children.append(lbl)
            self._subtile_widgets.append(lbl)
            return
        existing = get_element_subtiles(self._selected_id)

        def _on_z(cc, rr, inp):
            if update_subtile_z(self._selected_id, cc, rr, inp.text, set_element_subtile):
                self._dirty = True

        def _on_beh(cc, rr, v):
            update_subtile_behavior(self._selected_id, cc, rr, v, set_element_subtile)
            self._dirty = True

        widgets, _ = build_subtile_widgets(
            tiles, existing, start_y, _on_z, _on_beh, ep,
        )
        for w in widgets:
            ep.children.append(w)
        self._subtile_widgets = widgets
        self._subtile_y = start_y

    def _on_subtile_z(self, col, row, inp):
        if update_subtile_z(self._selected_id, col, row, inp.text, set_element_subtile):
            self._dirty = True

    def _on_subtile_behavior(self, col, row, behavior):
        update_subtile_behavior(self._selected_id, col, row, behavior, set_element_subtile)
        self._dirty = True

    def _on_prop_choice(self, key, value):
        self._editing_props[key] = value
        self._dirty = True

    def _on_prop_int(self, key):
        inp = self._prop_widgets.get(key)
        if inp:
            try:
                self._editing_props[key] = int(inp.text) if inp.text else 0
                self._dirty = True
            except ValueError:
                pass

    def _on_prop_str(self, key):
        inp = self._prop_widgets.get(key)
        if inp:
            self._editing_props[key] = inp.text
            self._dirty = True

    def _on_new(self):
        eid = generate_new_id("nuevo_elemento", get_all_elements())
        first_sprite = next(iter(get_sprite_registry().keys()), "pasto")
        create_element(eid, first_sprite, eid, "decorative", {}, tileset_idx=None)
        self._dirty = True
        self._select_element(eid)

    def _on_clone(self):
        if not self._selected_id:
            return
        el = get_element(self._selected_id)
        if not el:
            return
        eid = generate_new_id(self._selected_id + "_copia", get_all_elements())
        new_el = copy.deepcopy(el)
        set_element(eid, new_el)
        self._dirty = True
        self._select_element(eid)

    def _on_delete(self):
        if not self._selected_id:
            return
        delete_element(self._selected_id)
        self._selected_id = None
        self._dirty = True
        self._editor_panel.visible = False

    def _on_rename(self):
        if not self._selected_id:
            return
        new_id = self._prompt_new_id(self._selected_id)
        if not new_id or new_id == self._selected_id:
            return
        if element_exists(new_id):
            return
        if not rename_element(self._selected_id, new_id):
            return
        maps_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "orm", "levels", "mapas")
        updated = rename_element_maps(self._selected_id, new_id, maps_dir)
        if updated:
            print(f"  Actualizados {updated} archivo(s) de mapa")
        self._selected_id = new_id
        self._dirty = True
        self._select_element(new_id)

    def _prompt_new_id(self, current_id):
        import pygame
        from editor.translation import I18n
        font = I18n.instancia().fuente(14) if I18n.instancia() else pygame.font.SysFont("Arial", 14)
        font_b = I18n.instancia().fuente(14, bold=True) if I18n.instancia() else pygame.font.SysFont("Arial", 14, bold=True)
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
            title = font_b.render("Renombrar elemento", True, (220, 190, 120))
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

    def _on_save(self):
        if not self._selected_id:
            return
        el = get_element(self._selected_id)
        if not el:
            return
        el["name"] = self._name_input.text if self._name_input.text else self._selected_id
        el["sprite_id"] = self._sprite_selector.get_selected() or el["sprite_id"]
        ts_idx_text = self._tileset_idx_input.text.strip()
        if ts_idx_text:
            try:
                set_element_tileset_idx(self._selected_id, int(ts_idx_text))
            except ValueError:
                pass
        else:
            set_element_tileset_idx(self._selected_id, None)
        new_beh = self._behavior_selector.get_selected() or el.get("behavior", "decorative")
        old_beh = el.get("behavior")
        el["behavior"] = new_beh
        drops_data = getattr(self, "_drops_data", None)
        apply_props_to_element(el, new_beh, self._editing_props, drops_data)
        tiles = get_multi_tile_tiles(el.get("sprite_id")) if new_beh == "multi_tile" else []
        apply_multi_tile(el, el.get("sprite_id"), tiles)
        set_element(self._selected_id, el)
        self._editing_props = {}
        self._dirty = False
        self._rebuild_properties()
        self._select_element(self._selected_id)

    def _select_element(self, eid):
        self._selected_id = eid
        el = get_element(eid)
        if not el:
            self._editor_panel.visible = False
            return
        self._editor_panel.visible = True
        self._build_editor_widgets()
        self._eid_label.text = f"ID: {eid}"
        self._name_input.text = el.get("name", eid)
        sid = el.get("sprite_id")
        self._sprite_selector.set_selected(sid)
        self._update_sprite_preview(sid)
        # Load tileset_idx
        ts_idx = get_element_tileset_idx(eid)
        self._tileset_idx_input.text = str(ts_idx) if ts_idx is not None else ""
        beh = el.get("behavior", "decorative")
        self._behavior_selector.set_selected(beh)
        self._editing_props = dict(el.get("properties", {}))
        self._rebuild_properties()

    def _update_sprite_preview(self, sprite_id):
        self._sprite_preview_surf = None
        if not sprite_id:
            return
        info = get_sprite_registry().get(sprite_id)
        if not info:
            return
        fname = info.get("file")
        if not fname:
            return
        spr = obtener_sprite(fname)
        if spr:
            self._sprite_preview_surf = pygame.transform.scale(spr, (24, 24))

    def handle_event(self, event):
        if not self.visible:
            return False

        ar = self.get_abs_rect()
        hdr = pygame.Rect(ar.x, ar.y + TOOLBAR_H, self._left_w, HEADER_H)

        # Filter click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if hdr.collidepoint(mx, my):
                keys = [k for k, _ in FILTER_GROUPS]
                idx = keys.index(self._filter_group)
                self._filter_group = keys[(idx + 1) % len(keys)]
                self._list_scroll = 0
                return True

        # Scrollbar drag
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            r = self._get_list_rect()
            sb_rect = pygame.Rect(r.x + r.w, r.y, SCROLLBAR_W, r.h)
            if sb_rect.collidepoint(mx, my):
                self._scroll_dragging = True
                self._update_scroll_from_mouse(my)
                return True

        if event.type == pygame.MOUSEMOTION and self._scroll_dragging:
            r = self._get_list_rect()
            self._update_scroll_from_mouse(event.pos[1])
            return True

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._scroll_dragging = False

        # List click
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            r = self._get_list_rect()
            if r and r.collidepoint(mx, my):
                local_y = my - r.y + self._list_scroll
                idx = local_y // ROW_H
                filtered = self._get_filtered_elements()
                if 0 <= idx < len(filtered):
                    self._select_element(filtered[idx])
                    self._dirty = False
                    return True

        if event.type == pygame.MOUSEWHEEL:
            r = self._get_list_rect()
            mx, my = pygame.mouse.get_pos()
            full_rect = pygame.Rect(r.x, r.y, r.w + SCROLLBAR_W, r.h)
            if full_rect.collidepoint(mx, my):
                filtered = self._get_filtered_elements()
                max_scroll = max(0, len(filtered) * ROW_H - r.h)
                self._list_scroll = max(0, min(max_scroll, self._list_scroll - event.y * ROW_H * 3))
                return True

        if self._editor_panel and self._editor_panel.visible:
            if self._editor_panel.handle_event(event):
                return True

        return super().handle_event(event)

    def _update_scroll_from_mouse(self, my):
        r = self._get_list_rect()
        if r.h <= 0:
            return
        filtered = self._get_filtered_elements()
        total_h = len(filtered) * ROW_H
        max_scroll = max(0, total_h - r.h)
        ratio = (my - r.y) / r.h
        self._list_scroll = max(0, min(max_scroll, int(ratio * (total_h)) - r.h // 2))

    def _get_element_group(self, eid):
        el = get_element(eid)
        if not el:
            return None
        beh = el.get("behavior", "decorative")
        bdata = BEHAVIORS.get(beh)
        return bdata.get("group") if bdata else None

    def _get_filtered_elements(self):
        all_el = get_all_elements()
        if self._filter_group is None:
            return all_el
        return [eid for eid in all_el if self._get_element_group(eid) == self._filter_group]

    def _get_list_rect(self):
        ar = self.get_abs_rect()
        return pygame.Rect(ar.x, ar.y + TOOLBAR_H + HEADER_H, self._left_w - SCROLLBAR_W,
                           self.rect.h - TOOLBAR_H - HEADER_H)

    def draw(self, surface):
        if not self.visible:
            return

        super().draw(surface)

        ar = self.get_abs_rect()
        lx, ly = ar.x, ar.y + TOOLBAR_H
        lw, lh = self._left_w, self.rect.h - TOOLBAR_H

        i18n = I18n.instancia()
        fuente_b = i18n.fuente(12, bold=True) if i18n else pygame.font.SysFont("Arial", 12, bold=True)
        fuente = i18n.fuente(12) if i18n else pygame.font.SysFont("Arial", 12)

        # Header with filter
        hdr = pygame.Rect(lx, ly, lw, HEADER_H)
        pygame.draw.rect(surface, (42, 46, 55), hdr)
        pygame.draw.rect(surface, (55, 60, 70), hdr, 1)

        filtro_label = dict(FILTER_GROUPS).get(self._filter_group, "Todos")
        txt = fuente_b.render(f"F: {filtro_label} ▼", True, (200, 210, 220))
        surface.blit(txt, (lx + PADDING, ly + (HEADER_H - txt.get_height()) // 2))

        filtered = self._get_filtered_elements()
        ctxt = fuente.render(f"({len(filtered)})", True, (130, 140, 150))
        surface.blit(ctxt, (lx + lw - ctxt.get_width() - PADDING, ly + (HEADER_H - ctxt.get_height()) // 2))

        # List items
        lr = self._get_list_rect()
        clip = surface.get_clip()
        surface.set_clip(lr)
        for i, eid in enumerate(filtered):
            sy = lr.y + i * ROW_H - self._list_scroll
            if sy + ROW_H < lr.y or sy > lr.y + lr.h:
                continue
            sel = eid == self._selected_id
            bg = (55, 60, 72) if sel else (38, 42, 50)
            pygame.draw.rect(surface, bg, (lr.x, sy, lr.w, ROW_H))
            if sel:
                pygame.draw.rect(surface, (70, 130, 200), (lr.x, sy, 3, ROW_H))
            name = get_element_name(eid)
            tc = (200, 210, 220) if sel else (160, 170, 180)
            txt = fuente.render(eid, True, tc)
            surface.blit(txt, (PADDING, sy + (ROW_H - txt.get_height()) // 2))
            nc = (130, 140, 150) if sel else (110, 120, 130)
            nt = fuente.render(f"({name})", True, nc)
            surface.blit(nt, (100, sy + (ROW_H - nt.get_height()) // 2))
        surface.set_clip(clip)

        # Scrollbar
        total_h = len(filtered) * ROW_H
        if total_h > lr.h:
            sb_x = lr.x + lr.w
            sb_rect = pygame.Rect(sb_x, lr.y, SCROLLBAR_W, lr.h)
            pygame.draw.rect(surface, (35, 38, 44), sb_rect)
            max_scroll = total_h - lr.h
            thumb_h = max(12, int(sb_rect.h * lr.h / total_h))
            thumb_y = lr.y + int((self._list_scroll / max_scroll) * (sb_rect.h - thumb_h)) if max_scroll > 0 else lr.y
            thumb = pygame.Rect(sb_x + 1, thumb_y, SCROLLBAR_W - 2, thumb_h)
            pygame.draw.rect(surface, (100, 110, 125), thumb)
            pygame.draw.rect(surface, (130, 140, 155), thumb, 1)

        # Sprite preview in editor panel area
        if self._sprite_preview_surf:
            px = self._editor_panel.rect.x + 310
            py = self._editor_panel.rect.y + PADDING + 28
            surface.blit(self._sprite_preview_surf, (px, py))



