from editor.widgets.base import Container


class MenuManager(Container):
    """Gestiona paneles sin TabBar. El cambio de panel se hace desde el menú superior."""

    def __init__(self, x, y, w, h):
        super().__init__(x, y, w, h)
        self._panel_registry = []
        self._panel_instances = {}
        self._active_id = None

    # ── Registro ────────────────────────────────────────────

    def register_tab(self, tab_id, label, panel_class, *args, **kwargs):
        self._panel_registry.append((tab_id, label, panel_class, args, kwargs))

    # ── Acceso a paneles ─────────────────────────────────────

    def _get_or_create_panel(self, tab_id):
        p = self._panel_instances.get(tab_id)
        if p is not None:
            return p
        for tid, label, cls, args, kwargs in self._panel_registry:
            if tid == tab_id:
                p = cls(0, 0, self.rect.w, self.rect.h, *args, **kwargs)
                p.parent = self  # <-- clave: asigna parent para que _abs_rect() calcule bien
                self._panel_instances[tab_id] = p
                return p
        return None

    def get_active_panel(self):
        if self._active_id is None:
            return None
        return self._get_or_create_panel(self._active_id)

    def set_active_by_id(self, tab_id):
        self._active_id = tab_id

    def get_active_id(self):
        return self._active_id

    # ── Actualización ─────────────────────────────────────────

    def update(self, dt):
        panel = self.get_active_panel()
        if panel and hasattr(panel, 'update'):
            panel.update(dt)

    # ── Eventos ──────────────────────────────────────────────

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        panel = self.get_active_panel()
        if panel and panel.handle_event(event):
            return True
        return False

    # ── Dibujo ───────────────────────────────────────────────

    def draw(self, surface):
        if not self.visible:
            return
        panel = self.get_active_panel()
        if panel:
            panel.draw(surface)

    # ── Redimensión ──────────────────────────────────────────

    def set_size(self, w, h):
        super().set_size(w, h)
        for panel in self._panel_instances.values():
            panel.set_size(w, h)

    # ── Reconstrucción de UI (cambio de idioma) ─────────────

    def rebuild_ui(self):
        active_id = self._active_id
        self._panel_instances.clear()
        if active_id:
            self._active_id = active_id

    # ── Cierre de pestañas (ya no aplica sin TabBar) ──────

    def _on_close_tab(self, tab_id):
        if tab_id in self._panel_instances:
            del self._panel_instances[tab_id]
