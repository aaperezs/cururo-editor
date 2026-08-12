import json
import os
import copy
from editor.project import get_current_project

_DIALOGOS_DATA = {}
_TREE_DATA = {}


def _get_path():
    p = get_current_project()
    if p:
        return p.data_path("dialogos.json")
    return None


def _load_dialogos():
    global _DIALOGOS_DATA, _TREE_DATA
    _DIALOGOS_DATA = {}
    _TREE_DATA = {}
    p = get_current_project()
    if not p:
        return
    path = p.data_path("dialogos.json")
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        for personaje, contextos in raw.items():
            _DIALOGOS_DATA[personaje] = {}
            for ctx, value in contextos.items():
                if isinstance(value, dict) and "nodes" in value:
                    _DIALOGOS_DATA[personaje][ctx] = value.get("flat", [])
                    _TREE_DATA.setdefault(personaje, {})[ctx] = {
                        "nodes": copy.deepcopy(value["nodes"]),
                        "start": value.get("start", ""),
                    }
                else:
                    _DIALOGOS_DATA[personaje][ctx] = list(value) if isinstance(value, list) else []


def _save_dialogos():
    path = _get_path()
    if not path:
        return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    merged = {}
    all_keys = set(list(_DIALOGOS_DATA.keys()) + list(_TREE_DATA.keys()))
    for personaje in all_keys:
        merged[personaje] = {}
        flat_ctxs = _DIALOGOS_DATA.get(personaje, {})
        tree_ctxs = _TREE_DATA.get(personaje, {})
        all_ctxs = set(list(flat_ctxs.keys()) + list(tree_ctxs.keys()))
        for ctx in all_ctxs:
            if ctx in tree_ctxs:
                tree_info = tree_ctxs[ctx]
                entry = {
                    "flat": flat_ctxs.get(ctx, []),
                    "nodes": tree_info["nodes"],
                    "start": tree_info.get("start", ""),
                }
                merged[personaje][ctx] = entry
            else:
                merged[personaje][ctx] = flat_ctxs.get(ctx, [])
    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)


def _parse_key(key):
    if "/" in key:
        parts = key.split("/", 1)
        return parts[0], parts[1]
    return key, ""


def _make_key(personaje, contexto):
    return f"{personaje}/{contexto}"


def get_all_dialogo_keys():
    keys = set()
    for personaje, contextos in _DIALOGOS_DATA.items():
        for ctx in contextos:
            keys.add(_make_key(personaje, ctx))
    for personaje, contextos in _TREE_DATA.items():
        for ctx in contextos:
            keys.add(_make_key(personaje, ctx))
    return sorted(keys)


def get_all_personajes():
    return sorted(set(list(_DIALOGOS_DATA.keys()) + list(_TREE_DATA.keys())))


def get_contextos(personaje):
    ctxs = set()
    if personaje in _DIALOGOS_DATA:
        ctxs.update(_DIALOGOS_DATA[personaje].keys())
    if personaje in _TREE_DATA:
        ctxs.update(_TREE_DATA[personaje].keys())
    return sorted(ctxs)


def get_dialogo(personaje, contexto):
    d = _DIALOGOS_DATA.get(personaje, {}).get(contexto)
    return copy.deepcopy(d) if d else None


def get_dialogo_by_key(key):
    personaje, contexto = _parse_key(key)
    return get_dialogo(personaje, contexto)


def set_dialogo(personaje, contexto, lineas):
    if personaje not in _DIALOGOS_DATA:
        _DIALOGOS_DATA[personaje] = {}
    _DIALOGOS_DATA[personaje][contexto] = list(lineas)
    _save_dialogos()


def set_dialogo_by_key(key, lineas):
    personaje, contexto = _parse_key(key)
    set_dialogo(personaje, contexto, lineas)


def delete_dialogo(personaje, contexto):
    removed = False
    if personaje in _DIALOGOS_DATA and contexto in _DIALOGOS_DATA[personaje]:
        del _DIALOGOS_DATA[personaje][contexto]
        if not _DIALOGOS_DATA[personaje]:
            del _DIALOGOS_DATA[personaje]
        removed = True
    if personaje in _TREE_DATA and contexto in _TREE_DATA[personaje]:
        del _TREE_DATA[personaje][contexto]
        if not _TREE_DATA[personaje]:
            del _TREE_DATA[personaje]
        removed = True
    if removed:
        _save_dialogos()
    return removed


def delete_dialogo_by_key(key):
    personaje, contexto = _parse_key(key)
    return delete_dialogo(personaje, contexto)


def dialogo_exists(personaje, contexto):
    if personaje in _DIALOGOS_DATA and contexto in _DIALOGOS_DATA[personaje]:
        return True
    if personaje in _TREE_DATA and contexto in _TREE_DATA[personaje]:
        return True
    return False


def dialogo_exists_by_key(key):
    personaje, contexto = _parse_key(key)
    return dialogo_exists(personaje, contexto)


def create_dialogo(personaje, contexto):
    if dialogo_exists(personaje, contexto):
        return False
    if personaje not in _DIALOGOS_DATA:
        _DIALOGOS_DATA[personaje] = {}
    _DIALOGOS_DATA[personaje][contexto] = ["Nueva linea"]
    _save_dialogos()
    return True


def create_dialogo_by_key(key):
    personaje, contexto = _parse_key(key)
    return create_dialogo(personaje, contexto)


def rename_dialogo(old_key, new_key):
    if old_key == new_key:
        return True
    old_p, old_c = _parse_key(old_key)
    new_p, new_c = _parse_key(new_key)
    if dialogo_exists(new_p, new_c):
        return False
    moved = False
    if old_p in _DIALOGOS_DATA and old_c in _DIALOGOS_DATA[old_p]:
        lineas = _DIALOGOS_DATA[old_p].pop(old_c)
        if not _DIALOGOS_DATA[old_p]:
            del _DIALOGOS_DATA[old_p]
        if new_p not in _DIALOGOS_DATA:
            _DIALOGOS_DATA[new_p] = {}
        _DIALOGOS_DATA[new_p][new_c] = lineas
        moved = True
    if old_p in _TREE_DATA and old_c in _TREE_DATA[old_p]:
        tree = _TREE_DATA[old_p].pop(old_c)
        if not _TREE_DATA[old_p]:
            del _TREE_DATA[old_p]
        if new_p not in _TREE_DATA:
            _TREE_DATA[new_p] = {}
        _TREE_DATA[new_p][new_c] = tree
        moved = True
    if moved:
        _save_dialogos()
    return moved


# ── Tree API ──

NODE_DEFAULTS = {
    "dialogo": {"texto": "", "next": ""},
    "opcion": {"choices": [{"texto": "", "next": ""}]},
    "condicion": {"flag": "", "operador": "==", "valor": "", "next": "", "next_false": ""},
    "accion": {"tipo_accion": "set_flag", "params": {}, "next": ""},
    "salto": {"destino": "", "next": ""},
}

NODE_LABELS = {
    "dialogo": "Diálogo",
    "opcion": "Opción",
    "condicion": "Condición",
    "accion": "Acción",
    "salto": "Salto",
}

NODE_COLORS = {
    "dialogo": (70, 130, 200),
    "opcion": (200, 180, 60),
    "condicion": (180, 100, 200),
    "accion": (100, 200, 100),
    "salto": (200, 120, 80),
}


def create_tree_key(personaje, contexto):
    if personaje not in _TREE_DATA:
        _TREE_DATA[personaje] = {}
    if contexto not in _TREE_DATA[personaje]:
        nid = _new_node_id({})
        _TREE_DATA[personaje][contexto] = {
            "nodes": {nid: {"tipo": "dialogo", **copy.deepcopy(NODE_DEFAULTS["dialogo"])}},
            "start": nid,
        }
        _save_dialogos()
    return True


def get_tree(personaje, contexto):
    t = _TREE_DATA.get(personaje, {}).get(contexto)
    return copy.deepcopy(t) if t else None


def get_tree_by_key(key):
    p, c = _parse_key(key)
    return get_tree(p, c)


def set_tree(personaje, contexto, tree_data):
    if personaje not in _TREE_DATA:
        _TREE_DATA[personaje] = {}
    _TREE_DATA[personaje][contexto] = copy.deepcopy(tree_data)
    _save_dialogos()


def set_tree_by_key(key, tree_data):
    p, c = _parse_key(key)
    set_tree(p, c, tree_data)


def _new_node_id(existing_nodes):
    n = 1
    while f"n{n}" in existing_nodes:
        n += 1
    return f"n{n}"


def add_node(personaje, contexto, tipo, after_id=None):
    tree = _TREE_DATA.get(personaje, {}).get(contexto)
    if not tree:
        return None
    nid = _new_node_id(tree["nodes"])
    defaults = copy.deepcopy(NODE_DEFAULTS.get(tipo, {}))
    tree["nodes"][nid] = {"tipo": tipo, **defaults}
    if after_id and after_id in tree["nodes"]:
        parent = tree["nodes"][after_id]
        if parent["tipo"] in ("condicion",):
            if not parent.get("next"):
                parent["next"] = nid
            elif not parent.get("next_false"):
                parent["next_false"] = nid
        else:
            if isinstance(parent.get("next"), str) and not parent["next"]:
                parent["next"] = nid
            elif parent["tipo"] == "opcion":
                parent.setdefault("choices", [])
                parent["choices"].append({"texto": "", "next": nid})
    if not tree.get("start"):
        tree["start"] = nid
    _save_dialogos()
    return nid


def remove_node(personaje, contexto, nid):
    tree = _TREE_DATA.get(personaje, {}).get(contexto)
    if not tree or nid not in tree["nodes"]:
        return False
    del tree["nodes"][nid]
    # Clean up references
    for node in tree["nodes"].values():
        for key in ("next", "next_false"):
            if node.get(key) == nid:
                node[key] = ""
        if node["tipo"] == "opcion":
            node["choices"] = [c for c in node.get("choices", []) if c.get("next") != nid]
    if tree.get("start") == nid:
        remaining = list(tree["nodes"].keys())
        tree["start"] = remaining[0] if remaining else ""
    _save_dialogos()
    return True


def compile_to_flat(personaje, contexto):
    """Compila un árbol de diálogo a la lista plana de líneas (para runtime legacy)"""
    tree = _TREE_DATA.get(personaje, {}).get(contexto)
    if not tree:
        return get_dialogo(personaje, contexto) or []
    lines = []
    visited = set()
    nid = tree.get("start", "")
    while nid and nid not in visited and nid in tree["nodes"]:
        visited.add(nid)
        node = tree["nodes"][nid]
        if node["tipo"] == "dialogo":
            if node.get("texto"):
                lines.append(node["texto"])
            nid = node.get("next", "")
        elif node["tipo"] == "opcion":
            choices_text = " / ".join(
                c.get("texto", "?") for c in node.get("choices", [])
            )
            lines.append(f"[{choices_text}]")
            nid = ""
        elif node["tipo"] == "condicion":
            lines.append(f"[si {node.get('flag','')} {node.get('operador','')} {node.get('valor','')}]")
            nid = node.get("next", "")
        elif node["tipo"] == "accion":
            lines.append(f"[{node.get('tipo_accion','')}]")
            nid = node.get("next", "")
        elif node["tipo"] == "salto":
            lines.append(f"[→ {node.get('destino','')}]")
            nid = ""
        else:
            nid = ""
    return lines
