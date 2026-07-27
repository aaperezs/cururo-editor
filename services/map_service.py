import os
from levels.level_parser import LevelParser
from levels.level_manager import RUTA_MAPAS
from editor.services.project_service import project_service


class MapService:
    """Application service for map operations."""

    @staticmethod
    def list_maps():
        maps_dir = RUTA_MAPAS
        if not os.path.isdir(maps_dir):
            return []
        result = []
        for fname in sorted(os.listdir(maps_dir)):
            if fname.endswith(".txt") or fname.endswith(".json"):
                name = os.path.splitext(fname)[0]
                # Skip arena files
                if "-arena" in name:
                    continue
                result.append(name)
        return result

    @staticmethod
    def load_map(map_id):
        from levels.level_manager import LevelManager
        lm = LevelManager()
        if lm.ir_a_nivel(map_id):
            nivel = lm.obtener_nivel_actual()
            return nivel
        return None

    @staticmethod
    def parse_from_file(filepath):
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
        if filepath.endswith(".json"):
            import json
            data = json.loads(content)
            return LevelParser.parsear_mapa_v2(data, {})
        return LevelParser.parsear_mapa(content)

    @staticmethod
    def get_map_path(map_id):
        return os.path.join(RUTA_MAPAS, map_id)


map_service = MapService()
