import pygame
from editor.widgets.base import Widget
from editor.widgets.button import Button
from editor.widgets.text_input import TextInput


class Dialog(Widget):
    def __init__(self, x, y, w, h, title=""):
        super().__init__(x, y, w, h)
        self.visible = False
        self.title = title
        self._result = None
        self._fields = []
        self._buttons = []
        self._cancel_callback = None
        self._bg_color = (40, 45, 52)
        self._border_color = (70, 80, 95)
        self._title_color = (220, 190, 120)

    def build(self, fields, accept_text="Aceptar", cancel_text="Cancelar",
              accept_callback=None, cancel_callback=None):
        self._fields = []
        self._buttons = []
        self._cancel_callback = cancel_callback
        self._result = None

        y_offset = self.rect.y + 50
        for fname, fdefault, fmax, fnumeric in fields:
            lbl_rect = pygame.Rect(self.rect.x + 20, y_offset, self.rect.w - 40, 20)
            input_rect = pygame.Rect(self.rect.x + 20, y_offset + 22, self.rect.w - 40, 30)
            inp = TextInput(input_rect.x - self.rect.x, input_rect.y - self.rect.y,
                            input_rect.w, input_rect.h, default=fdefault,
                            max_chars=fmax, numeric_only=fnumeric)
            inp.parent = self
            self._fields.append({"name": fname, "input": inp, "label_rect": lbl_rect})
            y_offset += 66

        y_offset += 10
        bw = 100
        spacing = 20
        total_w = bw * 2 + spacing
        start_x = self.rect.x + (self.rect.w - total_w) // 2

        if not accept_callback:
            accept_callback = self._default_accept

        btn_accept = Button(start_x - self.rect.x, y_offset - self.rect.y, bw, 32,
                            accept_text, color=(60, 120, 60), hover_color=(80, 150, 80),
                            callback=accept_callback)
        btn_accept.parent = self
        self._buttons.append(btn_accept)

        if cancel_callback or True:
            if not cancel_callback:
                cancel_callback = self.cancel
            btn_cancel = Button(start_x + bw + spacing - self.rect.x, y_offset - self.rect.y,
                                bw, 32, cancel_text,
                                callback=cancel_callback)
            btn_cancel.parent = self
            self._buttons.append(btn_cancel)

    def _default_accept(self):
        self._result = {}
        for f in self._fields:
            self._result[f["name"]] = f["input"].get_value()
        self.visible = False

    def get_result(self):
        return self._result

    def cancel(self):
        self._result = None
        self.visible = False
        if self._cancel_callback:
            self._cancel_callback()

    def show(self):
        self.visible = True
        self._result = None
        for f in self._fields:
            f["input"].focused = False

    def _abs_rect(self):
        if self.parent:
            pr = self.parent.get_abs_rect() if hasattr(self.parent, 'get_abs_rect') else self.parent.rect
            return pygame.Rect(pr.x + self.rect.x, pr.y + self.rect.y, self.rect.w, self.rect.h)
        return self.rect.copy()

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False

        for btn in self._buttons:
            if btn.handle_event(event):
                return True

        for f in self._fields:
            if f["input"].handle_event(event):
                return True

        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.cancel()
            return True

        if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
            self._default_accept()
            return True

        return False

    def draw(self, surface):
        if not self.visible:
            return
        r = self._abs_rect()

        overlay = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, self._bg_color, r)
        pygame.draw.rect(surface, self._border_color, r, 2)

        from editor.translation import I18n
        i18n = I18n.instancia()
        fuente = i18n.fuente(18, bold=True) if i18n else pygame.font.SysFont("Arial", 18, bold=True)
        titulo = fuente.render(self.title, True, self._title_color)
        surface.blit(titulo, (r.x + (r.w - titulo.get_width()) // 2, r.y + 16))

        fuente_peq = i18n.fuente(14) if i18n else pygame.font.SysFont("Arial", 14)
        for f in self._fields:
            lbl = fuente_peq.render(f["name"], True, (180, 190, 200))
            surface.blit(lbl, (f["label_rect"].x, f["label_rect"].y))
            f["input"].draw(surface)

        for btn in self._buttons:
            btn.draw(surface)
