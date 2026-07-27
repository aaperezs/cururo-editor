import os
import json
from editor.project import get_current_project


def workspace_dir():
    p = get_current_project()
    if not p:
        return None
    d = os.path.join(p.root, ".cururo")
    os.makedirs(d, exist_ok=True)
    return d


def workspace_path():
    d = workspace_dir()
    return os.path.join(d, "workspace.json") if d else None


def save_workspace(data):
    path = workspace_path()
    if path:
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except (IOError, OSError):
            pass


def load_workspace():
    path = workspace_path()
    if path and os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError, OSError):
            pass
    return {}
