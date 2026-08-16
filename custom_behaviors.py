import pygame
from editor.translation import I18n
from editor.panels.base_panel import BasePanel
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.text_input import TextInput
from editor.behaviors import (
    get_behaviors, get_behavior, set_behavior, delete_behavior,
    get_behavior_list, get_behavior_groups,
)

PADDING = 6
TOOLBAR_H = 36
LEFT_W = 220
LIST_H = 24
ROW_H = 28
PROP_H = 32
SCROLLBAR_W = 10


class CustomBehaviorsPanel(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(x, y, w, h, i18n)
        self.bg_color = (30, 32, 36)
        self._selected_id = None
        self._list_scroll = 0
        self._prop_scroll = 0
        self._build_ui()

    def _build_ui(self):
        self.clear()

        tb = Panel(0, 0, self.rect.w, TOOLBAR_H, bg_color=(42, 46, 55), border_color=(60, 65, 75))
        self.add(tb)

        self._new_btn = Button(8, 4, 72, 28, self.i18n.t("behavior.new"), callback=self._on_new)
        self._new_btn.parent = tb; tb.children.append(self._new_btn)

        self._save_btn = Button(86, 4, 72, 28, self.i18n.t("behavior.save"), callback=self._on_save)
        self._save_btn.parent = tb; tb.children.append(self._save_btn)

        self._del_btn = Button(164, 4, 72, 28, self.i18n.t("behavior.delete"), callback=self._on_delete)
        self._del_btn.parent = tb; tb.children.append(self._del_btn)

        self._editor_panel = Panel(LEFT_W, TOOLBAR_H, self.rect.w - LEFT_W, self.rect.h - TOOLBAR_H,
                                   bg_color=(35, 38, 46))
        self.add(self._editor_panel)

    def _refresh_list(self):
        pass

    def _on_new(self):
        names = [bid for bid, _ in get_behavior_list()]
        base = "custom"
        n = 1
        while f"{base}_{n}" in names:
            n += 1
        bid = f"{base}_{n}"
        data = {
            "label": f"Custom {n}",
            "group": "decoracion",
            "class_path": "entities.generic.GenericEntity",
            "target_list": None,
            "properties": {}
        }
        set_behavior(bid, data)
        self._selected_id = bid
        self._prop_scroll = 0
        self._rebuild_editor()

    def _rebuild_editor(self):
        ep = self._editor_panel
        ep.clear()

        if not self._selected_id:
            lbl = Label(PADDING, PADDING, 200, 22,
                        self.i18n.t("behavior.no_selection"), font_size=12, color=(160, 165, 175))
            lbl.parent = ep; ep.children.append(lbl)
            return

        data = get_behavior(self._selected_id)
        if not data:
            return

        y = PADDING

        lbl = Label(PADDING, y, 80, 22, self.i18n.t("behavior.id"), font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._id_input = TextInput(90, y, 150, 22, default=self._selected_id, numeric_only=False, font_size=13)
        self._id_input.parent = ep; ep.children.append(self._id_input)
        self._id_input.numeric_only = False

        y += ROW_H

        lbl = Label(PADDING, y, 80, 22, self.i18n.t("behavior.label"), font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._label_input = TextInput(90, y, 200, 22, default=data.get("label", ""), numeric_only=False, font_size=13)
        self._label_input.parent = ep; ep.children.append(self._label_input)
        self._label_input.numeric_only = False

        y += ROW_H

        lbl = Label(PADDING, y, 80, 22, self.i18n.t("behavior.group"), font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        groups = get_behavior_groups()
        group_opts = [(g, g) for g in groups] + [("nuevo", "+ Nuevo grupo")]
        self._group_dd = _SimpleDropdown(90, y, 200, 22, group_opts,
                                         selected=data.get("group", "decoracion"))
        self._group_dd.parent = ep; ep.children.append(self._group_dd)

        y += ROW_H

        lbl = Label(PADDING, y, 80, 22, self.i18n.t("behavior.class_path"), font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._cp_input = TextInput(160, y, 200, 22, default=data.get("class_path") or "",
                                   numeric_only=False, font_size=13)
        self._cp_input.parent = ep; ep.children.append(self._cp_input)
        self._cp_input.numeric_only = False

        y += ROW_H

        lbl = Label(PADDING, y, 80, 22, self.i18n.t("behavior.target_list"), font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._tl_input = TextInput(160, y, 200, 22, default=data.get("target_list") or "",
                                   numeric_only=False, font_size=13)
        self._tl_input.parent = ep; ep.children.append(self._tl_input)
        self._tl_input.numeric_only = False

        y += ROW_H + 6

        sep = Panel(PADDING, y, ep.rect.w - PADDING * 2 - LEFT_W, 2, bg_color=(55, 60, 68))
        sep.parent = ep; ep.children.append(sep)
        y += 10

        header_lbl = Label(PADDING, y, 120, 22, self.i18n.t("behavior.properties"), font_size=12, color=(200, 205, 215))
        header_lbl.parent = ep; ep.children.append(header_lbl)
        add_prop_btn = Button(130, y, 80, 22, "+ Prop", callback=self._on_add_property)
        add_prop_btn.parent = ep; ep.children.append(add_prop_btn)
        y += ROW_H

        self._prop_widgets = []
        props = data.get("properties", {})
        for pkey, pdata in props.items():
            if y > ep.rect.h - 40:
                break
            bg = (42, 46, 55) if len(self._prop_widgets) % 2 == 0 else (38, 42, 50)
            prop_bg = Panel(0, y, ep.rect.w, PROP_H, bg_color=bg)
            prop_bg.parent = ep; ep.children.append(prop_bg)

            del_btn = Button(ep.rect.w - 28, y + 4, 24, 24, "X", callback=lambda k=pkey: self._on_remove_property(k))
            del_btn.parent = ep; ep.children.append(del_btn)

            lbl = Label(PADDING, y + 6, 60, 20, pkey + ":", font_size=11, color=(160, 165, 175))
            lbl.parent = ep; ep.children.append(lbl)

            ptype = pdata.get("type", "string")
            ptype_lbl = Label(70, y + 6, 50, 20, ptype, font_size=11, color=(100, 130, 200))
            ptype_lbl.parent = ep; ep.children.append(ptype_lbl)

            default_val = str(pdata.get("default", ""))
            dv = TextInput(130, y + 3, 100, 22, default=default_val, numeric_only=ptype == "int", font_size=12)
            dv.parent = ep; ep.children.append(dv)

            self._prop_widgets.append((pkey, pdata, dv, del_btn))
            y += PROP_H

    def _on_add_property(self):
        if not self._selected_id:
            return
        data = get_behavior(self._selected_id)
        if not data:
            return
        props = data.setdefault("properties", {})
        base = "prop"
        n = 1
        while f"{base}_{n}" in props:
            n += 1
        props[f"{base}_{n}"] = {"type": "string", "default": "", "label": f"Prop {n}"}
        set_behavior(self._selected_id, data)
        self._rebuild_editor()

    def _on_remove_property(self, key):
        if not self._selected_id:
            return
        data = get_behavior(self._selected_id)
        if not data:
            return
        data.get("properties", {}).pop(key, None)
        set_behavior(self._selected_id, data)
        self._prop_scroll = 0
        self._rebuild_editor()

    def _on_save(self):
        if not self._selected_id:
            return
        data = {
            "label": self._label_input.text if hasattr(self, '_label_input') else self._selected_id,
            "group": self._group_dd.get_selected() if hasattr(self, '_group_dd') else "decoracion",
            "class_path": self._cp_input.text if hasattr(self, '_cp_input') else None,
            "target_list": self._tl_input.text if hasattr(self, '_tl_input') else None,
            "properties": {},
        }
        if data["class_path"] == "":
            data["class_path"] = None
        if data["target_list"] == "":
            data["target_list"] = None

        old_data = get_behavior(self._selected_id)
        if old_data:
            data["properties"] = old_data.get("properties", {})

        new_id = self._id_input.text.strip() if hasattr(self, '_id_input') else self._selected_id
        if not new_id:
            new_id = self._selected_id

        if new_id != self._selected_id:
            delete_behavior(self._selected_id)
        set_behavior(new_id, data)
        self._selected_id = new_id
        self._rebuild_editor()

    def _on_delete(self):
        if not self._selected_id:
            return
        delete_behavior(self._selected_id)
        self._selected_id = None
        self._prop_scroll = 0
        self._rebuild_editor()

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        r = self.get_abs_rect()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if r.collidepoint(mx, my) and mx < r.x + LEFT_W and my > r.y + TOOLBAR_H:
                ly = r.y + TOOLBAR_H
                rel_y = my - ly
                idx = (rel_y // LIST_H) + self._list_scroll
                items = get_behavior_list()
                if 0 <= idx < len(items):
                    self._selected_id = items[idx][0]
                    self._prop_scroll = 0
                    self._rebuild_editor()
                return True

        if event.type == pygame.MOUSEWHEEL:
            mx, my = pygame.mouse.get_pos()
            in_list = r.collidepoint(mx, my) and mx < r.x + LEFT_W and my > r.y + TOOLBAR_H
            if in_list:
                self._list_scroll -= event.y
                items = get_behavior_list()
                max_scroll = max(0, len(items) - self._list_items_visible())
                self._list_scroll = max(0, min(self._list_scroll, max_scroll))
                return True

        for child in list(self.children):
            if child.visible and child.handle_event(event):
                return True
        return False

    def _list_items_visible(self):
        return max(1, (self.rect.h - TOOLBAR_H) // LIST_H)

    def draw(self, surface):
        if not self.visible:
            return
        r = self.get_abs_rect()
        pygame.draw.rect(surface, self.bg_color, r)

        list_x = r.x
        list_y = r.y + TOOLBAR_H
        list_w = LEFT_W
        list_h = r.h - TOOLBAR_H

        pygame.draw.rect(surface, (38, 42, 48), (list_x, list_y, list_w, list_h))
        pygame.draw.line(surface, (55, 60, 68), (list_x + list_w, list_y),
                         (list_x + list_w, list_y + list_h))

        i = I18n.instancia()
        font = i.fuente(13) if i else pygame.font.SysFont("Arial", 13)

        header = font.render(self.i18n.t("behavior.list"), True, (180, 185, 195))
        surface.blit(header, (list_x + PADDING, list_y + 4))

        items = get_behavior_list()
        for vi in range(self._list_items_visible()):
            li = self._list_scroll + vi
            if li >= len(items):
                break
            y = list_y + 26 + vi * LIST_H
            bid, blabel = items[li]
            if bid == self._selected_id:
                pygame.draw.rect(surface, (55, 80, 120), (list_x, y, list_w, LIST_H))
            elif vi % 2 == 0:
                pygame.draw.rect(surface, (42, 46, 55), (list_x, y, list_w, LIST_H))
            txt = font.render(blabel, True, (200, 205, 215))
            surface.blit(txt, (list_x + PADDING + 4, y + 4))

        if len(items) > self._list_items_visible():
            sb_x = list_x + list_w - SCROLLBAR_W
            sb_h = list_h
            pygame.draw.rect(surface, (40, 43, 50), (sb_x, list_y, SCROLLBAR_W, sb_h))
            thumb_h = max(16, int(sb_h * self._list_items_visible() / len(items)))
            max_s = len(items) - self._list_items_visible()
            thumb_y = list_y + int((sb_h - thumb_h) * self._list_scroll / max_s) if max_s > 0 else list_y
            pygame.draw.rect(surface, (75, 80, 90), (sb_x + 1, thumb_y, SCROLLBAR_W - 2, thumb_h))

        for child in self.children:
            if child.visible:
                child.draw(surface)


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
