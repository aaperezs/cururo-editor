import os
import re
import json
import pygame
from editor.project import discover_projects, list_templates, create_project
from editor.categories import get_all_categories, get_template_dirs

STATE_LIST = 0
STATE_NEW = 1

PLATFORMS = [("desktop", "Escritorio"), ("mobile", "Movil")]
QUALITIES = [("low", "Baja"), ("medium", "Media"), ("high", "Alta")]
TILE_SIZES = [16, 20, 24, 32]
PIXEL_SCALES = [1, 2, 3]
RES_SUGGESTED = {
    16: ["640x480", "800x600", "960x720"],
    20: ["800x600", "960x720"],
    24: ["960x720", "1200x900"],
    32: ["960x720", "1280x960"],
}
_re_res = re.compile(r"^\d+x\d+$")


class ProjectDialog:
    def __init__(self, search_dir):
        self.search_dirs = search_dir if isinstance(search_dir, (list, tuple)) else [search_dir]
        self.search_dir = self.search_dirs[0] if self.search_dirs else "."
        self.projects = self._discover_all()
        self.templates = list_templates()
        self.categories = get_all_categories()
        self.selected_index = 0
        self.font = None
        self.font_b = None
        self.font_title = None
        self.W, self.H = 560, 780
        self.ITEM_H = 40
        self.done = False
        self.result = None

        self.state = STATE_LIST

        self._new_name = ""
        self._selected_cat_idx = 0
        self._available_templates = self._templates_for_cat()
        self._selected_tpl_idx = 0
        self._selected_plat_idx = 0
        self._selected_qual_idx = 1
        self._new_title = ""
        self._new_res = "800x600"
        self._selected_tile_idx = 1  # 20px (default)
        self._selected_res_idx = 0
        self._selected_scale_idx = 0  # 1x
        self._tileset_enabled = False
        self._tileset_path = None
        self._warn_msg = ""
        self._cursor_visible = True
        self._cursor_timer = 0
        self._error_msg = ""
        self._focus = "name"

    def _discover_all(self):
        results = []
        seen = set()
        for d in self.search_dirs:
            for p in discover_projects(d):
                if p["path"] not in seen:
                    seen.add(p["path"])
                    results.append(p)
        return results

    def _open_project_folder(self):
        """Abre un selector de carpeta y carga un proyecto existente (cururo.json)."""
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.update()
        try:
            folder = filedialog.askdirectory(
                title="Seleccionar proyecto",
                initialdir=self.search_dirs[0] if self.search_dirs else ".",
            )
        finally:
            root.destroy()
        if not folder:
            return
        manifest = os.path.join(folder, "cururo.json")
        if not os.path.isfile(manifest):
            self._error_msg = "La carpeta no contiene un proyecto (falta cururo.json)"
            return
        try:
            with open(manifest, "r", encoding="utf-8") as f:
                data = json.load(f)
        except (json.JSONDecodeError, IOError):
            data = {}
        self.result = {
            "path": folder,
            "name": data.get("name", os.path.basename(folder)),
            "id": data.get("id", os.path.basename(folder)),
            "category": data.get("category", "blank"),
        }
        self.done = True

    def _templates_for_cat(self):
        cat_id = self.categories[self._selected_cat_idx]["id"]
        return [t for t in self.templates if t.get("category") == cat_id]

    def _layout_new(self):
        cat_start_y = 162
        cat_h = 32
        tpl_start_y = cat_start_y + len(self.categories) * cat_h + 12
        tpl_h = 24
        plat_start_y = tpl_start_y + len(self._available_templates) * tpl_h + 14
        opt_h = 22
        qual_start_y = plat_start_y + len(PLATFORMS) * opt_h + 14
        tile_label_y = qual_start_y + len(QUALITIES) * opt_h + 12
        tile_opt_y = tile_label_y + 18
        res_label_y = tile_opt_y + 24
        res_opt_y = res_label_y + 18
        res_input_y = res_opt_y + 24
        scale_label_y = res_input_y + 24
        scale_opt_y = scale_label_y + 18
        tileset_label_y = scale_opt_y + 24
        tileset_row_y = tileset_label_y + 18
        title_label_y = tileset_row_y + 26
        title_input_y = title_label_y + 18
        btn_y = self.H - 100
        return {
            "name_input": pygame.Rect(40, 86, self.W - 80, 28),
            "cat_start": cat_start_y,
            "cat_h": cat_h,
            "tpl_start": tpl_start_y,
            "tpl_h": tpl_h,
            "plat_start": plat_start_y,
            "qual_start": qual_start_y,
            "tile_label": tile_label_y,
            "tile_opt": pygame.Rect(40, tile_opt_y, self.W - 80, 20),
            "res_label": res_label_y,
            "res_opt": pygame.Rect(40, res_opt_y, self.W - 80, 20),
            "res_input": pygame.Rect(200, res_input_y, self.W - 240, 26),
            "scale_label": scale_label_y,
            "scale_opt": pygame.Rect(40, scale_opt_y, self.W - 80, 20),
            "tileset_label": tileset_label_y,
            "tileset_check": pygame.Rect(40, tileset_row_y, 18, 18),
            "tileset_btn": pygame.Rect(66, tileset_row_y - 2, 130, 22),
            "tileset_path": pygame.Rect(204, tileset_row_y - 2, self.W - 244, 22),
            "title_label": title_label_y,
            "title_input": pygame.Rect(40, title_input_y, self.W - 80, 26),
            "btn_y": btn_y,
            "create_btn": pygame.Rect(self.W // 2 - 60, btn_y, 120, 34),
            "cancel_btn": pygame.Rect(self.W // 2 - 60, btn_y + 38, 120, 34),
        }

    def _next_focus(self):
        order = ["name", "category", "template", "platform", "quality", "tile", "resolution", "scale", "tileset", "title"]
        return order[(order.index(self._focus) + 1) % len(order)]

    def _prev_focus(self):
        order = ["name", "category", "template", "platform", "quality", "tile", "resolution", "scale", "tileset", "title"]
        return order[(order.index(self._focus) - 1) % len(order)]

    def _recalc_res_sugeridas(self):
        """Al cambiar tile size, recalcula las resoluciones sugeridas."""
        ts = TILE_SIZES[self._selected_tile_idx]
        sugeridas = RES_SUGGESTED[ts]
        if self._new_res in sugeridas:
            self._selected_res_idx = sugeridas.index(self._new_res)
        else:
            self._selected_res_idx = 0
            self._new_res = sugeridas[0]

    def _pick_tileset(self):
        import tkinter as tk
        from tkinter import filedialog

        root = tk.Tk()
        root.withdraw()
        root.update()
        try:
            path = filedialog.askopenfilename(
                title="Seleccionar tileset (PNG)",
                filetypes=[("PNG", "*.png"), ("Imágenes", "*.png *.jpg *.bmp")],
            )
        finally:
            root.destroy()
        if path:
            self._tileset_path = path
            self._tileset_enabled = True

    def _input_key(self, event):
        if event.key == pygame.K_RETURN:
            if self._focus == "name":
                if self._new_name.strip():
                    self._focus = "category"
            elif self._focus == "category":
                self._focus = "template"
            elif self._focus == "template":
                self._focus = "platform"
            elif self._focus == "platform":
                self._focus = "quality"
            elif self._focus == "quality":
                self._focus = "tile"
            elif self._focus == "tile":
                self._focus = "resolution"
            elif self._focus == "resolution":
                self._focus = "scale"
            elif self._focus == "scale":
                self._focus = "tileset"
            elif self._focus == "tileset":
                self._tileset_enabled = not self._tileset_enabled
                if self._tileset_enabled and not self._tileset_path:
                    self._pick_tileset()
            elif self._focus == "title":
                return self._do_create()
            return True
        if event.key == pygame.K_ESCAPE:
            if self._focus == "name":
                self.state = STATE_LIST
            else:
                self._focus = self._prev_focus()
            return True
        if event.key == pygame.K_TAB:
            self._focus = self._next_focus()
            return True
        if event.key == pygame.K_UP:
            if self._focus == "category":
                self._selected_cat_idx = max(0, self._selected_cat_idx - 1)
                self._available_templates = self._templates_for_cat()
                self._selected_tpl_idx = 0
            elif self._focus == "template":
                self._selected_tpl_idx = max(0, self._selected_tpl_idx - 1)
            elif self._focus == "platform":
                self._selected_plat_idx = max(0, self._selected_plat_idx - 1)
            elif self._focus == "quality":
                self._selected_qual_idx = max(0, self._selected_qual_idx - 1)
            elif self._focus == "tile":
                self._selected_tile_idx = max(0, self._selected_tile_idx - 1)
                self._recalc_res_sugeridas()
            elif self._focus == "resolution":
                self._selected_res_idx = max(0, self._selected_res_idx - 1)
                self._new_res = RES_SUGGESTED[TILE_SIZES[self._selected_tile_idx]][self._selected_res_idx]
            elif self._focus == "scale":
                self._selected_scale_idx = max(0, self._selected_scale_idx - 1)
            elif self._focus == "tileset":
                self._tileset_enabled = not self._tileset_enabled
                if self._tileset_enabled and not self._tileset_path:
                    self._pick_tileset()
            return True
        if event.key == pygame.K_DOWN:
            if self._focus == "category":
                self._selected_cat_idx = min(len(self.categories) - 1, self._selected_cat_idx + 1)
                self._available_templates = self._templates_for_cat()
                self._selected_tpl_idx = 0
            elif self._focus == "template":
                self._selected_tpl_idx = min(len(self._available_templates) - 1, self._selected_tpl_idx + 1)
            elif self._focus == "platform":
                self._selected_plat_idx = min(len(PLATFORMS) - 1, self._selected_plat_idx + 1)
            elif self._focus == "quality":
                self._selected_qual_idx = min(len(QUALITIES) - 1, self._selected_qual_idx + 1)
            elif self._focus == "tile":
                self._selected_tile_idx = min(len(TILE_SIZES) - 1, self._selected_tile_idx + 1)
                self._recalc_res_sugeridas()
            elif self._focus == "resolution":
                sugeridas = RES_SUGGESTED[TILE_SIZES[self._selected_tile_idx]]
                self._selected_res_idx = min(len(sugeridas) - 1, self._selected_res_idx + 1)
                self._new_res = sugeridas[self._selected_res_idx]
            elif self._focus == "scale":
                self._selected_scale_idx = min(len(PIXEL_SCALES) - 1, self._selected_scale_idx + 1)
            elif self._focus == "tileset":
                self._tileset_enabled = not self._tileset_enabled
                if self._tileset_enabled and not self._tileset_path:
                    self._pick_tileset()
            return True
        if event.key == pygame.K_BACKSPACE:
            if self._focus == "name":
                self._new_name = self._new_name[:-1]
            elif self._focus == "resolution":
                self._new_res = self._new_res[:-1]
            elif self._focus == "title":
                self._new_title = self._new_title[:-1]
        else:
            if event.unicode:
                if self._focus == "name" and len(self._new_name) < 40:
                    self._new_name += event.unicode
                elif self._focus == "resolution" and len(self._new_res) < 12:
                    self._new_res += event.unicode
                    ts = TILE_SIZES[self._selected_tile_idx]
                    if self._new_res in RES_SUGGESTED[ts]:
                        self._selected_res_idx = RES_SUGGESTED[ts].index(self._new_res)
                elif self._focus == "title" and len(self._new_title) < 60:
                    self._new_title += event.unicode
        return True

    def _input_click_new(self, event):
        mx, my = event.pos
        L = self._layout_new()

        if L["name_input"].collidepoint(mx, my):
            self._focus = "name"
            return

        for i, cat in enumerate(self.categories):
            ry = L["cat_start"] + i * L["cat_h"]
            if 40 <= mx <= self.W - 40 and ry <= my <= ry + L["cat_h"] - 4:
                self._selected_cat_idx = i
                self._available_templates = self._templates_for_cat()
                self._selected_tpl_idx = 0
                self._focus = "category"
                return

        for i, tpl in enumerate(self._available_templates):
            ry = L["tpl_start"] + i * L["tpl_h"]
            if 40 <= mx <= self.W - 40 and ry <= my <= ry + L["tpl_h"] - 2:
                self._selected_tpl_idx = i
                self._focus = "template"
                return

        for i, plat in enumerate(PLATFORMS):
            ry = L["plat_start"] + i * 22
            if 40 <= mx <= self.W - 40 and ry <= my <= ry + 20:
                self._selected_plat_idx = i
                self._focus = "platform"
                return

        for i, qual in enumerate(QUALITIES):
            ry = L["qual_start"] + i * 22
            if 40 <= mx <= self.W - 40 and ry <= my <= ry + 20:
                self._selected_qual_idx = i
                self._focus = "quality"
                return

        if L["res_input"].collidepoint(mx, my):
            self._focus = "resolution"
            return

        if L["tile_opt"].collidepoint(mx, my):
            self._focus = "tile"
            return

        if L["res_opt"].collidepoint(mx, my):
            self._focus = "resolution"
            return

        if L["scale_opt"].collidepoint(mx, my):
            self._focus = "scale"
            return

        if L["tileset_check"].collidepoint(mx, my):
            self._tileset_enabled = not self._tileset_enabled
            if self._tileset_enabled and not self._tileset_path:
                self._pick_tileset()
            self._focus = "tileset"
            return

        if L["tileset_btn"].collidepoint(mx, my):
            self._pick_tileset()
            self._focus = "tileset"
            return

        if L["title_input"].collidepoint(mx, my):
            self._focus = "title"
            return

        if L["create_btn"].collidepoint(mx, my):
            self._do_create()
            return

        if L["cancel_btn"].collidepoint(mx, my):
            self.state = STATE_LIST

    def _validar_res(self, res):
        res = res.strip().lower().replace(" ", "")
        if not res:
            return "800x600"
        if not _re_res.match(res):
            return None
        w, h = res.split("x")
        w, h = int(w), int(h)
        if w < 320 or h < 240 or w > 7680 or h > 4320:
            return None
        return f"{w}x{h}"

    def _do_create(self):
        name = self._new_name.strip()
        if not name:
            self._error_msg = "Ingresa un nombre para el proyecto"
            return True
        if not self._available_templates:
            self._error_msg = "No hay plantillas para esta categoria"
            return True
        res = self._validar_res(self._new_res)
        if res is None:
            self._error_msg = "Resolucion invalida (formato WxH, ej. 1280x720)"
            self._focus = "resolution"
            return True
        tile_size = TILE_SIZES[self._selected_tile_idx]
        rw, rh = (int(p) for p in res.split("x"))
        if rw % tile_size != 0 or rh % tile_size != 0:
            self._warn_msg = (f"Resolucion {res} no es multiplo de tile size "
                              f"({tile_size}px): se usara letterbox")
        else:
            self._warn_msg = ""
        tpl = self._available_templates[self._selected_tpl_idx]
        platform = PLATFORMS[self._selected_plat_idx][0]
        quality = QUALITIES[self._selected_qual_idx][0]
        title = self._new_title.strip() or None
        safe = name.lower().replace(" ", "_").replace("-", "_")
        base = os.path.join(self.search_dir, safe)
        n = 1
        path = base
        while os.path.exists(path):
            path = f"{base}_{n}"
            n += 1
        graphics_config = {
            "tile_size": tile_size,
            "resolution": [rw, rh],
            "pixel_art_scale": PIXEL_SCALES[self._selected_scale_idx],
            "tileset": self._tileset_path if self._tileset_enabled else None,
        }
        result = create_project(tpl["id"], name, path,
                                platform=platform, quality=quality,
                                window_title=title, resolution=res,
                                graphics_config=graphics_config)
        if result:
            self.result = {"path": result, "name": name, "id": safe}
            self.done = True
        else:
            self._error_msg = "Error al crear el proyecto"
        return True

    def run(self):
        pygame.init()
        pygame.font.init()
        self.font = pygame.font.SysFont("Arial", 14)
        self.font_b = pygame.font.SysFont("Arial", 14, bold=True)
        self.font_title = pygame.font.SysFont("Arial", 18, bold=True)
        self.font_small = pygame.font.SysFont("Arial", 12)
        screen = pygame.display.set_mode((self.W, self.H))
        pygame.display.set_caption("Cururo Editor")
        clock = pygame.time.Clock()

        while not self.done:
            clock.tick(30)

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.done = True
                    self.result = None

                elif self.state == STATE_LIST:
                    if event.type == pygame.KEYDOWN:
                        # Fila 0: "+ Nuevo Proyecto". Última fila: "Cargar Proyecto...".
                        total = len(self.projects) + 2
                        if event.key == pygame.K_UP:
                            self.selected_index = max(0, self.selected_index - 1)
                        elif event.key == pygame.K_DOWN:
                            self.selected_index = min(total - 1, self.selected_index + 1)
                        elif event.key == pygame.K_RETURN:
                            if self.selected_index == 0:
                                self.state = STATE_NEW
                                self._new_name = ""
                                self._new_title = ""
                                self._new_res = "800x600"
                                self._selected_tile_idx = 1
                                self._selected_res_idx = 0
                                self._selected_scale_idx = 0
                                self._tileset_enabled = False
                                self._tileset_path = None
                                self._warn_msg = ""
                                self._error_msg = ""
                                self._focus = "name"
                            elif self.selected_index == total - 1:
                                self._open_project_folder()
                            elif self.projects:
                                idx = self.selected_index - 1
                                if 0 <= idx < len(self.projects):
                                    self.result = self.projects[idx]
                                    self.done = True
                        elif event.key == pygame.K_ESCAPE:
                            self.done = True
                            self.result = None
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        mx, my = event.pos
                        if 40 <= mx <= self.W - 40 and 80 <= my <= 80 + self.ITEM_H - 4:
                            self.state = STATE_NEW
                            self._new_name = ""
                            self._new_title = ""
                            self._new_res = "800x600"
                            self._selected_tile_idx = 1
                            self._selected_res_idx = 0
                            self._selected_scale_idx = 0
                            self._tileset_enabled = False
                            self._tileset_path = None
                            self._warn_msg = ""
                            self._error_msg = ""
                            self._focus = "name"
                        for i, p in enumerate(self.projects):
                            ry = 80 + self.ITEM_H + i * self.ITEM_H
                            if 40 <= mx <= self.W - 40 and ry <= my <= ry + self.ITEM_H - 4:
                                self.result = p
                                self.done = True
                        ry_load = 80 + self.ITEM_H + len(self.projects) * self.ITEM_H
                        if 40 <= mx <= self.W - 40 and ry_load <= my <= ry_load + self.ITEM_H - 4:
                            self._open_project_folder()

                elif self.state == STATE_NEW:
                    if event.type == pygame.KEYDOWN:
                        self._input_key(event)
                    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                        self._input_click_new(event)

            screen.fill((25, 28, 32))

            if self.state == STATE_LIST:
                self._draw_list(screen)
            else:
                self._draw_new(screen)

            pygame.display.flip()

        return self.result["path"] if self.result else None

    def _draw_list(self, screen):
        title = self.font_title.render("Cururo Editor", True, (200, 210, 220))
        screen.blit(title, (self.W // 2 - title.get_width() // 2, 20))

        if self._error_msg:
            err = self.font.render(self._error_msg, True, (220, 80, 80))
            screen.blit(err, (self.W // 2 - err.get_width() // 2, 44))

        sub = self.font.render("Proyectos:", True, (150, 160, 170))
        screen.blit(sub, (20, 55))

        ry = 80
        sel = self.selected_index == 0
        bg = (55, 70, 90) if sel else (42, 55, 70)
        pygame.draw.rect(screen, bg, (40, ry, self.W - 80, self.ITEM_H - 4))
        if sel:
            pygame.draw.rect(screen, (70, 160, 220), (40, ry, 3, self.ITEM_H - 4))
        plus = self.font_b.render("+ Nuevo Proyecto", True, (160, 210, 255))
        screen.blit(plus, (54, ry + 10))

        for i, p in enumerate(self.projects):
            ry = 80 + self.ITEM_H + i * self.ITEM_H
            sel = self.selected_index == i + 1
            bg = (55, 60, 72) if sel else (38, 42, 50)
            pygame.draw.rect(screen, bg, (40, ry, self.W - 80, self.ITEM_H - 4))
            if sel:
                pygame.draw.rect(screen, (70, 130, 200), (40, ry, 3, self.ITEM_H - 4))
            name = self.font_b.render(p["name"], True, (200, 210, 220))
            screen.blit(name, (54, ry + 4))
            cat = p.get("category", "?")
            pid = self.font.render(cat + " - " + p["id"], True, (130, 140, 150))
            screen.blit(pid, (54, ry + 22))

        ry_load = 80 + self.ITEM_H + len(self.projects) * self.ITEM_H
        sel_load = self.selected_index == len(self.projects) + 1
        bg = (50, 60, 66) if sel_load else (36, 42, 46)
        pygame.draw.rect(screen, bg, (40, ry_load, self.W - 80, self.ITEM_H - 4))
        if sel_load:
            pygame.draw.rect(screen, (60, 160, 180), (40, ry_load, 3, self.ITEM_H - 4))
        load_txt = self.font_b.render("Cargar Proyecto...", True, (150, 220, 220))
        screen.blit(load_txt, (54, ry_load + 10))

        if not self.projects:
            txt = self.font.render(
                "No hay proyectos. Cree uno nuevo.", True, (160, 170, 180))
            screen.blit(txt, (54, 80 + self.ITEM_H + 10))

        hint = self.font.render(
            "\u2191\u2193: navegar  Enter: abrir/crear  ESC: salir",
            True, (100, 110, 120))
        screen.blit(hint, (self.W // 2 - hint.get_width() // 2, self.H - 30))

    def _draw_opt(self, screen, x, y, label, idx, selected, focus, w):
        sel = idx == selected
        fcs = focus and sel
        bg = (55, 70, 90) if fcs else (42, 55, 70)
        pygame.draw.rect(screen, bg, (x, y, w, 20))
        if fcs:
            pygame.draw.rect(screen, (70, 160, 220), (x, y, 3, 20))
        elif sel:
            pygame.draw.rect(screen, (50, 100, 140), (x, y, 3, 20))
        txt = self.font.render(label, True, (200, 210, 220))
        screen.blit(txt, (x + 10, y + 2))

    def _draw_opt_single(self, screen, rect, label, focus):
        """Dropdown de una fila (valor actual + hint de flechas)."""
        bg = (55, 70, 90) if focus else (42, 55, 70)
        pygame.draw.rect(screen, bg, rect)
        if focus:
            pygame.draw.rect(screen, (70, 160, 220), (rect.x, rect.y, 3, rect.height))
        txt = self.font.render(label, True, (200, 210, 220))
        screen.blit(txt, (rect.x + 10, rect.y + 2))
        hint = self.font_small.render("\u2191\u2193", True, (120, 140, 160))
        screen.blit(hint, (rect.right - 24, rect.y + 3))

    def _draw_new(self, screen):
        L = self._layout_new()
        title = self.font_title.render("Nuevo Proyecto", True, (200, 210, 220))
        screen.blit(title, (self.W // 2 - title.get_width() // 2, 20))

        if self._error_msg:
            err = self.font.render(self._error_msg, True, (220, 80, 80))
            screen.blit(err, (self.W // 2 - err.get_width() // 2, 44))
        elif self._warn_msg:
            warn = self.font.render(self._warn_msg, True, (220, 190, 90))
            screen.blit(warn, (self.W // 2 - warn.get_width() // 2, 44))

        lbl = self.font.render("Nombre del proyecto:", True, (180, 190, 200))
        screen.blit(lbl, (40, 64))

        input_rect = L["name_input"]
        focus_color = (70, 130, 200) if self._focus == "name" else (60, 65, 75)
        pygame.draw.rect(screen, (50, 55, 65), input_rect)
        pygame.draw.rect(screen, focus_color, input_rect, 2)

        display_name = self._new_name
        self._cursor_timer += 1
        if self._cursor_timer >= 30:
            self._cursor_timer = 0
            self._cursor_visible = not self._cursor_visible
        if self._cursor_visible and self._focus == "name":
            display_name += "|"

        txt = self.font_b.render(display_name, True, (220, 220, 220))
        screen.blit(txt, (48, 92))

        safe = self._new_name.lower().replace(" ", "_").replace("-", "_") if self._new_name else "..."
        path_preview = self.font_small.render(
            os.path.join(self.search_dir, safe), True, (120, 130, 140))
        screen.blit(path_preview, (48, 118))

        cat_lbl = self.font.render("Categoria:", True, (180, 190, 200))
        screen.blit(cat_lbl, (40, 142))

        for i, cat in enumerate(self.categories):
            ry = L["cat_start"] + i * L["cat_h"]
            sel = i == self._selected_cat_idx
            focused = self._focus == "category" and sel
            bg = (55, 70, 90) if focused else (42, 55, 70)
            pygame.draw.rect(screen, bg, (40, ry, self.W - 80, L["cat_h"] - 4))
            if focused:
                pygame.draw.rect(screen, (70, 160, 220), (40, ry, 3, L["cat_h"] - 4))
            elif sel:
                pygame.draw.rect(screen, (50, 100, 140), (40, ry, 3, L["cat_h"] - 4))
            cname = self.font_b.render(cat["name"], True, (200, 210, 220))
            screen.blit(cname, (54, ry + 4))
            cdesc = self.font_small.render(cat["description"], True, (130, 140, 150))
            screen.blit(cdesc, (54, ry + 20))

        tpl_lbl = self.font.render("Plantilla:", True, (180, 190, 200))
        screen.blit(tpl_lbl, (40, L["tpl_start"] - 20))

        y = L["tpl_start"]
        if not self._available_templates:
            no_tpl = self.font.render("(sin plantillas)", True, (120, 130, 140))
            screen.blit(no_tpl, (48, y))
            y += L["tpl_h"]
        else:
            for i, tpl in enumerate(self._available_templates):
                sel = i == self._selected_tpl_idx
                focused = self._focus == "template" and sel
                bg = (55, 60, 72) if focused else (45, 48, 55)
                pygame.draw.rect(screen, bg, (40, y, self.W - 80, L["tpl_h"] - 2))
                if focused:
                    pygame.draw.rect(screen, (70, 130, 200), (40, y, 3, L["tpl_h"] - 2))
                tname = self.font.render(tpl["name"], True, (180, 200, 230))
                screen.blit(tname, (48, y + 4))
                y += L["tpl_h"]

        plat_lbl = self.font.render("Plataforma:", True, (180, 190, 200))
        screen.blit(plat_lbl, (40, L["plat_start"] - 20))
        for i, plat in enumerate(PLATFORMS):
            self._draw_opt(screen, 40, L["plat_start"] + i * 22, plat[1],
                           i, self._selected_plat_idx,
                           self._focus == "platform", self.W - 80)

        qual_lbl = self.font.render("Calidad grafica:", True, (180, 190, 200))
        screen.blit(qual_lbl, (40, L["qual_start"] - 20))
        for i, qual in enumerate(QUALITIES):
            self._draw_opt(screen, 40, L["qual_start"] + i * 22, qual[1],
                           i, self._selected_qual_idx,
                           self._focus == "quality", self.W - 80)

        # ── Configuración gráfica ──
        tile_lbl = self.font.render("Tile size (px):", True, (180, 190, 200))
        screen.blit(tile_lbl, (40, L["tile_label"]))
        self._draw_opt_single(screen, L["tile_opt"],
                              f"{TILE_SIZES[self._selected_tile_idx]} px",
                              self._focus == "tile")

        res_lbl = self.font.render("Resolucion sugerida:", True, (180, 190, 200))
        screen.blit(res_lbl, (40, L["res_label"]))
        sugeridas = RES_SUGGESTED[TILE_SIZES[self._selected_tile_idx]]
        self._draw_opt_single(screen, L["res_opt"], sugeridas[self._selected_res_idx],
                              self._focus == "resolution")

        res_lbl2 = self.font.render("Resolucion base (WxH):", True, (180, 190, 200))
        screen.blit(res_lbl2, (40, L["res_input"].top + 4))
        r_rect = L["res_input"]
        r_color = (70, 130, 200) if self._focus == "resolution" else (60, 65, 75)
        pygame.draw.rect(screen, (50, 55, 65), r_rect)
        pygame.draw.rect(screen, r_color, r_rect, 2)
        display_res = self._new_res
        if self._cursor_visible and self._focus == "resolution":
            display_res += "|"
        r_txt = self.font.render(display_res, True, (220, 220, 220))
        screen.blit(r_txt, (r_rect.x + 6, r_rect.y + 4))

        scale_lbl = self.font.render("Pixel art scale:", True, (180, 190, 200))
        screen.blit(scale_lbl, (40, L["scale_label"]))
        self._draw_opt_single(screen, L["scale_opt"],
                              f"{PIXEL_SCALES[self._selected_scale_idx]}x",
                              self._focus == "scale")

        ts_lbl = self.font.render("Tileset:", True, (180, 190, 200))
        screen.blit(ts_lbl, (40, L["tileset_label"]))
        check = L["tileset_check"]
        pygame.draw.rect(screen, (50, 55, 65), check)
        pygame.draw.rect(screen, (70, 130, 200) if self._focus == "tileset" else (60, 65, 75), check, 2)
        if self._tileset_enabled:
            pygame.draw.line(screen, (140, 200, 120), (check.x + 3, check.y + 9),
                             (check.x + 7, check.y + 13), 2)
            pygame.draw.line(screen, (140, 200, 120), (check.x + 7, check.y + 13),
                             (check.x + 15, check.y + 4), 2)
        btn = L["tileset_btn"]
        pygame.draw.rect(screen, (55, 70, 90), btn)
        pygame.draw.rect(screen, (70, 130, 200), btn, 1)
        btn_txt = self.font.render("Seleccionar...", True, (200, 210, 220))
        screen.blit(btn_txt, (btn.x + 8, btn.y + 3))
        path_rect = L["tileset_path"]
        pygame.draw.rect(screen, (45, 48, 55), path_rect)
        path_txt = self.font_small.render(
            os.path.basename(self._tileset_path) if self._tileset_enabled and self._tileset_path else "(sin tileset)",
            True, (150, 160, 170))
        screen.blit(path_txt, (path_rect.x + 6, path_rect.y + 4))

        title_lbl = self.font.render("Titulo de ventana (opcional):", True, (180, 190, 200))
        screen.blit(title_lbl, (40, L["title_label"]))
        t_rect = L["title_input"]
        t_color = (70, 130, 200) if self._focus == "title" else (60, 65, 75)
        pygame.draw.rect(screen, (50, 55, 65), t_rect)
        pygame.draw.rect(screen, t_color, t_rect, 2)
        display_title = self._new_title
        if self._cursor_visible and self._focus == "title":
            display_title += "|"
        t_txt = self.font.render(display_title, True, (220, 220, 220))
        screen.blit(t_txt, (t_rect.x + 6, t_rect.y + 4))

        create_btn = L["create_btn"]
        pygame.draw.rect(screen, (50, 100, 50), create_btn)
        pygame.draw.rect(screen, (70, 140, 70), create_btn, 2)
        c_txt = self.font_b.render("Crear", True, (220, 220, 220))
        screen.blit(c_txt, (create_btn.centerx - c_txt.get_width() // 2,
                            create_btn.centery - c_txt.get_height() // 2))

        cancel_btn = L["cancel_btn"]
        pygame.draw.rect(screen, (60, 60, 65), cancel_btn)
        pygame.draw.rect(screen, (75, 75, 80), cancel_btn, 2)
        esc_txt = self.font.render("Cancelar", True, (180, 180, 185))
        screen.blit(esc_txt, (cancel_btn.centerx - esc_txt.get_width() // 2,
                              cancel_btn.centery - esc_txt.get_height() // 2))

        hint = self.font.render(
            "TAB: cambiar foco  ESC: volver  Enter: crear  \u2191\u2193: opciones",
            True, (100, 110, 120))
        screen.blit(hint, (self.W // 2 - hint.get_width() // 2,
                           L["cancel_btn"].bottom + 10))
