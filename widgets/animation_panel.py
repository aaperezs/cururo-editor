import pygame
import uuid

from editor.animations import create as create_anim
from editor.animations import delete as delete_anim
from editor.animations import get, get_all
from editor.animations import set as set_anim
from editor.translation import I18n
from editor.panels.base_panel import BasePanel
from editor.widgets.button import Button
from editor.widgets.label import Label
from editor.widgets.panel import Panel
from editor.widgets.text_input import TextInput
from editor.common.sprite_loader import obtener as obtener_sprite

PADDING = 6
TOOLBAR_H = 36
LEFT_W = 220
LIST_H = 24
FRAME_H = 28

COLOR_PRESETS = [
    (255, 215, 0),    # Dorado
    (255, 165, 0),    # Naranja
    (255, 50, 50),    # Rojo
    (50, 130, 255),   # Azul
    (50, 255, 100),   # Verde
    (180, 50, 255),   # Purpura
    (255, 255, 255),  # Blanco
    (0, 255, 255),    # Cyan
    (255, 50, 150),   # Rosa
]

PREVIEW_SIZE = 64


class AnimationPanel(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(x, y, w, h, i18n)
        self.bg_color = (30, 32, 36)
        self._selected = None
        self._frames = []
        self._frame_widgets = []
        self._glow_enabled = False
        self._glow_color = [255, 215, 0]
        self._glow_radius = 8
        self._glow_alpha = 80
        self._build_ui()

    def _build_ui(self):
        self.clear()

        tb = Panel(0, 0, self.rect.w, TOOLBAR_H, bg_color=(42, 46, 55), border_color=(60, 65, 75))
        self.add(tb)
        self._new_btn = Button(8, 4, 72, 28, "Nueva", callback=self._on_new)
        self._new_btn.parent = tb; tb.children.append(self._new_btn)
        self._del_btn = Button(86, 4, 72, 28, "Eliminar", callback=self._on_delete)
        self._del_btn.parent = tb; tb.children.append(self._del_btn)
        self._save_btn = Button(164, 4, 72, 28, "Guardar", callback=self._on_save)
        self._save_btn.parent = tb; tb.children.append(self._save_btn)

        rx = LEFT_W
        rw = self.rect.w - rx
        cy = TOOLBAR_H
        ch = self.rect.h - cy
        self._editor_panel = Panel(rx, cy, rw, ch, bg_color=(35, 38, 46))
        self.add(self._editor_panel)
        self._build_editor()

    def _build_editor(self):
        ep = self._editor_panel
        ep.clear()
        self._frame_widgets = []

        glow_on = self._glow_toggle.toggled if hasattr(self, '_glow_toggle') else self._glow_enabled

        y = PADDING

        # --- Name ---
        lbl = Label(PADDING, y, 80, 22, "Nombre:", font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._name_input = TextInput(90, y, 200, 22, default="", max_chars=50, numeric_only=False)
        self._name_input.parent = ep; ep.children.append(self._name_input)
        y += 30

        # --- Interval ---
        lbl = Label(PADDING, y, 100, 22, "Intervalo (ms):", font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._interval_input = TextInput(120, y, 80, 22, default="500", max_chars=6, numeric_only=True)
        self._interval_input.parent = ep; ep.children.append(self._interval_input)
        y += 30

        # --- Separator ---
        sep = Panel(PADDING, y, ep.rect.w - PADDING * 2, 2, bg_color=(55, 60, 70))
        sep.parent = ep; ep.children.append(sep)
        y += 10

        # --- Glow section ---
        lbl = Label(PADDING, y, 60, 22, "Aurea:", font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._glow_toggle = Button(70, y, 60, 22, "Activar", callback=self._toggle_glow, toggle=True)
        self._glow_toggle.toggled = glow_on
        self._glow_toggle.parent = ep; ep.children.append(self._glow_toggle)
        y += 28

        self._glow_widgets = []
        y += self._rebuild_glow_at(y)

        # --- Separator ---
        sep2 = Panel(PADDING, y, ep.rect.w - PADDING * 2, 2, bg_color=(55, 60, 70))
        sep2.parent = ep; ep.children.append(sep2)
        y += 10

        # --- Frames ---
        lbl = Label(PADDING, y, 100, 22, "Frames:", font_size=12, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._add_frame_btn = Button(110, y, 80, 22, "+ Frame", callback=self._on_add_frame)
        self._add_frame_btn.parent = ep; ep.children.append(self._add_frame_btn)
        y += 28

        self._frames_y = y
        self._rebuild_frames()

    def _rebuild_glow_at(self, y):
        ep = self._editor_panel
        for w in self._glow_widgets:
            if w.parent:
                w.parent.children.remove(w)
        self._glow_widgets = []

        if not self._glow_toggle.toggled:
            return 0

        self._glow_toggle.text = "Activo"
        self._glow_toggle.text_color = (100, 220, 100)
        start_y = y

        # Color presets
        lbl = Label(PADDING, y, 80, 22, "Color:", font_size=11, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._glow_widgets.append(lbl)

        cx = 80
        for ci, c in enumerate(COLOR_PRESETS):
            btn = Button(cx, y, 18, 18, "", callback=lambda idx=ci: self._pick_color(idx))
            btn.color_sup = c
            btn.color_inf = tuple(min(255, v + 30) for v in c)
            btn.color_hover = tuple(min(255, v + 50) for v in c)
            btn.parent = ep; ep.children.append(btn)
            self._glow_widgets.append(btn)
            cx += 22
        y += 24

        # RGB inputs
        lbl_r = Label(PADDING, y, 12, 20, "R:", font_size=11, color=(200, 80, 80))
        lbl_r.parent = ep; ep.children.append(lbl_r)
        self._glow_widgets.append(lbl_r)
        self._glow_r = TextInput(22, y, 36, 20, default=str(self._glow_color[0]), max_chars=3, numeric_only=True)
        self._glow_r.parent = ep; ep.children.append(self._glow_r)
        self._glow_widgets.append(self._glow_r)

        lbl_g = Label(62, y, 12, 20, "G:", font_size=11, color=(80, 200, 80))
        lbl_g.parent = ep; ep.children.append(lbl_g)
        self._glow_widgets.append(lbl_g)
        self._glow_g = TextInput(78, y, 36, 20, default=str(self._glow_color[1]), max_chars=3, numeric_only=True)
        self._glow_g.parent = ep; ep.children.append(self._glow_g)
        self._glow_widgets.append(self._glow_g)

        lbl_b = Label(118, y, 12, 20, "B:", font_size=11, color=(80, 80, 200))
        lbl_b.parent = ep; ep.children.append(lbl_b)
        self._glow_widgets.append(lbl_b)
        self._glow_b = TextInput(134, y, 36, 20, default=str(self._glow_color[2]), max_chars=3, numeric_only=True)
        self._glow_b.parent = ep; ep.children.append(self._glow_b)
        self._glow_widgets.append(self._glow_b)
        y += 24

        # Radius + Alpha
        lbl = Label(PADDING, y, 50, 20, "Radio:", font_size=11, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._glow_widgets.append(lbl)
        self._glow_radius_inp = TextInput(55, y, 40, 20, default=str(self._glow_radius), max_chars=3, numeric_only=True)
        self._glow_radius_inp.parent = ep; ep.children.append(self._glow_radius_inp)
        self._glow_widgets.append(self._glow_radius_inp)

        lbl = Label(110, y, 50, 20, "Alpha:", font_size=11, color=(180, 185, 195))
        lbl.parent = ep; ep.children.append(lbl)
        self._glow_widgets.append(lbl)
        self._glow_alpha_inp = TextInput(160, y, 40, 20, default=str(self._glow_alpha), max_chars=3, numeric_only=True)
        self._glow_alpha_inp.parent = ep; ep.children.append(self._glow_alpha_inp)
        self._glow_widgets.append(self._glow_alpha_inp)
        y += 26

        return y - start_y

    def _read_glow_inputs(self):
        try:
            r = max(0, min(255, int(self._glow_r.text or "0")))
            g = max(0, min(255, int(self._glow_g.text or "0")))
            b = max(0, min(255, int(self._glow_b.text or "0")))
            self._glow_color = [r, g, b]
        except ValueError:
            pass
        try:
            self._glow_radius = max(1, int(self._glow_radius_inp.text or "1"))
        except ValueError:
            pass
        try:
            self._glow_alpha = max(0, min(255, int(self._glow_alpha_inp.text or "0")))
        except ValueError:
            pass

    def _toggle_glow(self):
        self._collect_frame_inputs()
        self._build_editor()

    def _pick_color(self, idx):
        if 0 <= idx < len(COLOR_PRESETS):
            self._glow_color = list(COLOR_PRESETS[idx])
            self._glow_r.text = str(self._glow_color[0])
            self._glow_g.text = str(self._glow_color[1])
            self._glow_b.text = str(self._glow_color[2])

    def _rebuild_frames(self):
        ep = self._editor_panel
        for w in self._frame_widgets:
            if w.parent:
                w.parent.children.remove(w)
        self._frame_widgets = []

        y = self._frames_y
        for i, frame_id in enumerate(self._frames):
            lbl = Label(PADDING, y, 20, 22, f"{i}:", font_size=11, color=(140, 150, 160))
            lbl.parent = ep; ep.children.append(lbl)
            self._frame_widgets.append(lbl)

            inp = TextInput(24, y, 150, 22, default=frame_id, max_chars=60, numeric_only=False)
            inp.parent = ep; ep.children.append(inp)
            self._frame_widgets.append(inp)

            rm_btn = Button(180, y, 22, 22, "X", callback=lambda idx=i: self._on_remove_frame(idx))
            rm_btn.parent = ep; ep.children.append(rm_btn)
            self._frame_widgets.append(rm_btn)

            up_btn = Button(206, y, 22, 22, "^", callback=lambda idx=i: self._on_move_frame(idx, -1))
            up_btn.parent = ep; ep.children.append(up_btn)
            self._frame_widgets.append(up_btn)

            dn_btn = Button(232, y, 22, 22, "v", callback=lambda idx=i: self._on_move_frame(idx, 1))
            dn_btn.parent = ep; ep.children.append(dn_btn)
            self._frame_widgets.append(dn_btn)

            y += FRAME_H

    def _collect_frame_inputs(self):
        inputs = [w for w in self._frame_widgets if isinstance(w, TextInput)]
        self._frames = [inp.text.strip() for inp in inputs]

    def _on_add_frame(self):
        self._collect_frame_inputs()
        self._frames.append("")
        self._rebuild_frames()

    def _on_remove_frame(self, idx):
        self._collect_frame_inputs()
        if 0 <= idx < len(self._frames):
            del self._frames[idx]
            self._rebuild_frames()

    def _on_move_frame(self, idx, direction):
        self._collect_frame_inputs()
        target = idx + direction
        if 0 <= target < len(self._frames):
            self._frames[idx], self._frames[target] = self._frames[target], self._frames[idx]
            self._rebuild_frames()

    def _load(self, name):
        data = get(name)
        if not data:
            return
        self._selected = name
        self._frames = list(data.get("frames", []))
        glow = data.get("glow", {})
        self._glow_enabled = glow.get("enabled", False)
        self._glow_color = list(glow.get("color", [255, 215, 0]))
        self._glow_radius = glow.get("radius", 8)
        self._glow_alpha = glow.get("alpha", 80)
        if hasattr(self, '_glow_toggle'):
            self._glow_toggle.toggled = self._glow_enabled
        self._build_editor()
        self._name_input.text = name
        self._interval_input.text = str(data.get("interval", 500))

    def _on_new(self):
        name = f"anim_{uuid.uuid4().hex[:6]}"
        if create_anim(name):
            self._selected = name
            self._frames = []
            self._glow_enabled = False
            self._glow_color = [255, 215, 0]
            self._glow_radius = 8
            self._glow_alpha = 80
            if hasattr(self, '_glow_toggle'):
                self._glow_toggle.toggled = False
            self._build_editor()
            self._name_input.text = name
            self._interval_input.text = "500"

    def _on_delete(self):
        if self._selected and delete_anim(self._selected):
            self._selected = None
            self._frames = []
            self._glow_enabled = False
            if hasattr(self, '_glow_toggle'):
                self._glow_toggle.toggled = False
            self._build_editor()
            self._name_input.text = ""
            self._interval_input.text = "500"

    def _on_save(self):
        self._collect_frame_inputs()
        name = self._name_input.text.strip()
        if not name:
            return
        try:
            interval = int(self._interval_input.text)
        except ValueError:
            interval = 500
        if self._glow_toggle.toggled:
            self._read_glow_inputs()
            glow = {
                "enabled": True,
                "color": list(self._glow_color),
                "radius": self._glow_radius,
                "alpha": self._glow_alpha,
            }
        else:
            glow = {"enabled": False}
        data = {
            "frames": [f for f in self._frames if f],
            "interval": interval,
            "glow": glow,
        }
        set_anim(name, data)
        self._selected = name

    def handle_event(self, event):
        if not self.visible or not self.enabled:
            return False
        if super().handle_event(event):
            return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            list_area = pygame.Rect(0, TOOLBAR_H, LEFT_W, self.rect.h - TOOLBAR_H)
            if list_area.collidepoint(mx, my):
                rel_y = my - TOOLBAR_H - 4
                idx = rel_y // LIST_H
                anims = get_all()
                if 0 <= idx < len(anims):
                    self._load(anims[idx])
                return True
        return False

    def _get_preview_sprite(self):
        if not self._frames:
            return None
        frames = [f for f in self._frames if f]
        if not frames:
            return None
        try:
            interval = int(self._interval_input.text)
        except ValueError:
            interval = 500
        if interval < 1:
            interval = 500
        idx = (pygame.time.get_ticks() // interval) % len(frames)
        sprite_id = frames[idx]
        sprite = obtener_sprite(sprite_id)
        return sprite

    def draw(self, surface):
        if not self.visible:
            return
        super().draw(surface)
        anims = get_all()
        x = 0
        y = TOOLBAR_H + 4
        i = I18n.instancia()
        f = i.fuente(12) if i else pygame.font.SysFont("Arial", 12)
        for name in anims:
            r = pygame.Rect(x, y, LEFT_W, LIST_H)
            if name == self._selected:
                pygame.draw.rect(surface, (50, 65, 85), r)
            elif r.collidepoint(pygame.mouse.get_pos()):
                pygame.draw.rect(surface, (45, 50, 60), r)
            txt = f.render(name, True, (200, 210, 220))
            surface.blit(txt, (x + 4, y + 3))
            y += LIST_H

        # --- Animation preview ---
        if not self._selected:
            return
        ep_r = self._editor_panel.get_abs_rect()
        px = ep_r.x + ep_r.w - PREVIEW_SIZE - PADDING
        py = ep_r.y + PADDING

        # Checkered bg
        for pyy in range(PREVIEW_SIZE):
            for pxx in range(PREVIEW_SIZE):
                c = (55, 58, 65) if ((px + pxx) // 4 + (py + pyy) // 4) % 2 == 0 else (65, 68, 75)
                pygame.draw.rect(surface, c, (px + pxx, py + pyy, 1, 1))

        sprite = self._get_preview_sprite()
        if sprite:
            sw, sh = sprite.get_size()
            preview_center_x = px + PREVIEW_SIZE // 2
            preview_center_y = py + PREVIEW_SIZE // 2

            # Glow behind preview
            if self._glow_toggle.toggled and hasattr(self, '_glow_r'):
                self._read_glow_inputs()
                color = tuple(self._glow_color)
                radius = self._glow_radius
                alpha = self._glow_alpha
                for r in range(radius, 0, -2):
                    a = int(alpha * (radius - r) / radius)
                    if a <= 0:
                        continue
                    gs = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(gs, (*color, a), (r + 2, r + 2), r)
                    surface.blit(gs, (preview_center_x - r - 2, preview_center_y - r - 2))

            blit_x = preview_center_x - sw // 2
            blit_y = preview_center_y - sh // 2
            surface.blit(sprite, (blit_x, blit_y))

        # Border
        pygame.draw.rect(surface, (80, 90, 105), (px, py, PREVIEW_SIZE, PREVIEW_SIZE), 1)

        # Label
        i18n = I18n.instancia()
        font = i18n.fuente(10) if i18n else pygame.font.SysFont("Arial", 10)
        lbl = font.render("Preview", True, (160, 170, 185))
        surface.blit(lbl, (px, py + PREVIEW_SIZE + 2))
