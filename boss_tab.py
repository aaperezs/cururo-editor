import copy
import os

import pygame

from editor.boss_data import get_all_bosses, get_boss, set_boss
from editor.boss_fight_types import BOSS_FIGHT_TYPES, get_default_phase
from editor.boss_crud import (
    create_new_boss, clone_boss, delete_boss_by_id, save_boss,
    add_phase, delete_phase,
)
from editor.panels.base_panel import BasePanel
from editor.project import get_current_project
from editor.translation import I18n
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.scroll_container import ScrollContainer
from editor.widgets.text_input import TextInput
from editor.widgets.simple_dropdown import SimpleDropdown as _SimpleDropdown

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

        self._build_sprite_section(ep, y)
        self._build_phases_section(ep)

    def _build_phases_section(self, ep):
        y = getattr(self, "_phases_title_y", 200)
        self._phases_title = Label(PADDING, y, 200, 18, self.i18n.t("boss.phases"), font_size=12, bold=True, color=(200, 210, 220))
        self._phases_title.parent = ep
        ep.children.append(self._phases_title)

        self._add_phase_btn = Button(ep.rect.w - 120, y, 110, 18, "+ " + self.i18n.t("boss.add_phase"))
        self._add_phase_btn.parent = ep
        ep.children.append(self._add_phase_btn)
        self._add_phase_btn.callback = self._on_add_phase
        y += 24

        self._phase_widgets = []
        self._phases_scroll = ScrollContainer(0, y, ep.rect.w,
                                              max(1, ep.rect.h - y))
        self._phases_scroll.parent = ep
        ep.children.append(self._phases_scroll)
        self._rebuild_phase_editor()

    def _build_sprite_section(self, ep, y):
        lbl = Label(PADDING, y, 80, 22, self.i18n.t("boss.sprite") + ":", font_size=12, color=(180, 185, 195))
        lbl.parent = ep
        ep.children.append(lbl)
        self._sprite_selector = _SimpleDropdown(90, y, 200, 22, self._get_sprite_options())
        self._sprite_selector.parent = ep
        ep.children.append(self._sprite_selector)
        self._sprite_selector._on_select = self._on_sprite_changed
        y += 28

        lbl = Label(PADDING, y, 80, 22, self.i18n.t("boss.sprite_rows") + ":", font_size=11, color=(180, 185, 195))
        lbl.parent = ep
        ep.children.append(lbl)
        self._sprite_rows_input = TextInput(90, y, 40, 22, default="1", max_chars=3, numeric_only=True)
        self._sprite_rows_input.parent = ep
        ep.children.append(self._sprite_rows_input)

        lbl = Label(150, y, 60, 22, self.i18n.t("boss.sprite_cols") + ":", font_size=11, color=(180, 185, 195))
        lbl.parent = ep
        ep.children.append(lbl)
        self._sprite_cols_input = TextInput(205, y, 40, 22, default="1", max_chars=3, numeric_only=True)
        self._sprite_cols_input.parent = ep
        ep.children.append(self._sprite_cols_input)

        lbl = Label(265, y, 110, 22, self.i18n.t("boss.sprite_cell") + ":", font_size=11, color=(180, 185, 195))
        lbl.parent = ep
        ep.children.append(lbl)
        self._sprite_fw_input = TextInput(370, y, 40, 22, default="60", max_chars=4, numeric_only=True)
        self._sprite_fw_input.parent = ep
        ep.children.append(self._sprite_fw_input)

        lbl = Label(420, y, 8, 22, "x", font_size=11, color=(180, 185, 195))
        lbl.parent = ep
        ep.children.append(lbl)
        self._sprite_fh_input = TextInput(430, y, 40, 22, default="60", max_chars=4, numeric_only=True)
        self._sprite_fh_input.parent = ep
        ep.children.append(self._sprite_fh_input)

        lbl = Label(500, y, 80, 22, self.i18n.t("boss.sprite_interval") + ":", font_size=11, color=(180, 185, 195))
        lbl.parent = ep
        ep.children.append(lbl)
        self._sprite_interval_input = TextInput(585, y, 45, 22, default="12", max_chars=4, numeric_only=True)
        self._sprite_interval_input.parent = ep
        ep.children.append(self._sprite_interval_input)
        y += 28

        self._sprite_preview = _SheetPreview(90, y, ep.rect.w - PADDING * 2 - 90, 92)
        self._sprite_preview.parent = ep
        self._sprite_preview.host = self
        ep.children.append(self._sprite_preview)
        y += 100

        self._phases_title_y = y

    def _get_sprite_options(self):
        options = [("", "--")]
        p = get_current_project()
        if not p:
            return options
        assets_dir_path = p.assets_path()
        if not os.path.isdir(assets_dir_path):
            return options
        for fname in sorted(os.listdir(assets_dir_path)):
            if not fname.lower().endswith(".png"):
                continue
            stem = os.path.splitext(fname)[0]
            if not options or options[-1][0] != stem:
                options.append((stem, stem))
        return options

    def _on_sprite_changed(self, _val=None):
        pass

    def _sprite_grid(self):
        try:
            return (int(self._sprite_rows_input.text or "1"),
                    int(self._sprite_cols_input.text or "1"))
        except ValueError:
            return (1, 1)

    def _load_sheet_frames(self):
        name = self._sprite_selector.get_selected()
        if not name:
            return None
        rows, cols = self._sprite_grid()
        try:
            fw = int(self._sprite_fw_input.text or "0")
            fh = int(self._sprite_fh_input.text or "0")
        except ValueError:
            return None
        if fw <= 0 or fh <= 0:
            return None
        p = get_current_project()
        path = p.assets_path(name + ".png") if p else None
        if not path or not os.path.exists(path):
            return None
        try:
            hoja = pygame.image.load(path).convert_alpha()
        except pygame.error:
            return None
        w, h = hoja.get_size()
        if fw * cols > w or fh * rows > h:
            return None
        frames = []
        for r in range(rows):
            for c in range(cols):
                frames.append(hoja.subsurface((c * fw, r * fh, fw, fh)).copy())
        return frames

    def _get_ft_options(self):
        return [(ftid, ftdata["label"]) for ftid, ftdata in BOSS_FIGHT_TYPES.items()]

    def _rebuild_phase_editor(self):
        sc = self._phases_scroll
        sc.clear()
        self._phase_widgets = []
        if not self._selected_id:
            return
        boss = get_boss(self._selected_id)
        if not boss:
            return
        phases = boss.get("phases", [])
        ftype = boss.get("fight_type", "orbital")
        y = 0
        for pi, phase in enumerate(phases):
            collapsed = pi in self._collapsed_phases
            y = self._draw_phase(sc, y, pi, phase, ftype, collapsed)
        sc.set_content_height(y)
        self._phase_widget_y_end = y

    def _draw_phase(self, sc, y, pi, phase, ftype, collapsed=False):
        cw = sc.rect.w - sc.scrollbar_w
        phase_bg = Panel(PADDING, y, cw - PADDING * 2, 24, bg_color=(45, 48, 56))
        sc.add(phase_bg)
        self._phase_widgets.append(phase_bg)

        lbl_text = self.i18n.t("boss.phase_n").format(n=pi + 1)
        lbl = Label(PADDING + 6, y + 2, 120, 20, lbl_text, font_size=11, bold=True, color=(200, 210, 220))
        sc.add(lbl)
        self._phase_widgets.append(lbl)

        hp_label = Label(140, y + 2, 90, 20,
                         self.i18n.t("boss.hp_threshold") + ": " + str(phase.get("hp_threshold", 0.0)),
                         font_size=10, color=(150, 160, 170))
        sc.add(hp_label)
        self._phase_widgets.append(hp_label)

        toggle_btn = Button(cw - 80, y + 1, 18, 18,
                            "v" if collapsed else "^")
        sc.add(toggle_btn)
        self._phase_widgets.append(toggle_btn)

        del_btn = Button(cw - 56, y + 1, 46, 18, self.i18n.t("boss.delete_phase"))
        sc.add(del_btn)
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

            sub_bg = Panel(PADDING, y, cw - PADDING * 2, 1, bg_color=(50, 55, 65))
            sc.add(sub_bg)
            self._phase_widgets.append(sub_bg)
            y += 4

            # Params section (agrupada)
            y = self._draw_section_fields(sc, y, pi, "params", p_schema,
                                          ft_config.get("phase_groups", {}), params, cw)

            # Visual section (agrupada)
            if v_schema:
                sep2 = Panel(PADDING + 10, y, cw - PADDING * 2 - 20, 1, bg_color=(55, 60, 70))
                sc.add(sep2)
                self._phase_widgets.append(sep2)
                y += 6
                y = self._draw_section_fields(sc, y, pi, "visual", v_schema,
                                              ft_config.get("visual_groups", {}), visual, cw)

        return y + 4

    def _group_fields_ordered(self, schema, groups_cfg):
        """Devuelve [(gid, gcfg, [(pkey, pdata), ...])] respetando orden del schema
        dentro de cada grupo y el orden de los grupos definidos en el schema."""
        groups = {}
        order = []
        for gid in groups_cfg:
            if gid not in groups:
                groups[gid] = []
                order.append(gid)
        for pkey, pdata in schema.items():
            gid = pdata.get("group") or "general"
            if gid not in groups:
                groups[gid] = []
                order.append(gid)
            groups[gid].append((pkey, pdata))
        return [(gid, groups_cfg.get(gid, {}), groups[gid]) for gid in order]

    def _draw_field(self, sc, x, y, pkey, pdata, val, inp_key):
        lbl = Label(x, y + 2, 132, 20, pdata.get("label", pkey) + ":", font_size=10, color=(170, 175, 185))
        sc.add(lbl)
        self._phase_widgets.append(lbl)

        ptype = pdata.get("type", "string")
        inp_x = x + 136
        if ptype == "float":
            inp = TextInput(inp_x, y + 1, 70, 20, default=str(val), max_chars=8, numeric_only=True)
        elif ptype == "int":
            inp = TextInput(inp_x, y + 1, 60, 20, default=str(val), max_chars=5, numeric_only=True)
        elif ptype == "color":
            display = "" if val is None or val == [None] else ",".join(str(c) for c in val)
            inp = TextInput(inp_x, y + 1, 110, 20, default=display, max_chars=24, numeric_only=False)
        else:
            inp = TextInput(inp_x, y + 1, 120, 20, default=str(val), max_chars=20, numeric_only=False)
        inp._boss_key = inp_key
        sc.add(inp)
        self._phase_widgets.append(inp)

    def _draw_section_fields(self, sc, y, pi, section, schema, groups_cfg, values, cw):
        for gid, gcfg, fields in self._group_fields_ordered(schema, groups_cfg):
            if not fields:
                continue
            gh = Label(PADDING + 14, y, 240, 14, self.i18n.t(gcfg.get("label_key", "boss.group.general")),
                       font_size=10, bold=True, color=(180, 185, 195))
            sc.add(gh)
            self._phase_widgets.append(gh)
            y += 14
            gsep = Panel(PADDING + 10, y, cw - PADDING * 2 - 20, 1, bg_color=(55, 60, 70))
            sc.add(gsep)
            self._phase_widgets.append(gsep)
            y += 4

            col_x = [PADDING + 14, PADDING + 14 + 320]
            for i in range(0, len(fields), 2):
                row = fields[i:i + 2]
                for j, (pkey, pdata) in enumerate(row):
                    val = values.get(pkey, pdata.get("default"))
                    inp_key = (pi, section, pkey)
                    self._draw_field(sc, col_x[j], y, pkey, pdata, val, inp_key)
                y += 24
        return y

    def _on_add_phase(self):
        if not self._selected_id:
            return
        add_phase(self._selected_id)
        self._dirty = True
        self._rebuild_phase_editor()

    def _on_new(self):
        bid = create_new_boss()
        self._dirty = True
        self._select_boss(bid)

    def _on_clone(self):
        if not self._selected_id:
            return
        bid = clone_boss(self._selected_id)
        if bid:
            self._dirty = True
            self._select_boss(bid)

    def _on_delete(self):
        if not self._selected_id:
            return
        delete_boss_by_id(self._selected_id)
        self._selected_id = None
        self._dirty = True
        self._editor_panel.visible = False

    def _on_save(self):
        if not self._selected_id:
            return
        boss = get_boss(self._selected_id)
        if not boss:
            return
        fields = {}
        fields["nombre"] = self._name_input.text if self._name_input.text else self._selected_id
        new_ft = self._ft_selector.get_selected()
        old_ft = boss.get("fight_type", "orbital")
        if new_ft and new_ft != old_ft:
            fields["fight_type"] = new_ft
            fields["phases"] = [get_default_phase(new_ft)]
        else:
            fields["fight_type"] = boss.get("fight_type", "orbital")
        try:
            fields["vida_maxima"] = int(self._hp_input.text) if self._hp_input.text else 80
        except ValueError:
            pass
        try:
            fields["proyectiles_necesarios"] = int(self._needed_input.text) if self._needed_input.text else 3
        except ValueError:
            pass
        try:
            fields["damage_per_cycle"] = int(self._dpc_input.text) if self._dpc_input.text else 20
        except ValueError:
            pass
        fields["icono"] = self._icon_input.text if self._icon_input.text else "?"
        fields["sprite_sheet"] = self._sprite_selector.get_selected() or ""
        try:
            fields["sprite_rows"] = int(self._sprite_rows_input.text or "1")
            fields["sprite_cols"] = int(self._sprite_cols_input.text or "1")
        except ValueError:
            fields["sprite_rows"] = 1
            fields["sprite_cols"] = 1
        try:
            fields["sprite_frame_w"] = int(self._sprite_fw_input.text or "0")
            fields["sprite_frame_h"] = int(self._sprite_fh_input.text or "0")
        except ValueError:
            fields["sprite_frame_w"] = 0
            fields["sprite_frame_h"] = 0
        try:
            fields["sprite_interval"] = int(self._sprite_interval_input.text or "0")
        except ValueError:
            fields["sprite_interval"] = 0
        boss.update(fields)
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
                schema_key = "phase_params" if section == "params" else "visual_schema"
                schema = ft_config.get(schema_key, {})
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
        self._sprite_selector.set_selected(boss.get("sprite_sheet", ""))
        self._sprite_rows_input.text = str(boss.get("sprite_rows", 1))
        self._sprite_cols_input.text = str(boss.get("sprite_cols", 1))
        self._sprite_fw_input.text = str(boss.get("sprite_frame_w", 60))
        self._sprite_fh_input.text = str(boss.get("sprite_frame_h", 60))
        self._sprite_interval_input.text = str(boss.get("sprite_interval", 12))

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






class _SheetPreview:
    ROWS = 2
    COLS = 4

    def __init__(self, x, y, w, h):
        self.rect = pygame.Rect(x, y, w, h)
        self.parent = None
        self.visible = True
        self.enabled = True

    def handle_event(self, event):
        return False

    def _abs_rect(self):
        if self.parent:
            pr = (self.parent.get_abs_rect() if hasattr(self.parent, 'get_abs_rect')
                  else self.parent.rect)
            return pygame.Rect(pr.x + self.rect.x, pr.y + self.rect.y,
                               self.rect.w, self.rect.h)
        return self.rect.copy()

    def draw(self, surface):
        if not self.visible:
            return
        host = getattr(self, "host", None) or self.parent
        loader = getattr(host, "_load_sheet_frames", None)
        frames = loader() if loader else None

        r = self._abs_rect()
        pygame.draw.rect(surface, (40, 43, 50), r)
        pygame.draw.rect(surface, (60, 65, 75), r, 1)

        if not frames:
            fuente = pygame.font.SysFont("Arial", 11)
            txt = fuente.render("--", True, (130, 140, 150))
            surface.blit(txt, (r.x + 6, r.y + (r.h - txt.get_height()) // 2))
            return

        cols = self.COLS
        rows = self.ROWS
        for i in range(min(len(frames), rows * cols)):
            frame = frames[i]
            px = r.x + 6 + (i % cols) * (64 + 6)
            py = r.y + 6 + (i // cols) * (40 + 6)
            fw, fh = frame.get_size()
            scale = min(56 / fw, 34 / fh, 1.0)
            show_w = max(1, int(fw * scale))
            show_h = max(1, int(fh * scale))
            scaled = pygame.transform.scale(frame, (show_w, show_h))
            pygame.draw.rect(surface, (70, 75, 85), (px - 2, py - 2, show_w + 4, show_h + 4))
            surface.blit(scaled, (px, py))
