import os
from editor.project import get_current_project

SCRIPTS_DIR = "scripts"


def _scripts_path():
    proj = get_current_project()
    if not proj:
        return None
    path = os.path.join(proj.root, SCRIPTS_DIR)
    os.makedirs(path, exist_ok=True)
    return path


def list_scripts():
    sp = _scripts_path()
    if not sp:
        return []
    files = []
    for f in sorted(os.listdir(sp)):
        if f.endswith(".py"):
            files.append(f[:-3])
    return files


def get_script(name):
    sp = _scripts_path()
    if not sp:
        return ""
    path = os.path.join(sp, name + ".py")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return f.read()
    return ""


def save_script(name, content):
    sp = _scripts_path()
    if not sp:
        return
    path = os.path.join(sp, name + ".py")
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)


def delete_script(name):
    sp = _scripts_path()
    if not sp:
        return
    path = os.path.join(sp, name + ".py")
    if os.path.exists(path):
        os.remove(path)


def create_script(name, template=""):
    save_script(name, template)
