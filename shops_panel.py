import pygame

from editor.panels.base_panel import BasePanel
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.text_input import TextInput
from editor.widgets.dropdown import Dropdown
from editor.project import get_current_project
from editor.shops_data import (
    _load_shops,
    get_shops,
    set_shops,
    validar_shops,
)
from editor.monedas_data import get_all_monedas
from editor.contadores_data import get_all_contadores
from editor.items_data import get_all_items

PADDING = 6
TOOLBAR_H = 36
LEFT_W = 220


class ShopsTab(BasePanel):
    """Editor de tiendas (data/shops.json)."""

    def __init__(self, x, y, w, h, i18n):
        super().__init__(x, y, w, h, i18n)
        self.bg_color = (30, 32, 36)
        _load_shops()
        self._shops = get_shops()
        self._selected_shop_idx = None
        self._selected_item_idx = None
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

        rx = 220
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

        # ── Shop header ──────────────────────────────────────────────
        self._shop_id_label = Label(PADDING, y, ep.rect.w - PADDING * 2, 20,
                                    f"ID: {shop.get('id', '')}", font_size=13, color=(200, 210, 220))
        self._shop_id_label.parent = ep; ep.children.append(self._shop_id_label)
        y += 26

        self._add_input_row(ep, "shop.id", shop.get("id", ""), y, lambda v: self._on_shop_field("id", v)); y += 28
        self._add_input_row(ep, "shop.nombre", shop.get("nombre", ""), y, lambda v: self._on_shop_field("nombre", v)); y += 28
        self._add_input_row(ep, "shop.descripcion", shop.get("descripcion", ""), y, lambda v: self._on_shop_field("descripcion", v)); y += 28

        monedas = get_all_monedas()
        self._add_dropdown_row(ep, "shop.moneda_principal", monedas, shop.get("moneda_principal", ""), y,
                               lambda v: self._on_shop_field("moneda_principal", v)); y += 28

        # ── Items list ──────────────────────────────────────────────
        items = shop.get("items", [])
        y += 10
        lbl = Label(PADDING, y, 200, 22, self.i18n.t("shop.items") + f" ({len(items)})", font_size=13, color=(180, 200, 160))
        lbl.parent = ep; ep.children.append(lbl)
        y += 24

        self._items_list_panel = Panel(PADDING, y, ep.rect.w - PADDING * 2, 150, bg_color=(30, 32, 36), border_color=(60, 65, 75))
        self._items_list_panel.parent = ep; ep.children.append(self._items_list_panel)
        self._build_items_list()
        y += 160

        # ── Item editor ─────────────────────────────────────────────
        if self._selected_item_idx is not None and 0 <= self._selected_item_idx < len(items):
            self._build_item_editor(ep, y, items[self._selected_item_idx])

    def _add_input_row(self, panel, key, default, y, on_change):
        lbl = Label(PADDING, y, 160, 22, key + ":", font_size=12, color=(180, 185, 195))
        lbl.parent = panel; panel.children.append(lbl)
        inp = TextInput(170, y, 300, 22, default=default, on_change=on_change)
        inp.parent = panel; panel.children.append(inp)

    def _add_dropdown_row(self, panel, key, options, default, y, on_change):
        lbl = Label(PADDING, y, 160, 22, key + ":", font_size=12, color=(180, 185, 195))
        lbl.parent = panel; panel.children.append(lbl)
        dd = Dropdown(170, y, 220, 22, options, default=default, on_change=on_change)
        dd.parent = panel; panel.children.append(dd)

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
            moneda = item.get("moneda_compra", "")
            precio_str = f"{precio.get(moneda, 0)} {moneda}"
            lbl = Label(8, 2, pl.rect.w - 16, 20, f"{i}: {item_id} - {precio_str}", font_size=11,
                        color=(200, 220, 200) if sel else (160, 170, 150))
            lbl.parent = item_panel; item_panel.children.append(lbl)
            # Click handler
            def make_select(idx):
                def _on_click():
                    self._selected_item_idx = idx
                    self._build_editor_widgets()
                return _on_click
            item_panel.on_click = make_select(i)

        # Add item button
        add_panel = Panel(4, 4 + len(items) * 28, pl.rect.w - 8, 24, bg_color=(40, 60, 40), border_color=(80, 120, 80))
        add_panel.parent = pl; pl.children.append(add_panel)
        add_lbl = Label(8, 2, pl.rect.w - 16, 20, "+ Añadir item", font_size=11, color=(180, 220, 180))
        add_lbl.parent = add_panel; add_panel.children.append(add_lbl)
        add_panel.on_click = self._on_add_item

    def _build_item_editor(self, panel, y, item):
        y += 10
        lbl = Label(PADDING, y, 200, 22, self.i18n.t("shop.item_editor"), font_size=13, color=(180, 200, 160))
        lbl.parent = panel; panel.children.append(lbl)
        y += 24

        items_validos = get_all_items()
        monedas = get_all_monedas()

        self._add_dropdown_row(panel, "item.item_id", items_validos, item.get("item_id", ""), y,
                               lambda v: self._on_item_field("item_id", v)); y += 28

        precio = item.get("precio", {})
        for moneda, valor in precio.items():
            self._add_input_row(panel, f"precio.{moneda}", str(valor), y,
                                lambda v, m=moneda: self._on_item_price(m, v)); y += 28

        self._add_dropdown_row(panel, "item.moneda_compra", monedas, item.get("moneda_compra", "oro"), y,
                               lambda v: self._on_item_field("moneda_compra", v)); y += 28

        self._add_input_row(panel, "item.stock", str(item.get("stock", 0)), y,
                            lambda v: self._on_item_field("stock", int(v))); y += 28
        self._add_input_row(panel, "item.max_stock", str(item.get("max_stock", 0)), y,
                            lambda v: self._on_item_field("max_stock", int(v))); y += 28
        self._add_input_row(panel, "item.max_stack", str(item.get("max_stack", 1)), y,
                            lambda v: self._on_item_field("max_stack", int(v))); y += 28

        # unlock (simplified - full builder would be more complex)
        unlock = item.get("unlock")
        unlock_str = "SÍ" if unlock else "NO"
        self._add_input_row(panel, "item.unlock", unlock_str, y, lambda v: None); y += 28

        # restock
        restock = item.get("restock")
        restock_str = "SÍ" if restock else "NO"
        self._add_input_row(panel, "item.restock", restock_str, y, lambda v: None); y += 28

        # Delete item button
        y += 10
        del_btn = Button(PADDING, y, 120, 28, "Eliminar item", callback=self._on_delete_item)
        del_btn.parent = panel; panel.children.append(del_btn)

    # ── Callbacks shop ──────────────────────────────────────────────

    def _on_new_shop(self):
        self._selected_shop_idx = len(self._shops)
        self._selected_item_idx = None
        self._shops.append({
            "id": "shop_nuevo",
            "nombre": "Tienda Nueva",
            "descripcion": "",
            "moneda_principal": "oro",
            "categorias": [],
            "items": [],
            "compra": {"items_aceptados": ["*"], "precios_compra": {}}
        })
        self._build_editor_widgets()
        self._set_status("Nueva tienda creada")

    def _on_clone_shop(self):
        if self._selected_shop_idx is None or not (0 <= self._selected_shop_idx < len(self._shops)):
            return
        orig = self._shops[self._selected_shop_idx]
        base_id = orig.get("id", "shop")
        new_id = base_id + "_copy"
        i = 1
        while any(s.get("id") == new_id for s in self._shops):
            new_id = f"{base_id}_copy{i}"
            i += 1
        nuevo = orig.copy()
        nuevo["id"] = new_id
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
        self._build_editor_widgets()
        self._set_status("Tienda eliminada")

    def _on_save(self):
        bloq, adv = validar_shops(self._shops)
        if bloq:
            self._set_status("Errores: " + "; ".join(bloq), error=True)
            return
        set_shops(self._shops)
        self._set_status("Guardado OK" + (f" | Avisos: {'; '.join(adv)}" if adv else ""))

    def _on_shop_field(self, key, val):
        if self._selected_shop_idx is not None and 0 <= self._selected_shop_idx < len(self._shops):
            if key in ("stock", "max_stock", "max_stack"):
                try:
                    val = int(val)
                except ValueError:
                    return
            self._shops[self._selected_shop_idx][key] = val
            if key == "id":
                self._shop_id_label.text = f"ID: {val}"

    # ── Callbacks item ──────────────────────────────────────────────

    def _on_add_item(self):
        if self._selected_shop_idx is None:
            return
        shop = self._shops[self._selected_shop_idx]
        items = shop.get("items", [])
        items.append({
            "item_id": "",
            "precio": {"oro": 0},
            "moneda_compra": "oro",
            "stock": 1,
            "max_stock": 1,
            "stock_infinito": False,
            "max_stack": 1,
            "unlock": None,
            "restock": None,
            "visible_si_bloqueado": False
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
            if key in ("stock", "max_stock", "max_stack"):
                try:
                    val = int(val)
                except ValueError:
                    return
            items[self._selected_item_idx][key] = val
            self._build_editor_widgets()

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
            self._build_editor_widgets()

    # ── Status ──────────────────────────────────────────────────────

    def _set_status(self, texto, error=False):
        self._status_text = texto
        self._status_error = error
        if hasattr(self, '_status_lbl'):
            self._status_lbl.text = texto
            self._status_lbl.color = (220, 80, 80) if error else (150, 200, 150)

    def _set_status(self, texto, error=False):
        self._status_text = texto
        self._status_error = error
        self._status_lbl.text = texto
        self._status_lbl.color = (220, 80, 80) if error else (150, 200, 150)

    def draw(self, surface):
        super().draw(surface)
        if self._selected_shop_idx is not None:
            self._draw_shops_list(surface)

    def _draw_shops_list(self, surface):
        # Left list handled by BasePanel
        pass

    def on_event(self, event):
        return super().on_event(event)