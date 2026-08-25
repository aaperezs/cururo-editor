import pygame

from editor.panels.base_panel import BasePanel
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.text_input import TextInput
from editor.project import get_current_project
from editor.save_system_data import (
    _load_config,
    get_config,
    set_config,
    get_field,
    set_field,
    validar_config,
)

PADDING = 6
ROW_H = 28
TOOLBAR_H = 36
HEADER_H = 26


class SaveSystemTab(BasePanel):
    """Editor de configuración del sistema de guardado (data/save_system.json)."""

    def __init__(self, x, y, w, h, i18n):
        super().__init__(x, y, w, h, i18n)
        self.bg_color = (30, 32, 36)
        _load_config()
        self._config = get_config()
        self._status_text = ""
        self._status_error = False
        self._build_ui()

    def _build_ui(self):
        self.clear()
        self.mostrar_descripcion("Configuración del sistema de guardado")

        tb = Panel(0, 0, self.rect.w, TOOLBAR_H, bg_color=(42, 46, 55), border_color=(60, 65, 75))
        self.add(tb)
        self._save_btn = Button(8, 4, 72, 28, "Guardar", callback=self._on_save)
        self._save_btn.parent = tb; tb.children.append(self._save_btn)
        self._reset_btn = Button(86, 4, 72, 28, "Resetear", callback=self._on_reset)
        self._reset_btn.parent = tb; tb.children.append(self._reset_btn)
        self._status_lbl = Label(164, 4, max(60, self.rect.w - 174), 28, "", font_size=12,
                                 color=(150, 200, 150))
        self._status_lbl.parent = tb; tb.children.append(self._status_lbl)

        # Editor panel
        rx = 0
        cy = TOOLBAR_H
        rw = self.rect.w
        ch = self.rect.h - cy
        self._editor = Panel(rx, cy, rw, ch, bg_color=(35, 38, 46))
        self.add(self._editor)

        self._build_fields()

    def _build_fields(self):
        self._editor.clear()
        y = PADDING
        mw = self._editor.rect.w - 2 * PADDING

        # General
        self._add_section("General", y)
        y += HEADER_H + 4

        self._slots_input = self._add_field("Slots totales:", str(self._config.get("slots", 10)), y, "slots")
        y += ROW_H + 4

        self._item_input = self._add_field("Item requerido:", self._config.get("save_point_item_id", "cinta_guardado"), y, "save_point_item_id")
        y += ROW_H + 4

        self._entity_input = self._add_field("Entidad save point:", self._config.get("save_point_entity_type", "maquina_escribir"), y, "save_point_entity_type")
        y += ROW_H + 4

        # Validaciones
        self._add_section("Validaciones", y)
        y += HEADER_H + 4

        validaciones = self._config.get("validaciones", {})
        self._checksum_check = self._add_checkbox("Use checksum SHA256:", validaciones.get("use_checksum", True), y, "use_checksum")
        y += ROW_H + 4

        self._consume_check = self._add_checkbox("Item se consume al guardar:", validaciones.get("item_se_consume", True), y, "item_se_consume")
        y += ROW_H + 4

        self._compress_input = self._add_field("Compress level (0-9):", str(validaciones.get("compress_level", 6)), y, "compress_level")
        y += ROW_H + 4

        # Dev Mode
        self._add_section("Dev Mode", y)
        y += HEADER_H + 4

        dev_mode = self._config.get("dev_mode", {})
        self._dev_enabled_check = self._add_checkbox("Dev mode habilitado:", dev_mode.get("enabled", True), y, "dev_enabled")
        y += ROW_H + 4

        self._f5_input = self._add_field("Hotkey save:", dev_mode.get("hotkey_save", "F5"), y, "hotkey_save")
        y += ROW_H + 4

        self._f9_input = self._add_field("Hotkey load:", dev_mode.get("hotkey_load", "F9"), y, "hotkey_load")
        y += ROW_H + 4

        # Schema
        self._add_section("Schema (include)", y)
        y += HEADER_H + 4

        schema = self._config.get("schema", {})
        include = schema.get("include", [])
        self._schema_input = self._add_field("Sistemas:", ", ".join(include), y, "schema_include")
        y += ROW_H + 4

    def _add_section(self, title, y):
        lbl = Label(PADDING, y, self._editor.rect.w - 2 * PADDING, HEADER_H, title,
                     font_size=14, color=(180, 200, 160), bold=True)
        lbl.parent = self._editor
        self._editor.children.append(lbl)

    def _add_field(self, label_text, value, y, field_name):
        lbl = Label(PADDING, y, 160, ROW_H, label_text, font_size=12, color=(160, 170, 150))
        lbl.parent = self._editor
        self._editor.children.append(lbl)

        inp = TextInput(170, y, min(300, self._editor.rect.w - 190), ROW_H, value, font_size=12)
        inp.parent = self._editor
        self._editor.children.append(inp)
        inp._field_name = field_name
        return inp

    def _add_checkbox(self, label_text, checked, y, field_name):
        lbl = Label(PADDING, y, 200, ROW_H, label_text, font_size=12, color=(160, 170, 150))
        lbl.parent = self._editor
        self._editor.children.append(lbl)

        box_w, box_h = 20, 20
        box_x = 210
        box_y = y + (ROW_H - box_h) // 2
        btn = Button(box_x, box_y, box_w, box_h, "X" if checked else "",
                     callback=lambda: self._toggle_checkbox(field_name, btn))
        btn.parent = self._editor
        self._editor.children.append(btn)
        btn._checked = checked
        btn._field_name = field_name
        return btn

    def _toggle_checkbox(self, field_name, btn):
        btn._checked = not btn._checked
        btn.text = "X" if btn._checked else ""

    def _on_save(self):
        self._collect_fields()
        ok, errores = validar_config(self._config)
        if not ok:
            self._status_text = " | ".join(errores)
            self._status_error = True
            self._status_lbl.text = self._status_text
            self._status_lbl.color = (200, 120, 120)
            return

        set_config(self._config)
        self._status_text = "Guardado"
        self._status_error = False
        self._status_lbl.text = self._status_text
        self._status_lbl.color = (150, 200, 150)

    def _on_reset(self):
        _load_config()
        self._config = get_config()
        self._build_fields()
        self._status_text = "Reset"
        self._status_error = False
        self._status_lbl.text = self._status_text
        self._status_lbl.color = (150, 200, 150)

    def _collect_fields(self):
        for child in self._editor.children:
            if hasattr(child, '_field_name'):
                fn = child._field_name
                if fn == "slots":
                    try:
                        self._config["slots"] = int(child.text)
                    except ValueError:
                        pass
                elif fn == "save_point_item_id":
                    self._config["save_point_item_id"] = child.text
                elif fn == "save_point_entity_type":
                    self._config["save_point_entity_type"] = child.text
                elif fn == "compress_level":
                    try:
                        self._config.setdefault("validaciones", {})["compress_level"] = int(child.text)
                    except ValueError:
                        pass
                elif fn == "hotkey_save":
                    self._config.setdefault("dev_mode", {})["hotkey_save"] = child.text
                elif fn == "hotkey_load":
                    self._config.setdefault("dev_mode", {})["hotkey_load"] = child.text
                elif fn == "schema_include":
                    items = [x.strip() for x in child.text.split(",") if x.strip()]
                    self._config.setdefault("schema", {})["include"] = items

            if hasattr(child, '_checked') and hasattr(child, '_field_name'):
                fn = child._field_name
                if fn == "use_checksum":
                    self._config.setdefault("validaciones", {})["use_checksum"] = child._checked
                elif fn == "item_se_consume":
                    self._config.setdefault("validaciones", {})["item_se_consume"] = child._checked
                elif fn == "dev_enabled":
                    self._config.setdefault("dev_mode", {})["enabled"] = child._checked

    def on_activate(self):
        _load_config()
        self._config = get_config()
        self._build_fields()

    def dibujar(self, pantalla):
        super().dibujar(pantalla)
