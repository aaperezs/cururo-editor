import os
import json
from editor.common.parser import parsear_mapa
from editor.project import get_current_project


class MapService:
    """Application service for map operations."""

    @staticmethod
    def _maps_dir():
        p = get_current_project()
        return p.maps_path() if p else ""

    @staticmethod
    def list_maps():
        maps_dir = MapService._maps_dir()
        if not os.path.isdir(maps_dir):
            return []
        result = []
        for fname in sorted(os.listdir(maps_dir)):
            if fname.endswith(".txt") or fname.endswith(".json"):
                name = os.path.splitext(fname)[0]
                if "-arena" in name:
                    continue
                result.append(name)
        return result

    @staticmethod
    def load_map(map_id):
        maps_dir = MapService._maps_dir()
        if not maps_dir:
            return None
        path_json = os.path.join(maps_dir, f"{map_id}.json")
        path_txt = os.path.join(maps_dir, f"{map_id}.txt")
        path = path_json if os.path.exists(path_json) else path_txt
        if not os.path.exists(path):
            return None
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if path.endswith(".json"):
            data = json.loads(content)
            from editor.common.parser import parsear_mapa
            return {"grid": data.get("grid", {}), "ancho": data.get("ancho", 0), "alto": data.get("alto", 0)}
        return parsear_mapa(content)

    @staticmethod
    def parse_from_file(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        if filepath.endswith(".json"):
            data = json.loads(content)
            return {"grid": data.get("grid", {}), "ancho": data.get("ancho", 0), "alto": data.get("alto", 0)}
        return parsear_mapa(content)

    @staticmethod
    def get_map_path(map_id):
        return os.path.join(MapService._maps_dir(), map_id)


map_service = MapService()
