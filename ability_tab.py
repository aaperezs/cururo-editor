import pygame
from editor.translation import I18n
from editor.panels.base_panel import BasePanel
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.text_input import TextInput
from editor.ability_data import (
    get_abilities, get_ability, set_ability, delete_ability,
    create_ability, get_ability_list, get_skin_list, is_protected
)

PADDING = 6
ROW_H = 28
TOOLBAR_H = 36
HEADER_H = 26
LEFT_W = 220
TECLA_OPTIONS = [("Q", "Q"), ("W", "W"), ("E", "E"), ("R", "R"), ("TAB", "TAB")]


class AbilityTab(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(x, y, w, h, i18n)
        self.bg_color = (30, 32, 36)
        self._selected_id = None
        self._list_scroll = 0
        self._dirty = False
        self._build_ui()

    def _build_ui(self):
        self.clear()
        tb = Panel(0, 0, self.rect.w, TOOLBAR_H, bg_color=(42, 46, 55), border_color=(60, 65, 75))
        self.add(tb)
        self._new_btn = Button(8, 4, 72, 28, self.i18n.t("ability.new"), callback=self._on_new)
        self._new_btn.parent = tb; tb.children.append(self._new_btn)
        self._clone_btn = Button(86, 4, 72, 28, self.i18n.t("ability.clone"), callback=self._on_clone)
        self._clone_btn.parent = tb; tb.children.append(self._clone_btn)
        self._del_btn = Button(164, 4, 72, 28, self.i18n.t("ability.delete"), callback=self._on_delete)
        self._del_btn.parent = tb; tb.children.append(self._del_btn)
        self._save_btn = Button(240, 4, 72, 28, self.i18n.t("ability.save"), callback=self._on_save)
        self._save_btn.parent = tb; tb.children.append(self._save_btn)
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

        lbl = Label(PADDING, y, 100, 22, self.i18n.t("ability.name") + ":",
                    font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._name_input = TextInput(110, y, 200, 22, default="", max_chars=30, numeric_only=False)
        self._name_input.parent = ep; ep.children.append(self._name_input)
        y += 30

        lbl = Label(PADDING, y, 100, 22, self.i18n.t("ability.pp_max") + ":",
                    font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._pp_input = TextInput(110, y, 60, 22, default="3", max_chars=4, numeric_only=True)
        self._pp_input.parent = ep; ep.children.append(self._pp_input)
        y += 30

        lbl = Label(PADDING, y, 100, 22, self.i18n.t("ability.key") + ":",
                    font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._key_selector = _SimpleDropdown(110, y, 80, 22, TECLA_OPTIONS)
        self._key_selector.parent = ep; ep.children.append(self._key_selector)
        y += 30

        lbl = Label(PADDING, y, 100, 22, self.i18n.t("ability.effect") + ":",
                    font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._effect_input = TextInput(110, y, 200, 22, default="", max_chars=30, numeric_only=False)
        self._effect_input.parent = ep; ep.children.append(self._effect_input)
        y += 30

        lbl = Label(PADDING, y, 100, 22, self.i18n.t("ability.skin") + ":",
                    font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._skin_selector = _SimpleDropdown(110, y, 120, 22, get_skin_list())
        self._skin_selector.parent = ep; ep.children.append(self._skin_selector)
        y += 30

        lbl = Label(PADDING, y, 100, 22, self.i18n.t("ability.action") + ":",
                    font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._action_input = TextInput(110, y, 200, 22, default="", max_chars=40, numeric_only=False)
        self._action_input.parent = ep; ep.children.append(self._action_input)
        y += 30

        # Color
        sep = Panel(PADDING, y, ep.rect.w - PADDING * 2, 2, bg_color=(55, 60, 70))
        sep.parent = ep; ep.children.append(sep)
        y += 10

        lbl = Label(PADDING, y, 200, 18, self.i18n.t("ability.color"),
                    font_size=12, bold=True, color=(200, 210, 220))
        lbl.parent = ep; ep.children.append(lbl)
        y += 24

        for ch_name, ch_key in [("R", 0), ("G", 1), ("B", 2)]:
            lbl = Label(PADDING + 10, y, 40, 22, ch_name + ":", font_size=11, color=(180, 185, 195))
            lbl.parent = ep; ep.children.append(lbl)
            inp = TextInput(55, y, 50, 22, default="0", max_chars=3, numeric_only=True)
            inp.parent = ep; ep.children.append(inp)
            setattr(self, f"_color_{ch_key}_input", inp)
            y += 26

        self._color_swatch = pygame.Rect(120, y - 52, 28, 28)
        y += 10

    def _on_new(self):
        base = "nueva_habilidad"
        hid = base
        n = 1
        while hid in get_abilities():
            hid = f"{base}_{n}"
            n += 1
        create_ability(hid)
        self._select_ability(hid)

    def _on_clone(self):
        if not self._selected_id:
            return
        data = get_ability(self._selected_id)
        if not data:
            return
        base = self._selected_id + "_copia"
        hid = base
        n = 1
        while hid in get_abilities():
            hid = f"{base}_{n}"
            n += 1
        set_ability(hid, data)
        self._select_ability(hid)

    def _on_delete(self):
        if not self._selected_id:
            return
        if is_protected(self._selected_id):
            return
        delete_ability(self._selected_id)
        self._selected_id = None
        self._dirty = True
        self._editor_panel.visible = False

    def _on_save(self):
        if not self._selected_id:
            return
        data = get_ability(self._selected_id)
        if not data:
            return
        data["nombre"] = self._name_input.text or self._selected_id
        data["pp_max"] = int(self._pp_input.text) if self._pp_input.text else 3
        data["tecla"] = self._key_selector.get_selected() or "Q"
        data["efecto"] = self._effect_input.text or "base"
        skin = self._skin_selector.get_selected()
        if skin:
            data["skin"] = skin
        data["accion"] = self._action_input.text or ""
        r = int(getattr(self, "_color_0_input").text or "0")
        g = int(getattr(self, "_color_1_input").text or "0")
        b = int(getattr(self, "_color_2_input").text or "0")
        data["color"] = [r, g, b]
        set_ability(self._selected_id, data)
        self._dirty = False
        self._select_ability(self._selected_id)

    def _select_ability(self, hid):
        self._selected_id = hid
        data = get_ability(hid)
        if not data:
            self._editor_panel.visible = False
            return
        self._editor_panel.visible = True
        self._build_editor_widgets()
        self._eid_label.text = f"ID: {hid}" + (" " + self.i18n.t("ability.protected") if is_protected(hid) else "")
        self._name_input.text = data.get("nombre", hid)
        self._pp_input.text = str(data.get("pp_max", 3))
        self._key_selector.set_selected(data.get("tecla", "Q"))
        self._effect_input.text = data.get("efecto", "")
        self._skin_selector.set_selected(data.get("skin", "base"))
        self._action_input.text = data.get("accion", "")
        color = data.get("color", [0, 255, 0])
        for i in range(3):
            getattr(self, f"_color_{i}_input").text = str(color[i]) if i < len(color) else "0"
        self._del_btn.enabled = not is_protected(hid)

    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            r = self._get_list_rect()
            if r and r.collidepoint(mx, my):
                local_y = my - r.y + self._list_scroll
                idx = local_y // ROW_H
                all_ab = sorted(get_abilities().keys())
                if 0 <= idx < len(all_ab):
                    self._select_ability(all_ab[idx])
                    return True
        if event.type == pygame.MOUSEWHEEL:
            r = self._get_list_rect()
            mx, my = pygame.mouse.get_pos()
            if r and r.collidepoint(mx, my):
                all_ab = sorted(get_abilities().keys())
                max_scroll = max(0, len(all_ab) * ROW_H - r.h)
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
        txt = fuente_b.render(self.i18n.t("ability.list"), True, (200, 210, 220))
        surface.blit(txt, (lx + PADDING, ly + (HEADER_H - txt.get_height()) // 2))
        cnt = len(get_abilities())
        ctxt = fuente.render(f"({cnt})", True, (130, 140, 150))
        surface.blit(ctxt, (lx + lw - ctxt.get_width() - PADDING, ly + (HEADER_H - ctxt.get_height()) // 2))
        lr = self._get_list_rect()
        clip = surface.get_clip()
        surface.set_clip(lr)
        all_ab = sorted(get_abilities().keys())
        for i, hid in enumerate(all_ab):
            sy = lr.y + i * ROW_H - self._list_scroll
            if sy + ROW_H < lr.y or sy > lr.y + lr.h:
                continue
            sel = hid == self._selected_id
            bg = (55, 60, 72) if sel else (38, 42, 50)
            pygame.draw.rect(surface, bg, (lr.x, sy, lr.w, ROW_H))
            if sel:
                pygame.draw.rect(surface, (70, 130, 200), (lr.x, sy, 3, ROW_H))
            data = get_ability(hid)
            name = data.get("nombre", hid) if data else hid
            tc = (200, 210, 220) if sel else (160, 170, 180)
            txt = fuente.render(hid, True, tc)
            surface.blit(txt, (PADDING, sy + (ROW_H - txt.get_height()) // 2))
            nc = (130, 140, 150) if sel else (110, 120, 130)
            nt = fuente.render(f"({name})", True, nc)
            surface.blit(nt, (100, sy + (ROW_H - nt.get_height()) // 2))
            if is_protected(hid):
                lock = fuente.render("o", True, (200, 180, 60))
                surface.blit(lock, (lr.x + lr.w - 18, sy + (ROW_H - lock.get_height()) // 2))
        surface.set_clip(clip)
        # Color swatch
        if self._selected_id:
            r = int(getattr(self, "_color_0_input").text or "0") if hasattr(self, "_color_0_input") else 0
            g = int(getattr(self, "_color_1_input").text or "0") if hasattr(self, "_color_1_input") else 0
            b = int(getattr(self, "_color_2_input").text or "0") if hasattr(self, "_color_2_input") else 0
            r = max(0, min(255, r)); g = max(0, min(255, g)); b = max(0, min(255, b))
            ep = self._editor_panel
            swatch = pygame.Rect(ep.rect.x + 120, ep.rect.y + self._color_swatch.y, 28, 28)
            pygame.draw.rect(surface, (r, g, b), swatch)
            pygame.draw.rect(surface, (80, 90, 105), swatch, 1)


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
