import json
import os
import time
from pathlib import Path


class RepositorioSaves:
    """Gestiona el índice de slots de guardado en workspace/saves/game/.

    Lee/escrive save_index.json con metadata de cada slot.
    Los archivos .json.gz, _meta.json y _thumb.png están en el mismo dir.
    """

    INDEX_FILENAME = "save_index.json"

    def __init__(self, game_save_dir=None):
        if game_save_dir is None:
            game_save_dir = self._default_save_dir()
        self._dir = Path(game_save_dir)
        self._dir.mkdir(parents=True, exist_ok=True)
        self._index_path = self._dir / self.INDEX_FILENAME
        self._index = self._cargar_indice()

    def get_dir(self):
        return self._dir

    def listar_slots(self):
        slots = []
        for i in range(1, 100):
            key = f"slot_{i}"
            if key in self._index:
                meta = self._index[key]
                meta["slot"] = i
                slots.append(meta)
        return slots

    def get_metadata(self, slot):
        key = f"slot_{slot}"
        return self._index.get(key, None)

    def existe_slot(self, slot):
        key = f"slot_{slot}"
        return key in self._index

    def registrar_slot(self, slot, metadata):
        key = f"slot_{slot}"
        self._index[key] = {
            "timestamp": metadata.get("timestamp", int(time.time())),
            "nivel_id": metadata.get("nivel_id", ""),
            "posicion": metadata.get("posicion", [0, 0]),
            "playtime_segundos": metadata.get("playtime_segundos", 0),
            "jefes_derrotados": metadata.get("jefes_derrotados", 0),
            "thumbnail": metadata.get("thumbnail", ""),
            "dev": metadata.get("dev", False)
        }
        self._guardar_indice()

    def eliminar_slot(self, slot):
        key = f"slot_{slot}"
        if key in self._index:
            del self._index[key]
            self._guardar_indice()
        self._limpiar_archivos_slot(slot)

    def get_slot_mas_reciente(self):
        if not self._index:
            return None
        mejor = None
        mejor_ts = -1
        for key, meta in self._index.items():
            if meta.get("dev", False):
                continue
            ts = meta.get("timestamp", 0)
            if ts > mejor_ts:
                mejor_ts = ts
                slot_num = int(key.replace("slot_", ""))
                mejor = slot_num
        return mejor

    def get_total_playtime(self):
        total = 0
        for key, meta in self._index.items():
            if not meta.get("dev", False):
                total += meta.get("playtime_segundos", 0)
        return total

    def _cargar_indice(self):
        try:
            with open(self._index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, dict):
                return data
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return {}

    def _guardar_indice(self):
        try:
            with open(self._index_path, "w", encoding="utf-8") as f:
                json.dump(self._index, f, indent=2, ensure_ascii=False)
        except (IOError, OSError):
            pass

    def _limpiar_archivos_slot(self, slot):
        prefijos = [
            f"save_{slot}.json.gz",
            f"save_{slot}.json",
            f"save_{slot}_meta.json",
            f"save_{slot}_thumb.png"
        ]
        for prefijo in prefijos:
            path = self._dir / prefijo
            if path.exists():
                try:
                    path.unlink()
                except OSError:
                    pass

    @staticmethod
    def _default_save_dir():
        return Path(os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            "..", "workspace", "saves", "game"
        )).resolve()
