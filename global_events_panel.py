# Editor de eventos globales (data/eventos_globales.json).
#
# Patrón del mapa: trigger → condiciones → acciones.
#   trigger:  on_boss_defeated | on_event_finalized
#   acciones: restock_shop | add_shop_stock | modify_shop_price

import pygame

from editor.panels.base_panel import BasePanel
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.text_input import TextInput
from editor.widgets.simple_dropdown import SimpleDropdown
from editor.project import get_current_project
from editor.events_data import (
    _load_eventos_globales,
    get_eventos_globales,
    set_eventos_globales,
    get_global_triggers,
    get_global_action_types,
    get_global_action_params,
)
from editor.shops_data import get_all_shops, get_shop
from editor.monedas_data import _load_monedas, get_all_monedas
from editor.widgets.event_constants import (
    CONDITION_PARAMS,
)

PADDING = 6
ROW_H = 28
TOOLBAR_H = 36
HEADER_H = 26
LEFT_W = 220

# Condiciones soportadas en eventos globales (reutiliza evaluación del mapa)
GLOBAL_CONDITION_TYPES = [
    "has_moneda", "item_count", "flag", "ability", "ability_equipped",
    "pp", "evaluar_evento", "damage",
]


class GlobalEventsTab(BasePanel):
    """Editor de eventos globales (data/eventos_globales.json)."""

    def __init__(self, x, y, w, h, i18n):
        super().__init__(x, y, w, h, i18n)
        self.bg_color = (30, 32, 36)
        _load_eventos_globales()
        _load_monedas()
        self._eventos = get_eventos_globales()
        self._selected_idx = None
        self._list_scroll = 0
        self._status_text = ""
        self._status_error = False
        self._build_ui()

    def _build_ui(self):
        self.clear()
        self.mostrar_descripcion(
            self.i18n.t("tab.global_events.desc") if not self._eventos else ""
        )
        tb = Panel(0, 0, self.rect.w, TOOLBAR_H, bg_color=(42, 46, 55), border_color=(60, 65, 75))
        self.add(tb)
        self._new_btn = Button(8, 4, 72, 28, self.i18n.t("global_event.new") or "Nuevo", callback=self._on_new)
        self._new_btn.parent = tb; tb.children.append(self._new_btn)
        self._clone_btn = Button(86, 4, 72, 28, self.i18n.t("global_event.clone") or "Clonar", callback=self._on_clone)
        self._clone_btn.parent = tb; tb.children.append(self._clone_btn)
        self._del_btn = Button(164, 4, 72, 28, self.i18n.t("global_event.delete") or "Eliminar", callback=self._on_delete)
        self._del_btn.parent = tb; tb.children.append(self._del_btn)
        self._save_btn = Button(242, 4, 72, 28, self.i18n.t("global_event.save") or "Guardar", callback=self._on_save)
        self._save_btn.parent = tb; tb.children.append(self._save_btn)
        self._status_lbl = Label(322, 4, max(60, self.rect.w - 332), 28, "", font_size=12,
                                 color=(150, 200, 150))
        self._status_lbl.parent = tb; tb.children.append(self._status_lbl)

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

        if self._selected_idx is None or not (0 <= self._selected_idx < len(self._eventos)):
            ep.visible = False
            return
        ep.visible = True
        evento = self._eventos[self._selected_idx]

        # ── Header ──────────────────────────────────────────────
        self._eid_label = Label(PADDING, y, ep.rect.w - PADDING * 2, 20,
                                f"ID: {evento.get('event_id', '')}", font_size=13, color=(200, 210, 220))
        self._eid_label.parent = ep; ep.children.append(self._eid_label)
        y += 26

        self._add_input_row(ep, "event_id", evento.get("event_id", ""), y,
                            lambda v: self._on_field("event_id", v)); y += 28

        # ── Trigger ─────────────────────────────────────────────
        triggers = get_global_triggers()
        trigger_actual = evento.get("trigger", triggers[0] if triggers else "")
        self._add_dropdown_row(ep, "trigger", triggers, trigger_actual, y,
                               lambda v: self._on_field("trigger", v)); y += 28

        if trigger_actual == "on_boss_defeated":
            self._add_input_row(ep, "boss_id", evento.get("boss_id", ""), y,
                                lambda v: self._on_field("boss_id", v)); y += 28
        elif trigger_actual == "on_event_finalized":
            self._add_input_row(ep, "watched_event_id", evento.get("watched_event_id", ""), y,
                                lambda v: self._on_field("watched_event_id", v)); y += 28

        # ── once ────────────────────────────────────────────────
        once = bool(evento.get("once", False))
        self._add_checkbox_row(ep, "once", once, y,
                               lambda v: self._on_field("once", v)); y += 30

        # ── Condiciones ─────────────────────────────────────────
        y += 4
        lbl = Label(PADDING, y, 200, 22, "Condiciones:", font_size=13, color=(180, 200, 160))
        lbl.parent = ep; ep.children.append(lbl)
        y += 24

        condiciones = evento.get("condiciones", [])
        for cidx, cond in enumerate(condiciones):
            c_tipo = cond.get("tipo", "")
            params = cond.get("params", {})
            lbl = Label(PADDING + 10, y, 240, 22, f"{c_tipo} {params}", font_size=11,
                        color=(160, 170, 180))
            lbl.parent = ep; ep.children.append(lbl)
            del_btn = Button(PADDING + 260, y, 30, 22, "X",
                             callback=lambda i=cidx: self._on_remove_cond(i))
            del_btn.parent = ep; ep.children.append(del_btn)
            y += 24

        add_cond = Button(PADDING + 10, y, 200, 22, "+ Añadir condición",
                          callback=self._on_add_cond)
        add_cond.parent = ep; ep.children.append(add_cond)
        y += 30

        # ── Acciones ────────────────────────────────────────────
        y += 4
        lbl = Label(PADDING, y, 200, 22, "Acciones:", font_size=13, color=(180, 200, 160))
        lbl.parent = ep; ep.children.append(lbl)
        y += 24

        acciones = evento.get("acciones", [])
        for aidx, acc in enumerate(acciones):
            a_tipo = acc.get("tipo", "")
            params = acc.get("params", {})
            lbl = Label(PADDING + 10, y, 200, 22, a_tipo, font_size=11, color=(200, 210, 220))
            lbl.parent = ep; ep.children.append(lbl)
            del_btn = Button(PADDING + 220, y, 30, 22, "X",
                             callback=lambda i=aidx: self._on_remove_accion(i))
            del_btn.parent = ep; ep.children.append(del_btn)
            y += 24
            # Params de la acción (editables)
            y = self._build_accion_params(ep, y, acc, aidx)
            y += 4

        add_acc = Button(PADDING + 10, y, 200, 22, "+ Añadir acción",
                         callback=self._on_add_accion)
        add_acc.parent = ep; ep.children.append(add_acc)

    def _build_accion_params(self, ep, y, acc, aidx):
        """Edita los params de una acción según su tipo."""
        a_tipo = acc.get("tipo", "")
        params = acc.get("params", {})
        shop_id = params.get("shop_id", "")
        item_id = params.get("item_id", "")

        # shop_id
        tiendas = get_all_shops()
        lbl = Label(PADDING + 20, y, 90, 22, "shop_id:", font_size=11, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        dd = SimpleDropdown(PADDING + 110, y, 200, 22, [(t, t) for t in tiendas], selected=shop_id)
        dd._on_select = lambda v, i=aidx: self._on_accion_param(i, "shop_id", v)
        dd.parent = ep; ep.children.append(dd)
        y += 26

        if a_tipo in ("restock_shop", "add_shop_stock", "modify_shop_price"):
            items_shop = self._get_items_shop(shop_id)
            lbl = Label(PADDING + 20, y, 90, 22, "item_id:", font_size=11, color=(180, 185, 195))
            lbl.parent = ep; ep.children.append(lbl)
            if a_tipo == "restock_shop":
                opts = [("", "(todos)")] + [(i, i) for i in items_shop]
            else:
                opts = [(i, i) for i in items_shop]
            dd = SimpleDropdown(PADDING + 110, y, 200, 22, opts, selected=item_id)
            dd._on_select = lambda v, i=aidx: self._on_accion_param(i, "item_id", v)
            dd.parent = ep; ep.children.append(dd)
            y += 26

        if a_tipo == "add_shop_stock":
            cantidad = str(params.get("cantidad", 1))
            lbl = Label(PADDING + 20, y, 90, 22, "cantidad:", font_size=11, color=(180, 185, 195))
            lbl.parent = ep; ep.children.append(lbl)
            inp = TextInput(PADDING + 110, y, 80, 22, default=cantidad, max_chars=6, numeric_only=True)
            inp._on_change = lambda i=aidx: self._on_accion_param(
                i, "cantidad", int(inp.text) if inp.text.isdigit() else 1)
            inp.parent = ep; ep.children.append(inp)
            y += 26

        if a_tipo == "modify_shop_price":
            moneda = params.get("moneda", "")
            monedas = get_all_monedas()
            lbl = Label(PADDING + 20, y, 90, 22, "moneda:", font_size=11, color=(180, 185, 195))
            lbl.parent = ep; ep.children.append(lbl)
            dd = SimpleDropdown(PADDING + 110, y, 120, 22, [(m, m) for m in monedas], selected=moneda)
            dd._on_select = lambda v, i=aidx: self._on_accion_param(i, "moneda", v)
            dd.parent = ep; ep.children.append(dd)
            precio = str(params.get("precio", 0))
            lbl2 = Label(PADDING + 240, y, 90, 22, "precio:", font_size=11, color=(180, 185, 195))
            lbl2.parent = ep; ep.children.append(lbl2)
            inp = TextInput(PADDING + 330, y, 80, 22, default=precio, max_chars=6, numeric_only=True)
            inp._on_change = lambda i=aidx: self._on_accion_param(
                i, "precio", int(inp.text) if inp.text.isdigit() else 0)
            inp.parent = ep; ep.children.append(inp)
            y += 26

        return y

    def _get_items_shop(self, shop_id):
        if not shop_id:
            return []
        shop = get_shop(shop_id)
        if not shop:
            return []
        return [it.get("item_id", "") for it in shop.get("items", []) if it.get("item_id")]

    # ── Callbacks ───────────────────────────────────────────────

    def _on_new(self):
        self._selected_idx = len(self._eventos)
        self._eventos.append({
            "event_id": "evento_nuevo",
            "trigger": "on_boss_defeated",
            "boss_id": "",
            "condiciones": [],
            "acciones": [],
            "once": False,
        })
        self._build_editor_widgets()
        self._set_status("Nuevo evento creado")

    def _on_clone(self):
        if self._selected_idx is None or not (0 <= self._selected_idx < len(self._eventos)):
            return
        orig = self._eventos[self._selected_idx]
        base_id = orig.get("event_id", "evento")
        new_id = base_id + "_copy"
        i = 1
        while any(e.get("event_id") == new_id for e in self._eventos):
            new_id = f"{base_id}_copy{i}"
            i += 1
        nuevo = copy_evento(orig)
        nuevo["event_id"] = new_id
        self._eventos.insert(self._selected_idx + 1, nuevo)
        self._selected_idx += 1
        self._build_editor_widgets()
        self._set_status(f"Clonado a {new_id}")

    def _on_delete(self):
        if self._selected_idx is None or not (0 <= self._selected_idx < len(self._eventos)):
            return
        del self._eventos[self._selected_idx]
        self._selected_idx = None
        self._build_ui()
        self._set_status("Evento eliminado")

    def _on_save(self):
        from editor.events_data import validar_eventos_globales
        bloq, adv = validar_eventos_globales(self._eventos)
        if bloq:
            print("[Eventos] Errores de validación:")
            for e in bloq:
                print(f"  - {e}")
            self._set_status("Errores: " + "; ".join(bloq[:3]) + ("..." if len(bloq) > 3 else ""), error=True)
            return
        if adv:
            print("[Eventos] Advertencias:")
            for a in adv:
                print(f"  - {a}")
        set_eventos_globales(self._eventos)
        self._set_status("Guardado OK" + (f" | Avisos: {'; '.join(adv[:3])}" if adv else ""))

    def _on_field(self, key, val):
        if self._selected_idx is None or not (0 <= self._selected_idx < len(self._eventos)):
            return
        evento = self._eventos[self._selected_idx]
        if key == "event_id":
            val = val.strip()
            if not val:
                return
            if val != evento.get("event_id"):
                if any(e.get("event_id") == val for e in self._eventos):
                    self._set_status("event_id duplicado", error=True)
                    return
            self._eid_label.text = f"ID: {val}"
        evento[key] = val
        if key == "trigger":
            self._build_editor_widgets()

    # ── Condiciones ─────────────────────────────────────────────

    def _on_add_cond(self):
        if self._selected_idx is None or not (0 <= self._selected_idx < len(self._eventos)):
            return
        evento = self._eventos[self._selected_idx]
        tipo = GLOBAL_CONDITION_TYPES[0]
        evento.setdefault("condiciones", [])
        evento["condiciones"].append({
            "tipo": tipo,
            "params": dict(CONDITION_PARAMS.get(tipo, {})),
        })
        self._build_editor_widgets()

    def _on_remove_cond(self, idx):
        if self._selected_idx is None or not (0 <= self._selected_idx < len(self._eventos)):
            return
        evento = self._eventos[self._selected_idx]
        condiciones = evento.get("condiciones", [])
        if 0 <= idx < len(condiciones):
            del condiciones[idx]
            self._build_editor_widgets()

    # ── Acciones ────────────────────────────────────────────────

    def _on_add_accion(self):
        if self._selected_idx is None or not (0 <= self._selected_idx < len(self._eventos)):
            return
        evento = self._eventos[self._selected_idx]
        tipo = "add_shop_stock"
        evento.setdefault("acciones", [])
        evento["acciones"].append({
            "tipo": tipo,
            "params": get_global_action_params(tipo),
        })
        self._build_editor_widgets()

    def _on_remove_accion(self, idx):
        if self._selected_idx is None or not (0 <= self._selected_idx < len(self._eventos)):
            return
        evento = self._eventos[self._selected_idx]
        acciones = evento.get("acciones", [])
        if 0 <= idx < len(acciones):
            del acciones[idx]
            self._build_editor_widgets()

    def _on_accion_param(self, aidx, key, val):
        if self._selected_idx is None or not (0 <= self._selected_idx < len(self._eventos)):
            return
        evento = self._eventos[self._selected_idx]
        acciones = evento.get("acciones", [])
        if 0 <= aidx < len(acciones):
            acciones[aidx].setdefault("params", {})[key] = val
            if key == "shop_id":
                acciones[aidx]["params"].pop("item_id", None)
            self._build_editor_widgets()

    # ── Helpers UI ──────────────────────────────────────────────

    def _add_input_row(self, panel, key, default, y, on_change):
        lbl = Label(PADDING, y, 160, 22, key + ":", font_size=12, color=(180, 185, 195))
        lbl.parent = panel; panel.children.append(lbl)
        inp = TextInput(170, y, 300, 22, default=default, max_chars=60, numeric_only=False)
        inp._on_change = lambda: on_change(inp.text)
        inp.parent = panel; panel.children.append(inp)

    def _add_dropdown_row(self, panel, key, options, default, y, on_change):
        lbl = Label(PADDING, y, 160, 22, key + ":", font_size=12, color=(180, 185, 195))
        lbl.parent = panel; panel.children.append(lbl)
        opts = [(o, o) for o in options]
        dd = SimpleDropdown(170, y, 220, 22, opts, selected=default)
        dd._on_select = on_change
        dd.parent = panel; panel.children.append(dd)

    def _add_checkbox_row(self, panel, key, checked, y, on_change):
        lbl = Label(PADDING, y, 160, 22, key + ":", font_size=12, color=(180, 185, 195))
        lbl.parent = panel; panel.children.append(lbl)
        cb = Checkbox(170, y, checked=checked)
        cb.callback = on_change
        cb.parent = panel; panel.children.append(cb)

    def _set_status(self, texto, error=False):
        self._status_text = texto
        self._status_error = error
        self._status_lbl.text = texto
        self._status_lbl.color = (220, 80, 80) if error else (150, 200, 150)

    # ── Dibujado lista lateral ──────────────────────────────────

    def draw(self, surface):
        super().draw(surface)
        if self._descripcion:
            self.draw_descripcion(surface)
        ar = self.get_abs_rect()
        lx, ly = ar.x, ar.y + TOOLBAR_H
        lw, lh = LEFT_W, self.rect.h - TOOLBAR_H
        hdr = pygame.Rect(lx, ly, lw, HEADER_H)
        pygame.draw.rect(surface, (42, 46, 55), hdr)
        pygame.draw.rect(surface, (55, 60, 70), hdr, 1)
        from editor.translation import I18n
        i18n = I18n.instancia()
        fuente_b = i18n.fuente(12, bold=True) if i18n else pygame.font.SysFont("Arial", 12, bold=True)
        fuente = i18n.fuente(12) if i18n else pygame.font.SysFont("Arial", 12)
        txt = fuente_b.render(self.i18n.t("tab.global_events") or "Eventos Globales", True, (200, 210, 220))
        surface.blit(txt, (lx + PADDING, ly + (HEADER_H - txt.get_height()) // 2))
        cnt = len(self._eventos)
        ctxt = fuente.render(f"({cnt})", True, (130, 140, 150))
        surface.blit(ctxt, (lx + lw - ctxt.get_width() - PADDING, ly + (HEADER_H - ctxt.get_height()) // 2))
        lr = pygame.Rect(lx, ly + HEADER_H, lw, lh - HEADER_H)
        clip = surface.get_clip()
        surface.set_clip(lr)
        for i, evento in enumerate(self._eventos):
            sy = lr.y + i * ROW_H - self._list_scroll
            if sy + ROW_H < lr.y or sy > lr.y + lr.h:
                continue
            sel = i == self._selected_idx
            bg = (55, 60, 72) if sel else (38, 42, 50)
            pygame.draw.rect(surface, bg, (lr.x, sy, lr.w, ROW_H))
            if sel:
                pygame.draw.rect(surface, (70, 130, 200), (lr.x, sy, 3, ROW_H))
            eid = evento.get("event_id", "")
            trigger = evento.get("trigger", "")
            tc = (200, 210, 220) if sel else (160, 170, 180)
            txt = fuente.render(eid, True, tc)
            surface.blit(txt, (PADDING, sy + (ROW_H - txt.get_height()) // 2))
            nc = (130, 140, 150) if sel else (110, 120, 130)
            nt = fuente.render(f"({trigger})", True, nc)
            surface.blit(nt, (120, sy + (ROW_H - nt.get_height()) // 2))
        surface.set_clip(clip)

    # ── Eventos ─────────────────────────────────────────────────

    def handle_event(self, event):
        if not self.visible:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            ar = self.get_abs_rect()
            lx, ly = ar.x, ar.y + TOOLBAR_H
            lw, lh = LEFT_W, self.rect.h - TOOLBAR_H
            lr = pygame.Rect(lx, ly + HEADER_H, lw, lh - HEADER_H)
            if lr.collidepoint(mx, my):
                local_y = my - lr.y + self._list_scroll
                idx = local_y // ROW_H
                if 0 <= idx < len(self._eventos):
                    self._selected_idx = idx
                    self._build_editor_widgets()
                    return True
        if event.type == pygame.MOUSEWHEEL:
            ar = self.get_abs_rect()
            lx, ly = ar.x, ar.y + TOOLBAR_H
            lw, lh = LEFT_W, self.rect.h - TOOLBAR_H
            lr = pygame.Rect(lx, ly + HEADER_H, lw, lh - HEADER_H)
            mx, my = pygame.mouse.get_pos()
            if lr.collidepoint(mx, my):
                max_scroll = max(0, len(self._eventos) * ROW_H - lr.h)
                self._list_scroll = max(0, min(max_scroll, self._list_scroll - event.y * ROW_H))
                return True
        if self._editor_panel and self._editor_panel.visible:
            if self._editor_panel.handle_event(event):
                return True
        return super().handle_event(event)


def copy_evento(evento):
    import copy
    return copy.deepcopy(evento)


# ── Checkbox widget (sin dependencias externas) ──────────────────────────
class Checkbox:
    """Checkbox rectangular 22x22."""

    def __init__(self, x, y, w=22, h=22, checked=False):
        self.rect = pygame.Rect(x, y, w, h)
        self.parent = None
        self.visible = True
        self.enabled = True
        self.checked = checked
        self.callback = None

    def _abs_rect(self):
        if self.parent:
            pr = self.parent.get_abs_rect() if hasattr(self.parent, "get_abs_rect") else self.parent.rect
            return pygame.Rect(pr.x + self.rect.x, pr.y + self.rect.y, self.rect.w, self.rect.h)
        return self.rect.copy()

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._abs_rect().collidepoint(event.pos):
                self.checked = not self.checked
                if self.callback:
                    self.callback(self.checked)
                return True
        return False

    def draw(self, surface):
        if not self.visible:
            return
        r = self._abs_rect()
        pygame.draw.rect(surface, (30, 32, 36), r, border_radius=4)
        pygame.draw.rect(surface, (60, 65, 75), r, 2, border_radius=4)
        if self.checked:
            pygame.draw.line(surface, (70, 130, 200),
                             (r.x + 4, r.y + 8), (r.x + 14, r.y + 18), 3)
            pygame.draw.line(surface, (70, 130, 200),
                             (r.x + 14, r.y + 8), (r.x + 4, r.y + 18), 3)
