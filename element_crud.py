import os
import copy
import json
from typing import Optional, Any, Dict, List, Tuple


def generate_new_id(base: str, existing_ids: List[str]) -> str:
    eid = base
    n = 1
    while eid in existing_ids:
        eid = f"{base}_{n}"
        n += 1
    return eid


def rename_element_maps(old_id: str, new_id: str, maps_dir: str) -> int:
    updated = 0
    for fname in os.listdir(maps_dir):
        if not fname.endswith(".json"):
            continue
        fpath = os.path.join(maps_dir, fname)
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                data = json.load(f)
            grid = data.get("grid", {})
            changed = False
            for key, eid in list(grid.items()):
                if eid == old_id:
                    grid[key] = new_id
                    changed = True
            if changed:
                with open(fpath, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2, ensure_ascii=False)
                updated += 1
        except Exception:
            pass
    return updated
