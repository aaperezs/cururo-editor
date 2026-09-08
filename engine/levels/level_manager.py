import json
import os

from engine.configs import *

from engine.levels.level_parser import LevelParser
from engine.project_paths import levels_dir

RUTA_MAPAS = levels_dir("mapas")


class LevelManager:
    def __init__(self):
        self.niveles = {}
        self.nivel_actual = None
        self.nivel_id_actual = None

        self._cargar_niveles()
        # Read spawn from gameplay.json
        import json
        import os
        gameplay_path = os.path.join(os.path.dirname(__file__), "..", "data", "gameplay.json")
        nivel_inicio = None
        try:
            with open(gameplay_path, "r", encoding="utf-8") as f:
                gameplay = json.load(f)
            spawn = gameplay.get("spawn")
            if spawn and spawn.get("map_id"):
                nivel_inicio = spawn["map_id"]
                if nivel_inicio not in self.niveles:
                    nivel_inicio = None
                    print(f"Advertencia: nivel de spawn '{spawn['map_id']}' no encontrado.")
        except (json.JSONDecodeError, IOError):
            pass
        if nivel_inicio is None:
            nivel_inicio = next(iter(self.niveles), "1-1")
            print(f"Advertencia: ningún spawn definido. Usando {nivel_inicio}")
        self.ir_a_nivel(nivel_inicio)

    def _cargar_niveles(self):
        if not os.path.isdir(RUTA_MAPAS):
            print(f"No se encontró la carpeta {RUTA_MAPAS}")
            return

        seen = set()
        for archivo in sorted(os.listdir(RUTA_MAPAS)):
            if archivo.endswith("_meta.json"):
                continue
            base, ext = os.path.splitext(archivo)
            if ext not in (".txt", ".json"):
                continue
            # Skip layer suffix files (we handle them per-level below)
            if base.endswith("_z1") or base.endswith("_z2") or base.endswith("_z3") or base.endswith("_z4"):
                continue
            nivel_id = base
            if nivel_id in seen:
                continue
            seen.add(nivel_id)

            ruta_base = os.path.join(RUTA_MAPAS, f"{nivel_id}.json")
            ruta_txt = os.path.join(RUTA_MAPAS, f"{nivel_id}.txt")
            meta_ruta = os.path.join(RUTA_MAPAS, f"{nivel_id}_meta.json")

            meta = None
            if os.path.exists(meta_ruta):
                try:
                    with open(meta_ruta, "r", encoding="utf-8") as f:
                        meta = json.load(f)
                except Exception:
                    pass

            multi_tiles = {}
            mt_ruta = os.path.join(RUTA_MAPAS, f"{nivel_id}_multitiles.json")
            if os.path.exists(mt_ruta):
                try:
                    with open(mt_ruta, "r", encoding="utf-8") as f:
                        raw = json.load(f)
                    for key, info in raw.items():
                        parts = key.split(",")
                        gx, gy, z = int(parts[0]), int(parts[1]), int(parts[2])
                        multi_tiles[(gx, gy, z)] = info
                except Exception:
                    pass

            # Collect all layer data
            layer_datas = []
            base_data = None

            # Try JSON first (v2 format)
            if os.path.exists(ruta_base):
                try:
                    with open(ruta_base, "r", encoding="utf-8") as f:
                        texto = f.read()
                    if texto.strip().startswith("{"):
                        base_data = json.loads(texto)
                        layer_datas.append({"z": 0, "data": base_data})
                    else:
                        # Legacy text format
                        base_data = None
                except Exception:
                    pass

            if base_data is None:
                # Try legacy .txt
                if os.path.exists(ruta_txt):
                    try:
                        with open(ruta_txt, "r", encoding="utf-8") as f:
                            texto = f.read()
                        if ext == ".txt" or not os.path.exists(ruta_base):
                            datos = LevelParser.cargar_nivel(texto, meta=meta)
                            if datos:
                                self.niveles[nivel_id] = datos
                                print(f"Nivel cargado: {nivel_id} ({datos['ancho']}x{datos['alto']})")
                            continue
                    except Exception as e:
                        print(f"Error cargando {archivo}: {e}")
                    continue

            if base_data is None:
                continue

            # Load additional z-layers (z1..z4)
            for z in range(1, 5):
                z_path = os.path.join(RUTA_MAPAS, f"{nivel_id}_z{z}.json")
                if os.path.exists(z_path):
                    try:
                        with open(z_path, "r", encoding="utf-8") as f:
                            z_data = json.load(f)
                            layer_datas.append({"z": z, "data": z_data})
                    except Exception:
                        pass

            # Parse all layers and merge
            try:
                if len(layer_datas) > 1:
                    datos = LevelParser.parsear_mapa_v2_con_capas(layer_datas, meta, multi_tiles)
                else:
                    mt_z0 = {(gx, gy): v for (gx, gy, z), v in multi_tiles.items() if z == 0}
                    datos = LevelParser.parsear_mapa_v2(base_data, meta, multi_tiles=mt_z0)
                if datos:
                    self.niveles[nivel_id] = datos
                    layer_info = f"capas={len(layer_datas)}" if len(layer_datas) > 1 else ""
                    print(f"Nivel cargado: {nivel_id} ({datos['ancho']}x{datos['alto']}) {layer_info}")
            except Exception as e:
                print(f"Error cargando {nivel_id}: {e}")

    def ir_a_nivel(self, nivel_id):
        if nivel_id in self.niveles:
            self.nivel_actual = self.niveles[nivel_id]
            self.nivel_id_actual = nivel_id
            print(f"Nivel cambiado a: {nivel_id}")
            return True
        return False

    def obtener_nivel_actual(self):
        return self.nivel_actual

    def obtener_id_actual(self):
        return self.nivel_id_actual

    def tiene_mapas(self):
        return bool(self.niveles)

    def mapa_con_inicio(self):
        """Devuelve el id del mapa con spawn configurado en gameplay.json, o None."""
        import json
        import os
        gameplay_path = os.path.join(os.path.dirname(__file__), "..", "data", "gameplay.json")
        try:
            with open(gameplay_path, "r", encoding="utf-8") as f:
                gameplay = json.load(f)
            spawn = gameplay.get("spawn")
            if spawn and spawn.get("map_id"):
                return spawn["map_id"]
        except (json.JSONDecodeError, IOError):
            pass
        return None

