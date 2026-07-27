import pygame
import copy
from editor.translation import I18n
from editor.panels.base_panel import BasePanel
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.text_input import TextInput
from editor.boss_fight_types import BOSS_FIGHT_TYPES, get_default_phase, DEFAULT_PHASE_PARAMS, DEFAULT_VISUAL
from editor.boss_data import get_all_bosses, get_boss, set_boss, delete_boss, create_boss


PADDING = 6
ROW_H = 28
TOOLBAR_H = 36
HEADER_H = 26
LEFT_W = 220


class BossTab(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(x, y, w, h, i18n)
        self.bg_color = (30, 32, 36)
        self._selected_id = None
        self._list_scroll = 0
        self._dirty = False
        self._collapsed_phases = set()
        self._build_ui()

    def _build_ui(self):
        self.clear()

        tb = Panel(0, 0, self.rect.w, TOOLBAR_H, bg_color=(42, 46, 55), border_color=(60, 65, 75))
        self.add(tb)

        self._new_btn = Button(8, 4, 72, 28, self.i18n.t("boss.new"), callback=self._on_new)
        self._new_btn.parent = tb
        tb.children.append(self._new_btn)

        self._clone_btn = Button(86, 4, 72, 28, self.i18n.t("boss.clone"), callback=self._on_clone)
        self._clone_btn.parent = tb
        tb.children.append(self._clone_btn)

        self._del_btn = Button(164, 4, 72, 28, self.i18n.t("boss.delete"), callback=self._on_delete)
        self._del_btn.parent = tb
        tb.children.append(self._del_btn)

        self._save_btn = Button(240, 4, 72, 28, self.i18n.t("boss.save"), callback=self._on_save)
        self._save_btn.parent = tb
        tb.children.append(self._save_btn)

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
        self._eid_label.parent = ep
        ep.children.append(self._eid_label)
        y += 26

        lbl = Label(PADDING, y, 80, 22, self.i18n.t("boss.name") + ":", font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._name_input = TextInput(90, y, 250, 22, default="", max_chars=40, numeric_only=False)
        self._name_input.parent = ep; ep.children.append(self._name_input)
        y += 28

        lbl = Label(PADDING, y, 80, 22, self.i18n.t("boss.fight_type") + ":", font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._ft_selector = _SimpleDropdown(90, y, 180, 22, self._get_ft_options())
        self._ft_selector.parent = ep; ep.children.append(self._ft_selector)
        y += 28

        lbl = Label(PADDING, y, 80, 22, self.i18n.t("boss.max_hp") + ":", font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._hp_input = TextInput(90, y, 60, 22, default="80", max_chars=5, numeric_only=True)
        self._hp_input.parent = ep; ep.children.append(self._hp_input)

        lbl2 = Label(170, y, 140, 22, self.i18n.t("boss.needed_projectiles") + ":", font_size=12, color=(180, 185, 195))
        lbl2.parent = ep; ep.children.append(lbl2)
        self._needed_input = TextInput(310, y, 50, 22, default="3", max_chars=3, numeric_only=True)
        self._needed_input.parent = ep; ep.children.append(self._needed_input)
        y += 28

        lbl = Label(PADDING, y, 80, 22, self.i18n.t("boss.damage_per_cycle") + ":", font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._dpc_input = TextInput(90, y, 50, 22, default="20", max_chars=4, numeric_only=True)
        self._dpc_input.parent = ep; ep.children.append(self._dpc_input)

        lbl3 = Label(170, y, 80, 22, self.i18n.t("boss.icon") + ":", font_size=12, color=(180, 185, 195))
        lbl3.parent = ep; ep.children.append(lbl3)
        self._icon_input = TextInput(240, y, 50, 22, default="?", max_chars=4, numeric_only=False)
        self._icon_input.parent = ep; ep.children.append(self._icon_input)
        y += 30

        sep = Panel(PADDING, y, ep.rect.w - PADDING * 2, 2, bg_color=(55, 60, 70))
        sep.parent = ep; ep.children.append(sep)
        y += 8

        self._phases_title = Label(PADDING, y, 200, 18, self.i18n.t("boss.phases"), font_size=12, bold=True, color=(200, 210, 220))
        self._phases_title.parent = ep; ep.children.append(self._phases_title)

        self._add_phase_btn = Button(ep.rect.w - 120, y, 110, 18, "+ " + self.i18n.t("boss.add_phase"))
        self._add_phase_btn.parent = ep; ep.children.append(self._add_phase_btn)
        self._add_phase_btn.callback = self._on_add_phase
        y += 24

        self._phase_widgets = []
        self._phase_y = y
        self._rebuild_phase_editor()

    def _get_ft_options(self):
        return [(ftid, ftdata["label"]) for ftid, ftdata in BOSS_FIGHT_TYPES.items()]

    def _rebuild_phase_editor(self):
        ep = self._editor_panel
        for w in self._phase_widgets:
            if w in ep.children:
                ep.children.remove(w)
        self._phase_widgets = []
        if not self._selected_id:
            return
        boss = get_boss(self._selected_id)
        if not boss:
            return
        phases = boss.get("phases", [])
        ftype = boss.get("fight_type", "orbital")
        y = self._phase_y
        for pi, phase in enumerate(phases):
            collapsed = pi in self._collapsed_phases
            y = self._draw_phase(ep, y, pi, phase, ftype, collapsed)
        self._phase_widget_y_end = y

    def _draw_phase(self, ep, y, pi, phase, ftype, collapsed=False):
        phase_bg = Panel(PADDING, y, ep.rect.w - PADDING * 2, 24, bg_color=(45, 48, 56))
        phase_bg.parent = ep; ep.children.append(phase_bg)
        self._phase_widgets.append(phase_bg)

        lbl_text = self.i18n.t("boss.phase_n").format(n=pi + 1)
        lbl = Label(PADDING + 6, y + 2, 120, 20, lbl_text, font_size=11, bold=True, color=(200, 210, 220))
        lbl.parent = ep; ep.children.append(lbl)
        self._phase_widgets.append(lbl)

        hp_label = Label(140, y + 2, 90, 20,
                         self.i18n.t("boss.hp_threshold") + ": " + str(phase.get("hp_threshold", 0.0)),
                         font_size=10, color=(150, 160, 170))
        hp_label.parent = ep; ep.children.append(hp_label)
        self._phase_widgets.append(hp_label)

        toggle_btn = Button(ep.rect.w - 80, y + 1, 18, 18,
                            "v" if collapsed else "^")
        toggle_btn.parent = ep; ep.children.append(toggle_btn)
        self._phase_widgets.append(toggle_btn)

        del_btn = Button(ep.rect.w - 56, y + 1, 46, 18, self.i18n.t("boss.delete_phase"))
        del_btn.parent = ep; ep.children.append(del_btn)
        self._phase_widgets.append(del_btn)

        def make_toggle(idx):
            def fn():
                if idx in self._collapsed_phases:
                    self._collapsed_phases.discard(idx)
                else:
                    self._collapsed_phases.add(idx)
                self._rebuild_phase_editor()
            return fn
        toggle_btn.callback = make_toggle(pi)

        def make_del(idx):
            def fn():
                boss = get_boss(self._selected_id)
                if boss and len(boss.get("phases", [])) > 1:
                    boss["phases"].pop(idx)
                    set_boss(self._selected_id, boss)
                    self._collapsed_phases.discard(idx)
                    self._dirty = True
                    self._rebuild_phase_editor()
            return fn
        del_btn.callback = make_del(pi)

        y += 26

        if not collapsed:
            params = phase.get("params", {})
            visual = phase.get("visual", {})

            ft_config = BOSS_FIGHT_TYPES.get(ftype, {})
            p_schema = ft_config.get("phase_params", {})
            v_schema = ft_config.get("visual_schema", {})

            sub_bg = Panel(PADDING, y, ep.rect.w - PADDING * 2, 1, bg_color=(50, 55, 65))
            sub_bg.parent = ep; ep.children.append(sub_bg)
            self._phase_widgets.append(sub_bg)

            # Params section
            for pkey, pdata in p_schema.items():
                val = params.get(pkey, pdata.get("default"))
                line_h = 24
                lbl = Label(PADDING + 14, y + 2, 150, 20, pdata.get("label", pkey) + ":", font_size=10, color=(170, 175, 185))
                lbl.parent = ep; ep.children.append(lbl)
                self._phase_widgets.append(lbl)

                ptype = pdata.get("type", "string")
                inp_key = (pi, "params", pkey)

                if ptype == "float":
                    inp = TextInput(PADDING + 170, y + 1, 70, 20, default=str(val), max_chars=8, numeric_only=True)
                    inp._boss_key = inp_key
                    inp.parent = ep; ep.children.append(inp)
                    self._phase_widgets.append(inp)
                elif ptype == "int":
                    inp = TextInput(PADDING + 170, y + 1, 60, 20, default=str(val), max_chars=5, numeric_only=True)
                    inp._boss_key = inp_key
                    inp.parent = ep; ep.children.append(inp)
                    self._phase_widgets.append(inp)
                elif ptype == "color":
                    inp = TextInput(PADDING + 170, y + 1, 120, 20,
                                    default=",".join(str(c) for c in val) if val and val != [None] else "",
                                    max_chars=20, numeric_only=False)
                    inp._boss_key = inp_key
                    inp.parent = ep; ep.children.append(inp)
                    self._phase_widgets.append(inp)
                else:
                    inp = TextInput(PADDING + 170, y + 1, 120, 20, default=str(val), max_chars=20, numeric_only=False)
                    inp._boss_key = inp_key
                    inp.parent = ep; ep.children.append(inp)
                    self._phase_widgets.append(inp)
                y += line_h

            # Visual section
            if v_schema:
                sep2 = Panel(PADDING + 10, y, ep.rect.w - PADDING * 2 - 20, 1, bg_color=(55, 60, 70))
                sep2.parent = ep; ep.children.append(sep2)
                self._phase_widgets.append(sep2)
                y += 6

            for pkey, pdata in v_schema.items():
                val = visual.get(pkey, pdata.get("default"))
                line_h = 24
                lbl = Label(PADDING + 14, y + 2, 150, 20, pdata.get("label", pkey) + ":", font_size=10, color=(170, 175, 185))
                lbl.parent = ep; ep.children.append(lbl)
                self._phase_widgets.append(lbl)

                inp_key = (pi, "visual", pkey)
                ptype = pdata.get("type", "string")

                if ptype == "color":
                    if val is None:
                        display = ""
                    else:
                        display = ",".join(str(c) for c in val)
                    inp = TextInput(PADDING + 170, y + 1, 120, 20, default=display, max_chars=20, numeric_only=False)
                    inp._boss_key = inp_key
                    inp.parent = ep; ep.children.append(inp)
                    self._phase_widgets.append(inp)
                elif ptype == "int":
                    inp = TextInput(PADDING + 170, y + 1, 60, 20, default=str(val), max_chars=5, numeric_only=True)
                    inp._boss_key = inp_key
                    inp.parent = ep; ep.children.append(inp)
                    self._phase_widgets.append(inp)
                else:
                    inp = TextInput(PADDING + 170, y + 1, 120, 20, default=str(val), max_chars=20, numeric_only=False)
                    inp._boss_key = inp_key
                    inp.parent = ep; ep.children.append(inp)
                    self._phase_widgets.append(inp)
                y += line_h

        return y + 4

    def _on_add_phase(self):
        if not self._selected_id:
            return
        boss = get_boss(self._selected_id)
        if not boss:
            return
        ftype = boss.get("fight_type", "orbital")
        default = get_default_phase(ftype)
        phases = boss.get("phases", [])
        # Set threshold between last phase and 0
        if phases:
            last_th = phases[-1].get("hp_threshold", 0.0)
            default["hp_threshold"] = last_th / 2 if last_th > 0 else 0.0
        else:
            default["hp_threshold"] = 0.5
        boss.setdefault("phases", []).append(default)
        # Sort by hp_threshold descending
        boss["phases"] = sorted(boss["phases"], key=lambda p: -p.get("hp_threshold", 0.0))
        set_boss(self._selected_id, boss)
        self._dirty = True
        self._rebuild_phase_editor()

    def _on_new(self):
        base = "nuevo_boss"
        bid = base
        n = 1
        while bid in get_all_bosses():
            n += 1
            bid = f"{base}_{n}"
        create_boss(bid)
        self._dirty = True
        self._select_boss(bid)

    def _on_clone(self):
        if not self._selected_id:
            return
        boss = get_boss(self._selected_id)
        if not boss:
            return
        base = self._selected_id + "_copia"
        bid = base
        n = 1
        while bid in get_all_bosses():
            n += 1
            bid = f"{base}_{n}"
        set_boss(bid, copy.deepcopy(boss))
        self._dirty = True
        self._select_boss(bid)

    def _on_delete(self):
        if not self._selected_id:
            return
        delete_boss(self._selected_id)
        self._selected_id = None
        self._dirty = True
        self._editor_panel.visible = False

    def _on_save(self):
        if not self._selected_id:
            return
        boss = get_boss(self._selected_id)
        if not boss:
            return
        boss["nombre"] = self._name_input.text if self._name_input.text else self._selected_id
        new_ft = self._ft_selector.get_selected()
        old_ft = boss.get("fight_type", "orbital")
        if new_ft and new_ft != old_ft:
            boss["fight_type"] = new_ft
            boss["phases"] = [get_default_phase(new_ft)]
        else:
            boss["fight_type"] = boss.get("fight_type", "orbital")
        try:
            boss["vida_maxima"] = int(self._hp_input.text) if self._hp_input.text else 80
        except ValueError:
            pass
        try:
            boss["proyectiles_necesarios"] = int(self._needed_input.text) if self._needed_input.text else 3
        except ValueError:
            pass
        try:
            boss["damage_per_cycle"] = int(self._dpc_input.text) if self._dpc_input.text else 20
        except ValueError:
            pass
        boss["icono"] = self._icon_input.text if self._icon_input.text else "?"
        self._sync_phase_inputs(boss)
        set_boss(self._selected_id, boss)
        self._dirty = False
        self._rebuild_phase_editor()

    def _sync_phase_inputs(self, boss):
        for w in self._phase_widgets:
            if hasattr(w, '_boss_key'):
                pi, section, pkey = w._boss_key
                phases = boss.setdefault("phases", [])
                while pi >= len(phases):
                    phases.append(get_default_phase(boss.get("fight_type", "orbital")))
                phase = phases[pi]
                if section not in phase:
                    phase[section] = {}
                text = w.text.strip()
                ft_config = BOSS_FIGHT_TYPES.get(boss.get("fight_type", "orbital"), {})
                schema = ft_config.get(section + "_schema", {})
                pdata = schema.get(pkey, {})
                ptype = pdata.get("type", "string")
                try:
                    if ptype == "float":
                        phase[section][pkey] = float(text) if text else pdata.get("default", 0.0)
                    elif ptype == "int":
                        phase[section][pkey] = int(text) if text else pdata.get("default", 0)
                    elif ptype == "color":
                        if text == "" or text == "None":
                            phase[section][pkey] = None
                        else:
                            parts = [int(c.strip()) for c in text.split(",") if c.strip()]
                            phase[section][pkey] = tuple(parts) if len(parts) == 3 else None
                    else:
                        phase[section][pkey] = text if text else pdata.get("default", "")
                except (ValueError, TypeError):
                    phase[section][pkey] = pdata.get("default")

    def _select_boss(self, bid):
        self._selected_id = bid
        boss = get_boss(bid)
        if not boss:
            self._editor_panel.visible = False
            return
        self._editor_panel.visible = True
        self._build_editor_widgets()
        self._eid_label.text = f"ID: {bid}"
        self._name_input.text = boss.get("nombre", bid)
        ftype = boss.get("fight_type", "orbital")
        self._ft_selector.set_selected(ftype)
        self._hp_input.text = str(boss.get("vida_maxima", 80))
        self._needed_input.text = str(boss.get("proyectiles_necesarios", 3))
        self._dpc_input.text = str(boss.get("damage_per_cycle", 20))
        self._icon_input.text = boss.get("icono", "?")

    def handle_event(self, event):
        if not self.visible:
            return False

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            r = self._get_list_rect()
            if r and r.collidepoint(mx, my):
                local_y = my - r.y + self._list_scroll
                idx = local_y // ROW_H
                all_b = get_all_bosses()
                if 0 <= idx < len(all_b):
                    self._select_boss(all_b[idx])
                    self._dirty = False
                    return True

        if event.type == pygame.MOUSEWHEEL:
            r = self._get_list_rect()
            mx, my = pygame.mouse.get_pos()
            if r and r.collidepoint(mx, my):
                all_b = get_all_bosses()
                max_scroll = max(0, len(all_b) * ROW_H - r.h)
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

        i18n = I18n.instancia() if hasattr(I18n, 'instancia') else None
        fuente_b = i18n.fuente(12, bold=True) if i18n and hasattr(i18n, 'fuente') else pygame.font.SysFont("Arial", 12, bold=True)
        fuente = i18n.fuente(12) if i18n and hasattr(i18n, 'fuente') else pygame.font.SysFont("Arial", 12)

        txt = fuente_b.render(self.i18n.t("boss.list"), True, (200, 210, 220))
        surface.blit(txt, (lx + PADDING, ly + (HEADER_H - txt.get_height()) // 2))

        cnt = len(get_all_bosses())
        ctxt = fuente.render(f"({cnt})", True, (130, 140, 150))
        surface.blit(ctxt, (lx + lw - ctxt.get_width() - PADDING, ly + (HEADER_H - ctxt.get_height()) // 2))

        lr = self._get_list_rect()
        clip = surface.get_clip()
        surface.set_clip(lr)
        all_b = get_all_bosses()
        for i, bid in enumerate(all_b):
            sy = lr.y + i * ROW_H - self._list_scroll
            if sy + ROW_H < lr.y or sy > lr.y + lr.h:
                continue
            sel = bid == self._selected_id
            bg = (55, 60, 72) if sel else (38, 42, 50)
            pygame.draw.rect(surface, bg, (lr.x, sy, lr.w, ROW_H))
            if sel:
                pygame.draw.rect(surface, (70, 130, 200), (lr.x, sy, 3, ROW_H))
            txt = fuente.render(bid, True, (200, 210, 220) if sel else (160, 170, 180))
            surface.blit(txt, (lr.x + PADDING, sy + (ROW_H - txt.get_height()) // 2))
        surface.set_clip(clip)


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
        fuente = pygame.font.SysFont("Arial", 12)
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
