import pygame

from editor.panels.base_panel import BasePanel
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.text_input import TextInput
from editor.project import get_current_project
from editor.contadores_data import (
    _load_contadores,
    get_contadores,
    set_contadores,
    validar_contadores,
)

PADDING = 6
ROW_H = 28
TOOLBAR_H = 36
HEADER_H = 26
LEFT_W = 220


class ContadoresTab(BasePanel):
    """Editor de contadores de progresión (data/contadores.json)."""

    def __init__(self, x, y, w, h, i18n):
        super().__init__(x, y, w, h, i18n)
        self.bg_color = (30, 32, 36)
        _load_contadores()
        self._contadores = get_contadores()
        self._selected_idx = None
        self._list_scroll = 0
        self._status_text = ""
        self._status_error = False
        self._build_ui()

    def _build_ui(self):
        self.clear()
        self.mostrar_descripcion(
            self.i18n.t("tab.contadores.desc") if not self._contadores else ""
        )
        tb = Panel(0, 0, self.rect.w, TOOLBAR_H, bg_color=(42, 46, 55), border_color=(60, 65, 75))
        self.add(tb)
        self._new_btn = Button(8, 4, 72, 28, self.i18n.t("contador.new"), callback=self._on_new)
        self._new_btn.parent = tb; tb.children.append(self._new_btn)
        self._clone_btn = Button(86, 4, 72, 28, self.i18n.t("contador.clone"), callback=self._on_clone)
        self._clone_btn.parent = tb; tb.children.append(self._clone_btn)
        self._del_btn = Button(164, 4, 72, 28, self.i18n.t("contador.delete"), callback=self._on_delete)
        self._del_btn.parent = tb; tb.children.append(self._del_btn)
        self._save_btn = Button(240, 4, 72, 28, self.i18n.t("contador.save"), callback=self._on_save)
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
        self._inps = None
        self._id_input = None
        self._nombre_input = None
        self._inicial_input = None
        self._maximo_input = None
        self._desc_input = None
        y = PADDING

        if self._selected_idx is None or not (0 <= self._selected_idx < len(self._contadores)):
            ep.visible = False
            return
        ep.visible = True
        contador = self._contadores[self._selected_idx]

        self._eid_label = Label(PADDING, y, ep.rect.w - PADDING * 2, 20,
                                f"ID: {contador.get('id', '')}", font_size=13, color=(200, 210, 220))
        self._eid_label.parent = ep; ep.children.append(self._eid_label)
        y += 26

        lbl = Label(PADDING, y, 110, 22, self.i18n.t("contador.id") + ":", font_size=12,
                    color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._id_input = TextInput(120, y, 220, 22, default=contador.get("id", ""),
                                    max_chars=30, numeric_only=False)
        self._id_input._on_change = self._on_id_change
        self._id_input.parent = ep; ep.children.append(self._id_input)
        y += 28

        lbl = Label(PADDING, y, 110, 22, self.i18n.t("contador.nombre") + ":", font_size=12,
                    color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._nombre_input = TextInput(120, y, 300, 22, default=contador.get("nombre", ""),
                                        max_chars=50, numeric_only=False)
        self._nombre_input._on_change = self._on_nombre_change
        self._nombre_input.parent = ep; ep.children.append(self._nombre_input)
        y += 28

        lbl = Label(PADDING, y, 110, 22, self.i18n.t("contador.inicial") + ":", font_size=12,
                    color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._inicial_input = TextInput(120, y, 100, 22, default=str(contador.get("inicial", 0)),
                                        max_chars=7, numeric_only=True)
        self._inicial_input._on_change = self._on_inicial_change
        self._inicial_input.parent = ep; ep.children.append(self._inicial_input)
        y += 28

        lbl = Label(PADDING, y, 110, 22, self.i18n.t("contador.maximo") + ":", font_size=12,
                    color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._maximo_input = TextInput(120, y, 100, 22, default=str(contador.get("maximo", 999999)),
                                        max_chars=7, numeric_only=True)
        self._maximo_input._on_change = self._on_maximo_change
        self._maximo_input.parent = ep; ep.children.append(self._maximo_input)
        y += 28

        lbl = Label(PADDING, y, 110, 22, self.i18n.t("contador.descripcion") + ":", font_size=12,
                    color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._desc_input = TextInput(120, y, 400, 22, default=contador.get("descripcion", ""),
                                     max_chars=200, numeric_only=False)
        self._desc_input._on_change = self._on_desc_change
        self._desc_input.parent = ep; ep.children.append(self._desc_input)

    def _set_status(self, texto, error=False):
        self._status_text = texto
        self._status_error = error
        self._status_lbl.text = texto
        self._status_lbl.color = (220, 80, 80) if error else (150, 200, 150)

    def _clear_status(self):
        self._set_status("")

    # ── Callbacks lista ──────────────────────────────────────────

    def _on_new(self):
        self._selected_idx = len(self._contadores)
        self._contadores.append({
            "id": "contador_nuevo",
            "nombre": "Contador Nuevo",
            "inicial": 0,
            "maximo": 999999,
            "descripcion": ""
        })
        self._build_editor_widgets()
        self._set_status("Nuevo contador creado")

    def _on_clone(self):
        if self._selected_idx is None or not (0 <= self._selected_idx < len(self._contadores)):
            return
        orig = self._contadores[self._selected_idx]
        base_id = orig.get("id", "contador")
        new_id = base_id + "_copy"
        i = 1
        while any(c.get("id") == new_id for c in self._contadores):
            new_id = f"{base_id}_copy{i}"
            i += 1
        nuevo = orig.copy()
        nuevo["id"] = new_id
        self._contadores.insert(self._selected_idx + 1, nuevo)
        self._selected_idx += 1
        self._build_editor_widgets()
        self._set_status(f"Clonado a {new_id}")

    def _on_delete(self):
        if self._selected_idx is None or not (0 <= self._selected_idx < len(self._contadores)):
            return
        del self._contadores[self._selected_idx]
        self._selected_idx = None
        self._build_editor_widgets()
        self._set_status("Contador eliminado")

    def _on_save(self):
        bloq, adv = validar_contadores(self._contadores)
        if bloq:
            self._set_status("Errores: " + "; ".join(bloq), error=True)
            return
        set_contadores(self._contadores)
        self._set_status("Guardado OK" + (f" | Avisos: {'; '.join(adv)}" if adv else ""))

    # ── Callbacks editor ─────────────────────────────────────────

    def _on_id_change(self, val):
        if self._selected_idx is None:
            return
        val = val.strip()
        if not val:
            return
        if val != self._contadores[self._selected_idx].get("id", ""):
            if any(c.get("id") == val for c in self._contadores):
                self._set_status("ID duplicado", error=True)
                return
            self._contadores[self._selected_idx]["id"] = val
            self._eid_label.text = f"ID: {val}"
            self._clear_status()

    def _on_nombre_change(self, val):
        if self._selected_idx is not None:
            self._contadores[self._selected_idx]["nombre"] = val

    def _on_inicial_change(self, val):
        if self._selected_idx is not None:
            try:
                self._contadores[self._selected_idx]["inicial"] = int(val)
            except ValueError:
                pass

    def _on_maximo_change(self, val):
        if self._selected_idx is not None:
            try:
                self._contadores[self._selected_idx]["maximo"] = int(val)
            except ValueError:
                pass

    def _on_desc_change(self, val):
        if self._selected_idx is not None:
            self._contadores[self._selected_idx]["descripcion"] = val

    # ── UI List ──────────────────────────────────────────────────

    def draw(self, surface):
        super().draw(surface)
        # Draw left list
        if self._selected_idx is not None:
            self._draw_list(surface)

    def _draw_list(self, surface):
        pass  # Handled by BasePanel list rendering

    def on_event(self, event):
        return super().on_event(event)