from editor.widgets.base import Container


class BasePanel(Container):
    """Panel base que ocupa todo el espacio del MenuManager (sin TabBar)."""

    def __init__(self, x, y, w, h, i18n):
        super().__init__(0, 0, w, h)
        self.i18n = i18n

    def update(self, dt):
        pass

    def set_size(self, w, h):
        old_w, old_h = self.rect.w, self.rect.h
        self.rect.w = w
        self.rect.h = h
        if (self.rect.w != old_w or self.rect.h != old_h) and hasattr(self, '_build_ui'):
            self._build_ui()
