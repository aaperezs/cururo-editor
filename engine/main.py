# main.py
import os
import sys

# Editor root contains 'engine/' package. When engine is at editor/engine/,
# editor_root = editor/. When engine is at project/engine/, editor/ won't exist here.
_engine_dir = os.path.dirname(os.path.abspath(__file__))
_editor_root = os.path.dirname(_engine_dir)
if os.path.isdir(os.path.join(_editor_root, "engine")):
    sys.path.insert(0, _editor_root)
# Also add grandparent so 'editor.project' is importable during development.
_grandparent = os.path.dirname(_editor_root)
if _grandparent not in sys.path:
    sys.path.insert(0, _grandparent)

_MODO_TEST = "--test" in sys.argv

_PROJECT_PATH = None
for _i, _arg in enumerate(sys.argv):
    if _arg == "--project" and _i + 1 < len(sys.argv):
        _PROJECT_PATH = sys.argv[_i + 1]
    elif _arg != "--test" and not _arg.startswith("-") and os.path.isdir(_arg):
        _PROJECT_PATH = _arg
if _PROJECT_PATH:
    _PROJECT_PATH = os.path.abspath(_PROJECT_PATH)
elif getattr(sys, "frozen", False):
    _PROJECT_PATH = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
else:
    _PROJECT_PATH = os.path.dirname(os.path.abspath(__file__))


import pygame

# Set up project path for editor data modules
try:
    from editor.project import set_current_project
    set_current_project(_PROJECT_PATH)
except ImportError:
    pass

# Resolución base del proyecto (la define el desarrollador en cururo.json).
# Debe fijarse ANTES de que los demás módulos importen ANCHO/ALTO.
if not _MODO_TEST:
    import json as _json
    try:
        with open(os.path.join(_PROJECT_PATH, "cururo.json"), encoding="utf-8") as _f:
            _manifest_res = _json.load(_f)
        _graphics_res = _manifest_res.get("graphics", {}).get("resolution")
        _graphics_scale = _manifest_res.get("graphics", {}).get("pixel_art_scale", 1)
        if not isinstance(_graphics_scale, int):
            try:
                _graphics_scale = int(_graphics_scale)
            except Exception:
                _graphics_scale = 1
        _manifest_res = _graphics_res if _graphics_res is not None else _manifest_res.get("resolution", "800x600")
        if isinstance(_manifest_res, (list, tuple)) and len(_manifest_res) == 2:
            _base_w = int(_manifest_res[0])
            _base_h = int(_manifest_res[1])
        elif isinstance(_manifest_res, dict):
            _base_w = int(_manifest_res.get("w", 800))
            _base_h = int(_manifest_res.get("h", 600))
        else:
            _base_w, _base_h = (int(p) for p in str(_manifest_res).strip().lower().replace(" ", "").split("x"))
        import engine.configs.constants as _const_res
        _const_res.ANCHO, _const_res.ALTO = _base_w, _base_h
        import engine.configs as _cfg_res
        _cfg_res.ANCHO, _cfg_res.ALTO = _base_w, _base_h
    except Exception:
        pass
from engine.configs import *
from engine.entities.food import Food
from engine.entities.segmento_perdido import SegmentoPerdido
from engine.game_state import GameState
from engine.systems.vn_state import finalizar_minijuego
from engine.handlers.input_manager import InputManager
from engine.managers.colision_manager import ColisionManager
from engine.managers.combate_manager import CombateManager
from engine.managers.comida_manager import ComidaManager
from engine.systems.event_bus import EventoObjetoDestruido
from engine.systems.ui import UI
from engine.systems.choice_box import ChoiceBox


# ============================================
# INICIALIZACIÓN
# ============================================

pygame.init()
pygame.mixer.init(frequency=22050, size=-16, channels=8)

# Cargar config del proyecto una vez (pantallas, ventana, plataforma, calidad)
_SCREENS_CFG = {}
_PROJECT_CATEGORY = "snake_rpg"
_PROJECT_TITLE = None
_PROJECT_PLATFORM = "desktop"
_PROJECT_QUALITY = "medium"
_PROJECT_FULLSCREEN = False
if not _MODO_TEST:
    import json
    try:
        with open(os.path.join(_PROJECT_PATH, "cururo.json"), encoding="utf-8") as f:
            manifest = json.load(f)
        _SCREENS_CFG = manifest.get("screens", {})
        _PROJECT_CATEGORY = manifest.get("category", "snake_rpg")
        _window = manifest.get("window")
        if isinstance(_window, dict):
            _PROJECT_TITLE = _window.get("title") or manifest.get("name")
            _PROJECT_FULLSCREEN = bool(_window.get("fullscreen", False))
        else:
            _PROJECT_TITLE = manifest.get("name")
        _PROJECT_PLATFORM = manifest.get("platform", "desktop")
        _PROJECT_QUALITY = manifest.get("quality", "medium")
    except Exception:
        pass

# Preferencias del usuario final (resolución de pantalla) sobre las del manifest.
if not _MODO_TEST:
    try:
        from engine.systems.user_prefs import load as _load_prefs, parse_resolution as _parse_prefs_res
        _prefs = _load_prefs()
    except Exception:
        _prefs = None
else:
    _prefs = None
if _prefs:
    _prefs_size = _parse_prefs_res(_prefs.get("resolution", "auto"))
    _prefs_fullscreen = bool(_prefs.get("fullscreen", False))
    _fullscreen = _prefs_fullscreen
else:
    _prefs_size = None
    _fullscreen = _PROJECT_FULLSCREEN or _PROJECT_PLATFORM == "mobile"

# Calcular window_size con pixel_art_scale si no hay prefs del usuario
if _prefs_size is None:
    _window_size = (_base_w * _graphics_scale, _base_h * _graphics_scale)
else:
    _window_size = _prefs_size

from engine.display import setup as _display_setup, present as _display_present, get_buffer as _display_buffer, set_letterbox_fill as _display_set_fill

pantalla = _display_setup(
    window_size=_window_size,
    fullscreen=_fullscreen,
)
pygame.display.set_caption(_PROJECT_TITLE or "Cururo")
reloj = pygame.time.Clock()


# ============================================
# ALERTA DE PROYECTO INVALIDO
# ============================================

def _alerta(titulo, detalle):
    """Pantalla de aviso que bloquea hasta que el usuario presiona una tecla."""
    from display import get_buffer as _get_buffer, present as _present
    surf = _get_buffer()
    if surf is None:
        return
    pygame.font.init()
    font = pygame.font.SysFont("Arial", 20, bold=True)
    font_d = pygame.font.SysFont("Arial", 16)
    font_h = pygame.font.SysFont("Arial", 15)
    surf.fill((18, 20, 26))
    w, h = surf.get_size()
    t = font.render(titulo, True, (230, 180, 90))
    surf.blit(t, ((w - t.get_width()) // 2, h // 2 - 70))
    dy = h // 2 - 20
    for linea in detalle:
        l = font_d.render(linea, True, (200, 205, 210))
        surf.blit(l, ((w - l.get_width()) // 2, dy))
        dy += 26
    hint = font_h.render("Presiona ENTER o ESC para salir", True, (120, 130, 140))
    surf.blit(hint, ((w - hint.get_width()) // 2, h - 60))
    _present()
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return
            if event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_RETURN, pygame.K_ESCAPE, pygame.K_SPACE):
                    return
        pygame.time.wait(30)


def _validar_proyecto():
    """Devuelve (titulo, detalle) si el proyecto no tiene mapa/inicio, o (None, None)."""
    import json
    import os
    from engine.levels.level_manager import LevelManager
    lm = LevelManager()
    if not lm.tiene_mapas():
        return ("Debes crear un mapa",
                ["El proyecto no tiene mapas.", "Crea un mapa y configura el inicio del personaje en el editor."])
    
    gameplay_path = os.path.join(os.path.dirname(__file__), "data", "gameplay.json")
    try:
        with open(gameplay_path, "r", encoding="utf-8") as f:
            gameplay = json.load(f)
        spawn = gameplay.get("spawn")
        if not spawn or not spawn.get("map_id"):
            return ("Debes definir el punto de inicio",
                    ["No hay spawn definido en gameplay.json.",
                     "Abre el editor y coloca el sprite 'inicio' en algún mapa."])
        if spawn["map_id"] not in lm.niveles:
            return ("El nivel de inicio no existe",
                    [f"El nivel '{spawn['map_id']}' definido como inicio no existe.",
                     "Verifica el campo 'spawn.map_id' en gameplay.json."])
    except (json.JSONDecodeError, IOError):
        return ("Error al leer configuración",
                ["No se pudo leer gameplay.json.",
                 "Verifica que el archivo exista y sea válido."])
    
    return (None, None)


# ============================================
# FUNCIONES AUXILIARES (definidas una vez, usan `estado` como global)
# ============================================

def mostrar_mensaje(texto, duracion=60):
    estado.mensaje_temporal = texto
    estado.tiempo_mensaje = duracion



def perder_segmentos(cantidad):
    """Maneja la pérdida de segmentos - NUNCA baja de 3, pero si tiene 3 muere"""
    if estado.snake.invencible or estado.god_mode:
        return False

    longitud_actual = estado.snake.get_longitud()

    if longitud_actual <= 3:
        estado.game_over = True
        estado.death_cause = f"Longitud mínima ({longitud_actual} segs)"
        mostrar_mensaje("¡Has muerto! (longitud mínima)", 60)
        cabeza = estado.snake.get_cabeza()
        if cabeza:
            estado.particles.crear_explosion(
                cabeza[0] + TAMANO_CELDA//2,
                cabeza[1] + TAMANO_CELDA//2,
                30, ROJO
            )
        return True

    max_perder = longitud_actual - 3
    if cantidad > max_perder:
        cantidad = max_perder

    if cantidad <= 0:
        return False

    perdidos = estado.snake.perder_segmentos(cantidad)

    if perdidos:
        for pos in perdidos:
            if pos:
                segmento = SegmentoPerdido(pos[0], pos[1], estado.nivel_ancho, estado.nivel_alto)
                estado.segmentos_perdidos.append(segmento)

        cabeza = estado.snake.get_cabeza()
        if cabeza:
            estado.particles.crear_explosion(
                cabeza[0] + TAMANO_CELDA//2,
                cabeza[1] + TAMANO_CELDA//2,
                cantidad=15, color=VERDE
            )

        mostrar_mensaje(f"¡Perdiste {len(perdidos)} segmentos!", 60)

        if estado.snake.get_longitud() <= 3:
            pass

    return False

def recoger_segmentos():
    """Recoge segmentos perdidos"""
    cabeza = estado.snake.get_cabeza()
    if not cabeza:
        return

    cabeza_rect = pygame.Rect(cabeza[0], cabeza[1], TAMANO_CELDA, TAMANO_CELDA)

    for segmento in estado.segmentos_perdidos[:]:
        if segmento.esta_vivo() and not segmento.recogido:
            if cabeza_rect.colliderect(segmento.get_rect()):
                segmento.recogido = True
                estado.snake.crecer(1)
                cx = segmento.x + TAMANO_CELDA // 2
                cy = segmento.y + TAMANO_CELDA // 2
                estado.text_service.spawn("+1", cx, cy - 10, 30, VERDE_CLARO)
                estado.particles.crear_anillo_sonico(cx, cy, (100, 255, 100))
                estado.segmentos_perdidos.remove(segmento)
        elif not segmento.esta_vivo() and not segmento.recogido:
            estado.segmentos_perdidos.remove(segmento)



# ============================================
# FUNCIÓN DE DIBUJADO
# ============================================

def dibujar():
    from engine.utils.sprite_manager import obtener as obtener_sprite

    # ── VN Mode ──
    if estado.fondo_activo:
        sp = obtener_sprite(estado.fondo_activo)
        if sp:
            modo = getattr(estado, "fondo_modo", "fill")
            iw, ih = sp.get_size()
            if modo == "fill":
                sp = pygame.transform.scale(sp, (ANCHO, ALTO))
            elif modo == "fit":
                scale = min(ANCHO / iw, ALTO / ih)
                nw, nh = int(iw * scale), int(ih * scale)
                sp = pygame.transform.smoothscale(sp, (nw, nh))
                surf = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
                surf.fill((0, 0, 0))
                surf.blit(sp, ((ANCHO - nw) // 2, (ALTO - nh) // 2))
                sp = surf
            elif modo == "center":
                surf = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
                surf.fill((0, 0, 0))
                surf.blit(sp, ((ANCHO - iw) // 2, (ALTO - ih) // 2))
                sp = surf
            pantalla.blit(sp, (0, 0))
        else:
            pantalla.fill((0, 0, 0))
        for info in estado.personajes_visibles.values():
            sp_char = obtener_sprite(info["sprite"])
            if sp_char:
                px = {0: 100, 1: ANCHO // 2 - sp_char.get_width() // 2, 2: ANCHO - 100 - sp_char.get_width()}.get(info["posicion"], ANCHO // 2 - sp_char.get_width() // 2)
                py = ALTO - sp_char.get_height() - 40
                pantalla.blit(sp_char, (px, py))
        ui.dibujar(pantalla, estado.snake, estado.comida, estado.mensaje_temporal,
                   estado.monedas)
        if estado.mostrando_opciones:
            choice_box.dibujar(pantalla, estado.opciones, estado.opcion_seleccionada,
                               getattr(estado, "opcion_pregunta", ""))
        return

    pantalla.fill(FOREST_BG)
    ox, oy = estado.camera.get_offset()
    pasto_sprite = obtener_sprite("pasto")
    deco_sprites = [obtener_sprite(f"deco_{i}") for i in range(4)]
    deco_hash = (estado.nivel_ancho + estado.nivel_alto) ^ 42

    en_arena = estado.arena_boss.activa and estado.boss and estado.boss.vivo
    z_overlay = []

    if not en_arena or estado.arena_boss.es_nivel_completo:
        cols_totales = estado.nivel_ancho // TAMANO_CELDA
        rows_totales = estado.nivel_alto // TAMANO_CELDA
        first_col = max(0, -ox // TAMANO_CELDA)
        first_row = max(0, -oy // TAMANO_CELDA)
        last_col = min(cols_totales - 1, (-ox + ANCHO) // TAMANO_CELDA)
        last_row = min(rows_totales - 1, (-oy + ALTO) // TAMANO_CELDA)
        z_layers = sorted(estado.grid_por_capa.keys())
        z_ground = [z for z in z_layers if z <= 1]
        z_overlay[:] = [z for z in z_layers if z >= 2]

        def _draw_tiles(z_list):
            for row in range(first_row, last_row + 1):
                for col in range(first_col, last_col + 1):
                    px = col * TAMANO_CELDA + ox
                    py = row * TAMANO_CELDA + oy
                    for z in z_list:
                        layer_grid = estado.grid_por_capa[z]
                        sprite_id = layer_grid.get((col, row))
                        if sprite_id:
                            sp = obtener_sprite(sprite_id)
                            if sp:
                                pantalla.blit(sp, (px, py))

        # Pass 1: ground tiles (Z <= Z_MAPA_PRINCIPAL)
        for row in range(first_row, last_row + 1):
            for col in range(first_col, last_col + 1):
                px = col * TAMANO_CELDA + ox
                py = row * TAMANO_CELDA + oy
                pantalla.blit(pasto_sprite, (px, py))
                d = (col * 7 + row * 13 + deco_hash) % 25
                if d < 4 and deco_sprites[d]:
                    pantalla.blit(deco_sprites[d], (px, py))
                for z in z_ground:
                    layer_grid = estado.grid_por_capa[z]
                    sprite_id = layer_grid.get((col, row))
                    if sprite_id:
                        sp = obtener_sprite(sprite_id)
                        if sp:
                            pantalla.blit(sp, (px, py))

        # Entities (Z-sorted)
        _entity_groups = {}
        _entity_groups = {}
        def _add_entity(e, z_attr="z"):
            z = getattr(e, z_attr, 0)
            _entity_groups.setdefault(z, []).append(e)
        for e in estado.decorativos:  _add_entity(e)
        for e in estado.hierba_alta:  _add_entity(e)
        for e in estado.paredes:      _add_entity(e)
        for e in estado.bloqueantes:  _add_entity(e)
        for e in estado.bloques_acero: _add_entity(e)
        for z in sorted(_entity_groups.keys()):
            for e in _entity_groups[z]:
                e.dibujar(pantalla, ox, oy)
        # Food always drawn on top of all Z-sorted entities
        if comida_manager.comida_disponible() and estado.comida is not None:
            estado.comida.dibujar(pantalla, ox, oy)

    # Always draw arena boss (handles inactive/active internally)
    estado.arena_boss.dibujar(pantalla, ox, oy)
    estado.portal_boss.dibujar(pantalla, ox, oy)

    if not estado.arena_boss.activa:
        for enemigo in estado.enemigos:
            enemigo.dibujar(pantalla, ox, oy)

    for segmento in estado.segmentos_perdidos:
        segmento.dibujar(pantalla, ox, oy)

    habilidad_equipada = estado.habilidades.get_habilidad_equipada()
    tiene_manto = (habilidad_equipada and
                  habilidad_equipada.get("efecto") == "manto" and
                  estado.habilidades.get_pp_actual() > 0)

    estado.snake.dibujar(pantalla, tiene_manto, ox, oy)
    estado.particles.dibujar(pantalla, ox, oy)

    # Pass 2: overlay tiles (Z > Z_MAPA_PRINCIPAL) — se dibujan encima de entidades y snake
    if not en_arena and z_overlay:
        for row in range(first_row, last_row + 1):
            for col in range(first_col, last_col + 1):
                px = col * TAMANO_CELDA + ox
                py = row * TAMANO_CELDA + oy
                for z in z_overlay:
                    layer_grid = estado.grid_por_capa.get(z, {})
                    sprite_id = layer_grid.get((col, row))
                    if sprite_id:
                        sp = obtener_sprite(sprite_id)
                        if sp:
                            pantalla.blit(sp, (px, py))

    # Textos flotantes (nuevo sistema)
    estado.text_service.draw(pantalla)
    # Legacy floating texts
    fuente_flotante = pygame.font.SysFont("Arial", 18, bold=True)
    for tf in estado.textos_flotantes:
        alpha = int(255 * (tf["timer"] / max(tf["max_timer"], 1)))
        color = (*tf["color"][:3], alpha)
        surf = pygame.Surface((60, 30), pygame.SRCALPHA)
        txt = fuente_flotante.render(tf["texto"], True, color[:3])
        txt.set_alpha(alpha)
        surf.blit(txt, (30 - txt.get_width() // 2, 0))
        pantalla.blit(surf, (tf["x"] + ox - 30, tf["y"] + oy))

    ui.dibujar(pantalla, estado.snake, estado.comida, estado.mensaje_temporal,
               estado.monedas)
    estado.habilidades.dibujar_ui(pantalla)

    fuente = pygame.font.SysFont("Arial", 12)
    texto = fuente.render("E: Interactuar | Q: Habilidad | TAB: Cambiar", True, GRIS)
    pantalla.blit(texto, (ANCHO - 310, 80))

    # Oscurecer fondo durante diálogo post-boss para evitar teleport visual
    if estado.dialogo.activo and estado.arena_boss.activa and estado.boss:
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        pantalla.blit(overlay, (0, 0))

    # ── Opciones de diálogo (choice box) ──
    if estado.mostrando_opciones:
        choice_box.dibujar(pantalla, estado.opciones, estado.opcion_seleccionada,
                           getattr(estado, "opcion_pregunta", ""))

# ============================================
# MODO NOVELA VISUAL (usa scene_player en lugar del loop de snake)
# ============================================

def _run_vn_mode(pantalla):
    from engine.systems.scene_player import load_scenes, find_first_scene, get_chapters
    from engine.systems.screen_manager import ScreenManager
    if not _MODO_TEST:
        sm = ScreenManager(pantalla, _SCREENS_CFG)
        sm.run()
        pantalla = _display_buffer()
    scenes_data = load_scenes()
    chapters = get_chapters(scenes_data)
    if not chapters:
        return
    from engine.systems.vn_state import VnGameState, finalizar_minijuego
    estado = VnGameState()
    estado.fondo_activo = "fondo_ejemplo"
    estado.fondo_modo = "fill"
    reloj_vn = pygame.time.Clock()
    from engine.utils.sprite_manager import obtener as obtener_sprite
    def _iniciar_arbol(estado_ref, dialogo_id):
        if "/" not in dialogo_id:
            return
        personaje, contexto = dialogo_id.split("/", 1)
        sm = estado_ref.stack_manager
        sm._arbol_dialogo = {"personaje": personaje, "contexto": contexto, "nid_actual": None, "_iniciado": False}
        sm._avanzar_arbol_dialogo(estado_ref)
        sm._bloqueo_por = "dialogo_tree"

    first = find_first_scene(scenes_data)
    if first:
        ctx = first.get("dialogo_id", "")
        _iniciar_arbol(estado, ctx)
    estado._scene_navegacion = None
    while True:
        reloj_vn.tick(30)
        _display_set_fill(obtener_sprite(estado.fondo_activo) if estado.fondo_activo else None)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            if event.type == pygame.KEYDOWN:
                if estado.mostrando_minijuego:
                    estado.sistema_minijuego.handle_event(event)
                    continue
                if estado.dialogo.activo:
                    if event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        estado.dialogo.avanzar()
                elif estado.mostrando_opciones:
                    if event.key == pygame.K_UP:
                        estado.opcion_seleccionada = max(0, estado.opcion_seleccionada - 1) if estado.opcion_seleccionada >= 0 else len(estado.opciones) - 1
                    elif event.key == pygame.K_DOWN:
                        estado.opcion_seleccionada = (estado.opcion_seleccionada + 1) % len(estado.opciones) if estado.opcion_seleccionada >= 0 else 0
                    elif event.key in (pygame.K_SPACE, pygame.K_RETURN):
                        if 0 <= estado.opcion_seleccionada < len(estado.opciones):
                            opcion = estado.opciones[estado.opcion_seleccionada]
                            estado.mostrando_opciones = False
                            estado.stack_manager.ejecutar_secuencia(opcion.get("acciones", []))
                elif event.key == pygame.K_ESCAPE:
                    return
        estado.dialogo.actualizar()
        estado.stack_manager.actualizar(estado)
        if estado._scene_navegacion:
            nav = estado._scene_navegacion
            estado._scene_navegacion = None
            chapters = get_chapters(scenes_data)
            if nav[0] < len(chapters):
                ch = chapters[nav[0]]
                escenas = ch.get("escenas", [])
                if nav[1] < len(escenas):
                    sc = escenas[nav[1]]
                    estado.fondo_activo = "fondo_ejemplo"
                    ctx = sc.get("dialogo_id", "")
                    _iniciar_arbol(estado, ctx)
        if estado.mostrando_minijuego:
            dt_ms = reloj_vn.tick(30)
            terminado = estado.sistema_minijuego.actualizar(dt_ms)
            estado.stack_manager.actualizar(estado)
            estado.sistema_minijuego.dibujar(pantalla)
            if terminado:
                finalizar_minijuego(estado)
            _display_present()
            continue
        if not estado.dialogo.activo and not estado.mostrando_opciones:
            pass
        pantalla.fill((5, 8, 15))
        bg = obtener_sprite(estado.fondo_activo) if estado.fondo_activo else None
        if bg:
            bg = pygame.transform.scale(bg, (ANCHO, ALTO)) if bg.get_width() != ANCHO else bg
            pantalla.blit(bg, (0, 0))
        for pj_id, info in estado.personajes_visibles.items():
            sp = obtener_sprite(info.get("sprite", ""))
            if sp:
                px = [80, 300, 520][info.get("posicion", 1)]
                py = ALTO - sp.get_height() - 60
                pantalla.blit(sp, (px, py))
        if estado.dialogo.activo:
            estado.dialogo.dibujar(pantalla)
        if estado.mostrando_opciones:
            from engine.systems.choice_box import ChoiceBox
            cb = ChoiceBox()
            cb.dibujar(pantalla, estado.opciones, estado.opcion_seleccionada,
                       getattr(estado, "opcion_pregunta", ""))
        _display_present()
        if not estado.corriendo:
            break

# ============================================
# BUCLE PRINCIPAL (outer: menu → juego → menu ...)
# ============================================

if _PROJECT_CATEGORY == "visual_novel":
    _run_vn_mode(pantalla)
    pygame.quit()
    sys.exit()

_display_set_fill(None)

_alerta_problema = _validar_proyecto()
if _alerta_problema[0]:
    if _MODO_TEST:
        print(f"[ERROR] {_alerta_problema[0]}: {' '.join(_alerta_problema[1])}")
        pygame.quit()
        sys.exit(1)
    _alerta(*_alerta_problema)
    pygame.quit()
    sys.exit(1)

while True:
    estado = GameState()
    ui = UI()
    choice_box = ChoiceBox()
    move_accumulator = 0.0

    # ── Managers ──
    combate_manager = CombateManager(estado, mostrar_mensaje, perder_segmentos)
    comida_manager = ComidaManager(estado)
    colision_manager = ColisionManager(estado, perder_segmentos, mostrar_mensaje)
    event_handler = InputManager(estado, mostrar_mensaje)

    # ── Botín al destruir objetos ──
    from engine.repositories import RepositorioBotin

    def _on_objeto_destruido(evento):
        """Cuando un objeto se destruye, puede dropear minerales"""
        if evento.tipo != "bloqueante":
            return
        _repo_botin = RepositorioBotin()
        evento_id, config = _repo_botin.obtener_drop_aleatorio()
        if evento_id and config:
            tipo = config.get("tipo")
            nombre = config.get("nombre", evento_id)
            icono = config.get("icono", "")
            if tipo == "mineral":
                estado.inventario.agregar_item(evento_id, 1)
                mostrar_mensaje(f"{icono} ¡Encontraste {nombre}!", 60)
            elif tipo == "gema":
                estado.inventario.agregar_item(evento_id, 1)
                estado.habilidades.recargar_pp(cantidad=5)
                mostrar_mensaje(f"{icono} ¡{nombre}! PP recuperados!", 60)
            elif tipo == "escama":
                estado.snake.crecer(1)
                mostrar_mensaje(f"{icono} ¡{nombre}! +1 segmento!", 60)

    estado.event_bus.suscribir(EventoObjetoDestruido, _on_objeto_destruido)

    # ── Pantallas (splash, título, menú, prólogo) ──
    if SCREENS_ENABLED and not _MODO_TEST:
        from engine.systems.screen_manager import ScreenManager
        sm = ScreenManager(pantalla, _SCREENS_CFG)
        sm.run()
        pantalla = _display_buffer()

    # ── Game loop ──
    while estado.corriendo:
        # --- INPUT (siempre, incluso durante game over / dialogos) ---
        event_handler.process_events()

        # --- PAUSA ---
        if estado.pausa:
            ui.mostrar_pausa(pantalla)
            _display_present()
            reloj.tick(10)
            continue

        # --- FORJA ---
        if estado.mostrando_forja:
            estado.sistema_forja.actualizar()
            dibujar()
            estado.sistema_forja.dibujar(pantalla)
            _display_present()
            reloj.tick(10)
            continue

        # --- MENÚS ---
        if estado.mostrando_trueque:
            ui.mostrar_menu_trueque(pantalla, estado.snake)
            continue

        if estado.mostrando_inventario:
            ui.mostrar_inventario(pantalla, estado)
            _display_present()
            reloj.tick(10)
            continue

        # --- GAME OVER ---
        if estado.game_over:
            if estado.death_cause:
                print(f"[MUERTE] {estado.death_cause}")
                estado.death_cause = ""
            ui.mostrar_game_over(pantalla, estado.snake, estado)
            _display_present()
            reloj.tick(10)
            continue

        # --- DIALOGO (pausa el juego) ---
        if estado.dialogo.activo:
            estado.dialogo.actualizar()
            estado.stack_manager.actualizar(estado)
            dibujar()
            estado.dialogo.dibujar(pantalla)
            _display_present()
            reloj.tick(10)
            continue

        # --- VENTANA (pantalla completa tipo cutscene) ---
        if estado.ventana.activo:
            estado.ventana.actualizar()
            estado.stack_manager.actualizar(estado)
            estado.ventana.dibujar(pantalla)
            _display_present()
            reloj.tick(10)
            continue

        # --- MINIJUEGO ---
        if estado.mostrando_minijuego:
            dt_ms = reloj.tick(30)
            terminado = estado.sistema_minijuego.actualizar(dt_ms)
            estado.stack_manager.actualizar(estado)
            estado.sistema_minijuego.dibujar(pantalla)
            if terminado:
                finalizar_minijuego(estado)
            _display_present()
            continue

        # --- MOVIMIENTO (FPS fijo, movimiento por acumulador) ---
        move_accumulator += estado.get_speed_multiplier()
        movio = False
        while move_accumulator >= 1.0:
            estado.snake.mover(desplazar=True)
            move_accumulator -= 1.0
            movio = True
        if not movio:
            estado.snake.mover(desplazar=False)

        # Actualizar cooldown de enroscamiento (previene bucle infinito roca-pared)
        if hasattr(estado.snake, '_no_enroscar_hasta') and estado.snake._no_enroscar_hasta > 0:
            estado.snake._no_enroscar_hasta -= 1

        # --- PROCESAR ACCIONES DE EVENTOS (esperar, comando_automatico, etc.) ---
        estado.stack_manager.actualizar(estado)

        # --- CÁMARA ---
        cabeza = estado.snake.get_cabeza()
        if cabeza:
            estado.camera.seguir(cabeza)
            estado.camera.actualizar()

        # --- CAMBIO DE NIVEL ---
        if estado.cambiando_nivel:
            destino = estado.gate_destino
            estado.cambiar_nivel(destino)
            continue

        # --- COMIDA ---
        comida_manager.actualizar()

        # --- COLISIONES ---
        if colision_manager.verificar_colisiones():
            continue
        if colision_manager.verificar_autocolision():
            continue
        colision_manager.verificar_gate()
        colision_manager.verificar_avance_libre()

        # --- COMBATE ---
        if combate_manager.actualizar_enemigos():
            continue
        if combate_manager.actualizar_jefe():
            continue

        # --- EFECTOS DE EQUIPO ---
        estado.inventario.aplicar_todos_efectos(estado.snake, estado)

        # Regeneración de PP si hay objeto equipado que lo conceda
        for slot, obj in estado.inventario.equipo.items():
            for efecto in obj.efectos:
                if efecto.get("tipo") == "regeneracion_pp":
                    estado.habilidades.recargar_pp(cantidad=0.01)

        # --- SEGMENTOS PERDIDOS ---
        recoger_segmentos()
        for segmento in estado.segmentos_perdidos[:]:
            segmento.actualizar()
            if not segmento.esta_vivo() and not segmento.recogido:
                estado.segmentos_perdidos.remove(segmento)

        # --- TEXTOS FLOTANTES ---
        estado.text_service.update()
        for tf in estado.textos_flotantes[:]:
            tf["timer"] -= 1
            tf["y"] -= 1
            if tf["timer"] <= 0:
                estado.textos_flotantes.remove(tf)

        # --- PARTÍCULAS ---
        estado.particles.actualizar()

        # --- MENSAJE TEMPORAL ---
        if estado.tiempo_mensaje > 0:
            estado.tiempo_mensaje -= 1
            if estado.tiempo_mensaje == 0:
                estado.mensaje_temporal = ""

        # --- DIBUJADO ---
        dibujar()
        _display_present()
        reloj.tick(VELOCIDAD_DEUDA if estado.snake.tiene_deuda() else VELOCIDAD_BASE)

    # ── ¿Volver al menú o salir del juego? ──
    if not estado.volver_a_menu:
        break

pygame.quit()

