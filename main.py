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
from editor.menu.manager import MenuManager
from editor.menu.bar import MenuBar
from editor.menu.item import MenuSection, MenuItem
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
from editor.widgets.message_bar import MessageBar
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
from editor.menu.data import _load_menus
from editor.menu.panel import MenuTab
from editor.monedas_panel import MonedasTab
from editor.contadores_panel import ContadoresTab
from editor.shops_panel import ShopsTab
from editor.global_events_panel import GlobalEventsTab
from editor.save_system_panel import SaveSystemTab


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
    "monedas": MonedasTab,
    "contadores": ContadoresTab,
    "shops": ShopsTab,
    "global_events": GlobalEventsTab,
    "save_system": SaveSystemTab,
}

MENUBAR_H = 26
MESSAGEBAR_H = 28
MIN_W = 720
MIN_H = 560


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
        self.message_bar = MessageBar(0, self.alto - MESSAGEBAR_H, self.ancho, MESSAGEBAR_H, right_margin=90)
        self.menu.set_notify_hook(self._notify)
        self.restore_workspace()

    # ── Acciones del menú ─────────────────────────────────

    def _open_panel(self, panel_id):
        self.menu.set_active_by_id(panel_id)
        self.menu.get_active_panel()

    def _notify(self, message, level="info"):
        self.message_bar.notify(message, level)

    def nuevo_proyecto(self):
        """Abre el diálogo de nuevo proyecto usando ProjectDialog."""
        from editor.project_dialog import ProjectDialog
        from editor.project import set_current_project
        from editor.elements import _load_elements
        from editor.behaviors import _load as _load_behaviors

        search_dir = _default_projects_dirs()
        dialog = ProjectDialog(search_dir)
        result_path = dialog.run()

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
        for pid in ("elements", "items", "abilities", "bosses", "behaviors", "events", "dialogos", "menus", "monedas", "shops", "contadores", "save_system"):
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
                    "monedas": "Monedas",
                    "shops": "Tiendas",
                    "contadores": "Contadores",
                    "save_system": "Sistema de Guardado",
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
        m = MenuManager(0, MENUBAR_H, self.ancho, self.alto - MENUBAR_H - MESSAGEBAR_H)
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
        self.menu.set_size(w, h - MENUBAR_H - MESSAGEBAR_H)
        self.message_bar.set_size(w, MESSAGEBAR_H)
        self.message_bar.set_pos(0, h - MESSAGEBAR_H)

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
        if "dialogos" in available:
            dlg_panel = self.menu._panel_instances.get("dialogos")
            if dlg_panel and hasattr(dlg_panel, "persistir_dialogos"):
                dlg_panel.persistir_dialogos()
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
                    import ctypes
                    hwnd = pygame.display.get_wm_info().get("window")
                    if hwnd:
                        ctypes.windll.user32.ShowWindow(hwnd, 3)  # SW_MAXIMIZE
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
                    w = max(MIN_W, event.w)
                    h = max(MIN_H, event.h)
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

                if self.message_bar.handle_event(event):
                    continue

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
            self.message_bar.update(time_delta)

            self.screen.fill((25, 28, 32))
            self.menu_bar.draw(self.screen)
            self.menu.draw(self.screen)
            self.menu_bar.draw_dropdown(self.screen)
            self.message_bar.draw(self.screen)
            self._draw_lang_selector()

            # Process menu bar actions that open panels (deferred)
            pygame.display.flip()

        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    app = EditorApp()
    app.run()
