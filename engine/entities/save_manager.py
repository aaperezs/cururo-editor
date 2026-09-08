import time

from engine.repositories import RepositorioSaveSystem


SAVE_VERSION = 1


class SaveManager:
    """Gestiona slots de guardado: serialización, compresión, checksum, E/S disco."""

    def __init__(self):
        from engine.repositories.repositorio_saves import RepositorioSaves
        self._repo_config = RepositorioSaveSystem()
        self._repo_saves = RepositorioSaves()
        self._dev_dir = self._repo_config.get_dev_mode().get(
            "spatial_save_dir", "workspace/saves/dev"
        )
        self._config = self._repo_config.get_config()
        self._validaciones = self._repo_config.get_validaciones()

    # ── Guardar ──

    def guardar(self, estado, slot: int, dev: bool = False) -> bool:
        """Serializa estado completo y guarda en slot."""
        import gzip
        import hashlib
        import json
        from pathlib import Path

        schema_include = self._repo_config.get_schema_include()
        data = self._serializar(estado, schema_include)
        meta = self._extraer_metadata(estado)
        meta["slot"] = slot
        meta["dev"] = dev

        save_payload = {
            "version": SAVE_VERSION,
            "metadata": meta,
            "estado": data
        }

        json_bytes = json.dumps(save_payload, separators=(',', ':')).encode('utf-8')

        if dev:
            dev_dir = Path(self._dev_dir)
            dev_dir.mkdir(parents=True, exist_ok=True)
            (dev_dir / f"dev_{slot}.json").write_bytes(json_bytes)
            meta_path = dev_dir / f"dev_{slot}_meta.json"
            meta_path.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8')
            return True

        compress_level = self._validaciones.get("compress_level", 6)
        compressed = gzip.compress(json_bytes, compresslevel=compress_level)

        use_checksum = self._validaciones.get("use_checksum", True)
        checksum = hashlib.sha256(compressed).hexdigest() if use_checksum else ""

        save_dir = self._repo_saves.get_dir()
        save_dir.mkdir(parents=True, exist_ok=True)

        (save_dir / f"save_{slot}.json.gz").write_bytes(compressed)

        meta["checksum"] = checksum
        (save_dir / f"save_{slot}_meta.json").write_text(
            json.dumps(meta, indent=2, ensure_ascii=False), encoding='utf-8'
        )

        self._repo_saves.registrar_slot(slot, meta)
        return True

    # ── Cargar ──

    def cargar(self, slot: int, dev: bool = False) -> dict | None:
        """Carga y deserializa un save slot. Retorna dict estado o None."""
        import gzip
        import hashlib
        import json
        from pathlib import Path

        if dev:
            dev_dir = Path(self._dev_dir)
            json_path = dev_dir / f"dev_{slot}.json"
            if not json_path.exists():
                return None
            save_payload = json.loads(json_path.read_bytes())
        else:
            save_dir = self._repo_saves.get_dir()
            compressed_path = save_dir / f"save_{slot}.json.gz"
            meta_path = save_dir / f"save_{slot}_meta.json"

            if not compressed_path.exists():
                return None

            compressed = compressed_path.read_bytes()

            use_checksum = self._validaciones.get("use_checksum", True)
            if use_checksum and meta_path.exists():
                meta = json.loads(meta_path.read_text(encoding='utf-8'))
                expected = meta.get("checksum", "")
                if expected and hashlib.sha256(compressed).hexdigest() != expected:
                    raise SaveCorruptError(f"Slot {slot}: checksum inválido")

            json_bytes = gzip.decompress(compressed)
            save_payload = json.loads(json_bytes)

        save_version = save_payload.get("version", 1)
        if save_version < SAVE_VERSION:
            self._migrar(save_payload)

        return save_payload.get("estado", {})

    def cargar_metadata(self, slot: int, dev: bool = False) -> dict | None:
        """Retorna metadata de un slot sin cargar el estado completo."""
        import json
        from pathlib import Path

        if dev:
            dev_dir = Path(self._dev_dir)
            meta_path = dev_dir / f"dev_{slot}_meta.json"
            if not meta_path.exists():
                return None
            return json.loads(meta_path.read_text(encoding='utf-8'))

        meta = self._repo_saves.get_metadata(slot)
        return meta

    # ── Borrar ──

    def eliminar(self, slot: int, dev: bool = False) -> bool:
        if dev:
            from pathlib import Path
            dev_dir = Path(self._dev_dir)
            for name in [f"dev_{slot}.json", f"dev_{slot}_meta.json"]:
                p = dev_dir / name
                if p.exists():
                    try:
                        p.unlink()
                    except OSError:
                        pass
            return True

        self._repo_saves.eliminar_slot(slot)
        return True

    # ── Listar ──

    def listar_slots(self) -> list[dict]:
        """Lista todos los slots con metadata."""
        return self._repo_saves.listar_slots()

    def get_slot_mas_reciente(self) -> int | None:
        return self._repo_saves.get_slot_mas_reciente()

    def existe_slot(self, slot: int) -> bool:
        return self._repo_saves.existe_slot(slot)

    # ── Serialización ──

    def _serializar(self, estado, schema_include: list[str]) -> dict:
        data = {}
        for key in schema_include:
            valor = self._obtener_attr(estado, key)
            if valor is not None:
                data[key] = self._serializar_objeto(valor)
        return data

    def _obtener_attr(self, estado, attr):
        """Obtiene atributo de estado con soporte para snake (SnakeContext)."""
        if attr == "snake":
            snake_ctx = getattr(estado, "snake_ctx", None)
            if snake_ctx:
                snake = snake_ctx.snake
                return {
                    "body": [list(s) for s in snake.body],
                    "direccion": snake.direccion,
                    "invencible": snake.invencible,
                    "deuda": snake.deuda,
                    "skin_actual": getattr(snake, "skin_actual", "base"),
                }
            return None
        if attr == "inventario":
            inv = getattr(estado, "inventario", None)
            if inv:
                items_dict = {}
                for iid, obj in inv.items.items():
                    items_dict[iid] = {"cantidad": obj.cantidad}
                equipo_dict = {}
                for slot_name, obj in inv.equipo.items():
                    equipo_dict[slot_name] = obj.id
                return {"items": items_dict, "equipo": equipo_dict}
            return None
        if attr == "monedas":
            mon = getattr(estado, "monedas", None)
            if mon:
                return dict(mon._valores)
            return None
        if attr == "flags":
            fl = getattr(estado, "flags", None)
            if fl:
                return dict(fl._data)
            return None
        if attr == "contadores":
            ct = getattr(estado, "contadores", None)
            if ct:
                return dict(ct._valores)
            return None
        if attr == "shop_state":
            ss = getattr(estado, "shop_system", None)
            if ss:
                return ss.get_estado_save()
            return None
        if attr == "nivel_actual":
            lm = getattr(estado, "level_manager", None)
            if lm:
                return lm.obtener_id_actual()
            return None
        if attr == "posicion_mundo":
            snake_ctx = getattr(estado, "snake_ctx", None)
            if snake_ctx and snake_ctx.snake.body:
                return list(snake_ctx.snake.body[0])
            return [0, 0]
        if attr == "progreso_historia":
            return getattr(estado, "progreso_historia", 0)
        if attr == "camera":
            cam = getattr(estado, "camera", None)
            if cam:
                return {"x": cam.x, "y": cam.y}
            return None
        if attr == "habilidades":
            hab = getattr(estado, "habilidades", None)
            if hab:
                return {
                    "habilidad_equipada": getattr(hab, "habilidad_equipada", None),
                    "pp_actual": getattr(hab, "pp_actual", 0),
                }
            return None
        if attr == "segmentos_perdidos":
            sp = getattr(estado, "segmentos_perdidos", [])
            return []
        return getattr(estado, attr, None)

    def _serializar_objeto(self, obj):
        """Serializa recursivamente: dataclasses, dicts, lists, tipos basicos."""
        if obj is None or isinstance(obj, (int, float, str, bool)):
            return obj
        if isinstance(obj, dict):
            return {str(k): self._serializar_objeto(v) for k, v in obj.items()}
        if isinstance(obj, (list, tuple)):
            return [self._serializar_objeto(v) for v in obj]
        if hasattr(obj, "__dataclass_fields__"):
            return {f: self._serializar_objeto(getattr(obj, f))
                    for f in obj.__dataclass_fields__}
        return str(obj)

    # ── Metadata ──

    def _extraer_metadata(self, estado) -> dict:
        lm = getattr(estado, "level_manager", None)
        snake_ctx = getattr(estado, "snake_ctx", None)
        ct = getattr(estado, "contadores", None)

        nivel_id = lm.obtener_id_actual() if lm else ""
        posicion = list(snake_ctx.snake.body[0]) if snake_ctx and snake_ctx.snake.body else [0, 0]
        jefes = ct.get("jefes_derrotados", 0) if ct else 0

        return {
            "timestamp": int(time.time()),
            "nivel_id": nivel_id,
            "posicion": posicion,
            "playtime_segundos": getattr(estado, "playtime_segundos", 0),
            "jefes_derrotados": jefes,
            "thumbnail": "",
        }

    # ── Migraciones ──

    def _migrar(self, save_payload: dict):
        from engine.runtime.save_migrations import migrar
        migrar(save_payload)


class SaveCorruptError(Exception):
    """Save file integrity check failed."""
    pass
