import pygame

from engine.display import get_buffer as _display_buffer, present as _display_present, setup as _display_setup
from engine.systems.user_prefs import load, save, parse_resolution


class SettingsScreen:
    """Menu de resolucion del usuario final.

    Se abre como modal (p. ej. desde el titulo con la tecla R). Aplica y
    persiste la eleccion en data/user_prefs.json.
    """

    def __init__(self, config=None, display_size=None):
        self.config = config or {}
        self.display_size = display_size or (800, 600)
        self._prefs = load()
        self._options = self._build_options()
        self._selected = self._index_of_current()
        self._font = None
        self._font_b = None
        self._font_title = None

    def _desktop(self):
        try:
            sizes = pygame.display.get_desktop_sizes()
            if sizes:
                return max(sizes, key=lambda s: s[0] * s[1])
        except Exception:
            pass
        return self.display_size

    def _build_options(self):
        desk_w, desk_h = self._desktop()
        opts = [("auto", "Automatico (ajustar al escritorio)", None, False)]
        presets = [(1024, 768), (1280, 960), (1600, 1200),
                   (1280, 720), (1600, 900), (1920, 1080)]
        seen = set()
        for w, h in presets:
            cw, ch = min(w, desk_w), min(h, desk_h)
            if (cw, ch) in seen:
                continue
            seen.add((cw, ch))
            opts.append(("res", f"Ventana {cw}x{ch}", (cw, ch), False))
        opts.append(("full", "Pantalla completa (estirar)", None, True))
        return opts

    def _index_of_current(self):
        size = parse_resolution(self._prefs.get("resolution", "auto"))
        full = bool(self._prefs.get("fullscreen", False))
        for i, (kind, _, opt_size, opt_full) in enumerate(self._options):
            if kind == "auto" and size is None and not full:
                return i
            if kind == "res" and size == opt_size and not full:
                return i
            if kind == "full" and full:
                return i
        return 0

    def _aplicar(self):
        kind, _, size, full = self._options[self._selected]
        if kind == "res":
            self._prefs["resolution"] = f"{size[0]}x{size[1]}"
            self._prefs["fullscreen"] = False
        elif kind == "full":
            self._prefs["resolution"] = "auto"
            self._prefs["fullscreen"] = True
        else:
            self._prefs["resolution"] = "auto"
            self._prefs["fullscreen"] = False
        save(self._prefs)
        _display_setup(window_size=size, fullscreen=full)

    def run(self):
        pygame.font.init()
        self._font = pygame.font.SysFont("Arial", 16)
        self._font_b = pygame.font.SysFont("Arial", 16, bold=True)
        self._font_title = pygame.font.SysFont("Arial", 22, bold=True)
        clock = pygame.time.Clock()
        while True:
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit()
                    raise SystemExit
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_UP:
                        self._selected = (self._selected - 1) % len(self._options)
                    elif event.key == pygame.K_DOWN:
                        self._selected = (self._selected + 1) % len(self._options)
                    elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        self._aplicar()
                        return
                    elif event.key == pygame.K_ESCAPE:
                        return
            self._draw()
            _display_present()

    def _draw(self):
        surf = _display_buffer()
        if surf is None:
            return
        w, h = surf.get_size()
        surf.fill((18, 20, 26))
        title = self._font_title.render("Resolucion", True, (220, 200, 160))
        surf.blit(title, ((w - title.get_width()) // 2, 50))
        y = 110
        for i, (kind, label, size, full) in enumerate(self._options):
            sel = i == self._selected
            bg = (55, 70, 90) if sel else (38, 42, 50)
            pygame.draw.rect(surf, bg, (60, y, w - 120, 34))
            if sel:
                pygame.draw.rect(surf, (70, 160, 220), (60, y, 3, 34))
            if sel:
                txt = self._font_b.render(label, True, (220, 220, 220))
            else:
                txt = self._font.render(label, True, (180, 190, 200))
            surf.blit(txt, (80, y + 8))
            y += 40
        hint = self._font.render(
            "\u2191\u2193: elegir  Enter: aplicar  ESC: volver", True, (120, 130, 140))
        surf.blit(hint, ((w - hint.get_width()) // 2, h - 40))

