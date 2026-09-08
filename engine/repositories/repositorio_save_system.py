from .base import RepositorioBase


class RepositorioSaveSystem(RepositorioBase):
    """Repositorio de configuración del sistema de guardado.

    Carga data/save_system.json y expone la config con validaciones.
    Todo es configurable por el usuario en el editor.
    """

    def __init__(self):
        super().__init__("save_system.json")

    def get_config(self):
        cfg = self._data.get("save_system", {})
        if not cfg:
            return self._defaults()
        return cfg

    def get_slots(self):
        return self.get_config().get("slots", 10)

    def get_save_point_item_id(self):
        """ID del item requerido para guardar. Vacío = no requiere item."""
        return self.get_config().get("save_point_item_id", "")

    def get_schema_include(self):
        return self.get_config().get("schema", {}).get("include", [])

    def get_schema_exclude(self):
        return self.get_config().get("schema", {}).get("exclude", [])

    def get_slot_metadata_fields(self):
        return self.get_config().get("slot_metadata", [])

    def get_validaciones(self):
        defaults = self._defaults()["validaciones"]
        v = self.get_config().get("validaciones", {})
        defaults.update(v)
        return defaults

    def get_autosave_triggers(self):
        return self.get_config().get("autosave_triggers", [])

    def get_dev_mode(self):
        defaults = self._defaults()["dev_mode"]
        d = self.get_config().get("dev_mode", {})
        defaults.update(d)
        return d

    def get_version(self):
        return self.get_config().get("version", 1)

    @staticmethod
    def _defaults():
        return {
            "version": 1,
            "slots": 10,
            "slot_naming": "save_{n}",
            "save_point_item_id": "",
            "autosave_triggers": [],
            "schema": {
                "include": [
                    "snake", "inventario", "monedas", "flags", "contadores",
                    "shop_state", "nivel_actual", "posicion_mundo",
                    "progreso_historia", "camera", "habilidades",
                    "segmentos_perdidos"
                ],
                "exclude": ["particles", "textos_flotantes_timer", "cache_sprites"]
            },
            "slot_metadata": [
                "timestamp", "nivel_id", "posicion", "playtime_segundos",
                "jefes_derrotados", "thumbnail_base64"
            ],
            "validaciones": {
                "min_slots": 1,
                "max_slots": 99,
                "requiere_item_para_guardar": False,
                "item_se_consume": False,
                "thumbnail_size": [160, 90],
                "compress_level": 6,
                "use_checksum": True
            },
            "dev_mode": {
                "enabled": True,
                "spatial_save_dir": "workspace/saves/dev",
                "no_item_required": True,
                "no_checksum": True,
                "uncompressed": True,
                "hotkey_save": "F5",
                "hotkey_load": "F9"
            }
        }
