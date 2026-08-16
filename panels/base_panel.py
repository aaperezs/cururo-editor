from editor.widgets.base import Container


class BasePanel(Container):
    """Panel base que ocupa todo el espacio del MenuManager (sin TabBar)."""

    def __init__(self, x, y, w, h, i18n):
        super().__init__(0, 0, w, h)
        self.i18n = i18n
        self._descripcion = ""

    def update(self, dt):
        pass

    def set_size(self, w, h):
        old_w, old_h = self.rect.w, self.rect.h
        self.rect.w = w
        self.rect.h = h
        if (self.rect.w != old_w or self.rect.h != old_h) and hasattr(self, '_build_ui'):
            self._build_ui()

    def mostrar_descripcion(self, message):
        """Guarda una descripcion placeholder para paneles sin datos."""
        self._descripcion = message or ""

    def draw_descripcion(self, surface):
        """Dibuja la descripcion placeholder centrada. Devuelve True si dibujo algo."""
        if not self._descripcion:
            return False
        import pygame
        from editor.translation import I18n
        r = self.get_abs_rect()
        i18n = I18n.instancia()
        fuente = i18n.fuente(15) if i18n else pygame.font.SysFont("Arial", 15)
        fuente_sm = i18n.fuente(12) if i18n else pygame.font.SysFont("Arial", 12)

        icon = fuente.render("\u25B6", True, (70, 130, 200))
        surface.blit(icon, (r.x + (r.w - icon.get_width()) // 2, r.y + r.h // 2 - 70))

        import textwrap
        lines = []
        for raw in self._descripcion.split("\n"):
            wrapped = textwrap.wrap(raw, width=max(20, r.w // 7))
            lines.extend(wrapped if wrapped else [""])
        max_lines = 8
        lines = lines[:max_lines]
        line_h = 22
        block_h = len(lines) * line_h
        y = r.y + r.h // 2 - block_h // 2
        for line in lines:
            txt = fuente_sm.render(line, True, (150, 158, 168))
            surface.blit(txt, (r.x + (r.w - txt.get_width()) // 2, y))
            y += line_h
        return True
