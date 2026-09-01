"""Global message bar for transient info / persistent warnings and errors.

Siempre visible en la base de la ventana. Los mensajes info se auto-ocultan;
warn/error persisten hasta cerrar o copiar. El mensaje se copia al portapapeles
con click derecho.
"""

import pygame

from editor.widgets.base import Widget
from editor.ui.theme import Theme
from editor.ui.fonts import get_font_manager


class MessageBar(Widget):
    """Barra inferior de mensajes globales (info/warn/error) con copiado."""

    def __init__(self, x, y, w, h, right_margin=0):
        super().__init__(x, y, w, h)
        self.text = ""
        self.level = "info"
        self._timer = 0
        self._duration = 180  # frames @60fps = 3s (solo info)
        self._copy_rect = None
        self.right_margin = right_margin

    # ── API ──────────────────────────────────────────────

    def notify(self, message, level="info", duration=None):
        self.text = str(message)
        self.level = level if level in ("info", "warn", "error") else "info"
        if level == "info":
            self._timer = duration or self._duration
        else:
            self._timer = 0  # persiste hasta cerrar/copiar

    def clear(self):
        self.text = ""
        self.level = "info"
        self._timer = 0

    def update(self, dt):
        if self._timer > 0:
            self._timer -= 1
            if self._timer <= 0:
                self.text = ""

    # ── Eventos ──────────────────────────────────────────

    def handle_event(self, event):
        if not self.visible or not self.enabled or not self.text:
            return False
        r = self.get_abs_rect()

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3:
            if r.collidepoint(event.pos):
                self._copy_text()
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self._copy_rect and self._copy_rect.collidepoint(event.pos):
                self._copy_text()
                return True
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and self.text:
            self.clear()
            return True
        return False

    def _copy_text(self):
        try:
            import pyperclip
            pyperclip.copy(self.text)
        except ImportError:
            return
        self.notify(f"{self.text}  (copiado)", "info", duration=60)

    # ── Dibujo ────────────────────────────────────────────

    def draw(self, surface):
        if not self.visible:
            return
        r = self.get_abs_rect()
        theme = Theme.get()
        font = get_font_manager().get(theme.font_sizes["body"])

        def _c(c):
            return c.as_tuple() if hasattr(c, 'as_tuple') else c

        if self.level == "error":
            bg = (60, 32, 34)
            fg = (235, 150, 150)
        elif self.level == "warn":
            bg = (60, 48, 26)
            fg = (235, 200, 130)
        else:
            bg = theme.surface_elevated
            fg = theme.text_dim

        pygame.draw.rect(surface, _c(bg), r)
        pygame.draw.line(surface, _c(theme.border), (r.x, r.y), (r.x + r.w, r.y), 1)

        if not self.text:
            return

        prefix = "⚠ " if self.level == "warn" else ("✖ " if self.level == "error" else "")
        label = f"{prefix}{self.text}"
        txt = font.render(label, True, _c(fg))
        max_w = r.w - self.right_margin - 96
        if txt.get_width() > max_w:
            clipped = label
            while clipped and font.render(clipped + "…", True, _c(fg)).get_width() > max_w:
                clipped = clipped[:-1]
            txt = font.render(clipped + "…", True, _c(fg))

        surface.blit(txt, (r.x + 10, r.y + (r.h - txt.get_height()) // 2))

        copy_txt = font.render("[⧉ copiar]", True, _c(fg))
        cx = r.x + r.w - self.right_margin - copy_txt.get_width() - 8
        cy = r.y + (r.h - copy_txt.get_height()) // 2
        self._copy_rect = pygame.Rect(cx - 4, r.y, copy_txt.get_width() + 8, r.h)
        pygame.draw.line(surface, _c(theme.border), (cx - 4, r.y + 3), (cx - 4, r.y + r.h - 3))
        surface.blit(copy_txt, (cx, cy))
