#!/usr/bin/env python3
import sys
import os

_editor_root = os.path.dirname(os.path.abspath(__file__))
_src_root = os.path.dirname(_editor_root)
if _src_root not in sys.path:
    sys.path.insert(0, _src_root)

project_root = None
if len(sys.argv) > 1:
    project_root = os.path.abspath(sys.argv[1])
else:
    from editor.project_dialog import ProjectDialog
    search_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    dialog = ProjectDialog(search_dir)
    project_root = dialog.run()

if not project_root:
    print("No se selecciono ningun proyecto. Saliendo.")
    sys.exit(0)

from editor.project import set_current_project, sys_path_setup
sys_path_setup(project_root)
set_current_project(project_root)

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
from editor.dialog_tab import DialogTab


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
    "dialogos": DialogTab,
}

MENUBAR_H = 26


class EditorApp:
    def __init__(self):
        pygame.init()
        _load_elements()
        _load_abilities()
        _load_items()
        _load_bosses()
        _load_animations()
        _load_dialogos()
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

        templates = list_templates()
        if not templates:
            return

        name = ""
        template_id = templates[0]["id"]
        error = ""
        done = False
        result_path = None

        font = self.i18n.fuente(16)
        font_b = self.i18n.fuente(16, bold=True)
        font_small = self.i18n.fuente(12)

        input_rect = pygame.Rect(0, 0, 300, 30)
        create_btn = pygame.Rect(0, 0, 100, 30)
        cancel_btn = pygame.Rect(0, 0, 100, 30)
        dialog_w, dialog_h = 400, 250
        dx = (self.ancho - dialog_w) // 2
        dy = (self.alto - dialog_h) // 2

        while not done:
            for event in pygame.event.get([pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN, pygame.QUIT]):
                if event.type == pygame.QUIT:
                    return
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_ESCAPE:
                        done = True
                        result_path = None
                    elif event.key == pygame.K_RETURN:
                        if name.strip():
                            safe = name.strip().lower().replace(" ", "_").replace("-", "_")
                            search_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                            path = os.path.join(search_dir, safe)
                            n = 1
                            while os.path.exists(path):
                                path = os.path.join(search_dir, f"{safe}_{n}")
                                n += 1
                            r = create_project(template_id, name.strip(), path)
                            if r:
                                result_path = r
                                done = True
                            else:
                                error = "Error al crear proyecto"
                    elif event.key == pygame.K_TAB:
                        idx = next((i for i, t in enumerate(templates)
                                    if t["id"] == template_id), 0)
                        template_id = templates[(idx + 1) % len(templates)]["id"]
                    elif event.key == pygame.K_BACKSPACE:
                        name = name[:-1]
                    elif event.unicode and len(name) < 40:
                        name += event.unicode
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    mx, my = event.pos
                    cx = self.ancho // 2
                    cy = self.alto // 2
                    input_rect.center = (cx, cy - 30)
                    create_btn.center = (cx - 60, cy + 40)
                    cancel_btn.center = (cx + 60, cy + 40)
                    if create_btn.collidepoint(mx, my) and name.strip():
                        safe = name.strip().lower().replace(" ", "_").replace("-", "_")
                        search_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                        path = os.path.join(search_dir, safe)
                        n = 1
                        while os.path.exists(path):
                            path = os.path.join(search_dir, f"{safe}_{n}")
                            n += 1
                        r = create_project(template_id, name.strip(), path)
                        if r:
                            result_path = r
                            done = True
                        else:
                            error = "Error al crear proyecto"
                    elif cancel_btn.collidepoint(mx, my):
                        done = True
                        result_path = None

            overlay = pygame.Surface((self.ancho, self.alto), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            self.screen.blit(overlay, (0, 0))

            cx = self.ancho // 2
            cy = self.alto // 2
            input_rect.center = (cx, cy - 30)
            create_btn.center = (cx - 60, cy + 40)
            cancel_btn.center = (cx + 60, cy + 40)

            pygame.draw.rect(self.screen, (40, 44, 52), (dx, dy, dialog_w, dialog_h))
            pygame.draw.rect(self.screen, (60, 65, 75), (dx, dy, dialog_w, dialog_h), 2)

            title = font_b.render("Nuevo Proyecto", True, (200, 210, 220))
            self.screen.blit(title, (cx - title.get_width() // 2, dy + 20))

            lbl = font.render("Nombre:", True, (180, 190, 200))
            self.screen.blit(lbl, (dx + 30, cy - 60))

            pygame.draw.rect(self.screen, (50, 55, 65), input_rect)
            pygame.draw.rect(self.screen, (70, 130, 200), input_rect, 2)
            display = name + ("|" if pygame.time.get_ticks() % 600 < 300 else " ")
            txt = font.render(display, True, (220, 220, 220))
            self.screen.blit(txt, (input_rect.x + 6, input_rect.y + 4))

            tmpl_label = font_small.render(
                "Plantilla: " + next((t["name"] for t in templates
                                      if t["id"] == template_id), ""),
                True, (150, 170, 200))
            self.screen.blit(tmpl_label, (dx + 30, cy + 2))

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

            if error:
                err = font.render(error, True, (220, 80, 80))
                self.screen.blit(err, (cx - err.get_width() // 2, dy + dialog_h - 30))

            pygame.display.flip()
            self.clock.tick(30)

        if result_path:
            set_current_project(result_path)
            _load_elements()
            _load_behaviors()
            self._rebuild_ui()
            self.save_workspace()

    def abrir_proyecto(self):
        print("[Menu] Abrir Proyecto")

    def guardar(self):
        self.save_workspace()
        print("[Menu] Guardado")

    def guardar_como(self):
        print("[Menu] Guardar Como...")

    def exportar(self):
        """Exporta el juego como ejecutable standalone con PyInstaller"""
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
        root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        main_py = os.path.join(root, "orm", "main.py")
        if os.path.exists(main_py):
            subprocess.Popen([sys.executable, main_py, "--test"], cwd=root)
        else:
            print(f"[Menu] No se encuentra {main_py}")

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

        archivo = MenuSection("Archivo", [
            MenuItem("Nuevo Proyecto", action=self.nuevo_proyecto, shortcut="Ctrl+N"),
            MenuItem("Abrir Proyecto...", action=self.abrir_proyecto, shortcut="Ctrl+O"),
            MenuItem("Guardar", action=self.guardar, shortcut="Ctrl+S"),
            MenuItem("Guardar Como...", action=self.guardar_como, shortcut="Ctrl+Shift+S"),
            MenuItem(separator_before=True, label="Exportar...", action=self.exportar, shortcut="Ctrl+E"),
            MenuItem(separator_before=True, label="Salir", action=self.salir, shortcut="Alt+F4"),
        ])
        mb.add_section(archivo.label, archivo.items)

        editar = MenuSection("Editar", [
            MenuItem("Deshacer", action=self.deshacer, shortcut="Ctrl+Z"),
            MenuItem("Rehacer", action=self.rehacer, shortcut="Ctrl+Y"),
            MenuItem(separator_before=True, label="Preferencias...", action=self.preferencias, shortcut="Ctrl+,"),
        ])
        mb.add_section(editar.label, editar.items)

        arte = MenuSection("Arte", [
            MenuItem("Sprites", action=lambda: self._open_panel("sprites"), shortcut="Ctrl+1"),
            MenuItem("Mapas", action=lambda: self._open_panel("maps"), shortcut="Ctrl+2"),
            MenuItem("Animaciones", action=lambda: self._open_panel("animations"), shortcut="Ctrl+3"),
            MenuItem("Scripts", action=lambda: self._open_panel("scripts"), separator_before=True),
        ])
        mb.add_section(arte.label, arte.items)

        pantallas = MenuSection("Pantallas", [
            MenuItem("Pantallas", action=lambda: self._open_panel("screens")),
        ])
        mb.add_section(pantallas.label, pantallas.items)

        herramientas = MenuSection("Herramientas", [
            MenuItem("Elementos", action=lambda: self._open_panel("elements")),
            MenuItem("Comportamientos", action=lambda: self._open_panel("behaviors")),
            MenuItem("Habilidades", action=lambda: self._open_panel("abilities")),
            MenuItem("Items", action=lambda: self._open_panel("items")),
            MenuItem("Bosses", action=lambda: self._open_panel("bosses")),
            MenuItem("Eventos", action=lambda: self._open_panel("events")),
            MenuItem("Dialogos", action=lambda: self._open_panel("dialogos")),
        ])
        mb.add_section(herramientas.label, herramientas.items)

        ejecutar = MenuSection("Ejecutar", [
            MenuItem("Iniciar juego", action=self.run_game, shortcut="Ctrl+R"),
        ])
        mb.add_section(ejecutar.label, ejecutar.items)

        ayuda = MenuSection("Ayuda", [
            MenuItem("Acerca de Cururo", action=self.acerca_de),
        ])
        mb.add_section(ayuda.label, ayuda.items)

        return mb

    def _crear_menu_manager(self):
        m = MenuManager(0, MENUBAR_H, self.ancho, self.alto - MENUBAR_H)
        for tab_id, cls in PANEL_CLASSES.items():
            m.register_tab(tab_id, self.i18n.t(f"tab.{tab_id}"), cls, self.i18n)
        return m

    def _rebuild_ui(self):
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
        data = {
            "active_panel": self.menu.get_active_id(),
            "language": self.i18n.lang,
            "window": {"w": self.ancho, "h": self.alto},
        }
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
        panel_id = data.get("active_panel", "maps")
        self.menu.set_active_by_id(panel_id)
        self.menu.get_active_panel()
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
