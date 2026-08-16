import os
import pygame
import pygame_gui

from editor.translation import I18n
from editor.panels.base_panel import BasePanel
from editor.pygame_gui_theme import create_gui
from editor.asset_data import (
    get_assets, get_asset, get_assets_by_type, set_asset_meta,
    delete_asset, import_asset, asset_path, get_asset_list,
    ASSET_TIPOS, MODO_POSICION,
)

PADDING = 6
TOOLBAR_H = 36
HEADER_H = 26
LEFT_W = 220
THUMB_W = 180
THUMB_H = 120


class AssetPanel(BasePanel):
    def __init__(self, x, y, w, h, i18n):
        super().__init__(0, 0, w, h, i18n)
        self.bg_color = (30, 32, 36)
        self._gui = create_gui((w, h), offset_getter=lambda: (
            self.get_abs_rect().x, self.get_abs_rect().y
        ))
        self._selected_id = None
        self._filter_tipo = None
        self._preview_surf = None
        self._build_ui()

    def _build_ui(self):
        prev_id = self._selected_id
        self._gui.clear_and_reset()
        w, h = self.rect.w, self.rect.h
        self.mostrar_descripcion(
            self.i18n.t("tab.assets.desc") if not get_assets() else ""
        )

        # Toolbar
        self._import_btn = pygame_gui.elements.UIButton(
            pygame.Rect(8, 4, 100, 28), self.i18n.t("asset.import"), self._gui
        )
        self._del_btn = pygame_gui.elements.UIButton(
            pygame.Rect(116, 4, 80, 28), self.i18n.t("asset.delete"), self._gui
        )
        self._save_btn = pygame_gui.elements.UIButton(
            pygame.Rect(204, 4, 80, 28), self.i18n.t("asset.save"), self._gui
        )

        # Filter buttons
        x = 300
        for tid, tlabel in [("all", "Todos"), ("background", "Fondos"),
                            ("character", "Pers."), ("cg", "CG"), ("sprite", "Sprites")]:
            btn = pygame_gui.elements.UIButton(
                pygame.Rect(x, 4, 64, 28), tlabel, self._gui
            )
            setattr(self, f"_filter_{tid}_btn", btn)
            x += 68

        # Left list
        cy = TOOLBAR_H
        self._asset_list = pygame_gui.elements.UISelectionList(
            pygame.Rect(0, cy, LEFT_W, h - cy),
            item_list=self._get_filtered_list(),
            manager=self._gui,
            default_selection=prev_id,
        )

        # Right area
        rx, rw = LEFT_W, w - LEFT_W
        self._editor_panel = pygame_gui.elements.UIPanel(
            pygame.Rect(rx, cy, rw, h - cy), manager=self._gui
        )

        if prev_id and prev_id in get_assets():
            self._selected_id = prev_id
            self._build_editor_widgets()

    def _get_filtered_list(self):
        if self._filter_tipo:
            return sorted(get_assets_by_type(self._filter_tipo).keys())
        return sorted(get_assets().keys())

    def _build_editor_widgets(self):
        ep = self._editor_panel
        ep.kill()
        self._editor_panel = pygame_gui.elements.UIPanel(
            pygame.Rect(ep.rect.x, ep.rect.y, ep.rect.w, ep.rect.h),
            manager=self._gui
        )
        if not self._selected_id:
            return
        data = get_asset(self._selected_id)
        if not data:
            return
        ew = ep.rect.w
        y = PADDING

        # ID label
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, ew - PADDING * 2, 20),
            f"ID: {self._selected_id}", self._gui, container=ep
        )
        y += 26

        # Name
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 80, 22), "Nombre:", self._gui, container=ep
        )
        self._name_input = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(90, y, 200, 22),
            initial_text=data.get("nombre", self._selected_id),
            manager=self._gui, container=ep
        )
        y += 30

        # Type (readonly)
        tipo = data.get("tipo", "background")
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 80, 22), "Tipo:", self._gui, container=ep
        )
        pygame_gui.elements.UILabel(
            pygame.Rect(90, y, 200, 22),
            ASSET_TIPOS.get(tipo, tipo), self._gui, container=ep
        )
        y += 26

        # Position mode dropdown
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 100, 22), "Posición:", self._gui, container=ep
        )
        opts = [(k, v) for k, v in MODO_POSICION.items()]
        current = data.get("modo_posicion", "fill")
        self._modo_dd = _AssetDropdown(
            110, y + ep.rect.y, 120, 22, opts, selected=current,
            parent_ep=ep
        )
        y += 30

        # Unlock flag
        pygame_gui.elements.UILabel(
            pygame.Rect(PADDING, y, 100, 22), "Flag desbloqueo:", self._gui, container=ep
        )
        self._flag_input = pygame_gui.elements.UITextEntryLine(
            pygame.Rect(110, y, 200, 22),
            initial_text=data.get("desbloqueo_flag", ""),
            manager=self._gui, container=ep
        )
        y += 30

        # Preview
        self._preview_surf = None
        fpath = asset_path(self._selected_id)
        if fpath:
            try:
                self._preview_surf = pygame.image.load(fpath).convert_alpha()
            except Exception:
                self._preview_surf = None
        if self._preview_surf:
            pw = ew - PADDING * 2
            ph = ep.rect.h - y - PADDING
            px = PADDING
            self._preview_rect = pygame.Rect(px, y, pw, ph)

    def _on_import(self):
        import tkinter.filedialog as fd
        root = tkinter.Tk() if not hasattr(self, '_tk') else None
        if root:
            root.withdraw()
        fpath = fd.askopenfilename(
            title="Seleccionar imagen",
            filetypes=[("Imágenes", "*.png *.jpg *.jpeg"), ("PNG", "*.png"), ("JPG", "*.jpg *.jpeg")]
        )
        if root:
            root.destroy()
        if not fpath:
            return
        base = os.path.splitext(os.path.basename(fpath))[0]
        # Ask for ID and type via callback
        self._prompt_import(fpath, base)

    def _prompt_import(self, fpath, default_id):
        font = I18n.instancia().fuente(14) if I18n.instancia() else pygame.font.SysFont("Arial", 14)
        font_b = I18n.instancia().fuente(14, bold=True) if I18n.instancia() else pygame.font.SysFont("Arial", 14, bold=True)
        screen = pygame.display.get_surface()
        W, H = screen.get_width(), screen.get_height()
        dw, dh = 440, 280
        dx, dy = (W - dw) // 2, (H - dh) // 2
        tipo_opts = [(k, v) for k, v in ASSET_TIPOS.items()]
        modo_opts = [(k, v) for k, v in MODO_POSICION.items()]
        focus = 0
        fields = [
            {"label": "ID", "value": default_id},
            {"label": "Nombre", "value": default_id},
        ]
        selected_tipo = "background"
        selected_modo = "fill"
        cursor_pos = [len(f["value"]) for f in fields]
        clock = pygame.time.Clock()
        result = None
        done = False
        bg = pygame.Surface((W, H), pygame.SRCALPHA)
        bg.fill((0, 0, 0, 180))
        while not done:
            clock.tick(30)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        done = True
                    elif event.key == pygame.K_RETURN:
                        aid = fields[0]["value"].strip()
                        name = fields[1]["value"].strip()
                        if aid and import_asset(fpath, aid, tipo=selected_tipo,
                                                meta={"nombre": name, "modo_posicion": selected_modo}):
                            result = aid
                            done = True
                    elif event.key == pygame.K_TAB:
                        focus = (focus + 1) % (len(fields) + 2)
                    elif focus < len(fields):
                        if event.key == pygame.K_BACKSPACE:
                            if cursor_pos[focus] > 0:
                                fields[focus]["value"] = fields[focus]["value"][:cursor_pos[focus] - 1] + fields[focus]["value"][cursor_pos[focus]:]
                                cursor_pos[focus] -= 1
                        elif event.key == pygame.K_DELETE:
                            if cursor_pos[focus] < len(fields[focus]["value"]):
                                fields[focus]["value"] = fields[focus]["value"][:cursor_pos[focus]] + fields[focus]["value"][cursor_pos[focus] + 1:]
                        elif event.key == pygame.K_LEFT:
                            cursor_pos[focus] = max(0, cursor_pos[focus] - 1)
                        elif event.key == pygame.K_RIGHT:
                            cursor_pos[focus] = min(len(fields[focus]["value"]), cursor_pos[focus] + 1)
                        elif event.key == pygame.K_HOME:
                            cursor_pos[focus] = 0
                        elif event.key == pygame.K_END:
                            cursor_pos[focus] = len(fields[focus]["value"])
                        elif event.unicode and event.unicode.isprintable():
                            fields[focus]["value"] = fields[focus]["value"][:cursor_pos[focus]] + event.unicode + fields[focus]["value"][cursor_pos[focus]:]
                            cursor_pos[focus] += 1
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    # Check tipo dropdown
                    td_rect = pygame.Rect(dx + 80, dy + 180, 140, 22)
                    if td_rect.collidepoint(mx, my):
                        focus = len(fields)
                    md_rect = pygame.Rect(dx + 240, dy + 180, 120, 22)
                    if md_rect.collidepoint(mx, my):
                        focus = len(fields) + 1
                    for fi in range(len(fields)):
                        fx = dx + 80
                        fy = dy + 50 + fi * 42
                        fr = pygame.Rect(fx, fy, dw - 100, 26)
                        if fr.collidepoint(mx, my):
                            focus = fi
                            if fields[fi]["value"]:
                                for ci in range(len(fields[fi]["value"]) + 1):
                                    w_txt = font.render(fields[fi]["value"][:ci], True, (220, 220, 220))
                                    if w_txt.get_width() >= mx - fr.x - 4:
                                        cursor_pos[fi] = ci
                                        break
            # Render
            screen.blit(bg, (0, 0))
            pygame.draw.rect(screen, (45, 50, 58), (dx, dy, dw, dh))
            pygame.draw.rect(screen, (70, 80, 95), (dx, dy, dw, dh), 2)
            title = font_b.render("Importar asset", True, (220, 190, 120))
            screen.blit(title, (dx + (dw - title.get_width()) // 2, dy + 14))
            for fi, f in enumerate(fields):
                fy = dy + 50 + fi * 42
                lbl = font.render(f["label"] + ":", True, (180, 190, 200))
                screen.blit(lbl, (dx + 20, fy + 4))
                inp_r = pygame.Rect(dx + 80, fy, dw - 100, 26)
                bg_c = (70, 80, 100) if fi == focus else (55, 60, 70)
                pygame.draw.rect(screen, bg_c, inp_r)
                pygame.draw.rect(screen, (80, 90, 105), inp_r, 1)
                txt_surf = font.render(f["value"], True, (220, 220, 220))
                screen.blit(txt_surf, (inp_r.x + 4, inp_r.y + (inp_r.h - txt_surf.get_height()) // 2))
                if fi == focus and (pygame.time.get_ticks() // 500) % 2 == 0:
                    cx = inp_r.x + 4 + font.render(f["value"][:cursor_pos[fi]], True, (220, 220, 220)).get_width()
                    pygame.draw.line(screen, (200, 200, 200), (cx, inp_r.y + 3), (cx, inp_r.y + inp_r.h - 3))
            # Tipo dropdown
            lbl = font.render("Tipo:", True, (180, 190, 200))
            screen.blit(lbl, (dx + 20, dy + 182))
            td_rect = pygame.Rect(dx + 80, dy + 180, 140, 22)
            bg_c = (60, 65, 80) if focus == len(fields) else (50, 55, 65)
            pygame.draw.rect(screen, bg_c, td_rect)
            pygame.draw.rect(screen, (80, 90, 105), td_rect, 1)
            tlabel = ASSET_TIPOS.get(selected_tipo, selected_tipo)
            tsurf = font.render(tlabel, True, (220, 220, 220))
            screen.blit(tsurf, (td_rect.x + 4, td_rect.y + (td_rect.h - tsurf.get_height()) // 2))
            # Modo dropdown
            mod_lbl = font.render("Modo:", True, (180, 190, 200))
            screen.blit(mod_lbl, (dx + 230, dy + 182))
            md_rect = pygame.Rect(dx + 280, dy + 180, 120, 22)
            bg_c = (60, 65, 80) if focus == len(fields) + 1 else (50, 55, 65)
            pygame.draw.rect(screen, bg_c, md_rect)
            pygame.draw.rect(screen, (80, 90, 105), md_rect, 1)
            mlabel = MODO_POSICION.get(selected_modo, selected_modo)
            msurf = font.render(mlabel, True, (220, 220, 220))
            screen.blit(msurf, (md_rect.x + 4, md_rect.y + (md_rect.h - msurf.get_height()) // 2))
            # Hint
            hint = font.render("TAB: cambiar campo  ENTER: importar  ESC: cancelar", True, (130, 140, 150))
            screen.blit(hint, (dx + (dw - hint.get_width()) // 2, dy + dh - 22))
            pygame.display.flip()
        if result:
            self._selected_id = result
            self._build_ui()

    def _on_save(self):
        if not self._selected_id:
            return
        meta = {}
        if hasattr(self, '_name_input'):
            meta["nombre"] = self._name_input.get_text().strip() or self._selected_id
        if hasattr(self, '_modo_dd'):
            meta["modo_posicion"] = self._modo_dd.get_selected() or "fill"
        if hasattr(self, '_flag_input'):
            meta["desbloqueo_flag"] = self._flag_input.get_text().strip()
        set_asset_meta(self._selected_id, meta)

    def _on_delete(self):
        if not self._selected_id:
            return
        delete_asset(self._selected_id)
        self._selected_id = None
        self._preview_surf = None
        self._build_ui()

    def _on_filter(self, tipo):
        self._filter_tipo = tipo
        self._selected_id = None
        self._preview_surf = None
        self._build_ui()

    def update(self, dt):
        self._gui.update(dt)

    def handle_event(self, event):
        if not self.visible:
            return False
        r = self.get_abs_rect()
        if hasattr(event, 'pos'):
            e = pygame.event.Event(event.type, {
                "pos": (event.pos[0] - r.x, event.pos[1] - r.y),
                "button": getattr(event, "button", 0),
                "buttons": getattr(event, "buttons", (0, 0, 0)),
                "rel": getattr(event, "rel", (0, 0)),
            })
        else:
            e = event
        self._gui.process_events(e)

        if e.type == pygame_gui.UI_BUTTON_PRESSED:
            el = e.ui_element
            if el == self._import_btn: self._on_import(); return True
            if el == self._del_btn: self._on_delete(); return True
            if el == self._save_btn: self._on_save(); return True
            for tid in ["all", "background", "character", "cg", "sprite"]:
                btn = getattr(self, f"_filter_{tid}_btn", None)
                if el == btn:
                    self._on_filter(None if tid == "all" else tid)
                    return True

        elif e.type == pygame_gui.UI_SELECTION_LIST_NEW_SELECTION:
            key = e.text
            if key in get_assets():
                self._selected_id = key
                self._build_editor_widgets()
                return True

        # Custom dropdowns
        if hasattr(self, '_modo_dd') and self._modo_dd.handle_event(e):
            return True

        return True

    def draw(self, surface):
        if not self.visible:
            return
        r = self.get_abs_rect()
        pygame.draw.rect(surface, self.bg_color, r)
        self._gui.draw_ui(surface.subsurface(r))
        if self._descripcion:
            self.draw_descripcion(surface)
        # Draw preview
        if self._preview_surf and self._selected_id:
            ep = self._editor_panel
            pr = pygame.Rect(r.x + ep.rect.x + self._preview_rect.x,
                             r.y + ep.rect.y + self._preview_rect.y,
                             self._preview_rect.w, self._preview_rect.h)
            pygame.draw.rect(surface, (40, 42, 50), pr)
            pygame.draw.rect(surface, (70, 75, 85), pr, 1)
            # Scale to fit
            iw, ih = self._preview_surf.get_size()
            scale = min(pr.w / iw, pr.h / ih) if iw > 0 and ih > 0 else 1
            nw, nh = int(iw * scale), int(ih * scale)
            thumb = pygame.transform.smoothscale(self._preview_surf, (nw, nh))
            tx = pr.x + (pr.w - nw) // 2
            ty = pr.y + (pr.h - nh) // 2
            surface.blit(thumb, (tx, ty))

    def set_size(self, w, h):
        if self.rect.w != w or self.rect.h != h:
            self.rect.w = w
            self.rect.h = h
            self._gui.set_window_resolution((w, h))
            self._build_ui()


class _AssetDropdown:
    MAX_VISIBLE = 8

    def __init__(self, x, y, w, h, options, selected=None, parent_ep=None):
        self.rect = pygame.Rect(x, y, w, h)
        self.parent_ep = parent_ep
        self._all_options = list(options)
        self._selected = selected or (options[0][0] if options else None)
        self._open = False
        self._filter_text = ""
        self._filtered = list(options)
        self._scroll_offset = 0

    def get_selected(self):
        return self._selected

    def _abs_rect(self):
        return self.rect

    def handle_event(self, event):
        r = self._abs_rect()
        if self._open:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self._open = False
                    self._filter_text = ""
                    self._filtered = list(self._all_options)
                    self._scroll_offset = 0
                    return True
                elif event.key == pygame.K_RETURN:
                    if self._filtered:
                        self._selected = self._filtered[0][0]
                        self._open = False
                        self._filter_text = ""
                        self._filtered = list(self._all_options)
                        self._scroll_offset = 0
                    return True
                elif event.key == pygame.K_UP:
                    if self._filtered:
                        idx = max(0, self._get_selected_idx())
                        new_idx = max(0, idx - 1)
                        if new_idx < self._scroll_offset:
                            self._scroll_offset = new_idx
                        self._selected = self._filtered[new_idx][0]
                    return True
                elif event.key == pygame.K_DOWN:
                    if self._filtered:
                        idx = min(len(self._filtered) - 1, self._get_selected_idx())
                        new_idx = min(len(self._filtered) - 1, idx + 1)
                        if new_idx >= self._scroll_offset + self.MAX_VISIBLE:
                            self._scroll_offset = new_idx - self.MAX_VISIBLE + 1
                        self._selected = self._filtered[new_idx][0]
                    return True
            if event.type == pygame.MOUSEWHEEL:
                max_scroll = max(0, len(self._filtered) - self.MAX_VISIBLE)
                self._scroll_offset = max(0, min(max_scroll, self._scroll_offset - event.y))
                return True
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = event.pos
            if r.collidepoint(mx, my):
                self._open = not self._open
                self._filter_text = ""
                self._filtered = list(self._all_options)
                self._scroll_offset = 0
                return True
            if self._open:
                ih = 20
                vis = min(len(self._filtered), self.MAX_VISIBLE)
                total_h = vis * ih + 2
                dy = r.y + r.h
                dd_rect = pygame.Rect(r.x, dy, r.w, total_h)
                if dd_rect.collidepoint(mx, my):
                    click_idx = (my - dd_rect.y) // ih
                    idx = self._scroll_offset + click_idx
                    if 0 <= idx < len(self._filtered):
                        self._selected = self._filtered[idx][0]
                        self._open = False
                        self._filter_text = ""
                        self._filtered = list(self._all_options)
                        self._scroll_offset = 0
                        return True
                self._open = False
                self._filter_text = ""
                self._filtered = list(self._all_options)
                self._scroll_offset = 0
                return True
        return False

    def _get_selected_idx(self):
        for i, (val, lbl) in enumerate(self._filtered):
            if val == self._selected:
                return i
        return 0
