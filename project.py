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

    def stacks_path(self, *parts):
        return os.path.join(self.root, "levels", "mapas_stacks", *parts)


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
                })
            except (json.JSONDecodeError, IOError):
                pass
    return results


def list_templates():
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
                results.append({
                    "id": entry,
                    "name": data.get("name", entry),
                    "path": full,
                })
            except (json.JSONDecodeError, IOError):
                pass
    return results


def create_project(template_id, project_name, target_dir):
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
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2, ensure_ascii=False)

    return target_dir
