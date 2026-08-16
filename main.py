#!/usr/bin/env python3
import sys
import os

_FROZEN = bool(getattr(sys, "frozen", False))
if _FROZEN:
    _MEIPASS = getattr(sys, "_MEIPASS", os.path.dirname(sys.executable))
    _editor_root = os.path.join(_MEIPASS, "editor")
    _src_root = _MEIPASS
else:
    _editor_root = os.path.dirname(os.path.abspath(__file__))
    _src_root = os.path.dirname(_editor_root)
if _src_root not in sys.path:
    sys.path.insert(0, _src_root)


def _default_projects_dir():
    """Directorio principal de búsqueda/creación de proyectos.

    En frozen devuelve la carpeta del exe (y sus proyectos viven junto a él).
    """
    if _FROZEN:
        return os.path.dirname(sys.executable)
    return _src_root


def _default_projects_dirs():
    """Carpetas donde buscar proyectos existentes.

    En frozen: carpeta del exe, su padre y el directorio de trabajo actual
    (por si el exe se mueve y los proyectos viven en otra ruta).
    """
    if _FROZEN:
        exe_dir = os.path.dirname(sys.executable)
        dirs = [exe_dir]
        parent = os.path.dirname(exe_dir)
        if parent not in dirs:
            dirs.append(parent)
        cwd = os.getcwd()
        if cwd not in dirs:
            dirs.append(cwd)
        return dirs
    return [_src_root]


# ── Modo runtime embebido (CururoEditor.exe --runtime --project <root>) ──
# El editor empaqueta el runtime ORM dentro del mismo exe. Al lanzar el exe
# con el flag --runtime se ejecuta el juego en lugar del editor.
if _FROZEN and "--runtime" in sys.argv:
    _rt_project = None
    for _i, _arg in enumerate(sys.argv):
        if _arg == "--project" and _i + 1 < len(sys.argv):
            _rt_project = sys.argv[_i + 1]
    _rt_orm_root = os.path.join(_MEIPASS, "orm")
    _rt_main = os.path.join(_rt_orm_root, "main.py")
    if os.path.exists(_rt_main):
        sys.path.insert(0, _MEIPASS)
        sys.path.insert(0, _rt_orm_root)
        sys.argv = ["main.py", "--project", _rt_project] if _rt_project else ["main.py"]
        import runpy
        runpy.run_path(_rt_main, run_name="__main__")
    sys.exit(0)

project_root = None
if len(sys.argv) > 1:
    project_root = os.path.abspath(sys.argv[1])
else:
    from editor.project_dialog import ProjectDialog
    search_dir = _default_projects_dirs()
    dialog = ProjectDialog(search_dir)
    project_root = dialog.run()

if not project_root:
    print("No se selecciono ningun proyecto. Saliendo.")
    sys.exit(0)

from editor.project import set_current_project, sys_path_setup
sys_path_setup(project_root)
set_current_project(project_root)

if not os.path.isdir(os.path.join(project_root, "utils")):
    _orm_root = os.path.join(_src_root, "orm")
    if os.path.isdir(os.path.join(_orm_root, "utils")) and _orm_root not in sys.path:
        sys.path.insert(0, _orm_root)
elif _FROZEN:
    _orm_root = os.path.join(_MEIPASS, "orm")
    if os.path.isdir(os.path.join(_orm_root, "utils")) and _orm_root not in sys.path:
        sys.path.insert(0, _orm_root)

import pygame
from editor.translation import I18n
from editor.widgets.menu_manager import MenuManager
from editor.widgets.menu_bar import MenuBar
from editor.widgets.menu_item import MenuSection, MenuItem
from editor.sprite_editor import SpriteEditorPanel
from editor.map_editor import MapEditorPanel
from editor.event_editor import EventEditorPanel
from editor.element_tab import ElementTab
from editor.elements import _load_elements
from editor.ability_data import _load_abilities
from editor.ability_tab import AbilityTab
from editor.items_data import _load_items
from editor.item_tab import ItemTab
from editor.boss_tab import BossTab
from editor.boss_data import _load as _load_bosses
from editor import workspace
from editor.widgets.animation_panel import AnimationPanel
from editor.animations import _load as _load_animations
from editor.script_panel import ScriptPanel
from editor.custom_behaviors import CustomBehaviorsPanel
from editor.screens_panel import ScreensPanel
from editor import behaviors as editor_behaviors
from editor.dialog_data import _load_dialogos
from editor.dialog_tree_panel import DialogTreePanel
from editor.character_data import _load_characters
from editor.character_panel import CharacterPanel
from editor.asset_data import _load_assets
from editor.asset_panel import AssetPanel
from editor.scene_data import _load_scenes
from editor.scene_panel import ScenePanel
from editor.minigame_data import _load_minigames
from editor.minigame_panel import MiniGamePanel
from editor.audio_data import _load_audio
from editor.audio_panel import AudioPanel
from editor.menu_data import _load_menus
from editor.menu_panel import MenuTab


PANEL_CLASSES = {
    "sprites": SpriteEditorPanel,
    "elements": ElementTab,
    "abilities": AbilityTab,
    "items": ItemTab,
    "bosses": BossTab,
    "maps": MapEditorPanel,
    "events": EventEditorPanel,
    "animations": AnimationPanel,
    "scripts": ScriptPanel,
    "behaviors": CustomBehaviorsPanel,
    "screens": ScreensPanel,
    "dialogos": DialogTreePanel,
    "characters": CharacterPanel,
    "assets": AssetPanel,
    "scenes": ScenePanel,
    "minigames": MiniGamePanel,
    "audio": AudioPanel,
    "menus": MenuTab,
}

MENUBAR_H = 26


def _work_area():
    try:
        import ctypes
        from ctypes import wintypes

        rect = wintypes.RECT()
        if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
            return rect.left, rect.top, rect.right, rect.bottom
    except Exception:
        pass
    return None


def _clamp_window_pos(x, y, w, h):
    if x is None or y is None:
        return x, y
    area = _work_area()
    if not area:
        return x, y
    left, top, right, bottom = area
    area_w, area_h = right - left, bottom - top
    if w <= area_w:
        x = min(max(x, left), right - w)
    else:
        x = left
    if h <= area_h:
        y = min(max(y, top), bottom - h)
    else:
        y = top
    return x, y


def _is_maximized():
    try:
        import ctypes
        from ctypes import wintypes

        info = pygame.display.get_wm_info()
        hwnd = info.get("window")
        if not hwnd:
            return None

        class _WINDOWPLACEMENT(ctypes.Structure):
            _fields_ = [
                ("length", wintypes.UINT),
                ("flags", wintypes.UINT),
                ("showCmd", wintypes.UINT),
                ("ptMinPosition", wintypes.POINT),
                ("ptMaxPosition", wintypes.POINT),
                ("rcNormalPosition", wintypes.RECT),
            ]

        placement = _WINDOWPLACEMENT()
        placement.length = ctypes.sizeof(_WINDOWPLACEMENT)
        if not ctypes.windll.user32.GetWindowPlacement(hwnd, ctypes.byref(placement)):
            return None
        return placement.showCmd == 3
    except Exception:
        return None


def _restore_fallback_maximize(x, y, w, h):
    try:
        px, py = _clamp_window_pos(x, y, w, h)
        pygame.display.set_mode((w, h), pygame.RESIZABLE)
        pygame.display.set_window_position((px, py))
    except pygame.error:
        pass


class EditorApp:
    def __init__(self):
        pygame.init()
        _load_elements()
        _load_abilities()
        _load_items()
        _load_bosses()
        _load_animations()
        _load_dialogos()
        _load_characters()
        _load_assets()
        _load_scenes()
        _load_minigames()
        _load_audio()
        _load_menus()
        editor_behaviors._load()
        self.ancho = 1100
        self.alto = 700
        self.screen = pygame.display.set_mode((self.ancho, self.alto), pygame.RESIZABLE)
        pygame.display.set_caption("Cururo Editor")
        self.clock = pygame.time.Clock()
        self.running = True
        self.i18n = I18n("es")
        self.lang_bar = [("ES", "es"), ("EN", "en")]

        self.menu_bar = self._crear_menu_bar()
        self.menu = self._crear_menu_manager()
        self.restore_workspace()

    # ── Acciones del menú ─────────────────────────────────

    def _open_panel(self, panel_id):
        self.menu.set_active_by_id(panel_id)
        self.menu.get_active_panel()

    def nuevo_proyecto(self):
        import pygame
        from editor.project import create_project, list_templates, set_current_project
        from editor.elements import _load_elements
        from editor.behaviors import _load as _load_behaviors
        from editor.categories import get_all_categories

        all_categories = get_all_categories()
        templates = list_templates()
        if not all_categories or not templates:
            return

        PLATFORMS = [("desktop", "Escritorio"), ("mobile", "Movil")]
        QUALITIES = [("low", "Baja"), ("medium", "Media"), ("high", "Alta")]

        name = ""
        title = ""
        sel_cat_idx = 0
        sel_tpl_idx = 0
        sel_plat_idx = 0
        sel_qual_idx = 1
        error = ""
        done = False
        result_path = None
        focus = "name"

        def _templates_for_cat():
            cat_id = all_categories[sel_cat_idx]["id"]
            return [t for t in templates if t.get("category") == cat_id]

        font = self.i18n.fuente(16)
        font_b = self.i18n.fuente(16, bold=True)
        font_small = self.i18n.fuente(12)

        dialog_w, dialog_h = 450, 560
        dx = (self.ancho - dialog_w) // 2
        dy = (self.alto - dialog_h) // 2
        top = dy

        cat_start = top + 146
        cat_h = 30
        tpl_start = cat_start + len(all_categories) * cat_h + 16
        tpl_h = 24
        opt_h = 22
        plat_start = tpl_start + 24 + 12
        qual_start = plat_start + len(PLATFORMS) * opt_h + 12
        title_label = qual_start + len(QUALITIES) * opt_h + 14
        title_input_y = title_label + 22

        cx_center = self.ancho // 2
        create_btn = pygame.Rect(0, 0, 110, 30)
        create_btn.center = (cx_center - 60, dy + dialog_h - 50)
        cancel_btn = pygame.Rect(0, 0, 110, 30)
        cancel_btn.center = (cx_center + 60, dy + dialog_h - 50)

        _order = ["name", "cat", "template", "platform", "quality", "title"]

        def _next_focus():
            return _order[(_order.index(focus) + 1) % len(_order)]

        def _prev_focus():
            return _order[(_order.index(focus) - 1) % len(_order)]

        def _do_create():
            nonlocal result_path, done, error
            if not name.strip():
                error = "El nombre no puede estar vacio"
                return
            available = _templates_for_cat()
            if not available:
                error = "Sin plantillas para esta categoria"
                return
            tpl = available[sel_tpl_idx]
            safe = name.strip().lower().replace(" ", "_").replace("-", "_")
            search_dir = _default_projects_dir()
            path = os.path.join(search_dir, safe)
            n = 1
            while os.path.exists(path):
                path = os.path.join(search_dir, f"{safe}_{n}")
                n += 1
            r = create_project(
                tpl["id"], name.strip(), path,
                platform=PLATFORMS[sel_plat_idx][0],
                quality=QUALITIES[sel_qual_idx][0],
                window_title=title.strip() or None,
            )
            if r:
                result_path = r
                done = True
            else:
                error = "Error al crear proyecto"

        while not done:
            for event in pygame.event.get([pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.QUIT]):
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        if focus == "name":
                            done = True
                            result_path = None
                        else:
                            focus = _prev_focus()
                    elif event.key == pygame.K_RETURN:
                        if focus == "name":
                            if name.strip():
                                focus = "cat"
                        elif focus == "cat":
                            focus = "template"
                        elif focus == "template":
                            focus = "platform"
                        elif focus == "platform":
                            focus = "quality"
                        elif focus == "quality":
                            focus = "title"
                        elif focus == "title":
                            _do_create()
                    elif event.key == pygame.K_TAB:
                        focus = _next_focus()
                    elif event.key == pygame.K_UP:
                        if focus == "cat":
                            sel_cat_idx = max(0, sel_cat_idx - 1)
                            sel_tpl_idx = 0
                        elif focus == "template":
                            sel_tpl_idx = max(0, sel_tpl_idx - 1)
                        elif focus == "platform":
                            sel_plat_idx = max(0, sel_plat_idx - 1)
                        elif focus == "quality":
                            sel_qual_idx = max(0, sel_qual_idx - 1)
                    elif event.key == pygame.K_DOWN:
                        if focus == "cat":
                            sel_cat_idx = min(len(all_categories) - 1, sel_cat_idx + 1)
                            sel_tpl_idx = 0
                        elif focus == "template":
                            available = _templates_for_cat()
                            sel_tpl_idx = min(len(available) - 1, sel_tpl_idx + 1)
                        elif focus == "platform":
                            sel_plat_idx = min(len(PLATFORMS) - 1, sel_plat_idx + 1)
                        elif focus == "quality":
                            sel_qual_idx = min(len(QUALITIES) - 1, sel_qual_idx + 1)
                    elif event.key == pygame.K_BACKSPACE:
                        if focus == "name":
                            name = name[:-1]
                        elif focus == "title":
                            title = title[:-1]
                    elif event.unicode:
                        if focus == "name" and len(name) < 40:
                            name += event.unicode
                        elif focus == "title" and len(title) < 60:
                            title += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    input_rect = pygame.Rect(0, 0, 300, 30)
                    input_rect.center = (cx_center, top + 100)
                    if input_rect.collidepoint(mx, my):
                        focus = "name"
                    for i, cat in enumerate(all_categories):
                        ry = cat_start + i * cat_h
                        if dx + 30 <= mx <= dx + dialog_w - 30 and ry <= my <= ry + cat_h - 2:
                            sel_cat_idx = i
                            sel_tpl_idx = 0
                            focus = "cat"
                    available = _templates_for_cat()
                    for i, tpl in enumerate(available):
                        ry = tpl_start + i * tpl_h
                        if dx + 30 <= mx <= dx + dialog_w - 30 and ry <= my <= ry + tpl_h - 2:
                            sel_tpl_idx = i
                            focus = "template"
                    for i, plat in enumerate(PLATFORMS):
                        ry = plat_start + i * opt_h
                        if dx + 30 <= mx <= dx + dialog_w - 30 and ry <= my <= ry + opt_h - 2:
                            sel_plat_idx = i
                            focus = "platform"
                    for i, qual in enumerate(QUALITIES):
                        ry = qual_start + i * opt_h
                        if dx + 30 <= mx <= dx + dialog_w - 30 and ry <= my <= ry + opt_h - 2:
                            sel_qual_idx = i
                            focus = "quality"
                    t_input = pygame.Rect(dx + 40, title_input_y, dialog_w - 80, 26)
                    if t_input.collidepoint(mx, my):
                        focus = "title"
                    if create_btn.collidepoint(mx, my) and name.strip():
                        _do_create()
                    if cancel_btn.collidepoint(mx, my):
                        done = True
                        result_path = None

            overlay = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            pygame.draw.rect(self.screen, (40, 44, 52), (dx, dy, dialog_w, dialog_h))
            pygame.draw.rect(self.screen, (60, 65, 75), (dx, dy, dialog_w, dialog_h), 2)

            dialog_title = font_b.render("Nuevo Proyecto", True, (200, 210, 220))
            self.screen.blit(dialog_title, (cx_center - dialog_title.get_width() // 2, dy + 16))

            if error:
                err = font.render(error, True, (220, 80, 80))
                self.screen.blit(err, (cx_center - err.get_width() // 2, dy + 44))

            lbl = font.render("Nombre:", True, (180, 190, 200))
            self.screen.blit(lbl, (dx + 30, top + 64))

            input_rect = pygame.Rect(0, 0, 300, 30)
            input_rect.center = (cx_center, top + 100)
            border_c = (70, 130, 200) if focus == "name" else (60, 65, 75)
            pygame.draw.rect(self.screen, (50, 55, 65), input_rect)
            pygame.draw.rect(self.screen, border_c, input_rect, 2)
            display = name + ("|" if focus == "name" and pygame.time.get_ticks() % 600 < 300 else " ")
            txt = font.render(display, True, (220, 220, 220))
            self.screen.blit(txt, (input_rect.x + 6, input_rect.y + 4))

            cat_lbl = font_small.render("Categoria:", True, (150, 170, 200))
            self.screen.blit(cat_lbl, (dx + 30, cat_start - 18))

            for i, cat in enumerate(all_categories):
                ry = cat_start + i * cat_h
                sel = i == sel_cat_idx
                fcs = focus == "cat" and sel
                bg = (55, 70, 90) if fcs else (42, 55, 70)
                pygame.draw.rect(self.screen, bg, (dx + 30, ry, dialog_w - 60, cat_h - 2))
                if fcs:
                    pygame.draw.rect(self.screen, (70, 160, 220), (dx + 30, ry, 3, cat_h - 2))
                elif sel:
                    pygame.draw.rect(self.screen, (50, 100, 140), (dx + 30, ry, 3, cat_h - 2))
                cname = font_small.render(cat["name"], True, (200, 210, 220))
                self.screen.blit(cname, (dx + 40, ry + 4))

            tpl_lbl = font_small.render("Plantilla:", True, (150, 170, 200))
            self.screen.blit(tpl_lbl, (dx + 30, tpl_start - 18))

            available = _templates_for_cat()
            if not available:
                no_tpl = font_small.render("(sin plantillas)", True, (120, 130, 140))
                self.screen.blit(no_tpl, (dx + 40, tpl_start))
            else:
                for i, tpl in enumerate(available):
                    ry = tpl_start + i * tpl_h
                    sel = i == sel_tpl_idx
                    fcs = focus == "template" and sel
                    bg = (55, 60, 72) if fcs else (45, 48, 55)
                    pygame.draw.rect(self.screen, bg, (dx + 30, ry, dialog_w - 60, tpl_h - 2))
                    if fcs:
                        pygame.draw.rect(self.screen, (70, 130, 200), (dx + 30, ry, 3, tpl_h - 2))
                    tname = font_small.render(tpl["name"], True, (180, 200, 230))
                    self.screen.blit(tname, (dx + 40, ry + 2))

            plat_lbl = font_small.render("Plataforma:", True, (150, 170, 200))
            self.screen.blit(plat_lbl, (dx + 30, plat_start - 18))
            for i, plat in enumerate(PLATFORMS):
                ry = plat_start + i * opt_h
                sel = i == sel_plat_idx
                fcs = focus == "platform" and sel
                bg = (55, 70, 90) if fcs else (42, 55, 70)
                pygame.draw.rect(self.screen, bg, (dx + 30, ry, dialog_w - 60, opt_h - 2))
                if fcs:
                    pygame.draw.rect(self.screen, (70, 160, 220), (dx + 30, ry, 3, opt_h - 2))
                elif sel:
                    pygame.draw.rect(self.screen, (50, 100, 140), (dx + 30, ry, 3, opt_h - 2))
                ptxt = font_small.render(plat[1], True, (200, 210, 220))
                self.screen.blit(ptxt, (dx + 40, ry + 2))

            qual_lbl = font_small.render("Calidad grafica:", True, (150, 170, 200))
            self.screen.blit(qual_lbl, (dx + 30, qual_start - 18))
            for i, qual in enumerate(QUALITIES):
                ry = qual_start + i * opt_h
                sel = i == sel_qual_idx
                fcs = focus == "quality" and sel
                bg = (55, 70, 90) if fcs else (42, 55, 70)
                pygame.draw.rect(self.screen, bg, (dx + 30, ry, dialog_w - 60, opt_h - 2))
                if fcs:
                    pygame.draw.rect(self.screen, (70, 160, 220), (dx + 30, ry, 3, opt_h - 2))
                elif sel:
                    pygame.draw.rect(self.screen, (50, 100, 140), (dx + 30, ry, 3, opt_h - 2))
                qtxt = font_small.render(qual[1], True, (200, 210, 220))
                self.screen.blit(qtxt, (dx + 40, ry + 2))

            title_lbl = font_small.render("Titulo de ventana (opcional):", True, (150, 170, 200))
            self.screen.blit(title_lbl, (dx + 30, title_label))
            t_input = pygame.Rect(dx + 40, title_input_y, dialog_w - 80, 26)
            t_color = (70, 130, 200) if focus == "title" else (60, 65, 75)
            pygame.draw.rect(self.screen, (50, 55, 65), t_input)
            pygame.draw.rect(self.screen, t_color, t_input, 2)
            t_disp = title + ("|" if focus == "title" and pygame.time.get_ticks() % 600 < 300 else " ")
            t_txt = font_small.render(t_disp, True, (220, 220, 220))
            self.screen.blit(t_txt, (t_input.x + 6, t_input.y + 4))

            pygame.draw.rect(self.screen, (50, 100, 50), create_btn)
            pygame.draw.rect(self.screen, (70, 140, 70), create_btn, 2)
            ct = font.render("Crear", True, (220, 220, 220))
            self.screen.blit(ct, (create_btn.centerx - ct.get_width() // 2,
                                  create_btn.centery - ct.get_height() // 2))

            pygame.draw.rect(self.screen, (60, 60, 65), cancel_btn)
            pygame.draw.rect(self.screen, (75, 75, 80), cancel_btn, 2)
            et = font.render("Cancelar", True, (180, 180, 185))
            self.screen.blit(et, (cancel_btn.centerx - et.get_width() // 2,
                                  cancel_btn.centery - et.get_height() // 2))

            pygame.display.flip()
            self.clock.tick(30)

        if result_path:
            set_current_project(result_path)
            _load_elements()
            _load_behaviors()
            self._rebuild_ui()
            self.save_workspace()

    def abrir_proyecto(self):
        """Abre un selector de carpeta y carga el proyecto elegido."""
        import tkinter as tk
        from tkinter import filedialog, messagebox

        from editor.project import set_current_project
        from editor.elements import _load_elements
        from editor.behaviors import _load as _load_behaviors

        root = tk.Tk()
        root.withdraw()
        root.update()
        try:
            folder = filedialog.askdirectory(
                title="Abrir Proyecto",
                initialdir=_default_projects_dir(),
            )
        finally:
            root.destroy()
        if not folder:
            return
        if not os.path.isfile(os.path.join(folder, "cururo.json")):
            messagebox.showerror(
                "Abrir Proyecto",
                "La carpeta no contiene un proyecto (falta cururo.json).",
            )
            return
        self.save_workspace()
        set_current_project(folder)
        _load_elements()
        _load_behaviors()
        self._rebuild_ui()
        self.save_workspace()

    def guardar(self):
        self.save_workspace()
        print("[Menu] Guardado")

    def guardar_como(self):
        print("[Menu] Guardar Como...")

    def exportar(self):
        """Exporta el juego como ejecutable standalone con PyInstaller"""
        if _FROZEN:
            print("[Export] No disponible en la version compilada del editor")
            return
        self.save_workspace()
        from editor.project import get_current_project
        proj = get_current_project()
        if not proj:
            print("[Export] No hay proyecto abierto")
            return
        editor_root = os.path.dirname(os.path.abspath(__file__))
        orm_root = os.path.join(os.path.dirname(editor_root), "orm")
        if not os.path.exists(orm_root):
            print(f"[Export] No se encuentra el runtime ORM en {orm_root}")
            return
        target = os.path.join(proj, "export")
        import subprocess, shutil
        if os.path.exists(target):
            shutil.rmtree(target)
        os.makedirs(target)

        dirs = [
            "configs", "data", "domain", "entities", "handlers",
            "levels", "managers", "repositories", "runtime",
            "scripts", "services", "systems", "utils",
        ]
        datas = ",".join(
            f"(r'{os.path.join(orm_root, d)}', '{d}')" for d in dirs
        )
        assets_dir = os.path.join(orm_root, "assets")
        has_assets = os.path.isdir(assets_dir) and any(
            fname.lower().endswith((".png", ".jpg", ".gif", ".bmp"))
            for fname in os.listdir(assets_dir)
        )
        if has_assets:
            datas += f",(r'{assets_dir}', 'assets')"

        spec = f"""# -*- mode: python ; coding: utf-8 -*-
block_cipher = None
a = Analysis(
    ['main.py'],
    pathex=[r'{orm_root}'],
    binaries=[],
    datas=[{datas}],
    hiddenimports=['pygame'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)
pyd = PYZ(a.pure, a.zipped_data, cipher=block_cipher)
exe = EXE(
    pyd, a.scripts, a.binaries, a.zipfiles, a.datas, [],
    name='ORM',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=False,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"""
        spec_path = os.path.join(target, "build.spec")
        with open(spec_path, "w", encoding="utf-8") as f:
            f.write(spec)

        print(f"[Export] Generando ejecutable en {target} ...")
        try:
            result = subprocess.run(
                [sys.executable, "-m", "PyInstaller", spec_path,
                 "--distpath", target, "--workpath",
                 os.path.join(target, ".build"), "--noconfirm"],
                cwd=orm_root, capture_output=True, text=True, timeout=300
            )
        except subprocess.TimeoutExpired:
            import tkinter.messagebox as mb
            mb.showerror("Exportar", "Tiempo de espera agotado (5 min)")
            return
        if result.returncode != 0:
            print(f"[Export] Error:\n{result.stderr}")
            import tkinter.messagebox as mb
            mb.showerror("Exportar", f"Error al exportar:\n{result.stderr[-500:]}")
            return

        for p in (os.path.join(target, ".build"), spec_path):
            if os.path.exists(p):
                (shutil.rmtree if os.path.isdir(p) else os.remove)(p)

        exe_name = "ORM.exe"
        exe_path = os.path.join(target, exe_name)
        if not os.path.exists(exe_path):
            for item in os.listdir(target):
                full = os.path.join(target, item)
                candidate = os.path.join(full, exe_name) if os.path.isdir(full) else full
                if os.path.isfile(candidate) and candidate.endswith(".exe"):
                    shutil.move(candidate, exe_path)
                    if os.path.isdir(full):
                        shutil.rmtree(full)
                    break
        if os.path.exists(exe_path):
            os.startfile(target)
            import tkinter.messagebox as mb
            mb.showinfo("Exportar", f"Ejecutable generado:\n{target}\\ORM.exe")
        else:
            print(f"[Export] No se encontró el ejecutable en {target}")

    def salir(self):
        self.save_workspace()
        self.running = False

    def run_game(self):
        import subprocess, sys, os
        from editor.project import get_current_project
        p = get_current_project()
        if p is None:
            print("[Menu] No hay proyecto seleccionado")
            return
        if _FROZEN:
            exe = sys.executable
            subprocess.Popen(
                [exe, "--runtime", "--project", p.root],
                cwd=os.path.dirname(exe),
                creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
            )
            return
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        main_py = os.path.join(root, "orm", "main.py")
        if not os.path.exists(main_py):
            print(f"[Menu] No se encuentra {main_py}")
            return
        subprocess.Popen(
            [sys.executable, main_py, "--project", p.root],
            cwd=root,
            creationflags=subprocess.CREATE_NEW_CONSOLE if sys.platform == "win32" else 0,
        )

    def _undo_redo_event(self, key):
        panel = self.menu.get_active_panel()
        if panel and hasattr(panel, "handle_event"):
            import pygame
            mod = pygame.KMOD_CTRL
            fake = pygame.event.Event(pygame.KEYDOWN, key=key, mod=mod)
            panel.handle_event(fake)

    def deshacer(self):
        import pygame
        self._undo_redo_event(pygame.K_z)

    def rehacer(self):
        import pygame
        self._undo_redo_event(pygame.K_y)

    def preferencias(self):
        print("[Menu] Preferencias...")

    def acerca_de(self):
        print("[Menu] Acerca de Cururo")

    # ── Atajos de teclado ────────────────────────────────

    KEYBOARD_SHORTCUTS = {
        (pygame.KMOD_CTRL, pygame.K_n): "nuevo_proyecto",
        (pygame.KMOD_CTRL, pygame.K_o): "abrir_proyecto",
        (pygame.KMOD_CTRL, pygame.K_s): "guardar",
        (pygame.KMOD_CTRL | pygame.KMOD_SHIFT, pygame.K_s): "guardar_como",
        (pygame.KMOD_CTRL, pygame.K_e): "exportar",
        (pygame.KMOD_CTRL, pygame.K_COMMA): "preferencias",
        (pygame.KMOD_CTRL, pygame.K_1): "_open_panel_sprites",
        (pygame.KMOD_CTRL, pygame.K_2): "_open_panel_maps",
        (pygame.KMOD_CTRL, pygame.K_3): "_open_panel_animations",
        (pygame.KMOD_CTRL, pygame.K_r): "run_game",
    }

    def _handle_shortcuts(self, event):
        if event.type != pygame.KEYDOWN:
            return False
        mods = 0
        if event.mod & pygame.KMOD_CTRL: mods |= pygame.KMOD_CTRL
        if event.mod & pygame.KMOD_SHIFT: mods |= pygame.KMOD_SHIFT
        if event.mod & pygame.KMOD_ALT: mods |= pygame.KMOD_ALT
        action = self.KEYBOARD_SHORTCUTS.get((mods, event.key))
        if action:
            if action == "_open_panel_sprites":
                self._open_panel("sprites")
            elif action == "_open_panel_maps":
                self._open_panel("maps")
            elif action == "_open_panel_animations":
                self._open_panel("animations")
            else:
                getattr(self, action)()
            return True
        return False

    # ── Construcción de UI ────────────────────────────────

    def _crear_menu_bar(self):
        mb = MenuBar(0, 0, self.ancho)
        available = self._get_available_panels()

        archivo_items = [
            MenuItem("Nuevo Proyecto", action=self.nuevo_proyecto, shortcut="Ctrl+N"),
            MenuItem("Abrir Proyecto...", action=self.abrir_proyecto, shortcut="Ctrl+O"),
            MenuItem("Guardar", action=self.guardar, shortcut="Ctrl+S"),
            MenuItem("Guardar Como...", action=self.guardar_como, shortcut="Ctrl+Shift+S"),
        ]
        if not _FROZEN:
            archivo_items.append(MenuItem(separator_before=True, label="Exportar...", action=self.exportar, shortcut="Ctrl+E"))
        archivo_items.append(MenuItem(separator_before=True, label="Salir", action=self.salir, shortcut="Alt+F4"))
        archivo = MenuSection("Archivo", archivo_items)
        mb.add_section(archivo.label, archivo.items)

        editar = MenuSection("Editar", [
            MenuItem("Deshacer", action=self.deshacer, shortcut="Ctrl+Z"),
            MenuItem("Rehacer", action=self.rehacer, shortcut="Ctrl+Y"),
            MenuItem(separator_before=True, label="Preferencias...", action=self.preferencias, shortcut="Ctrl+,"),
        ])
        mb.add_section(editar.label, editar.items)

        mundo_items = []
        if "maps" in available:
            mundo_items.append(MenuItem("Mapas", action=lambda: self._open_panel("maps"), shortcut="Ctrl+2"))
        if "scenes" in available:
            mundo_items.append(MenuItem("Escenas", action=lambda: self._open_panel("scenes")))
        if "screens" in available:
            mundo_items.append(MenuItem("Pantallas", action=lambda: self._open_panel("screens")))
        if "characters" in available:
            mundo_items.append(MenuItem("Personajes", action=lambda: self._open_panel("characters")))
        if mundo_items:
            mundo = MenuSection("Mundo", mundo_items)
            mb.add_section(mundo.label, mundo.items)

        contenido_items = []
        for pid in ("elements", "items", "abilities", "bosses", "behaviors", "events", "dialogos", "menus"):
            if pid in available:
                label = {
                    "elements": "Elementos",
                    "items": "Items",
                    "abilities": "Habilidades",
                    "bosses": "Bosses",
                    "behaviors": "Comportamientos",
                    "events": "Eventos",
                    "dialogos": "Dialogos",
                    "menus": "Menús",
                }[pid]
                contenido_items.append(
                    MenuItem(label, action=lambda pid=pid: self._open_panel(pid))
                )
        if contenido_items:
            contenido = MenuSection("Contenido", contenido_items)
            mb.add_section(contenido.label, contenido.items)

        arte_items = []
        if "sprites" in available:
            arte_items.append(MenuItem("Sprites", action=lambda: self._open_panel("sprites"), shortcut="Ctrl+1"))
        if "animations" in available:
            arte_items.append(MenuItem("Animaciones", action=lambda: self._open_panel("animations"), shortcut="Ctrl+3"))
        if "assets" in available:
            arte_items.append(MenuItem("Assets", action=lambda: self._open_panel("assets")))
        if arte_items:
            arte = MenuSection("Arte", arte_items)
            mb.add_section(arte.label, arte.items)

        if "audio" in available:
            mb.add_section("Audio", [MenuItem("Audio", action=lambda: self._open_panel("audio"))])

        if "minigames" in available:
            mb.add_section("Minijuegos", [MenuItem("Minijuegos", action=lambda: self._open_panel("minigames"))])

        if "scripts" in available:
            mb.add_section("Scripts", [MenuItem("Scripts", action=lambda: self._open_panel("scripts"))])

        ejecutar = MenuSection("Ejecutar", [
            MenuItem("Iniciar juego", action=self.run_game, shortcut="Ctrl+R"),
        ])
        mb.add_section(ejecutar.label, ejecutar.items)

        ayuda = MenuSection("Ayuda", [
            MenuItem("Acerca de Cururo", action=self.acerca_de),
        ])
        mb.add_section(ayuda.label, ayuda.items)

        return mb

    def _get_available_panels(self):
        from editor.project import get_current_project
        proj = get_current_project()
        if proj:
            return set(proj.get_available_panels())
        return set(PANEL_CLASSES.keys())

    def _crear_menu_manager(self):
        m = MenuManager(0, MENUBAR_H, self.ancho, self.alto - MENUBAR_H)
        available = self._get_available_panels()
        for tab_id, cls in PANEL_CLASSES.items():
            if tab_id in available:
                m.register_tab(tab_id, self.i18n.t(f"tab.{tab_id}"), cls, self.i18n)
        return m

    def _rebuild_ui(self):
        from editor import behaviors as editor_behaviors
        editor_behaviors._load()
        active_id = self.menu.get_active_id()
        self.menu = self._crear_menu_manager()
        if active_id:
            self.menu.set_active_by_id(active_id)
            self.menu.get_active_panel()

    def _resize(self, w, h):
        self.ancho = w
        self.alto = h
        self.menu_bar.set_size(w, MENUBAR_H)
        self.menu.set_size(w, h - MENUBAR_H)

    # ── Workspace ─────────────────────────────────────────

    def save_workspace(self):
        win = {"w": self.ancho, "h": self.alto}
        try:
            if pygame.display.get_init():
                x, y = pygame.display.get_window_position()
                if x > -10000 or y > -10000:
                    win["x"], win["y"] = x, y
        except pygame.error:
            pass
        max_info = _is_maximized()
        if max_info is not None:
            win["maximized"] = max_info
        data = {
            "active_panel": self.menu.get_active_id(),
            "language": self.i18n.lang,
            "window": win,
        }
        available = self._get_available_panels()
        if "maps" in available:
            maps_panel = self.menu._panel_instances.get("maps")
            if maps_panel and hasattr(maps_panel, "get_workspace_data"):
                data["maps"] = maps_panel.get_workspace_data()
        workspace.save_workspace(data)

    def restore_workspace(self):
        data = workspace.load_workspace()
        if not data:
            return
        lang = data.get("language", "es")
        self.i18n.set_lang(lang)
        self.menu = self._crear_menu_manager()
        win = data.get("window", {})
        if win.get("w") and win.get("h"):
            self.ancho = win["w"]
            self.alto = win["h"]
            self.screen = pygame.display.set_mode((self.ancho, self.alto), pygame.RESIZABLE)
            self._resize(self.ancho, self.alto)
            x = win.get("x")
            y = win.get("y")
            if win.get("maximized"):
                try:
                    import pygame._sdl2 as _sdl2
                    _sdl2.Window.from_display_module().maximize()
                except Exception:
                    _restore_fallback_maximize(x, y, self.ancho, self.alto)
            elif x is not None and y is not None:
                try:
                    px, py = _clamp_window_pos(x, y, self.ancho, self.alto)
                    pygame.display.set_window_position((px, py))
                except pygame.error:
                    pass
        panel_id = data.get("active_panel", "maps")
        available = self._get_available_panels()
        if panel_id not in available:
            panel_id = next(iter(available), "maps")
        self.menu.set_active_by_id(panel_id)
        self.menu.get_active_panel()
        if "maps" in available:
            maps_panel = self.menu._get_or_create_panel("maps")
            maps_data = data.get("maps")
            if maps_data and maps_panel and hasattr(maps_panel, "restore_workspace"):
                maps_panel.restore_workspace(maps_data)

    # ── Selector de idioma ────────────────────────────────

    def _draw_lang_selector(self):
        fuente = self.i18n.fuente(11)
        lx = self.ancho - 80
        for lname, lcode in self.lang_bar:
            active = self.i18n.lang == lcode
            c = (70, 130, 200) if active else (50, 55, 65)
            pygame.draw.rect(self.screen, c, (lx, self.alto - 24, 36, 20))
            pygame.draw.rect(self.screen, (80, 90, 105), (lx, self.alto - 24, 36, 20), 1)
            txt = fuente.render(lname, True, (220, 220, 220))
            self.screen.blit(txt, (lx + (36 - txt.get_width()) // 2, self.alto - 22))
            lx += 40

    # ── Loop principal ────────────────────────────────────

    def run(self):
        while self.running:
            time_delta = self.clock.tick(60) / 1000.0

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.save_workspace()
                    self.running = False
                elif event.type == pygame.VIDEORESIZE:
                    w, h = event.w, event.h
                    self.screen = pygame.display.set_mode((w, h), pygame.RESIZABLE)
                    self._resize(w, h)

                # Shortcuts (before menu bar, so they work even with menu open)
                if self._handle_shortcuts(event):
                    continue

                # Menu bar first (dropdowns consume events while open)
                if self.menu_bar.handle_event(event):
                    continue

                # If menu bar dropdown is open, don't pass to panels
                if self.menu_bar.is_open():
                    continue

                self.menu.handle_event(event)

                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    mx, my = event.pos
                    lx = self.ancho - 80
                    for lname, lcode in self.lang_bar:
                        if lx <= mx <= lx + 36 and self.alto - 24 <= my <= self.alto - 4:
                            self.i18n.set_lang(lcode)
                            self._rebuild_ui()
                            break
                        lx += 40

            self.menu.update(time_delta)

            self.screen.fill((25, 28, 32))
            self.menu_bar.draw(self.screen)
            self.menu.draw(self.screen)
            self.menu_bar.draw_dropdown(self.screen)
            self._draw_lang_selector()

            # Process menu bar actions that open panels (deferred)
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    app = EditorApp()
    app.run()
