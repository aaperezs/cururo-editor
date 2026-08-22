import pygame
from editor.widgets.base import Widget
from editor.widgets.dropdown import Dropdown
from editor.translation import I18n
from editor.clipboard import clipboard_get, clipboard_set
from editor.widgets.event_constants import (
    TRIGGERS, CONDITION_TYPES, ACTION_TYPES,
    CONDITION_PARAMS, ACTION_PARAMS, DROPDOWN_PARAMS,
    COND_OPERATOR_OPTIONS,
    COL_BG, COL_BORDER, COL_CARD_BG, COL_CARD_BORDER,
    COL_TEXT, COL_TEXT_DIM, COL_ACCENT, COL_GREEN, COL_RED,
    COL_EDIT_BG, COL_FIELD_BG, COL_FIELD_BORDER,
    CARD_MARGIN, INDENT, TRIGGER_W,
    get_map_list as _get_map_list,
    get_boss_list as _get_boss_list,
    get_moneda_list as _get_moneda_list,
    get_param_options as _get_param_options_raw,
)


def _get_param_options(pk, ct=None):
    return _get_param_options_raw(pk, ct)


class EventEditorWidget(Widget):
    def __init__(self, x, y, w, h, on_set_spawn=None, on_clear_spawn=None, on_change=None):

        super().__init__(x, y, w, h)
        self.selected_pos = None
        self.selected_z = 0
        self.selected_sprite_id = None
        self.eventos = []
        self._scroll = 0
        self._edit = None
        self._edit_value = ""
        self._edit_cursor = 0
        self._edit_sel_start = None
        self._edit_field_x = None
        self._dropdown = None

        self._spawn_pos = None
        self._spawn_z = 0
        self._on_set_spawn = on_set_spawn
        self._on_clear_spawn = on_clear_spawn
        self._on_change = on_change
        self._msg_cache = {}
        self._msg_cache_tick = 0
        self._sb_dragging = False
        self._sb_drag_start = 0
        self._hover_del = None       # (ev_idx, kind, item_idx) or None
        self._hover_add = None       # "cond"/"act"/(ev_idx, None) or None

    def _mark_dirty(self):
        if self._on_change:
            self._on_change()

    def _abs_rect(self):
        if self.parent:
            pr = self.parent.get_abs_rect() if hasattr(self.parent, 'get_abs_rect') else self.parent.rect
            return pygame.Rect(pr.x + self.rect.x, pr.y + self.rect.y, self.rect.w, self.rect.h)
        return self.rect.copy()

    def set_spawn(self, pos, z):
        self._spawn_pos = pos
        self._spawn_z = z

    def set_selection(self, pos, z, sprite_id):
        self.selected_pos = pos
        self.selected_z = z
        self.selected_sprite_id = sprite_id
        if pos is None:
            self.eventos = []
        self._dropdown = None
        self._edit = None

    def set_eventos(self, eventos):
        self.eventos = eventos if eventos else []
        self._msg_cache.clear()

    def get_eventos(self):
        return self.eventos

    def _make_evento(self):
        return {"trigger": "contact", "boss_id": "", "watched_event_id": "", "condiciones": [], "acciones": [], "once": False, "id": ""}

    def _card_height(self, ev):
        h = 18 + 22 + 22 + 14
        h += len(ev.get("condiciones", [])) * 22 + 18
        h += 14
        for act in ev.get("acciones", []):
            if act.get("tipo") == "show_message" and "mensaje" in act.get("params", {}):
                h += 44
            else:
                h += 22
        h += 18 + 6 + CARD_MARGIN
        return h

    def _fuente(self, size=13):
        i = I18n.instancia()
        return i.fuente(size) if i else pygame.font.SysFont("Arial", size)

    def _fuente_peq(self):
        return self._fuente(11)

    def _trigger_locale(self, t):
        return f"event.trigger_{t}"

    def _cond_locale(self, t):
        return f"event.condition.{t}"

    def _action_locale(self, t):
        return f"event.action.{t}"

    def _confirm_edit(self):
        if not self._edit:
            return
        ev_idx, kind, item_idx, pk = self._edit
        if 0 <= ev_idx < len(self.eventos):
            ev = self.eventos[ev_idx]
            if kind == "event":
                ev[pk] = self._edit_value
                self._mark_dirty()
            else:
                lst = ev.get("condiciones" if kind == "cond" else "acciones", [])
                if 0 <= item_idx < len(lst):
                    try:
                        v = int(self._edit_value)
                    except ValueError:
                        v = self._edit_value
                    lst[item_idx]["params"][pk] = v
                    self._mark_dirty()
        self._edit = None
        self._edit_value = ""
        self._edit_cursor = 0
        self._edit_sel_start = None
        self._msg_cache.clear()

    # --- inline text editing helpers ---

    def _sel_range(self):
        if self._edit_sel_start is None:
            return None
        lo = min(self._edit_sel_start, self._edit_cursor)
        hi = max(self._edit_sel_start, self._edit_cursor)
        return (lo, hi) if hi > lo else None

    def _copy_selection(self):
        r = self._sel_range()
        if r:
            clipboard_set(self._edit_value[r[0]:r[1]])
        return r is not None

    def _delete_selection(self):
        r = self._sel_range()
        if r:
            self._edit_value = self._edit_value[:r[0]] + self._edit_value[r[1]:]
            self._edit_cursor = r[0]
            self._edit_sel_start = None
            self._msg_cache.clear()
            return True
        return False

    def _insert_at_cursor(self, text):
        self._edit_value = (
            self._edit_value[:self._edit_cursor] +
            text +
            self._edit_value[self._edit_cursor:])
        self._edit_cursor += len(text)
        self._edit_sel_start = None
        self._msg_cache.clear()

    def _draw_edit_field(self, surface, font, x, y, w, h, color=COL_TEXT):
        show_cursor = pygame.time.get_ticks() % 1000 < 500
        rng = self._sel_range()
        txt = self._edit_value

        if rng:
            pre_w = font.render(txt[:rng[0]], True, color).get_width()
            sel_w = font.render(txt[rng[0]:rng[1]], True, color).get_width()
            sel_rect = pygame.Rect(x + pre_w, y, sel_w, h)
            pygame.draw.rect(surface, (50, 100, 150), sel_rect)

        rendered = font.render(txt, True, color)
        surface.blit(rendered, (x, y))

        if show_cursor:
            pre_w = font.render(txt[:self._edit_cursor], True, color).get_width()
            cursor_x = x + pre_w
            if cursor_x < x + w:
                pygame.draw.rect(surface, (200, 200, 200), (cursor_x, y, 1, h))

    def _find_click_target(self, mx, my, r):
        if not self.selected_pos:
            return None
        i = I18n.instancia()
        fpeq = i.fuente(11) if i else pygame.font.SysFont("Arial", 11)

        # Spawn button
        spawn_btn = pygame.Rect(r.x + 6, r.y + 28, r.w - 12, 22)
        if spawn_btn.collidepoint(mx, my):
            return ("spawn",)

        y0 = r.y + 60 - self._scroll
        for ev_idx, ev in enumerate(self.eventos):
            ey = y0 + sum(self._card_height(self.eventos[i]) for i in range(ev_idx))
            ch = self._card_height(ev)
            if my < ey or my > ey + ch:
                continue
            cx = r.x + 10
            cw = r.w - 20

            # Delete X
            dx = cx + cw - 18
            if dx <= mx <= dx + 16 and ey + 2 <= my <= ey + 16:
                return ("del_event", ev_idx)

            cy = ey + 18

            # Trigger dropdown
            if cx <= mx <= cx + TRIGGER_W and cy <= my <= cy + 20:
                return ("trigger", ev_idx, cx, cy)

            # Once checkbox (right of trigger)
            trig_label = i.t(self._trigger_locale(ev["trigger"]))
            trig_w = TRIGGER_W
            once_x = cx + trig_w + 8
            once_w = 80
            if once_x <= mx <= once_x + once_w and cy <= my <= cy + 20:
                return ("once", ev_idx)

            cy += 22

            # Event ID field (click to edit)
            if cx + 24 <= mx <= cx + cw - 4 and cy <= my <= cy + 18:
                return ("edit_event_id", ev_idx)

            cy += 22

            # Boss ID field (only for on_boss_defeated trigger)
            if ev.get("trigger") == "on_boss_defeated":
                if cx + 50 <= mx <= cx + cw - 4 and cy <= my <= cy + 18:
                    return ("param_dropdown", ev_idx, "boss", 0, "boss_id", cx + 50, cy)

            # Watched event ID field (only for on_event_finalized trigger)
            if ev.get("trigger") == "on_event_finalized":
                if cx + 50 <= mx <= cx + cw - 4 and cy <= my <= cy + 18:
                    return ("edit_param", ev_idx, "boss", 0, "watched_event_id")

            # Conditions
            conds = ev.get("condiciones", [])
            cy += 14
            for ci, cond in enumerate(conds):
                ct = cond.get("tipo", "has_moneda")
                # Remove X (check first to avoid overlap)
                rx = cx + cw - 16
                if rx <= mx <= rx + 14 and cy + 1 <= my <= cy + 15:
                    return ("del_cond", ev_idx, ci)
                # Condition type dropdown
                if cx <= mx <= cx + 100 and cy <= my <= cy + 18:
                    return ("cond_type", ev_idx, ci, cx, cy)
                # Params
                px = cx + 104
                for pk, pv in cond.get("params", {}).items():
                    if px <= mx <= px + 60 and cy <= my <= cy + 18:
                        if pk in DROPDOWN_PARAMS:
                            return ("param_dropdown", ev_idx, "cond", ci, pk, px, cy, ct)
                        return ("edit_param", ev_idx, "cond", ci, pk)
                    px += 64
                cy += 22

            # Add condition
            if cx <= mx <= cx + 100 and cy <= my <= cy + 18:
                return ("add_cond", ev_idx)
            cy += 18

            # Actions
            acts = ev.get("acciones", [])
            cy += 14
            for ai, act in enumerate(acts):
                at = act.get("tipo", "show_message")
                # Remove X (check first to avoid overlap)
                rx = cx + cw - 16
                if rx <= mx <= rx + 14 and cy + 1 <= my <= cy + 15:
                    return ("del_act", ev_idx, ai)
                # Action type dropdown
                if cx <= mx <= cx + 100 and cy <= my <= cy + 18:
                    return ("act_type", ev_idx, ai, cx, cy)
                # Params
                px = cx + 104
                for pk, pv in act.get("params", {}).items():
                    if at == "show_message" and pk == "mensaje":
                        txt_w = cw - (px - cx) - 4
                        if px <= mx <= px + txt_w and cy <= my <= cy + 40:
                            return ("edit_param", ev_idx, "act", ai, pk)
                    else:
                        if px <= mx <= px + 60 and cy <= my <= cy + 18:
                            if pk in DROPDOWN_PARAMS:
                                return ("param_dropdown", ev_idx, "act", ai, pk, px, cy)
                            return ("edit_param", ev_idx, "act", ai, pk)
                    px += 64
                if at == "show_message" and "mensaje" in act.get("params", {}):
                    cy += 44
                else:
                    cy += 22

            # Add action
            if cx <= mx <= cx + 100 and cy <= my <= cy + 18:
                return ("add_act", ev_idx)
            cy += 18

        # Add event
        add_y = y0 + sum(self._card_height(ev) for ev in self.eventos) + 5
        if r.x + 8 <= mx <= r.x + r.w - 8 and add_y <= my <= add_y + 26:
            return ("add_event",)

        return None

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        r = self._abs_rect()
        i = I18n.instancia()

        # Dropdown event handling (click, scroll, keys)
        if self._dropdown:
            if self._dropdown.handle_event(event):
                if not self._dropdown.is_open:
                    self._dropdown = None
                return True

        # Scrollbar dragging
        if event.type == pygame.MOUSEMOTION and self._sb_dragging:
            total_h = sum(self._card_height(ev) for ev in self.eventos)
            max_scroll = max(0, total_h - (r.h - 60) + 30)
            if max_scroll > 0:
                sb_h = r.h - 60
                thumb_h = max(16, int(sb_h * (r.h - 60) / (total_h + 30)))
                track_h = sb_h - thumb_h
                if track_h > 0:
                    dy = event.pos[1] - self._sb_drag_start
                    px_per_scroll = max_scroll / track_h
                    self._scroll = max(0, min(max_scroll, self._scroll + int(dy * px_per_scroll)))
                    self._sb_drag_start = event.pos[1]
            return True

        if event.type == pygame.MOUSEMOTION:
            self._hover_del = None
            self._hover_add = None
            if self.selected_pos and r.collidepoint(event.pos):
                target = self._find_click_target(event.pos[0], event.pos[1], r)
                if target:
                    cmd = target[0]
                    if cmd == "del_event":
                        self._hover_del = (target[1], "event")
                    elif cmd == "del_cond":
                        self._hover_del = (target[1], "cond", target[2])
                    elif cmd == "del_act":
                        self._hover_del = (target[1], "act", target[2])
                    elif cmd in ("add_cond", "add_act"):
                        self._hover_add = (cmd, target[1])

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self._sb_dragging = False

        # Editing
        if event.type == pygame.KEYDOWN and self._edit:
            ev_idx, kind, item_idx, pk = self._edit
            is_mensaje = (kind == "act" and
                          ev_idx < len(self.eventos) and
                          item_idx < len(self.eventos[ev_idx].get("acciones", [])) and
                          self.eventos[ev_idx].get("acciones", [])[item_idx].get("tipo") == "show_message" and
                          pk == "mensaje")
            mods = pygame.key.get_mods()
            ctrl = mods & pygame.KMOD_CTRL
            shift = mods & pygame.KMOD_SHIFT

            # Ctrl shortcuts
            if ctrl:
                if event.key == pygame.K_a:
                    self._edit_sel_start = 0
                    self._edit_cursor = len(self._edit_value)
                    return True
                if event.key == pygame.K_c:
                    self._copy_selection()
                    return True
                if event.key == pygame.K_v:
                    pasted = clipboard_get()
                    if pasted:
                        self._delete_selection()
                        if not is_mensaje:
                            pasted = pasted.split("\n")[0]
                        self._insert_at_cursor(pasted)
                    return True
                if event.key == pygame.K_x:
                    self._copy_selection()
                    self._delete_selection()
                    return True
                if event.key == pygame.K_z:
                    return True
                if event.key in (pygame.K_LEFT, pygame.K_RIGHT):
                    words = self._edit_value.split(" ")
                    idx = self._edit_cursor
                    if event.key == pygame.K_LEFT:
                        while idx > 0 and self._edit_value[idx - 1] == " ":
                            idx -= 1
                        while idx > 0 and self._edit_value[idx - 1] != " ":
                            idx -= 1
                    else:
                        end = len(self._edit_value)
                        while idx < end and self._edit_value[idx] == " ":
                            idx += 1
                        while idx < end and self._edit_value[idx] != " ":
                            idx += 1
                    if shift:
                        if self._edit_sel_start is None:
                            self._edit_sel_start = self._edit_cursor
                        self._edit_cursor = idx
                    else:
                        self._edit_cursor = idx
                        self._edit_sel_start = None
                    return True

            if event.key == pygame.K_RETURN:
                if is_mensaje and mods & pygame.KMOD_SHIFT:
                    self._insert_at_cursor("\n")
                else:
                    self._confirm_edit()
                return True
            elif event.key in (pygame.K_INSERT, pygame.K_TAB):
                self._confirm_edit()
                return True
            elif event.key == pygame.K_ESCAPE:
                self._edit = None
                self._edit_value = ""
                self._edit_cursor = 0
                self._edit_sel_start = None
                self._msg_cache.clear()
                return True
            elif event.key == pygame.K_LEFT:
                if self._edit_cursor > 0:
                    if shift:
                        if self._edit_sel_start is None:
                            self._edit_sel_start = self._edit_cursor
                        self._edit_cursor -= 1
                    else:
                        self._edit_cursor -= 1
                        self._edit_sel_start = None
                elif shift:
                    self._edit_sel_start = None
                return True
            elif event.key == pygame.K_RIGHT:
                if self._edit_cursor < len(self._edit_value):
                    if shift:
                        if self._edit_sel_start is None:
                            self._edit_sel_start = self._edit_cursor
                        self._edit_cursor += 1
                    else:
                        self._edit_cursor += 1
                        self._edit_sel_start = None
                elif shift:
                    self._edit_sel_start = None
                return True
            elif event.key == pygame.K_HOME:
                if shift:
                    if self._edit_sel_start is None:
                        self._edit_sel_start = self._edit_cursor
                    self._edit_cursor = 0
                else:
                    self._edit_cursor = 0
                    self._edit_sel_start = None
                return True
            elif event.key == pygame.K_END:
                if shift:
                    if self._edit_sel_start is None:
                        self._edit_sel_start = self._edit_cursor
                    self._edit_cursor = len(self._edit_value)
                else:
                    self._edit_cursor = len(self._edit_value)
                    self._edit_sel_start = None
                return True
            elif event.key == pygame.K_DELETE:
                if self._edit_sel_start is not None:
                    self._delete_selection()
                elif self._edit_cursor < len(self._edit_value):
                    self._edit_value = (
                        self._edit_value[:self._edit_cursor] +
                        self._edit_value[self._edit_cursor + 1:])
                    self._msg_cache.clear()
                return True
            elif event.key == pygame.K_BACKSPACE:
                if self._edit_sel_start is not None:
                    self._delete_selection()
                elif self._edit_cursor > 0:
                    self._edit_value = (
                        self._edit_value[:self._edit_cursor - 1] +
                        self._edit_value[self._edit_cursor:])
                    self._edit_cursor -= 1
                    self._msg_cache.clear()
                return True
            else:
                if event.unicode.isprintable():
                    self._delete_selection()
                    self._insert_at_cursor(event.unicode)
                    return True

        if event.type == pygame.MOUSEWHEEL:
            total_h = sum(self._card_height(ev) for ev in self.eventos)
            max_scroll = max(0, total_h - (r.h - 60) + 30)
            self._scroll = max(0, min(max_scroll, self._scroll - event.y * 20))
            return True

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if not r.collidepoint(mx, my):
                return False

            # Scrollbar click
            total_h = sum(self._card_height(ev) for ev in self.eventos)
            max_scroll = max(0, total_h - (r.h - 60) + 30)
            if max_scroll > 0:
                sb_w = 12
                sb_x = r.x + r.w - sb_w
                sb_y = r.y + 60
                sb_h = r.h - 60
                if sb_x <= mx <= sb_x + sb_w and sb_y <= my <= sb_y + sb_h:
                    thumb_h = max(16, int(sb_h * (r.h - 60) / (total_h + 30)))
                    thumb_y = sb_y + int((sb_h - thumb_h) * self._scroll / max_scroll)
                    if thumb_y <= my <= thumb_y + thumb_h:
                        # Drag thumb
                        self._sb_dragging = True
                        self._sb_drag_start = my
                        return True
                    # Click on track - move to position
                    rel = my - sb_y - thumb_h // 2
                    self._scroll = int(rel / (sb_h - thumb_h) * max_scroll)
                    self._scroll = max(0, min(max_scroll, self._scroll))
                    return True

            target = self._find_click_target(mx, my, r)
            if not target:
                return False

            cmd = target[0]

            if cmd == "spawn":
                is_spawn = self._spawn_pos == tuple(self.selected_pos) if self.selected_pos else False
                if is_spawn:
                    if self._on_clear_spawn:
                        self._on_clear_spawn()
                else:
                    if self._on_set_spawn:
                        self._on_set_spawn(tuple(self.selected_pos), self.selected_z)
                return True

            if cmd == "del_event":
                ev_idx = target[1]
                self.eventos.pop(ev_idx)
                self._mark_dirty()
                return True

            if cmd == "trigger":
                ev_idx, cx, cy = target[1], target[2], target[3]
                opts = [(t, i.t(self._trigger_locale(t))) for t in TRIGGERS]
                self._dropdown = Dropdown(cx, cy + 20, 180, opts,
                    lambda v, idx=ev_idx: self._set_trigger(idx, v[0] if isinstance(v, tuple) else v))
                self._dropdown.open()
                return True

            if cmd == "once":
                ev_idx = target[1]
                if 0 <= ev_idx < len(self.eventos):
                    self.eventos[ev_idx]["once"] = not self.eventos[ev_idx].get("once", False)
                    self._mark_dirty()
                return True

            if self._edit:
                edit_target = None
                if target[0] == "edit_event_id":
                    edit_target = (target[1], "event", 0, "id")
                elif target[0] == "edit_param":
                    edit_target = (target[1], target[2], target[3], target[4])
                if edit_target == self._edit and self._edit_field_x is not None:
                    fpeq = i.fuente(11) if i else pygame.font.SysFont("Arial", 11)
                    rel_x = mx - self._edit_field_x
                    cursor = 0
                    for ch in range(len(self._edit_value) + 1):
                        w = fpeq.render(self._edit_value[:ch], True, (0,0,0)).get_width()
                        if w > rel_x:
                            break
                        cursor = ch
                    self._edit_cursor = cursor
                    self._edit_sel_start = None
                    return True

            if cmd == "edit_event_id":
                ev_idx = target[1]
                if 0 <= ev_idx < len(self.eventos):
                    self._edit = (ev_idx, "event", 0, "id")
                    self._edit_value = str(self.eventos[ev_idx].get("id", ""))
                    self._edit_cursor = len(self._edit_value)
                    self._edit_sel_start = None
                return True

            if cmd == "cond_type":
                ev_idx, ci, cx, cy = target[1], target[2], target[3], target[4]
                opts = [(t, i.t(self._cond_locale(t))) for t in CONDITION_TYPES]
                self._dropdown = Dropdown(cx, cy + 18, 180, opts,
                    lambda v, idx=ev_idx, cii=ci: self._set_cond_type(idx, cii, v[0] if isinstance(v, tuple) else v))
                self._dropdown.open()
                return True

            if cmd == "act_type":
                ev_idx, ai, cx, cy = target[1], target[2], target[3], target[4]
                opts = [(t, i.t(self._action_locale(t))) for t in ACTION_TYPES]
                self._dropdown = Dropdown(cx, cy + 18, 180, opts,
                    lambda v, idx=ev_idx, aii=ai: self._set_action_type(idx, aii, v[0] if isinstance(v, tuple) else v))
                self._dropdown.open()
                return True

            if cmd == "edit_param":
                ev_idx, kind, item_idx, pk = target[1], target[2], target[3], target[4]
                ev = self.eventos[ev_idx]
                if kind == "boss":
                    self._edit = (ev_idx, "event", 0, pk)
                    self._edit_value = str(ev.get(pk, ""))
                    self._edit_cursor = len(self._edit_value)
                    self._edit_sel_start = None
                else:
                    lst = ev.get("condiciones" if kind == "cond" else "acciones", [])
                    if 0 <= item_idx < len(lst):
                        self._edit = (ev_idx, kind, item_idx, pk)
                        self._edit_value = str(lst[item_idx]["params"].get(pk, ""))
                        self._edit_cursor = len(self._edit_value)
                        self._edit_sel_start = None
                return True

            if cmd == "param_dropdown":
                ev_idx, kind, item_idx, pk, _, py = target[1], target[2], target[3], target[4], target[5], target[6]
                ct = target[7] if len(target) > 7 else None
                opts = _get_param_options(pk, ct)
                if not opts:
                    opts = [("", f"(sin {pk})")]
                # Clamp horizontal position to stay within widget
                r = self._abs_rect()
                dd_x = target[5] - 2
                dd_x = max(r.x + 2, min(dd_x, r.x + r.w - 182))
                self._dropdown = Dropdown(dd_x, py + 18, 180, opts,
                    lambda v, idx=ev_idx, k=kind, ii=item_idx, pk=pk: self._set_param_dropdown(idx, k, ii, pk, v))
                self._dropdown.open()
                return True

            if cmd == "del_cond":
                ev_idx, ci = target[1], target[2]
                if 0 <= ev_idx < len(self.eventos):
                    conds = self.eventos[ev_idx].get("condiciones", [])
                    if 0 <= ci < len(conds):
                        conds.pop(ci)
                        self._mark_dirty()
                return True

            if cmd == "del_act":
                ev_idx, ai = target[1], target[2]
                if 0 <= ev_idx < len(self.eventos):
                    acts = self.eventos[ev_idx].get("acciones", [])
                    if 0 <= ai < len(acts):
                        acts.pop(ai)
                        self._mark_dirty()
                return True

            if cmd == "add_cond":
                ev_idx = target[1]
                if 0 <= ev_idx < len(self.eventos):
                    self.eventos[ev_idx]["condiciones"].append(
                        {"tipo": "has_moneda", "params": dict(CONDITION_PARAMS["has_moneda"])}
                    )
                    self._mark_dirty()
                return True

            if cmd == "add_act":
                ev_idx = target[1]
                if 0 <= ev_idx < len(self.eventos):
                    self.eventos[ev_idx]["acciones"].append(
                        {"tipo": "show_message", "params": dict(ACTION_PARAMS["show_message"])}
                    )
                    self._mark_dirty()
                    # Ajustar scroll para mantener el boton "+ Accion" visible
                    r = self._abs_rect()
                    total_h = sum(self._card_height(ev) for ev in self.eventos)
                    self._scroll = max(0, min(total_h - (r.h - 60) + 30, self._scroll))
                return True

            if cmd == "add_event":
                self.eventos.append(self._make_evento())
                self._mark_dirty()
                return True

        return False

    def _set_param_dropdown(self, ev_idx, kind, item_idx, pk, value):
        if 0 <= ev_idx < len(self.eventos):
            val = value[0] if isinstance(value, tuple) else value
            if kind == "boss":
                self.eventos[ev_idx][pk] = val
                self._mark_dirty()
                return
            lst = self.eventos[ev_idx].get("condiciones" if kind == "cond" else "acciones", [])
            if 0 <= item_idx < len(lst):
                lst[item_idx]["params"][pk] = value[0] if isinstance(value, tuple) else value
                self._mark_dirty()

    def _set_trigger(self, ev_idx, value):
        if 0 <= ev_idx < len(self.eventos):
            self.eventos[ev_idx]["trigger"] = value
            self._mark_dirty()

    def _set_cond_type(self, ev_idx, ci, value):
        if 0 <= ev_idx < len(self.eventos):
            conds = self.eventos[ev_idx].get("condiciones", [])
            if 0 <= ci < len(conds):
                conds[ci]["tipo"] = value
                conds[ci]["params"] = dict(CONDITION_PARAMS.get(value, {}))
                self._mark_dirty()

    def _set_action_type(self, ev_idx, ai, value):
        if 0 <= ev_idx < len(self.eventos):
            acts = self.eventos[ev_idx].get("acciones", [])
            if 0 <= ai < len(acts):
                acts[ai]["tipo"] = value
                acts[ai]["params"] = dict(ACTION_PARAMS.get(value, {}))
                self._mark_dirty()

    def _draw_header(self, surface, r, i, fonte, fpeq):
        sid = self.selected_sprite_id or "none"
        header = f"{i.t(f'entity.{sid}')} @ {self.selected_pos} (Z={self.selected_z})"
        surface.blit(fonte.render(header, True, COL_TEXT), (r.x + 10, r.y + 6))

        is_spawn = self._spawn_pos == tuple(self.selected_pos) if self.selected_pos else False
        spawn_bg = (130, 60, 20) if is_spawn else COL_FIELD_BG
        spawn_text = i.t("event.spawn_here") if not is_spawn else f"{i.t('event.spawn_remove')} ({self._spawn_pos[0]},{self._spawn_pos[1]})"
        spawn_rect = pygame.Rect(r.x + 10, r.y + 28, r.w - 20, 22)
        pygame.draw.rect(surface, spawn_bg, spawn_rect)
        pygame.draw.rect(surface, COL_FIELD_BORDER, spawn_rect, 1)
        surface.blit(fpeq.render(spawn_text, True, COL_TEXT), (spawn_rect.x + (spawn_rect.w - fpeq.size(spawn_text)[0]) // 2, spawn_rect.y + 3))

    def _draw_events_scroll_area(self, surface, r, i, fonte, fpeq):
        mx, my = pygame.mouse.get_pos()
        clip = surface.get_clip()
        surface.set_clip(r)
        y0 = r.y + 60 - self._scroll
        cx = r.x + 10
        cw = r.w - 20

        for ev_idx, ev in enumerate(self.eventos):
            ey = y0 + sum(self._card_height(self.eventos[i]) for i in range(ev_idx))
            ch = self._card_height(ev)

            pygame.draw.rect(surface, COL_CARD_BG, (cx, ey, cw, ch))
            pygame.draw.rect(surface, COL_CARD_BORDER, (cx, ey, cw, ch), 1)

            # Delete X (hover-aware)
            dx = cx + cw - 18
            del_rect = pygame.Rect(dx, ey + 2, 16, 14)
            if self._hover_del and self._hover_del[0] == ev_idx and self._hover_del[1] == "event":
                pygame.draw.rect(surface, COL_RED, del_rect)
            else:
                pygame.draw.rect(surface, COL_CARD_BG, del_rect)
            surface.blit(fpeq.render("X", True, (255, 255, 255) if self._hover_del and self._hover_del[0] == ev_idx and self._hover_del[1] == "event" else COL_RED), (dx + 4, ey + 2))

            cy = ey + 18

            # Trigger dropdown
            trig_label = i.t(self._trigger_locale(ev["trigger"]))
            trig_w = TRIGGER_W
            pygame.draw.rect(surface, COL_ACCENT, (cx, cy, trig_w, 20))
            pygame.draw.rect(surface, COL_FIELD_BORDER, (cx, cy, trig_w, 20), 1)
            surface.blit(fpeq.render(trig_label + "  ▼", True, COL_TEXT), (cx + 3, cy + 2))

            once_val = ev.get("once", False)
            once_x = cx + trig_w + 8
            once_label = i.t("event.once")
            check = "✔" if once_val else "□"
            col_check = COL_GREEN if once_val else COL_TEXT_DIM
            surface.blit(fpeq.render(check, True, col_check), (once_x, cy + 2))
            surface.blit(fpeq.render(once_label, True, COL_TEXT_DIM), (once_x + 14, cy + 2))

            cy += 22

            # Event ID field
            id_val = ev.get("id", "")
            surface.blit(fpeq.render("ID:", True, COL_TEXT_DIM), (cx, cy))
            id_fw = cw - 34
            if self._edit == (ev_idx, "event", 0, "id"):
                pygame.draw.rect(surface, COL_EDIT_BG, (cx + 26, cy, id_fw, 18))
                self._edit_field_x = cx + 28
                self._draw_edit_field(surface, fpeq, cx + 28, cy + 2, id_fw - 2, 14)
            else:
                pygame.draw.rect(surface, COL_FIELD_BG, (cx + 26, cy, id_fw, 18))
                pygame.draw.rect(surface, COL_FIELD_BORDER, (cx + 26, cy, id_fw, 18), 1)
                txt = id_val if id_val else "(sin ID)"
                col = COL_TEXT if id_val else COL_TEXT_DIM
                surface.blit(fpeq.render(txt, True, col), (cx + 28, cy + 1))
            cy += 22

            # Boss ID field (only for on_boss_defeated)
            if ev.get("trigger") == "on_boss_defeated":
                boss_id = ev.get("boss_id", "")
                surface.blit(fpeq.render("Boss:", True, COL_TEXT_DIM), (cx, cy))
                boss_fw = cw - 60
                pygame.draw.rect(surface, COL_FIELD_BG, (cx + 50, cy, boss_fw, 18))
                pygame.draw.rect(surface, COL_FIELD_BORDER, (cx + 50, cy, boss_fw, 18), 1)
                lbl = boss_id if boss_id else "(seleccionar)"
                col = COL_TEXT if boss_id else COL_TEXT_DIM
                surface.blit(fpeq.render(lbl + " ▼", True, col), (cx + 52, cy + 1))
                cy += 22

            # Watched event ID field (only for on_event_finalized)
            if ev.get("trigger") == "on_event_finalized":
                watched_id = ev.get("watched_event_id", "")
                surface.blit(fpeq.render("Evento:", True, COL_TEXT_DIM), (cx, cy))
                ev_fw = cw - 70
                if self._edit == (ev_idx, "event", 0, "watched_event_id"):
                    pygame.draw.rect(surface, COL_EDIT_BG, (cx + 50, cy, ev_fw, 18))
                    self._edit_field_x = cx + 52
                    self._draw_edit_field(surface, fpeq, cx + 52, cy + 2, ev_fw - 2, 14)
                else:
                    pygame.draw.rect(surface, COL_FIELD_BG, (cx + 50, cy, ev_fw, 18))
                    pygame.draw.rect(surface, COL_FIELD_BORDER, (cx + 50, cy, ev_fw, 18), 1)
                    txt = watched_id if watched_id else "(id del evento)"
                    col = COL_TEXT if watched_id else COL_TEXT_DIM
                    surface.blit(fpeq.render(txt, True, col), (cx + 52, cy + 1))
                cy += 22

            # Conditions header
            surface.blit(fpeq.render(i.t("event.conditions"), True, COL_TEXT_DIM), (cx, cy))
            cy += 14

            conds = ev.get("condiciones", [])
            first_cond_y = cy if conds else None
            for ci, cond in enumerate(conds):
                ct = cond.get("tipo", "has_moneda")
                ct_label = i.t(self._cond_locale(ct))
                ct_w = min(100, fpeq.size(ct_label + " ▼")[0] + 6)
                ct_w = max(ct_w, 80)
                pygame.draw.rect(surface, COL_FIELD_BG, (cx + INDENT, cy, ct_w, 18))
                pygame.draw.rect(surface, COL_FIELD_BORDER, (cx + INDENT, cy, ct_w, 18), 1)
                surface.blit(fpeq.render(ct_label + " ▼", True, COL_TEXT), (cx + INDENT + 2, cy + 1))

                px = cx + INDENT + ct_w + 4
                for pk, pv in cond.get("params", {}).items():
                    if self._edit == (ev_idx, "cond", ci, pk):
                        val_rect = pygame.Rect(px, cy, 56, 18)
                        pygame.draw.rect(surface, COL_EDIT_BG, val_rect)
                        pygame.draw.rect(surface, COL_FIELD_BORDER, val_rect, 1)
                        self._edit_field_x = px + 2
                        self._draw_edit_field(surface, fpeq, px + 2, cy + 2, 52, 14)
                    else:
                        val_rect = pygame.Rect(px, cy, 56, 18)
                        pygame.draw.rect(surface, COL_FIELD_BG, val_rect)
                        pygame.draw.rect(surface, COL_FIELD_BORDER, val_rect, 1)
                        surface.blit(fpeq.render(str(pv), True, COL_TEXT), (px + 2, cy + 1))
                    px += 60

                # Remove X (hover-aware)
                rx = cx + cw - 16
                del_cond_rect = pygame.Rect(rx, cy + 1, 14, 14)
                cond_hover = self._hover_del and self._hover_del[0] == ev_idx and self._hover_del[1] == "cond" and self._hover_del[2] == ci
                if cond_hover:
                    pygame.draw.rect(surface, COL_RED, del_cond_rect)
                else:
                    pygame.draw.rect(surface, COL_CARD_BG, del_cond_rect)
                surface.blit(fpeq.render("X", True, COL_RED if not cond_hover else (255, 255, 255)), (rx + 3, cy + 1))
                cy += 22

            # Add condition (hover-aware)
            addc_hover = self._hover_add and self._hover_add[0] == "add_cond" and self._hover_add[1] == ev_idx
            addc_col = COL_ACCENT if addc_hover else COL_TEXT_DIM
            addc_txt = fpeq.render(i.t("event.add_condition"), True, addc_col)
            addc_w = addc_txt.get_width() + 10
            surface.blit(addc_txt, (cx + INDENT, cy + 1))
            cy += 18

            # Actions header
            surface.blit(fpeq.render(i.t("event.actions"), True, COL_TEXT_DIM), (cx, cy))
            cy += 14

            first_act_y = cy if ev.get("acciones", []) else None
            acts = ev.get("acciones", [])
            for ai, act in enumerate(acts):
                at = act.get("tipo", "show_message")
                at_label = i.t(self._action_locale(at))
                at_w = min(100, fpeq.size(at_label + " ▼")[0] + 6)
                at_w = max(at_w, 80)
                pygame.draw.rect(surface, COL_FIELD_BG, (cx + INDENT, cy, at_w, 18))
                pygame.draw.rect(surface, COL_FIELD_BORDER, (cx + INDENT, cy, at_w, 18), 1)
                surface.blit(fpeq.render(at_label + " ▼", True, COL_TEXT), (cx + INDENT + 2, cy + 1))

                px = cx + INDENT + at_w + 4
                for pk, pv in act.get("params", {}).items():
                    if at == "show_message" and pk == "mensaje":
                        txt_w = cw - (px - cx) - 4
                        if self._edit == (ev_idx, "act", ai, pk):
                            val_rect = pygame.Rect(px, cy, txt_w, 40)
                            pygame.draw.rect(surface, COL_EDIT_BG, val_rect)
                            pygame.draw.rect(surface, COL_FIELD_BORDER, val_rect, 1)
                            self._edit_field_x = px + 2
                            show_cursor = pygame.time.get_ticks() % 1000 < 500
                            rng = self._sel_range()
                            if rng:
                                pre_txt = self._edit_value[:rng[0]]
                                pre_lines = pre_txt.split("\n")
                                pre_li = min(len(pre_lines) - 1, 2)
                                sel_txt = self._edit_value[rng[0]:rng[1]]
                                sel_first = sel_txt.split("\n")[0]
                                sel_x = fpeq.render(pre_lines[-1], True, COL_TEXT).get_width() if pre_lines else 0
                                sel_w = fpeq.render(sel_first, True, COL_TEXT).get_width() if sel_first else 0
                                sel_rect = pygame.Rect(px + 2 + sel_x, cy + 1 + pre_li * 13, sel_w, 12)
                                pygame.draw.rect(surface, (50, 100, 150), sel_rect)
                            txt = self._edit_value
                            lines = txt.split("\n")
                            for li in range(min(len(lines), 3)):
                                line = lines[li]
                                surface.blit(fpeq.render(line, True, COL_TEXT), (px + 2, cy + 1 + li * 13))
                                if show_cursor and self._edit_cursor >= sum(len(l) + 1 for l in lines[:li]) and \
                                        (li == len(lines) - 1 or self._edit_cursor < sum(len(l) + 1 for l in lines[:li + 1])):
                                    line_cursor = self._edit_cursor - (sum(len(l) + 1 for l in lines[:li]) if li > 0 else 0)
                                    cx_pos = px + 2 + fpeq.render(line[:line_cursor], True, COL_TEXT).get_width()
                                    pygame.draw.rect(surface, (200, 200, 200), (cx_pos, cy + 1 + li * 13, 1, 12))
                        else:
                            val_rect = pygame.Rect(px, cy, txt_w, 40)
                            pygame.draw.rect(surface, COL_FIELD_BG, val_rect)
                            pygame.draw.rect(surface, COL_FIELD_BORDER, val_rect, 1)
                            cache_key = ("msg", str(pv))
                            if cache_key not in self._msg_cache:
                                lines = str(pv).split("\n")
                                surf = pygame.Surface((txt_w - 4, 40), pygame.SRCALPHA)
                                for li, line in enumerate(lines[:3]):
                                    surf.blit(fpeq.render(line, True, COL_TEXT), (2, 1 + li * 13))
                                self._msg_cache[cache_key] = surf
                            surface.blit(self._msg_cache[cache_key], (px, cy))
                        px += txt_w + 4
                    else:
                        if self._edit == (ev_idx, "act", ai, pk):
                            val_rect = pygame.Rect(px, cy, 56, 18)
                            pygame.draw.rect(surface, COL_EDIT_BG, val_rect)
                            pygame.draw.rect(surface, COL_FIELD_BORDER, val_rect, 1)
                            self._edit_field_x = px + 2
                            self._draw_edit_field(surface, fpeq, px + 2, cy + 2, 52, 14)
                        else:
                            val_rect = pygame.Rect(px, cy, 56, 18)
                            pygame.draw.rect(surface, COL_FIELD_BG, val_rect)
                            pygame.draw.rect(surface, COL_FIELD_BORDER, val_rect, 1)
                            surface.blit(fpeq.render(str(pv), True, COL_TEXT), (px + 2, cy + 1))
                        px += 64

                # Remove X (hover-aware)
                rx = cx + cw - 16
                act_hover = self._hover_del and self._hover_del[0] == ev_idx and self._hover_del[1] == "act" and self._hover_del[2] == ai
                if act_hover:
                    pygame.draw.rect(surface, COL_RED, (rx, cy + 1, 14, 14))
                    surface.blit(fpeq.render("X", True, (255, 255, 255)), (rx + 3, cy + 1))
                else:
                    pygame.draw.rect(surface, COL_CARD_BG, (rx, cy + 1, 14, 14))
                    surface.blit(fpeq.render("X", True, COL_RED), (rx + 3, cy + 1))
                if at == "show_message" and "mensaje" in act.get("params", {}):
                    cy += 44
                else:
                    cy += 22

            # Add action (hover-aware)
            adda_hover = self._hover_add and self._hover_add[0] == "add_act" and self._hover_add[1] == ev_idx
            adda_col = COL_ACCENT if adda_hover else COL_TEXT_DIM
            adda_txt = fpeq.render(i.t("event.add_action"), True, adda_col)
            adda_w = adda_txt.get_width() + 10
            surface.blit(adda_txt, (cx + INDENT, cy + 1))

            # Guide line for conditions/actions
            guide_x = cx + INDENT - 4
            guide_top = first_cond_y if first_cond_y else (cy if first_act_y else None)
            guide_bot = cy + 18
            if guide_top is not None:
                pygame.draw.line(surface, COL_BORDER, (guide_x, guide_top), (guide_x, guide_bot), 1)

        # Add event button
        add_y = y0 + sum(self._card_height(ev) for ev in self.eventos) + 5
        add_bg = (50, 100, 50)
        pygame.draw.rect(surface, add_bg, (r.x + 10, add_y, r.w - 20, 26))
        pygame.draw.rect(surface, (80, 140, 80), (r.x + 10, add_y, r.w - 20, 26), 1)
        surface.blit(fonte.render(f"+ {i.t('event.add')}", True, COL_TEXT), (r.x + (r.w - fonte.size(f"+ {i.t('event.add')}")[0]) // 2, add_y + 4))

        # Scrollbar
        total_h = sum(self._card_height(ev) for ev in self.eventos)
        max_scroll = max(0, total_h - (r.h - 60) + 30)
        if max_scroll > 0:
            sb_w = 12
            sb_x = r.x + r.w - sb_w
            sb_y = r.y + 60
            sb_h = r.h - 60
            pygame.draw.rect(surface, COL_FIELD_BG, (sb_x, sb_y, sb_w, sb_h))
            thumb_h = max(16, int(sb_h * (r.h - 60) / (total_h + 30)))
            thumb_y = sb_y + int((sb_h - thumb_h) * self._scroll / max_scroll)
            thumb_color = COL_ACCENT if self._sb_dragging else (90, 150, 220)
            pygame.draw.rect(surface, thumb_color, (sb_x + 2, thumb_y, sb_w - 4, thumb_h))

        surface.set_clip(clip)

    def draw(self, surface):
        if not self.visible:
            return
        r = self._abs_rect()
        i = I18n.instancia()
        fonte = self._fuente(13)
        fpeq = self._fuente_peq()

        pygame.draw.rect(surface, COL_BG, r)
        pygame.draw.rect(surface, COL_BORDER, r, 1)

        if self.selected_pos is None:
            txt = fonte.render(i.t("event.no_selection"), True, (120, 120, 120))
            surface.blit(txt, (r.x + (r.w - txt.get_width()) // 2, r.y + (r.h - txt.get_height()) // 2))
            return

        self._draw_header(surface, r, i, fonte, fpeq)
        self._draw_events_scroll_area(surface, r, i, fonte, fpeq)

        if self._dropdown:
            self._dropdown.draw(surface)
