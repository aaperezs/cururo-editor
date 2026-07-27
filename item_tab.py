import pygame
from editor.translation import I18n
from editor.panels.base_panel import BasePanel
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.text_input import TextInput
from editor.items_data import (
    get_all_items, get_item, set_item, delete_item, create_item, get_item_list,
    rename_item, item_exists
)
from editor.sprite_registry import get_sprite_registry, get_sprite_options
from utils.sprite_manager import obtener as obtener_sprite

PADDING = 6
ROW_H = 28
TOOLBAR_H = 36
HEADER_H = 26
LEFT_W = 220

TIPO_OPTIONS = [("equipo", "Equipo"), ("objeto_clave", "Objeto Clave")]
SLOT_OPTIONS = [("cabeza", "Cabeza"), ("cuello", "Cuello"), ("cola", "Cola")]
RAREZA_OPTIONS = [("comun", "Comun"), ("rara", "Rara"), ("epica", "Epica")]
EFFECT_TYPES = [
    ("velocidad_extra", "Velocidad extra"),
    ("negar_terreno", "Negar terreno"),
    ("regeneracion_pp", "Regeneracion PP"),
    ("longitud_minima_extra", "Longitud minima extra"),
]
TERRENO_OPTIONS = [("hierba_alta", "Hierba alta"), ("hielo", "Hielo")]


class ItemTab(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(x, y, w, h, i18n)
        self.bg_color = (30, 32, 36)
        self._selected_id = None
        self._list_scroll = 0
        self._dirty = False
        self._sprite_preview_surf = None
        self._effects = []
        self._build_ui()

    def _build_ui(self):
        self.clear()
        tb = Panel(0, 0, self.rect.w, TOOLBAR_H, bg_color=(42, 46, 55), border_color=(60, 65, 75))
        self.add(tb)
        self._new_btn = Button(8, 4, 72, 28, self.i18n.t("item.new"), callback=self._on_new)
        self._new_btn.parent = tb; tb.children.append(self._new_btn)
        self._clone_btn = Button(86, 4, 72, 28, self.i18n.t("item.clone"), callback=self._on_clone)
        self._clone_btn.parent = tb; tb.children.append(self._clone_btn)
        self._del_btn = Button(164, 4, 72, 28, self.i18n.t("item.delete"), callback=self._on_delete)
        self._del_btn.parent = tb; tb.children.append(self._del_btn)
        self._save_btn = Button(240, 4, 72, 28, self.i18n.t("item.save"), callback=self._on_save)
        self._save_btn.parent = tb; tb.children.append(self._save_btn)
        self._rename_btn = Button(318, 4, 80, 28, "Renombrar", callback=self._on_rename)
        self._rename_btn.parent = tb; tb.children.append(self._rename_btn)
        rx = LEFT_W
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
        self._eid_label.parent = ep; ep.children.append(self._eid_label)
        y += 26

        lbl = Label(PADDING, y, 80, 22, self.i18n.t("item.name") + ":",
                    font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._name_input = TextInput(90, y, 200, 22, default="", max_chars=30, numeric_only=False)
        self._name_input.parent = ep; ep.children.append(self._name_input)
        y += 30

        lbl = Label(PADDING, y, 80, 22, self.i18n.t("item.desc") + ":",
                    font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._desc_input = TextInput(90, y, 250, 22, default="", max_chars=80, numeric_only=False)
        self._desc_input.parent = ep; ep.children.append(self._desc_input)
        y += 30

        # Tipo selector (shared)
        lbl = Label(PADDING, y, 80, 22, "Tipo:", font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._tipo_selector = _SimpleDropdown(90, y, 130, 22, TIPO_OPTIONS)
        self._tipo_selector.parent = ep; ep.children.append(self._tipo_selector)
        self._tipo_selector._on_select = self._on_tipo_changed
        y += 30

        # Shared: sprite selector (used by both tipos)
        lbl = Label(PADDING, y, 80, 22, self.i18n.t("item.sprite") + ":",
                    font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._sprite_selector = _SimpleDropdown(90, y, 200, 22, self._get_sprite_options())
        self._sprite_selector.parent = ep; ep.children.append(self._sprite_selector)
        y += 30

        # --- Equipo panel ---
        self._equipo_panel = Panel(0, y - PADDING, ep.rect.w, ep.rect.h - (y - PADDING),
                                   bg_color=(35, 38, 46))
        self._equipo_panel.parent = ep; ep.children.append(self._equipo_panel)
        epanel = self._equipo_panel

        ey = PADDING
        lbl = Label(PADDING, ey, 80, 22, self.i18n.t("item.slot") + ":",
                    font_size=12, color=(180, 185, 195))
        lbl.parent = epanel; epanel.children.append(lbl)
        self._slot_selector = _SimpleDropdown(90, ey, 120, 22, SLOT_OPTIONS)
        self._slot_selector.parent = epanel; epanel.children.append(self._slot_selector)
        ey += 30

        lbl = Label(PADDING, ey, 80, 22, self.i18n.t("item.rarity") + ":",
                    font_size=12, color=(180, 185, 195))
        lbl.parent = epanel; epanel.children.append(lbl)
        self._rarity_selector = _SimpleDropdown(90, ey, 120, 22, RAREZA_OPTIONS)
        self._rarity_selector.parent = epanel; epanel.children.append(self._rarity_selector)
        ey += 34

        sep = Panel(PADDING, ey, epanel.rect.w - PADDING * 2, 2, bg_color=(55, 60, 70))
        sep.parent = epanel; epanel.children.append(sep)
        ey += 10

        lbl = Label(PADDING, ey, 200, 18, self.i18n.t("item.effects"),
                    font_size=12, bold=True, color=(200, 210, 220))
        lbl.parent = epanel; epanel.children.append(lbl)
        ey += 24

        self._effect_widgets = []
        self._effect_start_y = ey
        self._rebuild_effects()

        # --- Clave panel ---
        self._clave_panel = Panel(0, y - PADDING, ep.rect.w, ep.rect.h - (y - PADDING),
                                  bg_color=(35, 38, 46))
        self._clave_panel.parent = ep; ep.children.append(self._clave_panel)
        cpanel = self._clave_panel

        cy = PADDING
        lbl = Label(PADDING, cy, 80, 22, "Key ID:", font_size=12, color=(180, 185, 195))
        lbl.parent = cpanel; cpanel.children.append(lbl)
        self._key_id_input = TextInput(90, cy, 200, 22, default="", max_chars=40, numeric_only=False)
        self._key_id_input.parent = cpanel; cpanel.children.append(self._key_id_input)

        self._apply_tipo_visibility()

    def _get_sprite_options(self):
        return get_sprite_options()

    def _rebuild_effects(self):
        ep = self._equipo_panel if hasattr(self, '_equipo_panel') and self._equipo_panel else self._editor_panel
        for row in getattr(self, "_effect_widgets", []):
            for w in row:
                if w in ep.children:
                    ep.children.remove(w)
        self._effect_widgets = []
        if not self._selected_id:
            return
        y = self._effect_start_y
        for ei, ef in enumerate(self._effects):
            widgets = []
            # Type dropdown
            dd = _SimpleDropdown(PADDING + 10, y, 130, 20, EFFECT_TYPES)
            dd.set_selected(ef.get("tipo", ""))
            dd.parent = ep; ep.children.append(dd)
            widgets.append(dd)
            # Param field based on type
            etype = ef.get("tipo", "")
            if etype == "velocidad_extra":
                inp = TextInput(150, y, 60, 20, default=str(ef.get("valor", 1.0)),
                                max_chars=6, numeric_only=False)
                inp.parent = ep; ep.children.append(inp)
                widgets.append(inp)
            elif etype == "negar_terreno":
                inp = TextInput(150, y, 100, 20,
                                default=",".join(ef.get("terrenos", [])),
                                max_chars=30, numeric_only=False)
                inp.parent = ep; ep.children.append(inp)
                widgets.append(inp)
            elif etype == "regeneracion_pp":
                inp = TextInput(150, y, 60, 20, default=str(ef.get("pp_por_frame", 0.01)),
                                max_chars=6, numeric_only=False)
                inp.parent = ep; ep.children.append(inp)
                widgets.append(inp)
            elif etype == "longitud_minima_extra":
                inp = TextInput(150, y, 60, 20, default=str(ef.get("valor", 2)),
                                max_chars=4, numeric_only=True)
                inp.parent = ep; ep.children.append(inp)
                widgets.append(inp)
            # Remove X
            rm_btn = Button(270, y, 20, 20, "X", callback=lambda ei=ei: self._remove_effect(ei))
            rm_btn.color = (180, 60, 60); rm_btn.text_color = (255, 255, 255)
            rm_btn.parent = ep; ep.children.append(rm_btn)
            widgets.append(rm_btn)
            self._effect_widgets.append(widgets)
            y += 24
        # Add effect button
        add_btn = Button(PADDING + 10, y, 120, 22, self.i18n.t("item.add_effect"),
                         callback=self._add_effect)
        add_btn.color = (50, 90, 50); add_btn.text_color = (220, 220, 220)
        add_btn.parent = ep; ep.children.append(add_btn)
        self._effect_widgets.append([add_btn])
        self._effect_add_y = y

    def _on_tipo_changed(self, val):
        self._apply_tipo_visibility()

    def _apply_tipo_visibility(self):
        if not hasattr(self, '_tipo_selector') or not self._tipo_selector:
            return
        is_equipo = (self._tipo_selector.get_selected() == "equipo")
        if hasattr(self, '_equipo_panel') and self._equipo_panel:
            self._equipo_panel.visible = is_equipo
        if hasattr(self, '_clave_panel') and self._clave_panel:
            self._clave_panel.visible = not is_equipo

    def _add_effect(self):
        self._effects.append({"tipo": "velocidad_extra", "valor": 1.0})
        self._rebuild_effects()

    def _remove_effect(self, idx):
        if 0 <= idx < len(self._effects):
            self._effects.pop(idx)
            self._rebuild_effects()

    def _on_new(self):
        base = "item_nuevo"
        iid = base
        n = 1
        while iid in get_all_items():
            iid = f"{base}_{n}"
            n += 1
        create_item(iid)
        self._select_item(iid)

    def _on_clone(self):
        if not self._selected_id:
            return
        data = get_item(self._selected_id)
        if not data:
            return
        base = self._selected_id + "_copia"
        iid = base
        n = 1
        while iid in get_all_items():
            iid = f"{base}_{n}"
            n += 1
        set_item(iid, data)
        self._select_item(iid)

    def _on_delete(self):
        if not self._selected_id:
            return
        delete_item(self._selected_id)
        self._selected_id = None
        self._dirty = True
        self._editor_panel.visible = False

    def _on_save(self):
        if not self._selected_id:
            return
        data = get_item(self._selected_id)
        if not data:
            return
        data["nombre"] = self._name_input.text or self._selected_id
        data["descripcion"] = self._desc_input.text or ""
        data["tipo"] = self._tipo_selector.get_selected() or "equipo"
        data["sprite_id"] = self._sprite_selector.get_selected() or ""
        data["key_id"] = self._key_id_input.text if (hasattr(self, '_key_id_input') and self._key_id_input) else ""
        if data["tipo"] == "equipo":
            data["slot"] = self._slot_selector.get_selected() or "cabeza"
            data["rareza"] = self._rarity_selector.get_selected() or "comun"
            # Read effects
            effects = []
            for ei, ef in enumerate(self._effects):
                row = self._effect_widgets[ei]
                tipo = row[0].get_selected() if row[0].get_selected else row[0]._selected
                entry = {"tipo": tipo}
                if tipo == "velocidad_extra":
                    try:
                        entry["valor"] = float(row[1].text)
                    except ValueError:
                        entry["valor"] = 1.0
                elif tipo == "negar_terreno":
                    text = row[1].text if isinstance(row[1], TextInput) else ""
                    entry["terrenos"] = [t.strip() for t in text.split(",") if t.strip()]
                elif tipo == "regeneracion_pp":
                    try:
                        entry["pp_por_frame"] = float(row[1].text)
                    except ValueError:
                        entry["pp_por_frame"] = 0.01
                elif tipo == "longitud_minima_extra":
                    try:
                        entry["valor"] = int(row[1].text)
                    except ValueError:
                        entry["valor"] = 2
                effects.append(entry)
            data["efectos"] = effects
        else:
            data["slot"] = ""
            data["rareza"] = "comun"
            data["efectos"] = []
        set_item(self._selected_id, data)
        self._dirty = False
        self._select_item(self._selected_id)

    def _on_rename(self):
        if not self._selected_id:
            return
        new_id = self._prompt_new_id(self._selected_id)
        if not new_id or new_id == self._selected_id:
            return
        if item_exists(new_id):
            return
        if not rename_item(self._selected_id, new_id):
            return
        # Update elementos.json references (drop_list properties)
        import os, json
        from editor.project import get_current_project
        proj = get_current_project()
        if proj:
            el_path = proj.data_path("elementos.json")
            if os.path.exists(el_path):
                try:
                    with open(el_path, "r", encoding="utf-8") as f:
                        el_data = json.load(f)
                    el_changed = False
                    for eid, eobj in el_data.items():
                        props = eobj.get("properties", {})
                        for pk, pv in props.items():
                            if isinstance(pv, list):
                                for drop in pv:
                                    if isinstance(drop, dict) and drop.get("item") == self._selected_id:
                                        drop["item"] = new_id
                                        el_changed = True
                    if el_changed:
                        with open(el_path, "w", encoding="utf-8") as f:
                            json.dump(el_data, f, indent=2, ensure_ascii=False)
                except Exception:
                    pass
            # Update event stack files referencing old item ID
            stacks_dir = proj.data_path("stacks")
            if os.path.isdir(stacks_dir):
                updated_stacks = 0
                for fname in os.listdir(stacks_dir):
                    if not fname.endswith(".json"):
                        continue
                    fpath = os.path.join(stacks_dir, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            stack_data = json.load(f)
                        stack_changed = False
                        events = stack_data.get("events", [])
                        for ev in events:
                            evt_type = ev.get("event", "")
                            if evt_type in ("give_item", "remove_item"):
                                params = ev.get("params", {})
                                if params.get("item_id") == self._selected_id:
                                    params["item_id"] = new_id
                                    stack_changed = True
                        if stack_changed:
                            with open(fpath, "w", encoding="utf-8") as f:
                                json.dump(stack_data, f, indent=2, ensure_ascii=False)
                            updated_stacks += 1
                    except Exception:
                        pass
                if updated_stacks:
                    print(f"  Actualizados {updated_stacks} archivo(s) de stack")
        self._selected_id = new_id
        self._dirty = True
        self._select_item(new_id)

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
            title = font_b.render("Renombrar item", True, (220, 190, 120))
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

    def _select_item(self, iid):
        self._selected_id = iid
        data = get_item(iid)
        if not data:
            self._editor_panel.visible = False
            return
        self._editor_panel.visible = True
        self._effects = list(data.get("efectos", []))
        self._build_editor_widgets()
        self._eid_label.text = f"ID: {iid}"
        self._name_input.text = data.get("nombre", iid)
        self._desc_input.text = data.get("descripcion", "")
        self._tipo_selector.set_selected(data.get("tipo", "equipo"))
        sid = data.get("sprite_id", "")
        self._sprite_selector.set_selected(sid)
        self._update_sprite_preview(sid)
        self._slot_selector.set_selected(data.get("slot", "cabeza"))
        self._rarity_selector.set_selected(data.get("rareza", "comun"))
        if hasattr(self, '_key_id_input') and self._key_id_input:
            self._key_id_input.text = data.get("key_id", "")
        self._apply_tipo_visibility()

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
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            r = self._get_list_rect()
            if r and r.collidepoint(mx, my):
                local_y = my - r.y + self._list_scroll
                idx = local_y // ROW_H
                all_items = get_all_items()
                if 0 <= idx < len(all_items):
                    self._select_item(all_items[idx])
                    return True
        if event.type == pygame.MOUSEWHEEL:
            r = self._get_list_rect()
            mx, my = pygame.mouse.get_pos()
            if r and r.collidepoint(mx, my):
                all_items = get_all_items()
                max_scroll = max(0, len(all_items) * ROW_H - r.h)
                self._list_scroll = max(0, min(max_scroll, self._list_scroll - event.y * ROW_H))
                return True
        if self._editor_panel and self._editor_panel.visible:
            if self._editor_panel.handle_event(event):
                return True
        return super().handle_event(event)

    def _get_list_rect(self):
        ar = self.get_abs_rect()
        return pygame.Rect(ar.x, ar.y + TOOLBAR_H + HEADER_H, LEFT_W,
                           self.rect.h - TOOLBAR_H - HEADER_H)

    def draw(self, surface):
        if not self.visible:
            return
        super().draw(surface)
        ar = self.get_abs_rect()
        lx, ly = ar.x, ar.y + TOOLBAR_H
        lw, lh = LEFT_W, self.rect.h - TOOLBAR_H
        hdr = pygame.Rect(lx, ly, lw, HEADER_H)
        pygame.draw.rect(surface, (42, 46, 55), hdr)
        pygame.draw.rect(surface, (55, 60, 70), hdr, 1)
        i18n = I18n.instancia()
        fuente_b = i18n.fuente(12, bold=True) if i18n else pygame.font.SysFont("Arial", 12, bold=True)
        fuente = i18n.fuente(12) if i18n else pygame.font.SysFont("Arial", 12)
        txt = fuente_b.render(self.i18n.t("item.list"), True, (200, 210, 220))
        surface.blit(txt, (lx + PADDING, ly + (HEADER_H - txt.get_height()) // 2))
        cnt = len(get_all_items())
        ctxt = fuente.render(f"({cnt})", True, (130, 140, 150))
        surface.blit(ctxt, (lx + lw - ctxt.get_width() - PADDING, ly + (HEADER_H - ctxt.get_height()) // 2))
        lr = self._get_list_rect()
        clip = surface.get_clip()
        surface.set_clip(lr)
        all_items = get_all_items()
        for i, iid in enumerate(all_items):
            sy = lr.y + i * ROW_H - self._list_scroll
            if sy + ROW_H < lr.y or sy > lr.y + lr.h:
                continue
            sel = iid == self._selected_id
            bg = (55, 60, 72) if sel else (38, 42, 50)
            pygame.draw.rect(surface, bg, (lr.x, sy, lr.w, ROW_H))
            if sel:
                pygame.draw.rect(surface, (70, 130, 200), (lr.x, sy, 3, ROW_H))
            data = get_item(iid)
            name = data.get("nombre", iid) if data else iid
            tc = (200, 210, 220) if sel else (160, 170, 180)
            txt = fuente.render(iid, True, tc)
            surface.blit(txt, (PADDING, sy + (ROW_H - txt.get_height()) // 2))
            nc = (130, 140, 150) if sel else (110, 120, 130)
            nt = fuente.render(f"({name})", True, nc)
            surface.blit(nt, (100, sy + (ROW_H - nt.get_height()) // 2))
        surface.set_clip(clip)
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
        """Close other dropdowns in the same parent."""
        if not self.parent:
            return
        for child in list(self.parent.children):
            if isinstance(child, _SimpleDropdown) and child is not self and child._open:
                child._open = False
                child._filter_text = ""
                child._filtered = list(child._all_options)
                child._scroll_offset = 0

    def _bring_to_front(self):
        """Move self to end of parent.children so open list draws last (on top)."""
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
            # Scrollbar
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
            # Filter hint
            if self._filter_text:
                hint = fuente.render(f'"{self._filter_text}" ({len(self._filtered)})', True, (120, 140, 160))
                surface.blit(hint, (dd_rect.x + 4, dd_rect.y + dd_rect.h - 16))
            surface.set_clip(clip)
