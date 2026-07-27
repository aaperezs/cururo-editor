import pygame
import os
import json
from editor.translation import I18n
from editor.panels.base_panel import BasePanel
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.text_input import TextInput
from editor.behaviors import BEHAVIORS, DEFAULT_ELEMENT_PROPERTIES
from editor.elements import (
    get_all_elements, get_element, set_element, delete_element,
    create_element, get_element_name, get_element_subtiles, set_element_subtile
)
from editor.items_data import get_item_list
from editor.ability_data import get_ability_list
from editor.sprite_registry import get_sprite_registry, get_sprite_options, get_multi_tile_tiles
from utils.sprite_manager import obtener as obtener_sprite


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
        y = self._prop_y
        for pkey, pdata in props_schema.items():
            lbl = Label(PADDING + 10, y, 140, 22,
                        pdata.get("label", pkey) + ":",
                        font_size=11, color=(180, 185, 195))
            lbl.parent = ep
            ep.children.append(lbl)
            self._prop_widgets[f"lbl_{pkey}"] = lbl
            ptype = pdata.get("type", "bool")
            val = current_props.get(pkey, pdata.get("default"))
            if ptype == "bool":
                btn = Button(155, y, 60, 22,
                             self.i18n.t("app.yes") if val else self.i18n.t("app.no"))
                btn.color = (50, 110, 50) if val else (100, 60, 60)
                btn.text_color = (230, 230, 230) if val else (180, 180, 180)
                btn._bool_val = val
                def make_toggle(key, b):
                    def fn():
                        b._bool_val = not b._bool_val
                        b.text = self.i18n.t("app.yes") if b._bool_val else self.i18n.t("app.no")
                        b.color = (50, 110, 50) if b._bool_val else (100, 60, 60)
                        b.text_color = (230, 230, 230) if b._bool_val else (180, 180, 180)
                        self._editing_props[key] = b._bool_val
                        self._dirty = True
                    return fn
                btn.callback = make_toggle(pkey, btn)
                btn.parent = ep
                ep.children.append(btn)
                self._prop_widgets[pkey] = btn
            elif ptype == "choice":
                opts = pdata.get("options", [])
                dd = _SimpleDropdown(155, y, 140, 22, [(o, o) for o in opts])
                dd.set_selected(val)
                dd._on_select = lambda v, k=pkey: self._on_prop_choice(k, v)
                dd.parent = ep
                ep.children.append(dd)
                self._prop_widgets[pkey] = dd
            elif ptype == "int":
                inp = TextInput(155, y, 60, 22, default=str(val),
                                max_chars=5, numeric_only=True)
                inp._on_change = lambda k=pkey: self._on_prop_int(k)
                inp.parent = ep
                ep.children.append(inp)
                self._prop_widgets[pkey] = inp
            elif ptype == "drop_list":
                self._drops_data = list(val) if isinstance(val, list) else []
                self._prop_widgets[pkey] = self._drops_data
                self._rebuild_drops_ui(y + 24, pkey)
                y += 24 + max(1, len(self._drops_data)) * 26 + 28
                continue
            else:
                inp = TextInput(155, y, 200, 22, default=str(val),
                                max_chars=40, numeric_only=False)
                inp._on_change = lambda k=pkey: self._on_prop_str(k)
                inp.parent = ep
                ep.children.append(inp)
                self._prop_widgets[pkey] = inp
            y += 26

        if behavior == "multi_tile":
            self._build_subtile_ui(y, el)

    def _rebuild_drops_ui(self, start_y, pkey):
        ep = self._editor_panel
        # Remove old drop widgets
        for w in list(getattr(self, "_drop_widgets", [])):
            if w in ep.children:
                ep.children.remove(w)
        self._drop_widgets = []
        y = start_y
        item_opts = get_item_list()
        ability_opts = [("", "Cualquiera")] + get_ability_list()
        if not item_opts:
            lbl = Label(PADDING + 20, y, 200, 18, self.i18n.t("element.no_items"),
                        font_size=11, color=(140, 140, 150))
            lbl.parent = ep; ep.children.append(lbl)
            self._drop_widgets.append(lbl)
            return
        for di, drop in enumerate(self._drops_data):
            # Item
            dd = _SimpleDropdown(PADDING + 20, y, 130, 20, item_opts)
            dd.set_selected(drop.get("item", ""))
            dd._on_select = lambda v, d=drop: d.update({"item": v}) or self._mark_dirty()
            dd.parent = ep; ep.children.append(dd)
            self._drop_widgets.append(dd)
            # Probability
            inp = TextInput(155, y, 40, 20, default=str(drop.get("prob", 50)),
                            max_chars=3, numeric_only=True)
            inp._on_change = lambda d=drop, i=inp: self._on_drop_prob(d, i)
            inp.parent = ep; ep.children.append(inp)
            self._drop_widgets.append(inp)
            # Ability
            ab = _SimpleDropdown(200, y, 120, 20, ability_opts)
            ab.set_selected(drop.get("ability", ""))
            ab._on_select = lambda v, d=drop: d.update({"ability": v}) if v else d.pop("ability", None) or self._mark_dirty()
            ab.parent = ep; ep.children.append(ab)
            self._drop_widgets.append(ab)
            # Remove
            rm = Button(325, y, 20, 20, "X", callback=lambda di=di: self._remove_drop(di))
            rm.color = (180, 60, 60); rm.text_color = (255, 255, 255)
            rm.parent = ep; ep.children.append(rm)
            self._drop_widgets.append(rm)
            y += 26
        # Add button
        add_btn = Button(PADDING + 20, y, 100, 22, self.i18n.t("element.add_drop"),
                         callback=self._add_drop)
        add_btn.color = (50, 90, 50); add_btn.text_color = (220, 220, 220)
        add_btn.parent = ep; ep.children.append(add_btn)
        self._drop_widgets.append(add_btn)

    def _add_drop(self):
        self._drops_data.append({"item": "", "prob": 50})
        self._dirty = True
        self._rebuild_properties()

    def _remove_drop(self, idx):
        if 0 <= idx < len(self._drops_data):
            self._drops_data.pop(idx)
            self._dirty = True
            self._rebuild_properties()

    def _on_drop_prob(self, drop, inp):
        try:
            drop["prob"] = int(inp.text) if inp.text else 0
            self._dirty = True
        except ValueError:
            pass

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
            lbl.parent = ep; ep.children.append(lbl)
            self._subtile_widgets.append(lbl)
            return
        y = start_y + 4
        sep = Panel(PADDING, y, ep.rect.w - PADDING * 2, 2, bg_color=(55, 60, 70))
        sep.parent = ep; ep.children.append(sep)
        self._subtile_widgets.append(sep)
        y += 10
        title = Label(PADDING, y, 300, 18, "Sub-tiles:", font_size=12, bold=True, color=(200, 210, 220))
        title.parent = ep; ep.children.append(title)
        self._subtile_widgets.append(title)
        y += 24
        existing = get_element_subtiles(self._selected_id)
        existing_map = {(st["col"], st["row"]): st for st in existing}
        for t in tiles:
            col, row = t.get("col", 0), t.get("row", 0)
            st_data = existing_map.get((col, row), t)
            lbl = Label(PADDING + 10, y, 100, 20,
                        f"  ({col},{row})", font_size=11, color=(180, 185, 195))
            lbl.parent = ep; ep.children.append(lbl)
            self._subtile_widgets.append(lbl)
            z_inp = TextInput(PADDING + 80, y, 30, 20, default=str(st_data.get("z", 0)),
                              max_chars=2, numeric_only=True)
            z_inp._on_change = lambda cc=col, rr=row, inp=z_inp: self._on_subtile_z(cc, rr, inp)
            z_inp.parent = ep; ep.children.append(z_inp)
            self._subtile_widgets.append(z_inp)
            beh_opts = [(bid, bdata["label"]) for bid, bdata in BEHAVIORS.items()]
            beh_dd = _SimpleDropdown(PADDING + 115, y, 120, 20, beh_opts)
            beh_dd.set_selected(st_data.get("behavior", "decorative"))
            beh_dd._on_select = lambda v, cc=col, rr=row: self._on_subtile_behavior(cc, rr, v)
            beh_dd.parent = ep; ep.children.append(beh_dd)
            self._subtile_widgets.append(beh_dd)
            y += 24
        self._subtile_y = start_y

    def _on_subtile_z(self, col, row, inp):
        try:
            z = int(inp.text) if inp.text else 0
            set_element_subtile(self._selected_id, col, row, {"z": z})
            self._dirty = True
        except ValueError:
            pass

    def _on_subtile_behavior(self, col, row, behavior):
        set_element_subtile(self._selected_id, col, row, {"behavior": behavior})
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
        base = "nuevo_elemento"
        eid = base
        n = 1
        while eid in get_all_elements():
            eid = f"{base}_{n}"
            n += 1
        first_sprite = next(iter(get_sprite_registry().keys()), "pasto")
        create_element(eid, first_sprite, eid, "decorative", {})
        self._dirty = True
        self._select_element(eid)

    def _on_clone(self):
        if not self._selected_id:
            return
        el = get_element(self._selected_id)
        if not el:
            return
        base = self._selected_id + "_copia"
        eid = base
        n = 1
        while eid in get_all_elements():
            eid = f"{base}_{n}"
            n += 1
        import copy
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
        from editor.elements import rename_element, element_exists
        if element_exists(new_id):
            return
        # Update elementos.json
        if not rename_element(self._selected_id, new_id):
            return
        # Update all map files referencing the old ID
        import os, json
        maps_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), "orm", "levels", "mapas")
        updated = 0
        for fname in os.listdir(maps_dir):
            if not fname.endswith(".json"):
                continue
            fpath = os.path.join(maps_dir, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                changed = False
                grid = data.get("grid", {})
                for key, eid in list(grid.items()):
                    if eid == self._selected_id:
                        grid[key] = new_id
                        changed = True
                if changed:
                    with open(fpath, "w", encoding="utf-8") as f:
                        json.dump(data, f, indent=2, ensure_ascii=False)
                    updated += 1
            except Exception:
                pass
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
        new_beh = self._behavior_selector.get_selected() or el.get("behavior", "decorative")
        old_beh = el.get("behavior")
        el["behavior"] = new_beh
        if new_beh != old_beh:
            el["properties"] = dict(DEFAULT_ELEMENT_PROPERTIES.get(new_beh, {}))
        else:
            for k, v in self._editing_props.items():
                el["properties"][k] = v
            for pkey, widget in self._prop_widgets.items():
                if widget is getattr(self, "_drops_data", None):
                    el["properties"][pkey] = list(self._drops_data)
                    break
        if new_beh == "multi_tile":
            el["multi_tile"] = True
            sprite_id = el.get("sprite_id")
            tiles = get_multi_tile_tiles(sprite_id)
            if tiles and not el.get("subtiles"):
                el["subtiles"] = [dict(t) for t in tiles]
        else:
            el.pop("multi_tile", None)
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


class _SimpleDropdown:
    MAX_VISIBLE = 8

    def __init__(self, x, y, w, h, options, selected=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.parent = None
        self.visible = True
        self.enabled = True
        self._all_options = list(options)
        self._selected = selected or (options[0][0] if options else None)
        self._open = False
        self._on_select = None
        self._filter_text = ""
        self._filtered = list(options)
        self._scroll_offset = 0
        self._focus = False

    def _abs_rect(self):
        if self.parent:
            pr = (self.parent.get_abs_rect() if hasattr(self.parent, 'get_abs_rect')
                  else self.parent.rect)
            return pygame.Rect(pr.x + self.rect.x, pr.y + self.rect.y,
                               self.rect.w, self.rect.h)
        return self.rect.copy()

    def set_selected(self, value):
        self._selected = value

    def get_selected(self):
        return self._selected

    def _close_others(self):
        if not self.parent:
            return
        for child in list(self.parent.children):
            if isinstance(child, _SimpleDropdown) and child is not self and child._open:
                child._open = False
                child._filter_text = ""
                child._filtered = list(child._all_options)
                child._scroll_offset = 0

    def _bring_to_front(self):
        p = self.parent.children
        if p and p[-1] is not self:
            p.remove(self)
            p.append(self)

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        r = self._abs_rect()
        if self._open:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._open = False
                    self._filter_text = ""
                    self._filtered = list(self._all_options)
                    self._scroll_offset = 0
                    return True
                elif event.key == pygame.K_RETURN:
                    if self._filtered:
                        val = self._filtered[0][0]
                        self._selected = val
                        self._open = False
                        self._filter_text = ""
                        self._filtered = list(self._all_options)
                        self._scroll_offset = 0
                        if self._on_select:
                            self._on_select(val)
                    return True
                elif event.key == pygame.K_UP:
                    if self._filtered:
                        idx = self._get_selected_filtered_idx()
                        new_idx = max(0, idx - 1)
                        if new_idx < self._scroll_offset:
                            self._scroll_offset = new_idx
                        self._selected = self._filtered[new_idx][0]
                    return True
                elif event.key == pygame.K_DOWN:
                    if self._filtered:
                        idx = self._get_selected_filtered_idx()
                        new_idx = min(len(self._filtered) - 1, idx + 1)
                        if new_idx >= self._scroll_offset + self.MAX_VISIBLE:
                            self._scroll_offset = new_idx - self.MAX_VISIBLE + 1
                        self._selected = self._filtered[new_idx][0]
                    return True
                elif event.key == pygame.K_BACKSPACE:
                    self._filter_text = self._filter_text[:-1]
                    self._apply_filter()
                    return True
                elif event.unicode and event.unicode.isprintable():
                    self._filter_text += event.unicode
                    self._apply_filter()
                    return True

            if event.type == pygame.MOUSEWHEEL:
                max_scroll = max(0, len(self._filtered) - self.MAX_VISIBLE)
                self._scroll_offset = max(0, min(max_scroll, self._scroll_offset - event.y))
                return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if r.collidepoint(mx, my):
                if not self._open:
                    self._close_others()
                self._open = not self._open
                self._filter_text = ""
                self._filtered = list(self._all_options)
                self._scroll_offset = 0
                if self._open and self.parent:
                    self._bring_to_front()
                return True
            if self._open:
                ih = 20
                vis = min(len(self._filtered), self.MAX_VISIBLE)
                total_h = vis * ih + 2
                scr_h = pygame.display.get_surface().get_height() if pygame.display.get_surface() else 600
                space_below = scr_h - (r.y + r.h)
                open_up = total_h > space_below and r.y > total_h
                dy = r.y - total_h if open_up else r.y + r.h
                dd_rect = pygame.Rect(r.x, dy, r.w, total_h)
                if dd_rect.y < 0:
                    dd_rect.y = 0
                if scr_h and dd_rect.y + dd_rect.h > scr_h:
                    dd_rect.y = scr_h - dd_rect.h
                has_scroll = len(self._filtered) > self.MAX_VISIBLE
                sb_w = 10 if has_scroll else 0
                if has_scroll:
                    sb_rect = pygame.Rect(r.x + r.w - sb_w, dd_rect.y, sb_w, dd_rect.h)
                    if sb_rect.collidepoint(mx, my):
                        total = len(self._filtered)
                        max_scroll = total - vis
                        if max_scroll > 0:
                            thumb_h = max(12, int(sb_rect.h * vis / total))
                            thumb_y = sb_rect.y + int((self._scroll_offset / max_scroll) * (sb_rect.h - thumb_h))
                            thumb = pygame.Rect(sb_rect.x, thumb_y, sb_rect.w, thumb_h)
                            if thumb.collidepoint(mx, my):
                                ratio = (my - sb_rect.y) / sb_rect.h
                                self._scroll_offset = int(ratio * max_scroll)
                            elif my < thumb_y:
                                self._scroll_offset = max(0, self._scroll_offset - vis)
                            else:
                                self._scroll_offset = min(max_scroll, self._scroll_offset + vis)
                        return True
                item_rect = pygame.Rect(r.x, dd_rect.y, r.w - sb_w, vis * ih)
                if item_rect.collidepoint(mx, my):
                    click_idx = (my - dd_rect.y) // ih
                    idx = self._scroll_offset + click_idx
                    if 0 <= idx < len(self._filtered):
                        val, lbl = self._filtered[idx]
                        self._selected = val
                        self._open = False
                        self._filter_text = ""
                        self._filtered = list(self._all_options)
                        self._scroll_offset = 0
                        if self._on_select:
                            self._on_select(val)
                        return True
                self._open = False
                self._filter_text = ""
                self._filtered = list(self._all_options)
                self._scroll_offset = 0
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and self._open:
            self._open = False
            self._filter_text = ""
            self._filtered = list(self._all_options)
            self._scroll_offset = 0
            return True
        return False

    def _get_selected_filtered_idx(self):
        for i, (val, lbl) in enumerate(self._filtered):
            if val == self._selected:
                return i
        return 0

    def _apply_filter(self):
        ft = self._filter_text.lower()
        if not ft:
            self._filtered = list(self._all_options)
        else:
            self._filtered = [(v, l) for v, l in self._all_options
                              if ft in v.lower() or ft in l.lower()]
        self._scroll_offset = 0

    def draw(self, surface):
        if not self.visible:
            return
        r = self._abs_rect()
        i18n = I18n.instancia()
        fuente = i18n.fuente(12) if i18n else pygame.font.SysFont("Arial", 12)
        label = str(self._selected)
        for val, lbl in self._all_options:
            if val == self._selected:
                label = lbl
                break
        pygame.draw.rect(surface, (50, 55, 65), r)
        pygame.draw.rect(surface, (80, 90, 105), r, 1)
        txt = fuente.render(label, True, (220, 220, 220))
        surface.blit(txt, (r.x + 6, r.y + (r.h - txt.get_height()) // 2))
        pygame.draw.polygon(surface, (160, 170, 180), [
            (r.x + r.w - 12, r.y + r.h // 2 - 2),
            (r.x + r.w - 6, r.y + r.h // 2 - 2),
            (r.x + r.w - 9, r.y + r.h // 2 + 3)
        ])
        if self._open:
            ih = 20
            vis = min(len(self._filtered), self.MAX_VISIBLE)
            total_h = vis * ih + 2
            space_below = surface.get_height() - (r.y + r.h)
            open_up = total_h > space_below and r.y > total_h
            dy = r.y - total_h if open_up else r.y + r.h
            dd_rect = pygame.Rect(r.x, dy, r.w, total_h)
            if dd_rect.y < 0:
                dd_rect.y = 0
            if dd_rect.y + dd_rect.h > surface.get_height():
                dd_rect.y = surface.get_height() - dd_rect.h
            has_scroll = len(self._filtered) > self.MAX_VISIBLE
            sb_w = 10 if has_scroll else 0
            item_w = r.w - sb_w
            pygame.draw.rect(surface, (45, 48, 56), dd_rect)
            pygame.draw.rect(surface, (70, 75, 85), dd_rect, 1)
            clip = surface.get_clip()
            surface.set_clip(dd_rect)
            for i in range(vis):
                idx = self._scroll_offset + i
                if idx >= len(self._filtered):
                    break
                val, lbl = self._filtered[idx]
                ir = pygame.Rect(r.x, dy + i * ih, item_w, ih)
                sel = val == self._selected
                bg = (60, 65, 78) if sel else (45, 48, 56)
                pygame.draw.rect(surface, bg, ir)
                if i < vis - 1:
                    pygame.draw.line(surface, (70, 75, 85), (ir.x, ir.y + ih), (ir.x + ir.w, ir.y + ih))
                txt = fuente.render(lbl, True, (200, 200, 200))
                surface.blit(txt, (ir.x + 6, ir.y + (ih - txt.get_height()) // 2))
            if has_scroll:
                sb_x = r.x + r.w - sb_w
                track = pygame.Rect(sb_x, dy, sb_w, total_h)
                pygame.draw.rect(surface, (35, 38, 44), track)
                total = len(self._filtered)
                thumb_h = max(12, int(total_h * vis / total))
                max_scroll = total - vis
                thumb_y = dy + int((self._scroll_offset / max_scroll) * (total_h - thumb_h)) if max_scroll > 0 else dy
                thumb = pygame.Rect(sb_x + 1, thumb_y, sb_w - 2, thumb_h)
                pygame.draw.rect(surface, (100, 110, 125), thumb)
                pygame.draw.rect(surface, (130, 140, 155), thumb, 1)
            if self._filter_text:
                hint = fuente.render(f'"{self._filter_text}" ({len(self._filtered)})', True, (120, 140, 160))
                surface.blit(hint, (dd_rect.x + 4, dd_rect.y + dd_rect.h - 16))
            surface.set_clip(clip)
