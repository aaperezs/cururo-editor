import os
import json
import shutil

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


_current_project_path = None


class Project:
    def __init__(self, root_path):
        self.root = os.path.abspath(root_path)
        self._manifest_path = os.path.join(self.root, "cururo.json")
        self._manifest = self._load_manifest()
        self.name = self._manifest.get("name", os.path.basename(self.root))
        self.project_id = self._manifest.get("id", os.path.basename(self.root))
        self.category = self._manifest.get("category", "blank")
        self.platform = self._manifest.get("platform", "desktop")
        self.quality = self._manifest.get("quality", "medium")
        self._window = self._manifest.get("window")
        if not isinstance(self._window, dict):
            self._window = {}
        self.window_title = self._window.get("title", self.name)
        self.window_fullscreen = bool(self._window.get("fullscreen", False))

    def _parse_resolution(self, value):
        try:
            if isinstance(value, (list, tuple)) and len(value) == 2:
                return (int(value[0]), int(value[1]))
            if isinstance(value, dict):
                w = int(value.get("w", 800))
                h = int(value.get("h", 600))
                return (w, h)
            w, h = str(value).strip().lower().replace(" ", "").split("x")
            return (int(w), int(h))
        except (ValueError, AttributeError, TypeError):
            return (800, 600)

    # ── Configuración gráfica (bloque `graphics` del manifest, con fallback) ──

    @property
    def tile_size(self):
        return self._manifest.get("graphics", {}).get("tile_size", 20)

    @property
    def resolution(self):
        g = self._manifest.get("graphics", {}).get("resolution")
        if g:
            if isinstance(g, (list, tuple)) and len(g) == 2:
                return (int(g[0]), int(g[1]))
            return self._parse_resolution(g)
        return self._parse_resolution(self._manifest.get("resolution", "800x600"))

    @property
    def pixel_art_scale(self):
        return self._manifest.get("graphics", {}).get("pixel_art_scale", 1)

    @property
    def tileset(self):
        return self._manifest.get("graphics", {}).get("tileset", None)

    def _load_manifest(self):
        if os.path.exists(self._manifest_path):
            with open(self._manifest_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def data_path(self, *parts):
        return os.path.join(self.root, "data", *parts)

    def assets_path(self, *parts):
        return os.path.join(self.root, "assets", *parts)

    def levels_path(self, *parts):
        return os.path.join(self.root, "levels", *parts)

    def maps_path(self, *parts):
        return os.path.join(self.root, "levels", "mapas", *parts)

    def stacks_path(self, *parts):
        return os.path.join(self.root, "levels", "mapas_stacks", *parts)

    def get_available_panels(self):
        from editor.categories import get_panels_for_category
        return get_panels_for_category(self.category)

    def update_config(self, platform=None, quality=None, window_title=None, fullscreen=None,
                      resolution=None):
        if platform in ("desktop", "mobile"):
            self._manifest["platform"] = platform
        if quality in ("low", "medium", "high"):
            self._manifest["quality"] = quality
        if resolution:
            try:
                w, h = str(resolution).strip().lower().replace(" ", "").split("x")
                self._manifest["resolution"] = f"{int(w)}x{int(h)}"
                if isinstance(self._manifest.get("graphics"), dict):
                    self._manifest["graphics"]["resolution"] = [int(w), int(h)]
            except (ValueError, AttributeError):
                pass
        if window_title is not None:
            window = self._manifest.get("window")
            if not isinstance(window, dict):
                window = {}
            window["title"] = (window_title or "").strip() or self.name
            self._manifest["window"] = window
        if fullscreen is not None:
            window = self._manifest.get("window")
            if not isinstance(window, dict):
                window = {}
            window["fullscreen"] = bool(fullscreen)
            self._manifest["window"] = window
        with open(self._manifest_path, "w", encoding="utf-8") as f:
            json.dump(self._manifest, f, indent=2, ensure_ascii=False)


def set_current_project(path):
    global _current_project_path
    _current_project_path = path
    if path:
        sys_path_setup(path)


def get_current_project():
    global _current_project_path
    if _current_project_path is None:
        return None
    return Project(_current_project_path)


def sys_path_setup(project_root):
    import sys
    root = os.path.abspath(project_root)
    if root not in sys.path:
        sys.path.insert(0, root)


def discover_projects(search_dir):
    results = []
    if not os.path.isdir(search_dir):
        return results
    for entry in os.listdir(search_dir):
        full = os.path.join(search_dir, entry)
        manifest = os.path.join(full, "cururo.json")
        if os.path.isdir(full) and os.path.exists(manifest):
            try:
                with open(manifest, "r", encoding="utf-8") as f:
                    data = json.load(f)
                results.append({
                    "path": full,
                    "name": data.get("name", entry),
                    "id": data.get("id", entry),
                    "category": data.get("category", "blank"),
                })
            except (json.JSONDecodeError, IOError):
                pass
    return results


def list_templates(category=None):
    results = []
    if not os.path.isdir(TEMPLATES_DIR):
        return results
    for entry in sorted(os.listdir(TEMPLATES_DIR)):
        full = os.path.join(TEMPLATES_DIR, entry)
        manifest = os.path.join(full, "cururo.json")
        if os.path.isdir(full) and os.path.exists(manifest):
            try:
                with open(manifest, "r", encoding="utf-8") as f:
                    data = json.load(f)
                tpl_cat = data.get("category", "blank")
                if category is not None and tpl_cat != category:
                    continue
                results.append({
                    "id": entry,
                    "name": data.get("name", entry),
                    "path": full,
                    "category": tpl_cat,
                })
            except (json.JSONDecodeError, IOError):
                pass
    return results


def get_templates_for_category(category_id):
    return list_templates(category=category_id)


def create_project(template_id, project_name, target_dir, platform="desktop",
                   quality="medium", window_title=None, resolution="800x600",
                   graphics_config=None):
    template_path = os.path.join(TEMPLATES_DIR, template_id)
    if not os.path.isdir(template_path):
        return None

    os.makedirs(target_dir, exist_ok=True)

    for item in os.listdir(template_path):
        src = os.path.join(template_path, item)
        dst = os.path.join(target_dir, item)
        if os.path.isdir(src):
            shutil.copytree(src, dst, dirs_exist_ok=True)
        else:
            shutil.copy2(src, dst)

    manifest_path = os.path.join(target_dir, "cururo.json")
    if os.path.exists(manifest_path):
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        manifest["name"] = project_name
        safe_id = project_name.lower().replace(" ", "_").replace("-", "_")
        manifest["id"] = safe_id
        manifest["platform"] = platform if platform in ("desktop", "mobile") else "desktop"
        manifest["quality"] = quality if quality in ("low", "medium", "high") else "medium"
        try:
            rw, rh = str(resolution).strip().lower().replace(" ", "").split("x")
            manifest["resolution"] = f"{int(rw)}x{int(rh)}"
        except (ValueError, AttributeError):
            manifest["resolution"] = "800x600"
        window = manifest.get("window")
        if not isinstance(window, dict):
            window = {}
        window["title"] = (window_title or "").strip() or project_name
        manifest["window"] = window
        if graphics_config:
            g = dict(graphics_config)
            try:
                ts = int(g.get("tile_size"))
            except (ValueError, TypeError):
                ts = 20
            if ts not in (16, 20, 24, 32):
                ts = 20
            g["tile_size"] = ts
            res = g.get("resolution")
            if isinstance(res, (list, tuple)) and len(res) == 2:
                g["resolution"] = [int(res[0]), int(res[1])]
            elif isinstance(res, str):
                try:
                    rw, rh = (int(p) for p in res.strip().lower().replace(" ", "").split("x"))
                    g["resolution"] = [rw, rh]
                except (ValueError, AttributeError):
                    g["resolution"] = [800, 600]
            else:
                g["resolution"] = [800, 600]
            g.setdefault("pixel_art_scale", 1)
            g.setdefault("tileset", None)
            manifest["graphics"] = g
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    return target_dir
