# Editor de tiendas (data/shops.json).
#
# Estructura:
#   item:   { item_id, precio, stock_infinito, stock? }
#   tienda: { shop_id, nombre, descripcion, moneda_principal, items }
#
# La tienda SOLO tiene datos de tienda. El restock lo manejan los eventos
# globales (eventos_globales.json) apuntando por shop_id.

import json
import pygame

from editor.panels.base_panel import BasePanel
from editor.widgets.base import Widget
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.text_input import TextInput
from editor.widgets.simple_dropdown import SimpleDropdown
from editor.project import get_current_project
from editor.shops_data import (
    _load_shops,
    get_shops,
    set_shops,
    validar_shops,
    get_all_shops,
)
from editor.monedas_data import _load_monedas, get_all_monedas
from editor.items_data import _load_items, get_all_items

PADDING = 6
TOOLBAR_H = 36
HEADER_H = 26
LEFT_W = 220
ROW_H = 28


class ShopsTab(BasePanel):
    """Editor de tiendas (data/shops.json)."""

    def __init__(self, x, y, w, h, i18n):
        super().__init__(x, y, w, h, i18n)
        self.bg_color = (30, 32, 36)
        _load_shops()
        _load_monedas()
        _load_items()
        self._shops = get_shops()
        self._selected_shop_idx = None
        self._selected_item_idx = None
        self._list_scroll = 0
        self._status_text = ""
        self._status_error = False
        self._build_ui()

    def _build_ui(self):
        self.clear()
        self.mostrar_descripcion(
            self.i18n.t("tab.shops.desc") if not self._shops else ""
        )
        tb = Panel(0, 0, self.rect.w, TOOLBAR_H, bg_color=(42, 46, 55), border_color=(60, 65, 75))
        self.add(tb)
        self._new_btn = Button(8, 4, 72, 28, self.i18n.t("shop.new"), callback=self._on_new_shop)
        self._new_btn.parent = tb; tb.children.append(self._new_btn)
        self._clone_btn = Button(86, 4, 72, 28, self.i18n.t("shop.clone"), callback=self._on_clone_shop)
        self._clone_btn.parent = tb; tb.children.append(self._clone_btn)
        self._del_btn = Button(164, 4, 72, 28, self.i18n.t("shop.delete"), callback=self._on_delete_shop)
        self._del_btn.parent = tb; tb.children.append(self._del_btn)
        self._save_btn = Button(240, 4, 72, 28, self.i18n.t("shop.save"), callback=self._on_save)
        self._save_btn.parent = tb; tb.children.append(self._save_btn)
        self._status_lbl = Label(320, 4, max(60, self.rect.w - 330), 28, "", font_size=12,
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

        if self._selected_shop_idx is None or not (0 <= self._selected_shop_idx < len(self._shops)):
            ep.visible = False
            return
        ep.visible = True
        shop = self._shops[self._selected_shop_idx]

        # ── Shop header ──────────────────────────────────────────
        self._shop_id_label = Label(PADDING, y, ep.rect.w - PADDING * 2, 20,
                                    f"ID: {shop.get('shop_id', '')}", font_size=13, color=(200, 210, 220))
        self._shop_id_label.parent = ep; ep.children.append(self._shop_id_label)
        y += 26

        self._add_input_row(ep, "shop.shop_id", shop.get("shop_id", ""), y, lambda v: self._on_shop_field("shop_id", v)); y += 28
        self._add_input_row(ep, "shop.nombre", shop.get("nombre", ""), y, lambda v: self._on_shop_field("nombre", v)); y += 28
        self._add_input_row(ep, "shop.descripcion", shop.get("descripcion", ""), y, lambda v: self._on_shop_field("descripcion", v)); y += 28

        monedas = get_all_monedas()
        self._add_dropdown_row(ep, "shop.moneda_principal", monedas, shop.get("moneda_principal", ""), y,
                               lambda v: self._on_shop_field("moneda_principal", v)); y += 28

        # ── Items list ──────────────────────────────────────────
        items = shop.get("items", [])
        y += 10
        lbl = Label(PADDING, y, 200, 22, self.i18n.t("shop.items") + f" ({len(items)})", font_size=13, color=(180, 200, 160))
        lbl.parent = ep; ep.children.append(lbl)
        add_btn = Button(ep.rect.w - PADDING - 110, y, 110, 22, self.i18n.t("item.add"), callback=self._on_add_item)
        add_btn.parent = ep; ep.children.append(add_btn)
        y += 24

        self._items_list_panel = Panel(PADDING, y, ep.rect.w - PADDING * 2, 150, bg_color=(30, 32, 36), border_color=(60, 65, 75))
        self._items_list_panel.parent = ep; ep.children.append(self._items_list_panel)
        self._build_items_list()
        y += 160

        # ── Item editor ─────────────────────────────────────────
        if self._selected_item_idx is not None and 0 <= self._selected_item_idx < len(items):
            self._build_item_editor(ep, y, items[self._selected_item_idx])

    def _build_item_editor(self, panel, y, item):
        y += 10
        lbl = Label(PADDING, y, 200, 22, self.i18n.t("shop.item_editor"), font_size=13, color=(180, 200, 160))
        lbl.parent = panel; panel.children.append(lbl)
        y += 24

        items_validos = get_all_items()
        monedas = get_all_monedas()

        # 1. item_id dropdown
        self._add_dropdown_row(panel, "item.item_id", items_validos, item.get("item_id", ""), y,
                               lambda v: self._on_item_field("item_id", v)); y += 28

        # 2. precio inputs - uno por moneda
        precio = item.get("precio", {})
        for moneda in monedas:
            valor = str(precio.get(moneda, 0))
            self._add_input_row(panel, f"precio.{moneda}", valor, y,
                                lambda v, m=moneda: self._on_item_price(m, v),
                                numeric_only=True); y += 28

        # 3. stock_infinito checkbox (PRIMERO)
        stock_inf = item.get("stock_infinito", True)
        self._add_checkbox_row(panel, "stock_infinito", stock_inf, y,
                               lambda v: self._on_item_field("stock_infinito", v)); y += 28

        # 4. stock input (SOLO si !stock_infinito)
        if not stock_inf:
            stock_val = item.get("stock", 0)
            self._add_input_row(panel, "stock", str(stock_val), y,
                                lambda v: self._on_item_field("stock", v),
                                numeric_only=True); y += 28

        # 5. Botón eliminar item
        del_btn = Button(PADDING, y, 160, 26, self.i18n.t("item.delete"), callback=self._on_delete_item,
                         color=(90, 50, 50), hover_color=(120, 70, 70))
        del_btn.parent = panel; panel.children.append(del_btn)
        y += 32

    def _build_items_list(self):
        pl = self._items_list_panel
        pl.clear()
        shop = self._shops[self._selected_shop_idx]
        items = shop.get("items", [])
        for i, item in enumerate(items):
            sel = (i == self._selected_item_idx)
            bg = (50, 70, 50) if sel else (40, 45, 55)
            item_panel = Panel(4, 4 + i * 28, pl.rect.w - 8, 24, bg_color=bg, border_color=(80, 90, 100) if sel else (60, 65, 75))
            item_panel.parent = pl; pl.children.append(item_panel)
            item_id = item.get("item_id", "")
            precio = item.get("precio", {})
            monedas = list(precio.keys())
            precio_str = " + ".join(f"{precio[m]} {m}" for m in monedas) if monedas else "?"
            stock = item.get("stock", 0)
            stock_inf = item.get("stock_infinito", True)
            stock_str = "∞" if stock_inf else f"stock:{stock}"
            lbl = Label(8, 2, pl.rect.w - 16, 20, f"{item_id} - {precio_str} [{stock_str}]", font_size=11,
                        color=(200, 220, 200) if sel else (160, 170, 150))
            lbl.parent = item_panel; item_panel.children.append(lbl)

            def make_select(idx):
                def _on_click():
                    self._selected_item_idx = idx
                    self._build_editor_widgets()
                return _on_click
            item_panel.on_click = make_select(i)

    # ── Callbacks shop ──────────────────────────────────────────

    def _on_new_shop(self):
        monedas = get_all_monedas()
        self._selected_shop_idx = len(self._shops)
        self._selected_item_idx = None
        self._shops.append({
            "shop_id": "shop_nuevo",
            "nombre": "Tienda Nueva",
            "descripcion": "",
            "moneda_principal": monedas[0] if monedas else "",
            "items": [],
        })
        self._build_editor_widgets()
        self._set_status("Nueva tienda creada")

    def _on_clone_shop(self):
        if self._selected_shop_idx is None or not (0 <= self._selected_shop_idx < len(self._shops)):
            return
        orig = self._shops[self._selected_shop_idx]
        base_id = orig.get("shop_id", "shop")
        new_id = base_id + "_copy"
        i = 1
        while any(s.get("shop_id") == new_id for s in self._shops):
            new_id = f"{base_id}_copy{i}"
            i += 1
        nuevo = orig.copy()
        nuevo["shop_id"] = new_id
        self._shops.insert(self._selected_shop_idx + 1, nuevo)
        self._selected_shop_idx += 1
        self._selected_item_idx = None
        self._build_editor_widgets()
        self._set_status(f"Clonada a {new_id}")

    def _on_delete_shop(self):
        if self._selected_shop_idx is None or not (0 <= self._selected_shop_idx < len(self._shops)):
            return
        del self._shops[self._selected_shop_idx]
        self._selected_shop_idx = None
        self._selected_item_idx = None
        self._build_ui()
        self._set_status("Tienda eliminada")

    def _on_save(self):
        bloq, adv = validar_shops(self._shops)
        if bloq:
            print("[Shops] Errores de validación:")
            for e in bloq:
                print(f"  - {e}")
            self._set_status("Errores: " + "; ".join(bloq[:3]) + ("..." if len(bloq) > 3 else ""), error=True)
            return
        if adv:
            print("[Shops] Advertencias:")
            for a in adv:
                print(f"  - {a}")
        set_shops(self._shops)
        self._set_status("Guardado OK" + (f" | Avisos: {'; '.join(adv[:3])}" if adv else ""))

    def _on_shop_field(self, key, val):
        if self._selected_shop_idx is not None and 0 <= self._selected_shop_idx < len(self._shops):
            if key == "shop_id":
                val = val.strip()
                if not val:
                    return
                if val != self._shops[self._selected_shop_idx].get("shop_id"):
                    if any(s.get("shop_id") == val for s in self._shops):
                        self._set_status("shop_id duplicado", error=True)
                        return
                self._shop_id_label.text = f"ID: {val}"
            self._shops[self._selected_shop_idx][key] = val

    # ── Callbacks item ──────────────────────────────────────────

    def _on_add_item(self):
        if self._selected_shop_idx is None:
            return
        monedas = get_all_monedas()
        primera_moneda = monedas[0] if monedas else ""
        shop = self._shops[self._selected_shop_idx]
        items = shop.get("items", [])
        items.append({
            "item_id": "",
            "precio": {primera_moneda: 0} if primera_moneda else {},
            "stock_infinito": True,
        })
        self._selected_item_idx = len(items) - 1
        self._build_editor_widgets()

    def _on_delete_item(self):
        if self._selected_shop_idx is None or self._selected_item_idx is None:
            return
        shop = self._shops[self._selected_shop_idx]
        items = shop.get("items", [])
        if 0 <= self._selected_item_idx < len(items):
            del items[self._selected_item_idx]
        self._selected_item_idx = None
        self._build_editor_widgets()

    def _on_item_field(self, key, val):
        if self._selected_shop_idx is None or self._selected_item_idx is None:
            return
        shop = self._shops[self._selected_shop_idx]
        items = shop.get("items", [])
        if 0 <= self._selected_item_idx < len(items):
            item = items[self._selected_item_idx]
            if key == "stock":
                try:
                    val = int(val)
                except ValueError:
                    return
            item[key] = val
            if key == "stock_infinito":
                # Mostrar/ocultar el campo stock según el checkbox
                self._build_editor_widgets()
            else:
                # Refrescar solo la lista de items (el editor no se reconstruye
                # para no perder el foco del TextInput).
                self._build_items_list()

    def _on_item_price(self, moneda, val):
        if self._selected_shop_idx is None or self._selected_item_idx is None:
            return
        shop = self._shops[self._selected_shop_idx]
        items = shop.get("items", [])
        if 0 <= self._selected_item_idx < len(items):
            try:
                val = int(val)
            except ValueError:
                return
            if "precio" not in items[self._selected_item_idx]:
                items[self._selected_item_idx]["precio"] = {}
            items[self._selected_item_idx]["precio"][moneda] = val

    # ── Helpers UI ──────────────────────────────────────────────

    def _add_input_row(self, panel, key, default, y, on_change, numeric_only=False):
        lbl = Label(PADDING, y, 160, 22, key + ":", font_size=12, color=(180, 185, 195))
        lbl.parent = panel; panel.children.append(lbl)
        inp = TextInput(170, y, 300, 22, default=default, max_chars=60, numeric_only=numeric_only)
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

    # ── Status ──────────────────────────────────────────────────

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
        txt = fuente_b.render(self.i18n.t("tab.shops"), True, (200, 210, 220))
        surface.blit(txt, (lx + PADDING, ly + (HEADER_H - txt.get_height()) // 2))
        cnt = len(self._shops)
        ctxt = fuente.render(f"({cnt})", True, (130, 140, 150))
        surface.blit(ctxt, (lx + lw - ctxt.get_width() - PADDING, ly + (HEADER_H - ctxt.get_height()) // 2))
        lr = pygame.Rect(lx, ly + HEADER_H, lw, lh - HEADER_H)
        clip = surface.get_clip()
        surface.set_clip(lr)
        for i, shop in enumerate(self._shops):
            sy = lr.y + i * ROW_H - self._list_scroll
            if sy + ROW_H < lr.y or sy > lr.y + lr.h:
                continue
            sel = i == self._selected_shop_idx
            bg = (55, 60, 72) if sel else (38, 42, 50)
            pygame.draw.rect(surface, bg, (lr.x, sy, lr.w, ROW_H))
            if sel:
                pygame.draw.rect(surface, (70, 130, 200), (lr.x, sy, 3, ROW_H))
            sid = shop.get("shop_id", "")
            nombre = shop.get("nombre") or sid
            tc = (200, 210, 220) if sel else (160, 170, 180)
            txt = fuente.render(sid, True, tc)
            surface.blit(txt, (PADDING, sy + (ROW_H - txt.get_height()) // 2))
            nc = (130, 140, 150) if sel else (110, 120, 130)
            nt = fuente.render(f"({nombre})", True, nc)
            surface.blit(nt, (100, sy + (ROW_H - nt.get_height()) // 2))
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
                if 0 <= idx < len(self._shops):
                    self._selected_shop_idx = idx
                    self._selected_item_idx = None
                    self._build_editor_widgets()
                    return True
        if event.type == pygame.MOUSEWHEEL:
            ar = self.get_abs_rect()
            lx, ly = ar.x, ar.y + TOOLBAR_H
            lw, lh = LEFT_W, self.rect.h - TOOLBAR_H
            lr = pygame.Rect(lx, ly + HEADER_H, lw, lh - HEADER_H)
            mx, my = pygame.mouse.get_pos()
            if lr.collidepoint(mx, my):
                max_scroll = max(0, len(self._shops) * ROW_H - lr.h)
                self._list_scroll = max(0, min(max_scroll, self._list_scroll - event.y * ROW_H))
                return True
        if self._editor_panel and self._editor_panel.visible:
            if self._editor_panel.handle_event(event):
                return True
        return super().handle_event(event)


# ── Checkbox widget (sin dependencias externas) ──────────────────────────
class Checkbox(Widget):
    """Checkbox rectangular 22x22."""
    def __init__(self, x, y, w=22, h=22, checked=False):
        super().__init__(x, y, w, h)
        self.checked = checked
        self.callback = None

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
