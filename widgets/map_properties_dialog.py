"""Diálogo de propiedades del mapa con pestañas Precarga y Al cargar."""

import pygame
from editor.widgets.base import Widget
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.event_constants import PRELOAD_DEFAULT


class MapPropertiesDialog(Widget):
    """Diálogo de propiedades del mapa con dos pestañas: Precarga y Al cargar."""

    def __init__(self, x, y, w, h, preload=None, onload_events=None, on_save=None):
        super().__init__(x, y, w, h)
        self.visible = False
        self.preload = (preload or {}).copy()
        self.onload_events = (onload_events or []).copy()
        self.on_save = on_save
        self.active_tab = "preload"

        self._bg_color = (40, 45, 52)
        self._border_color = (70, 80, 95)

        self._build_ui()

    def _build_ui(self):
        self.children = []

        self.btn_close = Button(
            self.rect.w - 30, 4, 26, 22,
            "X", color=(120, 50, 50), callback=self.cancel
        )
        self.btn_close.parent = self
        self.children.append(self.btn_close)

        self.btn_tab_preload = Button(
            10, 30, 100, 26,
            "Precarga", toggle=True, callback=self._switch_tab_preload
        )
        self.btn_tab_preload.parent = self
        self.btn_tab_preload.toggled = True
        self.children.append(self.btn_tab_preload)

        self.btn_tab_onload = Button(
            120, 30, 100, 26,
            "Al cargar", toggle=True, callback=self._switch_tab_onload
        )
        self.btn_tab_onload.parent = self
        self.children.append(self.btn_tab_onload)

        self._preload_elements = []
        self._onload_elements = []
        self._build_preload_tab()
        self._build_onload_tab()
        self.children.extend(self._preload_elements)
        self.children.extend(self._onload_elements)

        self.btn_save = Button(
            self.rect.w - 220, self.rect.h - 42, 100, 32,
            "Guardar", color=(60, 120, 60), hover_color=(80, 150, 80),
            callback=self._save
        )
        self.btn_save.parent = self
        self.children.append(self.btn_save)

        self.btn_cancel = Button(
            self.rect.w - 110, self.rect.h - 42, 100, 32,
            "Cancelar", callback=self.cancel
        )
        self.btn_cancel.parent = self
        self.children.append(self.btn_cancel)

    def _build_preload_tab(self):
        y = 65

        self.lbl_no_comida = Label(20, y, 200, 24, "Deshabilitar comida:")
        self.lbl_no_comida.parent = self
        self._preload_elements.append(self.lbl_no_comida)

        self.btn_no_comida = Button(
            230, y, 80, 24,
            "ON" if self.preload.get("no_comida", False) else "OFF",
            toggle=True, callback=self._toggle_no_comida
        )
        self.btn_no_comida.toggled = self.preload.get("no_comida", False)
        self.btn_no_comida.parent = self
        self._preload_elements.append(self.btn_no_comida)

        y += 34
        self.lbl_no_enemigos = Label(20, y, 200, 24, "Deshabilitar enemigos:")
        self.lbl_no_enemigos.parent = self
        self._preload_elements.append(self.lbl_no_enemigos)

        self.btn_no_enemigos = Button(
            230, y, 80, 24,
            "ON" if self.preload.get("no_enemigos", False) else "OFF",
            toggle=True, callback=self._toggle_no_enemigos
        )
        self.btn_no_enemigos.toggled = self.preload.get("no_enemigos", False)
        self.btn_no_enemigos.parent = self
        self._preload_elements.append(self.btn_no_enemigos)

        y += 40
        self.lbl_musica = Label(20, y, 200, 24, "Música (ID de archivo):")
        self.lbl_musica.parent = self
        self._preload_elements.append(self.lbl_musica)

        from editor.widgets.text_input import TextInput
        self.inp_musica = TextInput(
            20, y + 26, 300, 24,
            default=self.preload.get("musica", ""),
            max_chars=50
        )
        self.inp_musica.parent = self
        self._preload_elements.append(self.inp_musica)

    def _build_onload_tab(self):
        self.lbl_onload = Label(20, 65, 400, 24, "Eventos al cargar (trigger: onload):")
        self.lbl_onload.parent = self
        self._onload_elements.append(self.lbl_onload)

        self.lbl_onload_info = Label(20, 95, 400, 24, "(Configurar en el editor de eventos)")
        self.lbl_onload_info.parent = self
        self._onload_elements.append(self.lbl_onload_info)

    def _switch_tab_preload(self):
        self.active_tab = "preload"
        self.btn_tab_preload.toggled = True
        self.btn_tab_onload.toggled = False
        for el in self._preload_elements:
            el.visible = True
        for el in self._onload_elements:
            el.visible = False

    def _switch_tab_onload(self):
        self.active_tab = "onload"
        self.btn_tab_preload.toggled = False
        self.btn_tab_onload.toggled = True
        for el in self._preload_elements:
            el.visible = False
        for el in self._onload_elements:
            el.visible = True

    def _toggle_no_comida(self):
        self.btn_no_comida.text = "ON" if self.btn_no_comida.toggled else "OFF"

    def _toggle_no_enemigos(self):
        self.btn_no_enemigos.text = "ON" if self.btn_no_enemigos.toggled else "OFF"

    def _save(self):
        self.preload = {
            "no_comida": self.btn_no_comida.toggled,
            "no_enemigos": self.btn_no_enemigos.toggled,
            "flags_iniciales": {},
            "musica": self.inp_musica.get_value() if hasattr(self, 'inp_musica') else ""
        }
        if self.on_save:
            self.on_save(self.preload, self.onload_events)
        self.visible = False

    def cancel(self):
        self.visible = False

    def show(self):
        self.visible = True
        self.btn_no_comida.toggled = self.preload.get("no_comida", False)
        self.btn_no_comida.text = "ON" if self.btn_no_comida.toggled else "OFF"
        self.btn_no_enemigos.toggled = self.preload.get("no_enemigos", False)
        self.btn_no_enemigos.text = "ON" if self.btn_no_enemigos.toggled else "OFF"
        if hasattr(self, 'inp_musica'):
            self.inp_musica.set_value(self.preload.get("musica", ""))
        self._switch_tab_preload()

    def handle_event(self, event):
        if not self.visible:
            return False
        for child in self.children:
            if child.handle_event(event):
                return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.cancel()
            return True
        return False

    def draw(self, surface):
        if not self.visible:
            return

        overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        r = self._abs_rect()
        pygame.draw.rect(surface, self._bg_color, r)
        pygame.draw.rect(surface, self._border_color, r, 2)

        from editor.translation import I18n
        i18n = I18n.instancia()
        fuente = i18n.fuente(16, bold=True) if i18n else pygame.font.SysFont("Arial", 16, bold=True)
        titulo = fuente.render("Propiedades del Mapa", True, (220, 190, 120))
        surface.blit(titulo, (r.x + (r.w - titulo.get_width()) // 2, r.y + 8))

        for child in self.children:
            child.draw(surface)
