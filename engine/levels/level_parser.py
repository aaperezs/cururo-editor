import json
import os

from engine.configs import *
from engine.configs.enemigos import get_enemigo_config
from engine.entities.arbol import Arbol
from engine.entities.bloque_acero import BloqueAcero
from engine.entities.enemigos import Eldir, EnemyMelee
from engine.entities.food import Food
from engine.entities.hierba_alta import HierbaAlta
from engine.entities.objeto_colision import ObjetoBloqueante, ObjetoColision, ObjetoPeligroso
from engine.entities.pared import Pared
from engine.entities.suelo import Pasto, PastoEsteril, Suelo


def _import_class(path):
    if not path:
        return None
    parts = path.split(".")
    module_path = ".".join(parts[:-1])
    class_name = parts[-1]
    import importlib
    mod = importlib.import_module(module_path)
    return getattr(mod, class_name)


# Behavior → factory override for complex entities
_BEHAVIOR_FACTORIES = {}


def _reg_factory(behavior, fn):
    _BEHAVIOR_FACTORIES[behavior] = fn


def _make_from_behavior(px, py, element_id, element_data, meta, gates_meta, pos, z_layer):
    behavior = element_data.get("behavior", "decorative")
    bdata = LevelParser._behaviors().get(behavior)
    if not bdata:
        return None, None

    # Check for custom factory
    factory = _BEHAVIOR_FACTORIES.get(behavior)
    if factory:
        entity = factory(px, py, element_id, element_data, meta, gates_meta, pos, z_layer)
        return entity, bdata.get("target_list")

    class_path = bdata.get("class_path")
    if not class_path:
        return None, None

    cls = _import_class(class_path)
    if not cls:
        return None, None

    try:
        entity = cls(px, py)
    except Exception:
        try:
            entity = cls(px, py, TAMANO_CELDA, TAMANO_CELDA)
        except Exception:
            return None, None

    if entity is not None:
        entity.z = z_layer
        props = element_data.get("properties", {})
        for key, value in props.items():
            if hasattr(entity, key):
                setattr(entity, key, value)

    return entity, bdata.get("target_list")


# Register complex factories
_reg_factory("food", lambda px, py, eid, ed, meta, gm, pos, z: _make_food(px, py, eid, ed, meta, gm, pos, z))
_reg_factory("enemigo_melee", lambda px, py, eid, ed, meta, gm, pos, z: _make_enemigo_melee(px, py, eid, ed, z))
_reg_factory("enemigo_shooter", lambda px, py, eid, ed, meta, gm, pos, z: _make_eldir(px, py, eid, ed, z))
_reg_factory("boss", lambda px, py, eid, ed, meta, gm, pos, z: _make_boss(px, py, meta, z))
_reg_factory("bloqueante", lambda px, py, eid, ed, meta, gm, pos, z: _make_bloqueante(px, py, eid, ed, z))
_reg_factory("peligroso", lambda px, py, eid, ed, meta, gm, pos, z: _make_peligroso(px, py, eid, ed, meta, gm, pos, z))
_reg_factory("suelo", lambda px, py, eid, ed, meta, gm, pos, z: _make_suelo(px, py, eid, ed, z))
_reg_factory("hierba", lambda px, py, eid, ed, meta, gm, pos, z: _make_hierba(px, py, ed, z))


def _make_food(px, py, sprite_id, element_data, meta, gates_meta, pos, z=0):
    tipo_map = {
        "normal": COMIDA_NORMAL,
        "mana": COMIDA_MANA,
        "dorada": COMIDA_ESPECIAL,
    }
    props = element_data.get("properties", {})
    ft = props.get("food_type", "normal")
    t = tipo_map.get(ft, COMIDA_NORMAL)
    entity = Food(px, py, t)
    entity.z = z
    anim = props.get("animation", "")
    if anim:
        entity.animation = anim
    return entity


def _make_enemigo_melee(px, py, sprite_id, element_data, z=0):
    props = element_data.get("properties", {})
    patron = props.get("patron", "vertical")
    config = get_enemigo_config("melee", patron)
    entity = EnemyMelee(px, py, config["patron"], config["velocidad"])
    entity.z = z
    anim = props.get("animation", "")
    if anim:
        entity.animation = anim
    return entity


def _make_eldir(px, py, sprite_id, element_data, z=0):
    props = element_data.get("properties", {})
    patron = props.get("patron", "shooter_h")
    config = get_enemigo_config("shooter", patron)
    entity = Eldir(
        px, py,
        tipo_movimiento=config["patron"],
        velocidad=config["velocidad"],
        intervalo_disparo=config["intervalo_disparo"],
        velocidad_proyectil=config["velocidad_proyectil"]
    )
    entity.z = z
    anim = props.get("animation", "")
    if anim:
        entity.animation = anim
    return entity


def _make_boss(px, py, meta, z=0):
    arena_file = meta.get("arena", "tronco") if meta else "tronco"
    from engine.entities.boss import Boss as BossEntity
    entity = BossEntity(px, py, arena_file)
    entity.z = z
    return entity


def _make_bloqueante(px, py, sprite_id, element_data, z_layer=0):
    from engine.entities.objeto_colision import ObjetoBloqueante
    from engine.entities.bloque_acero import BloqueAcero
    from engine.entities.arbol import Arbol
    from engine.entities.pared import Pared
    sprite_class_map = {
        "bloque_acero": BloqueAcero,
        "arbol": Arbol,
        "pared": Pared,
    }
    cls = sprite_class_map.get(sprite_id, ObjetoBloqueante)
    try:
        entity = cls(px, py)
    except Exception:
        entity = ObjetoBloqueante(px, py)
    entity.z = z_layer
    if isinstance(entity, ObjetoBloqueante):
        entity.tipo = "bloqueante"
        entity.sprite_id = element_data.get("sprite_id", sprite_id)
    # Default rock destructibility
    if sprite_id in ("roca", "roca_grieta", "roca_hielo", "roca_nieve"):
        entity.destructible = True
        entity.destructible_hp = 2
        if sprite_id == "roca":
            entity.cracked_sprite = "roca_grieta"
    props = element_data.get("properties", {})
    for key, value in props.items():
        setattr(entity, key, value)
    return entity


def _make_peligroso(px, py, sprite_id, element_data, meta=None, gates_meta=None, pos=None, z_layer=0):
    if sprite_id == "pared":
        entity = Pared(px, py, TAMANO_CELDA, TAMANO_CELDA)
    else:
        from engine.entities.objeto_colision import ObjetoPeligroso
        entity = ObjetoPeligroso(px, py, z=z_layer)
    props = element_data.get("properties", {})
    for key, value in props.items():
        if hasattr(entity, key):
            setattr(entity, key, value)
    # Map damage_type → tipo_daño (diferente nombre en behavior vs entidad)
    dt = props.get("damage_type")
    if dt:
        entity.tipo_daño = dt
    return entity


def _make_suelo(px, py, sprite_id, element_data, z=0):
    if sprite_id == "pasto_esteril":
        entity = PastoEsteril(px, py)
    elif sprite_id == "pasto":
        entity = Pasto(px, py)
    else:
        entity = Suelo(px, py)
    entity.z = z
    props = element_data.get("properties", {})
    for key, value in props.items():
        if hasattr(entity, key):
            setattr(entity, key, value)
    return entity


def _make_hierba(px, py, element_data, z=0):
    entity = HierbaAlta(px, py, sprite_id=element_data.get("sprite_id", "hierba_0"))
    entity.z = z
    return entity


class LevelParser:
    """Interpreta un mapa de texto plano o JSON y crea objetos del juego"""

    # Lazy-loaded data providers (can be set externally to break editor dependency)
    _behaviors_cache = None
    _elements_cache = None
    _sprite_registry_cache = None
    _get_multi_tiles_cache = None

    @classmethod
    def _behaviors(cls):
        if cls._behaviors_cache is None:
            from editor.behaviors import BEHAVIORS
            cls._behaviors_cache = BEHAVIORS
        return cls._behaviors_cache

    @classmethod
    def _get_element(cls, element_id):
        if cls._elements_cache is None:
            from editor.elements import _load_elements, get_element
            _load_elements()
            cls._elements_cache = get_element
        return cls._elements_cache(element_id)

    @classmethod
    def _get_element_subtiles(cls, eid):
        if cls._elements_cache is None:
            from editor.elements import _load_elements, get_element_subtiles
            _load_elements()
            # Re-init get_element too
            from editor.elements import get_element
            cls._elements_cache = get_element
            cls._subtiles_cache = get_element_subtiles
        if hasattr(cls, '_subtiles_cache'):
            return cls._subtiles_cache(eid)
        from editor.elements import get_element_subtiles
        cls._subtiles_cache = get_element_subtiles
        return cls._subtiles_cache(eid)

    @classmethod
    def _is_multi_tile_element(cls, eid):
        if cls._elements_cache is None:
            cls._get_element(eid)
        from editor.elements import is_multi_tile_element
        return is_multi_tile_element(eid)

    @classmethod
    def _sprite_registry(cls):
        if cls._sprite_registry_cache is None:
            from editor.sprite_registry import get_sprite_registry
            cls._sprite_registry_cache = get_sprite_registry()
        return cls._sprite_registry_cache

    @classmethod
    def _get_multi_tile_tiles(cls, sprite_id):
        if cls._get_multi_tiles_cache is None:
            from editor.sprite_registry import get_multi_tile_tiles
            cls._get_multi_tiles_cache = get_multi_tile_tiles
        return cls._get_multi_tiles_cache(sprite_id)

    CHAR_MAP = {
        '_': None,
        '.': None,
        '&': None,
        '*': 'pared',
        '#': 'bloque_acero',
        'I': 'inicio',
        'O': 'comida_normal',
        'M': 'comida_mana',
        'G': 'comida_dorada',
        'V': 'enemigo_melee_v',
        'H': 'enemigo_melee_h',
        'C': 'enemigo_melee_c',
        'S': 'enemigo_shooter_h',
        'T': 'enemigo_shooter_v',
        'R': 'roca',
        'A': 'arbol',
        'F': 'roca_hielo',
        'N': 'roca_nieve',
        'Y': 'hierba_0',
        'P': 'portal',
        'B': 'jefe',
        '$': 'cofre',
        '=': 'restricted',
    }

    @staticmethod
    def _parsear_metadatos(lineas):
        metadatos = {}
        for linea in lineas:
            if linea.startswith('# ') and '=' in linea:
                clave_valor = linea[1:].strip()
                clave, valor = clave_valor.split('=', 1)
                metadatos[clave.strip()] = valor.strip()
        return metadatos

    @staticmethod
    def parsear_mapa(mapa_texto, offset_x=0, offset_y=0):
        lineas = mapa_texto.strip().split('\n')
        lineas = [linea.rstrip() for linea in lineas if linea.strip()]

        metadatos = LevelParser._parsear_metadatos(lineas)
        lineas = [l for l in lineas if not l.startswith('# ')]

        alto = len(lineas)
        ancho = max(len(linea) for linea in lineas) if lineas else 0

        paredes = []
        bloqueantes = []
        bloques_acero = []
        enemigos = []
        comidas = []
        portales = []
        salidas = []
        inicio = None
        jefes = []
        arena_boss = None
        zona_boss = None
        hierba_alta = []
        zonas_restringidas = []
        suelos = []

        print(f"Parseando mapa {ancho}x{alto}")

        for y, linea in enumerate(lineas):
            for x, char in enumerate(linea):
                pos_x = x * TAMANO_CELDA
                pos_y = y * TAMANO_CELDA

                if char not in LevelParser.CHAR_MAP:
                    continue

                sprite_id = LevelParser.CHAR_MAP[char]

                if sprite_id is None:
                    continue

                # Legacy parsing uses sprite_id to find element
                el = LevelParser._get_element(sprite_id)
                element_id = sprite_id
                element_data = el or {"sprite_id": sprite_id, "behavior": "decorative", "properties": {}}

                entity, target = _make_from_behavior(
                    pos_x, pos_y, element_id, element_data,
                    metadatos, {}, (x, y), 0
                )

                if target == "paredes" or (hasattr(entity, '__class__') and entity.__class__.__name__ == "Pared"):
                    if sprite_id == "pared":
                        paredes.append(entity)
                    else:
                        pass

                if entity is None:
                    continue

                if target == "collidables":
                    if isinstance(entity, Pared):
                        paredes.append(entity)
                    elif isinstance(entity, (BloqueAcero, Arbol)):
                        bloques_acero.append(entity)
                    elif isinstance(entity, HierbaAlta):
                        hierba_alta.append(entity)
                    elif isinstance(entity, ObjetoBloqueante):
                        bloqueantes.append(entity)
                    elif isinstance(entity, ObjetoPeligroso):
                        paredes.append(entity)
                    else:
                        bloqueantes.append(entity)

                elif target == "suelos":
                    suelos.append(entity)
                elif target == "hierba_alta":
                    hierba_alta.append(entity)
                elif target == "comidas":
                    comidas.append(entity)
                elif target == "enemigos":
                    enemigos.append(entity)
                elif target == "jefes":
                    if entity:
                        from engine.entities.boss import Boss
                        if isinstance(entity, Boss):
                            arena_file = metadatos.get('arena', None)
                            zona_boss = (pos_x, pos_y, arena_file)
                            jefes.append(entity)

        return {
            'paredes': paredes,
            'bloqueantes': bloqueantes,
            'bloques_acero': bloques_acero,
            'enemigos': enemigos,
            'comidas': comidas,
            'portales': portales,
            'salidas': salidas,
            'inicio': inicio,
            'jefes': jefes,
            'arena_boss': arena_boss,
            'zona_boss': zona_boss,
            'hierba_alta': hierba_alta,
            'suelos': suelos,
            'zonas_restringidas': zonas_restringidas,
            'grid': grid,
            'ancho': ancho * TAMANO_CELDA,
            'alto': alto * TAMANO_CELDA,
        }

    # --- v2 (sprite-id / element-id based) ---

    @staticmethod
    def parsear_mapa_v2_con_capas(layers_data, meta=None, multi_tiles=None):
        meta = meta or {}
        multi_tiles = multi_tiles or {}
        all_results = []

        # Build per-layer multi_tiles
        layer_mt = {}
        for (gx, gy, z), info in multi_tiles.items():
            layer_mt.setdefault(z, {})[(gx, gy)] = info

        for ld in layers_data:
            z = ld.get("z", 0)
            data = ld.get("data", {})
            result = LevelParser.parsear_mapa_v2(data, meta, z_layer=z, multi_tiles=layer_mt.get(z, {}))
            if result:
                all_results.append(result)

        if not all_results:
            return None

        merged = {}
        keys = ["paredes", "bloqueantes", "bloques_acero", "enemigos", "comidas",
                "portales", "salidas", "hierba_alta",
                "suelos", "decorativos", "zonas_restringidas"]

        for k in keys:
            merged[k] = []
        merged["jefes"] = []
        merged["arena_boss"] = None
        merged["zona_boss"] = None
        merged["inicio"] = None

        for res in all_results:
            for k in keys:
                merged[k].extend(res.get(k, []))
            if res.get("inicio") and (not merged.get("inicio") or merged["inicio"] is None):
                merged["inicio"] = res["inicio"]
            if res.get("arena_boss"):
                merged["arena_boss"] = res["arena_boss"]
            if res.get("zona_boss"):
                merged["zona_boss"] = res["zona_boss"]
            if res.get("jefes"):
                merged["jefes"].extend(res["jefes"])

        # Composite resolved_grid from all layers (higher z overwrites lower z)
        merged["grid"] = {}
        merged["grid_por_capa"] = {}
        for ld, res in zip(layers_data, all_results):
            z = ld.get("z", 0)
            res_gpc = res.get("grid_por_capa", {})
            for sub_z, sub_g in res_gpc.items():
                if sub_z not in merged["grid_por_capa"]:
                    merged["grid_por_capa"][sub_z] = {}
                merged["grid_por_capa"][sub_z].update(sub_g)
                merged["grid"].update(sub_g)

        merged["ancho"] = all_results[0]["ancho"] if all_results else 0
        merged["alto"] = all_results[0]["alto"] if all_results else 0
        return merged

    @staticmethod
    def parsear_mapa_v2(data, meta=None, z_layer=0, multi_tiles=None):
        ancho = data.get("ancho", 0)
        alto = data.get("alto", 0)
        raw_grid = data.get("grid", {})
        meta = meta or {}
        multi_tiles = multi_tiles or {}

        grid = {}
        for key, sprite_id in raw_grid.items():
            if "," in key:
                parts = key.split(",")
                gx, gy = int(parts[0]), int(parts[1])
                grid[(gx, gy)] = sprite_id

        # Build lookup for multi-tile sub-cells
        mt_cells = {}  # (gx, gy) -> (anchor_gx, anchor_gy, subtiles_list)
        mt_coords_cache = {}
        for (ax, ay), info in multi_tiles.items():
            eid = info.get("element_id", "")
            if LevelParser._is_multi_tile_element(eid):
                el = LevelParser._get_element(eid)
                props = el.get("properties", {}) if el else {}
                rows = props.get("tile_rows", 1)
                cols = props.get("tile_cols", 1)
                subtiles = LevelParser._get_element_subtiles(eid)
                if not subtiles:
                    reg_tiles = LevelParser._get_multi_tile_tiles(el.get("sprite_id", ""))
                    subtiles = [dict(t) for t in reg_tiles]
                mt_coords_cache[(ax, ay)] = (rows, cols, subtiles)
                for r in range(rows):
                    for c in range(cols):
                        mt_cells[(ax + c, ay + r)] = (ax, ay, subtiles)

        paredes = []
        bloqueantes = []
        bloques_acero = []
        enemigos = []
        comidas = []
        portales = []
        salidas = []
        inicio = None
        jefes = []
        arena_boss = None
        zona_boss = None
        hierba_alta = []
        zonas_restringidas = []
        suelos = []
        decorativos = []

        print(f"Parseando mapa v2 {ancho}x{alto} Z={z_layer} [multi_tiles: {len(multi_tiles)}]")

        resolved_grid = {}
        subz_grid = {}  # {sub_z: {(gx, gy): sprite_file}} for multi-tile sub-tiles at different Z
        for (gx, gy), element_id in grid.items():
            el = LevelParser._get_element(element_id)
            if el:
                sid = el.get("sprite_id", element_id)
            else:
                sid = element_id
            reg = LevelParser._sprite_registry().get(sid)
            resolved_grid[(gx, gy)] = reg.get("file", sid) if reg else sid

        # Set of cells to skip (non-anchor multi-tile cells)
        skip_cells = set()

        # Process multi-tile anchors first
        for (gx, gy), element_id in list(grid.items()):
            cell_key = (gx, gy)
            if cell_key not in mt_cells:
                continue
            anchor_gx, anchor_gy, subtiles = mt_cells[cell_key]
            # Only process anchor (first cell of the multi-tile)
            if anchor_gx != gx or anchor_gy != gy:
                continue
            el = LevelParser._get_element(element_id)
            if not el:
                continue
            rows, cols, _ = mt_coords_cache.get((anchor_gx, anchor_gy), (1, 1, []))
            # Mark all sub-cells as skip
            for r in range(rows):
                for c in range(cols):
                    skip_cells.add((anchor_gx + c, anchor_gy + r))
            # Remove anchor from resolved_grid (sub-tiles will be added)
            resolved_grid.pop((gx, gy), None)
            # Create entity for each sub-tile
            for st in subtiles:
                col = st.get("col", 0)
                row = st.get("row", 0)
                sx = (anchor_gx + col) * TAMANO_CELDA
                sy = (anchor_gy + row) * TAMANO_CELDA
                st_behavior = st.get("behavior", "decorative")
                st_z = st.get("z", z_layer)
                st_el_data = {"sprite_id": element_id, "behavior": st_behavior, "properties": st.get("properties", {})}
                st_eid = f"{element_id}_{col}_{row}"
                entity, target = _make_from_behavior(
                    sx, sy, st_eid, st_el_data, meta, {}, (anchor_gx + col, anchor_gy + row), st_z
                )
                # Re-resolve grid for sub-tile sprite
                st_sid = el.get("sprite_id", element_id)
                reg_tiles = LevelParser._get_multi_tile_tiles(st_sid)
                st_file = None
                for rt in reg_tiles:
                    if rt.get("col") == col and rt.get("row") == row:
                        st_file = rt.get("file")
                        break
                # Place sub-tile in the correct per-Z grid
                target_z = st_z if st_z != z_layer else z_layer
                if st_file:
                    subz_grid.setdefault(target_z, {})[(anchor_gx + col, anchor_gy + row)] = st_file
                # Remove from resolved_grid if it was added there (it will render via subz_grid)
                resolved_grid.pop((anchor_gx + col, anchor_gy + row), None)
                if entity is None:
                    continue
                if hasattr(entity, 'z'):
                    entity.z = st_z
                # Route entity
                if target == "collidables":
                    if isinstance(entity, Pared): paredes.append(entity)
                    elif isinstance(entity, (BloqueAcero, Arbol)): bloques_acero.append(entity)
                    elif isinstance(entity, HierbaAlta): hierba_alta.append(entity)
                    elif isinstance(entity, ObjetoBloqueante): bloqueantes.append(entity)
                    elif isinstance(entity, ObjetoPeligroso): paredes.append(entity)
                    else: bloqueantes.append(entity)
                elif target == "suelos": suelos.append(entity)
                elif target == "hierba_alta": hierba_alta.append(entity)
                elif target == "comidas": comidas.append(entity)
                elif target == "enemigos": enemigos.append(entity)
                elif target == "jefes":
                    if entity: jefes.append(entity)

        for (gx, gy), element_id in grid.items():
            # Skip multi-tile cells (already processed above)
            if (gx, gy) in skip_cells:
                continue
            # Look up element from elementos.json
            el = LevelParser._get_element(element_id)
            if el is None:
                info = LevelParser._sprite_registry().get(element_id)
                if not info:
                    continue
                continue

            behavior = el.get("behavior", "decorative")
            if behavior == "spawn":
                resolved_grid.pop((gx, gy), None)
                continue

            # Any element with animation that doesn't have its own animation rendering
            # (decorative, suelo) gets a Decorativo entity instead
            anim_behaviors = ("decorative", "suelo")
            props = el.get("properties", {})
            anim = props.get("animation", "")
            if behavior in anim_behaviors and anim:
                px = gx * TAMANO_CELDA
                py = gy * TAMANO_CELDA
                from engine.entities.decorativo import Decorativo
                entity = Decorativo(px, py)
                entity.z = z_layer
                entity.sprite_id = el.get("sprite_id", element_id)
                entity.animation = anim
                resolved_grid.pop((gx, gy), None)
                decorativos.append(entity)
                continue

            if behavior == "decorative":
                continue

            px = gx * TAMANO_CELDA
            py = gy * TAMANO_CELDA

            entity, target = _make_from_behavior(
                px, py, element_id, el, meta, {}, (gx, gy), z_layer
            )

            if entity is None:
                continue
            if entity is not None and type(entity).dibujar is not ObjetoColision.dibujar and not isinstance(entity, Suelo):
                resolved_grid.pop((gx, gy), None)

            if target == "collidables":
                if isinstance(entity, Pared):
                    paredes.append(entity)
                elif isinstance(entity, (BloqueAcero, Arbol)):
                    bloques_acero.append(entity)
                elif isinstance(entity, HierbaAlta):
                    hierba_alta.append(entity)
                elif isinstance(entity, ObjetoBloqueante):
                    bloqueantes.append(entity)
                elif isinstance(entity, ObjetoPeligroso):
                    paredes.append(entity)
                else:
                    bloqueantes.append(entity)
            elif target == "suelos":
                suelos.append(entity)
            elif target == "hierba_alta":
                hierba_alta.append(entity)
            elif target == "comidas":
                comidas.append(entity)
            elif target == "enemigos":
                enemigos.append(entity)
            elif target == "jefes":
                if entity:
                    jefes.append(entity)
            elif target == "decorativos":
                if entity:
                    decorativos.append(entity)

        # Spawn now comes from gameplay.json, not from grid/meta
        inicio = None

        # Build grid_por_capa merging subz_grid entries into their Z layers
        all_grid = dict(resolved_grid)
        grid_por_capa = {z_layer: dict(resolved_grid)}
        for sub_z, sub_g in subz_grid.items():
            grid_por_capa.setdefault(sub_z, {}).update(sub_g)
            all_grid.update(sub_g)

        return {
            'paredes': paredes,
            'bloqueantes': bloqueantes,
            'bloques_acero': bloques_acero,
            'enemigos': enemigos,
            'comidas': comidas,
            'portales': portales,
            'salidas': salidas,
            'inicio': inicio,
            'jefes': jefes,
            'arena_boss': arena_boss,
            'zona_boss': zona_boss,
            'hierba_alta': hierba_alta,
            'suelos': suelos,
            'decorativos': decorativos,
            'zonas_restringidas': zonas_restringidas,
            'grid': all_grid,
            'grid_por_capa': grid_por_capa,
            'subz_grid': subz_grid,
            'ancho': ancho * TAMANO_CELDA,
            'alto': alto * TAMANO_CELDA,
        }

    @staticmethod
    def cargar_nivel(nivel_texto, offset_x=0, offset_y=0, meta=None):
        stripped = nivel_texto.strip()
        if stripped.startswith("{"):
            try:
                data = json.loads(stripped)
                return LevelParser.parsear_mapa_v2(data, meta)
            except (json.JSONDecodeError, KeyError):
                pass
        return LevelParser.parsear_mapa(nivel_texto, offset_x, offset_y)

    @staticmethod
    def cargar_nivel_desde_archivo(ruta, meta_ruta=None):
        if not os.path.exists(ruta):
            return None
        with open(ruta, "r", encoding="utf-8") as f:
            contenido = f.read()
        meta = None
        if meta_ruta and os.path.exists(meta_ruta):
            with open(meta_ruta, "r", encoding="utf-8") as f:
                meta = json.load(f)
        return LevelParser.cargar_nivel(contenido, meta=meta)
