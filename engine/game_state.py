from engine.camera import Camera
from engine.configs import *
from engine.configs.constants import ALTO, ANCHO
from engine.configs.z_layers import Z_ARENA_JEFE, Z_MAPA_PRINCIPAL
from engine.domain.snake_context import SnakeContext
from engine.domain.world_state import WorldState
from engine.entities.inventario import Inventario
from engine.entities.snake import Snake
from engine.levels.level_manager import LevelManager
from engine.services.text_service import TextService
from engine.systems.dialogo import DialogoSystem
from engine.systems.event_bus import BusEventos
from engine.systems.habilidades import SistemaHabilidades
from engine.systems.menu import MenuSystem
from engine.systems.particles import ParticleSystem
from engine.systems.shop_system import ShopSystem
from engine.systems.save_system import SaveSystem
from engine.systems.stack_manager import StackManager
from engine.systems.eventos_globales_system import EventosGlobalesSystem
from engine.systems.text_screen_player import TextScreenPlayer
from engine.runtime.contadores import ContadoresManager
from engine.runtime.flags import FlagsManager
from engine.runtime.monedas import MonedasManager
from engine.repositories import RepositorioMonedas, RepositorioContadores

import pygame


def _celdas_delante(cabeza, direccion):
    """Devuelve las 3 posiciones de celda en la direccion de la cabeza (en abanico)"""
    cx, cy = cabeza
    perp = []
    if direccion in ("ARRIBA", "ABAJO"):
        dy = -TAMANO_CELDA if direccion == "ARRIBA" else TAMANO_CELDA
        for px in (-TAMANO_CELDA, 0, TAMANO_CELDA):
            perp.append((cx + px, cy + dy))
    else:
        dx = -TAMANO_CELDA if direccion == "IZQUIERDA" else TAMANO_CELDA
        for py in (-TAMANO_CELDA, 0, TAMANO_CELDA):
            perp.append((cx + dx, cy + py))
    return perp


class GameState:
    """Application layer: orchestrates SnakeContext + WorldState + infrastructure systems."""

    def __init__(self):
        # ── Infrastructure systems ──
        self.level_manager = LevelManager()
        self.particles = ParticleSystem()
        self.habilidades = SistemaHabilidades()
        self.menu = MenuSystem()
        self.event_bus = BusEventos()
        self.stack_manager = StackManager(self)
        self.flags = FlagsManager()
        self.contadores = ContadoresManager(RepositorioContadores().get_definiciones())
        self.monedas = MonedasManager(RepositorioMonedas().get_definiciones())
        self.shop_system = ShopSystem()
        self.eventos_globales = EventosGlobalesSystem(self)
        self.save_system = SaveSystem(self)
        self.dialogo = DialogoSystem(flags=self.flags)
        self.ventana = TextScreenPlayer()
        self.camera = Camera(ANCHO, ALTO)
        self.inventario = Inventario()
        from engine.systems.forja import SistemaForja
        self.sistema_forja = SistemaForja(self)
        from engine.systems.minigame import MiniJuegoManager
        self.sistema_minijuego = MiniJuegoManager(self)
        from engine.systems.audio_manager import AudioManager
        self.audio = AudioManager()

        # ── Domain objects ──
        nivel = self.level_manager.obtener_nivel_actual()
        if nivel is None:
            raise RuntimeError("No hay mapa: el proyecto no tiene un mapa configurado")
        self.stack_manager.load_stacks(self.level_manager.obtener_id_actual())
        self.stack_manager.apply_preload()
        inicio_x, inicio_y = WorldState.posicion_inicio_static(nivel)
        snake = Snake(inicio_x, inicio_y, z=Z_MAPA_PRINCIPAL)
        snake.iniciar_dormido((inicio_x, inicio_y))
        self.snake_ctx = SnakeContext(snake)
        self.world = WorldState()
        self.world.cargar_entidades_nivel(nivel)
        self.camera = Camera(self.world.nivel_ancho, self.world.nivel_alto)
        self.camera.snap_to(inicio_x, inicio_y)
        self.world.inicializar_arena_boss(nivel, self.level_manager)
        self.world.crear_portal_boss(snake)
        if nivel['comidas']:
            self.world.comida = nivel['comidas'][0]
        elif not getattr(self, 'no_comida_spawn', False):
            self.world.spawn_comida(snake.body)
        if getattr(self, 'no_enemigos_spawn', False):
            self.world.enemigos = []
        self.stack_manager.execute_onload_events()
        if hasattr(self.stack_manager, '_preload_musica'):
            self.audio.play_bgm(self.stack_manager._preload_musica)

        # ── Session state ──
        self._jefe_derrotado = False
        self.death_cause = None
        self.corriendo = True
        self.volver_a_menu = False
        self.pausa = False
        self.game_over = False
        self.mostrando_trueque = False
        self.mostrando_inventario = False
        self.mostrando_forja = False
        self.proyectiles_comidos = 0
        self.proyectiles_necesarios = 3
        self.mensaje_temporal = ""
        self.tiempo_mensaje = 0
        self.cambiando_nivel = False
        self.gate_destino = None
        self.gate_salida_id = None
        self.text_service = TextService(pool_size=64)
        self.textos_flotantes = []  # legacy — migrate to text_service
        self.god_mode = False
        self.demo_habilidad_pendiente = False
        self.mandos_bloqueados = False
        self.nivel_origen = None
        self.demo_habilidad_id = None

        # ── Visual Novel state ──
        self.fondo_activo = None
        self.fondo_modo = "fill"
        self.personajes_visibles = {}
        self.mostrando_opciones = False
        self.opciones = []
        self.opcion_pregunta = ""
        self.opcion_seleccionada = -1

        # ── Minigame state ──
        self.mostrando_minijuego = False
        self.minijuego_id = None

        self._init_habilidades_iniciales()

        print(f"Nivel cargado: {self.level_manager.obtener_id_actual()}")
        print(f"   Inicio en: ({inicio_x}, {inicio_y}) [Z={Z_MAPA_PRINCIPAL}]")
        print(f"   Paredes: {len(self.world.paredes)}, Bloqueantes: {len(self.world.bloqueantes)}, "
              f"BloquesAcero: {len(self.world.bloques_acero)}, "
              f"Hierba: {len(self.world.hierba_alta)}, Enemigos: {len(self.world.enemigos)}")
        print(f"   Arena del jefe en Z={Z_ARENA_JEFE} (aislada)")

    # ────────────────────────────────────────────
    # Backward-compatible property delegation
    # ────────────────────────────────────────────

    @property
    def snake(self): return self.snake_ctx.snake

    @property
    def segmentos_perdidos(self): return self.snake_ctx.segmentos_perdidos
    @segmentos_perdidos.setter
    def segmentos_perdidos(self, v): self.snake_ctx.segmentos_perdidos = v

    @property
    def velocidad_extra(self): return self.snake_ctx.velocidad_extra
    @velocidad_extra.setter
    def velocidad_extra(self, v): self.snake_ctx.velocidad_extra = v

    @property
    def paredes(self): return self.world.paredes
    @property
    def bloqueantes(self): return self.world.bloqueantes
    @property
    def hierba_alta(self): return self.world.hierba_alta
    @property
    def bloques_acero(self): return self.world.bloques_acero
    @property
    def enemigos(self): return self.world.enemigos
    @property
    def decorativos(self): return self.world.decorativos
    @property
    def suelos(self): return self.world.suelos
    @property
    def arena_paredes(self): return self.world.arena_paredes
    @property
    def zonas_restringidas(self): return self.world.zonas_restringidas
    @property
    def terrenos_negados(self): return self.world.terrenos_negados
    @property
    def nivel_ancho(self): return self.world.nivel_ancho
    @property
    def nivel_alto(self): return self.world.nivel_alto
    @property
    def nivel_z0(self): return self.world.nivel_z0
    @property
    def grid(self): return self.world.grid
    @property
    def grid_por_capa(self): return self.world.grid_por_capa
    @property
    def zona_boss(self): return self.world.zona_boss
    @property
    def arena_boss(self): return self.world.arena_boss
    @property
    def boss(self): return self.world.boss
    @property
    def portal_boss(self): return self.world.portal_boss
    @property
    def comida(self): return self.world.comida
    @comida.setter
    def comida(self, v): self.world.comida = v
    @property
    def tile_overrides(self): return self.world.tile_overrides
    @tile_overrides.setter
    def tile_overrides(self, v): self.world.tile_overrides = v

    # ────────────────────────────────────────────

    def _init_habilidades_iniciales(self):
        from engine.configs.debug import HABILIDADES_INICIALES
        for habilidad_id in HABILIDADES_INICIALES:
            if habilidad_id == "golpe_cabeza":
                self.habilidades.desbloquear_habilidad(HabilidadID.GOLPE_CABEZA)
            elif habilidad_id == "manto_oscuridad":
                self.habilidades.desbloquear_habilidad(HabilidadID.MANTO_OSCURIDAD)
            elif habilidad_id == "cola_latigo":
                self.habilidades.desbloquear_habilidad(HabilidadID.COLA_LATIGO)
            elif habilidad_id == "base":
                pass

    def get_speed_multiplier(self):
        return self.snake_ctx.get_speed_multiplier(self.world.hierba_alta, self.world.terrenos_negados)

    def replace_tile_sprite(self, gx, gy, sprite_id, z=0):
        self.world.replace_tile_sprite(gx, gy, sprite_id, z)
        self._update_decorativo_override(gx, gy, sprite_id, z)

    def remove_tile_sprite(self, gx, gy, z=0):
        self.world.remove_tile_sprite(gx, gy, z)
        self._update_decorativo_override(gx, gy, None, z)

    def _update_decorativo_override(self, gx, gy, sprite_id, z):
        from engine.configs import TAMANO_CELDA
        px = gx * TAMANO_CELDA
        py = gy * TAMANO_CELDA
        for deco in self.world.decorativos:
            if int(deco.x) == px and int(deco.y) == py and deco.z == z:
                if sprite_id is None:
                    self.world.decorativos.remove(deco)
                else:
                    deco.sprite_id = sprite_id
                    deco.animation = ""

    def cambiar_nivel(self, nivel_id):
        self.gate_destino = None

        if nivel_id == "__return__":
            nivel_id = self.nivel_origen

        nivel_anterior = self.level_manager.obtener_id_actual()
        if nivel_anterior:
            self.world._saved_tile_overrides[nivel_anterior] = dict(self.world.tile_overrides)

        if nivel_id == "1-arena":
            self._nivel_antes_arena = nivel_anterior

        if not nivel_id or not self.level_manager.ir_a_nivel(nivel_id):
            print(f"Nivel {nivel_id} no encontrado")
            self.cambiando_nivel = False
            return False

        nivel = self.level_manager.obtener_nivel_actual()
        self.stack_manager.load_stacks(nivel_id)
        self.stack_manager.apply_preload()

        salida_id = self.gate_salida_id
        self.gate_salida_id = None
        inicio_x, inicio_y = WorldState.posicion_inicio_static(nivel)
        if salida_id:
            for (gx, gy, z), stack in self.stack_manager._stacks.items():
                for ev in stack.get("eventos", []):
                    if ev.get("id") == salida_id:
                        inicio_x = gx * TAMANO_CELDA
                        inicio_y = gy * TAMANO_CELDA
                        break

        total = self.snake.get_escamas() + LONGITUD_INICIAL

        self.snake.body = [[inicio_x, inicio_y]]
        for i in range(1, total):
            self.snake.body.append([inicio_x - i * TAMANO_CELDA, inicio_y])
        self.snake.iniciar_dormido((inicio_x, inicio_y))

        self.world.cargar_entidades_nivel(nivel)
        print(f"  CAMBIAR_NIVEL bloqueantes count={len(self.world.bloqueantes)}")
        for i, r in enumerate(self.world.bloqueantes):
            print(f"  CAMBIAR_NIVEL bloqueante[{i}] x={r.x} y={r.y} tipo={getattr(r,'tipo','?')}")
        self.world.limpiar_persistencia_nivel(nivel_id)
        self.camera = Camera(self.world.nivel_ancho, self.world.nivel_alto)
        # Posicionar cámara en la ubicación inicial del snake (sin suavizado)
        self.camera.snap_to(inicio_x, inicio_y)
        self.world.inicializar_arena_boss(nivel, self.level_manager)

        self.world.crear_portal_boss(self.snake)

        if nivel['comidas']:
            self.world.comida = nivel['comidas'][0]
        elif not getattr(self, 'no_comida_spawn', False):
            self.world.spawn_comida(self.snake.body)
        if getattr(self, 'no_enemigos_spawn', False):
            self.world.enemigos = []

        self.stack_manager.execute_onload_events()
        if hasattr(self.stack_manager, '_preload_musica'):
            self.audio.play_bgm(self.stack_manager._preload_musica)

        self.snake_ctx.segmentos_perdidos = []
        self.mensaje_temporal = f"¡Nivel {nivel_id}!"
        self.tiempo_mensaje = 90
        self.cambiando_nivel = False
        self._jefe_derrotado = False

        # Autosave al cambiar de nivel
        if hasattr(self, "save_system"):
            self.save_system.autosave("cambio_nivel")

        print(f"Cambio a nivel {nivel_id}")
        return True

    def reiniciar(self):
        self.__init__()
        print("¡Juego reiniciado!")

    def ejecutar_golpe_q(self):
        """Ejecuta la habilidad activa equipada (Q)"""
        efecto = self.habilidades.usar_habilidad()
        if not efecto or efecto == "base":
            if MOSTRAR_LOGS: print(f"[GOLPE] Sin efecto ({efecto}), saltando animacion")
            return

        cabeza = self.snake.get_cabeza()
        if not cabeza:
            if MOSTRAR_LOGS: print(f"[GOLPE] Sin cabeza de serpiente")
            return

        direccion = self.snake.direccion
        if MOSTRAR_LOGS: print(f"[GOLPE] efecto={efecto} cabeza=({cabeza[0]},{cabeza[1]}) dir={direccion}")

        # --- GOLPE DE CABEZA ---
        if efecto == "golpe":
            dx = dy = 0
            if direccion == "ARRIBA": dy = -TAMANO_CELDA
            elif direccion == "ABAJO": dy = TAMANO_CELDA
            elif direccion == "IZQUIERDA": dx = -TAMANO_CELDA
            elif direccion == "DERECHA": dx = TAMANO_CELDA

            golpe_x, golpe_y = cabeza[0] + dx, cabeza[1] + dy
            golpe_rect = pygame.Rect(golpe_x, golpe_y, TAMANO_CELDA, TAMANO_CELDA)
            cabeza_rect = pygame.Rect(cabeza[0], cabeza[1], TAMANO_CELDA, TAMANO_CELDA)
            self.particles.crear_explosion(golpe_x + TAMANO_CELDA//2, golpe_y + TAMANO_CELDA//2, 10, NARANJA)

            entidades = list(self.bloqueantes) + list(self.bloques_acero)
            if MOSTRAR_LOGS: print(f"[GOLPE] buscando entidades ({len(entidades)} disponibles)")
            for ent in entidades[:]:
                if not ent.activo:
                    continue
                rect = ent.get_rect()
                if rect and (golpe_rect.colliderect(rect) or cabeza_rect.colliderect(rect)):
                    if MOSTRAR_LOGS: print(f"[GOLPE] HIT ent x={ent.x} y={ent.y} tipo={type(ent).__name__}")
                    r = ent.golpear(snake=self.snake, estado=self, damage=1, attack_type="golpe")
                    if MOSTRAR_LOGS: print(f"[GOLPE] golpear() retorno={r}")
                    if r:
                        self.particles.crear_explosion(ent.x + TAMANO_CELDA//2, ent.y + TAMANO_CELDA//2, 15, GRIS)
                        if ent in self.bloqueantes:
                            self.bloqueantes.remove(ent)
                            if MOSTRAR_LOGS: print(f"[GOLPE] ent removido de bloqueantes")
                        elif ent in self.bloques_acero:
                            self.bloques_acero.remove(ent)
                            if MOSTRAR_LOGS: print(f"[GOLPE] ent removido de bloques_acero")
            if MOSTRAR_LOGS: print(f"[GOLPE] bloqueantes restantes={len(self.bloqueantes)}")

        # --- COLA LATIGO ---
        elif efecto == "latigo":
            celdas = _celdas_delante(cabeza, direccion)
            cortadas = 0
            for gx, gy in celdas:
                for g in self.hierba_alta[:]:
                    if g.activo and g.x == gx and g.y == gy:
                        g.activo = False
                        g.visible = False
                        self.particles.crear_explosion(gx + TAMANO_CELDA//2, gy + TAMANO_CELDA//2, 8, (100, 180, 50))
                        from engine.systems.event_bus import EventoObjetoDestruido
                        self.event_bus.publicar(EventoObjetoDestruido(g, (gx, gy), "hierba"))
                        self.stack_manager.on_entity_destroyed(gx, gy, "hierba_alta")
                        cortadas += 1
            if cortadas > 0:
                self.mensaje_temporal = f"¡Hierba cortada! ({cortadas})"
                self.tiempo_mensaje = 20
