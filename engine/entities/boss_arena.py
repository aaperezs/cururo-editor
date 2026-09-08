# entities/boss_arena.py
import pygame
from engine.configs import *
from engine.configs.z_layers import Z_MAPA_PRINCIPAL


class BossArena:
    def __init__(self, x, y, ancho=400, alto=300, z=Z_MAPA_PRINCIPAL, paredes=None, entidades=None, es_nivel_completo=False):
        self.x = x
        self.y = y
        self.ancho = ancho
        self.alto = alto
        self.z = z
        self.paredes = paredes if paredes else []
        self.entidades = entidades if entidades else []
        self._bloqueantes_arena = []
        self._bloques_arena = []
        self._hierba_arena = []
        self._enemigos_arena = []
        self.activa = False
        self.boss = None

        self.limite_izquierdo = x
        self.limite_derecho = x + ancho
        self.limite_superior = y
        self.limite_inferior = y + alto

        # UI del jefe
        self.ui_x = x + ancho // 2
        self.ui_y = y - 55

        # Sistema de entrada
        self.estado_entrada = "INACTIVO"
        self.tiempo_entrada = 0
        self.entrada_completa = False
        self.warning_alpha = 0
        self.punto_entrada = None
        self._primera_vez = False

        # Comida en la arena (opcional)
        self.comida_visible = True
        self.es_nivel_completo = es_nivel_completo

    def _categorizar_entidad(self, e, estado):
        """Clasifica una entidad y la agrega a la lista del estado correspondiente"""
        from engine.entities.arbol import Arbol
        from engine.entities.bloque_acero import BloqueAcero
        from engine.entities.enemigos import Eldir, EnemyMelee
        from engine.entities.hierba_alta import HierbaAlta
        from engine.entities.objeto_colision import ObjetoBloqueante
        if isinstance(e, ObjetoBloqueante) and not isinstance(e, (BloqueAcero, Arbol)):
            self._bloqueantes_arena.append(e)
            estado.bloqueantes.append(e)
        elif isinstance(e, (BloqueAcero, Arbol)):
            self._bloques_arena.append(e)
            estado.bloques_acero.append(e)
        elif isinstance(e, HierbaAlta):
            self._hierba_arena.append(e)
            estado.hierba_alta.append(e)
        elif isinstance(e, (EnemyMelee, Eldir)):
            self._enemigos_arena.append(e)
            estado.enemigos.append(e)

    def _salvar_entidades_principales(self, estado):
        """Guarda y remueve entidades del nivel principal para aislar la arena"""
        self._main_paredes = list(estado.paredes)
        self._main_bloqueantes = list(estado.bloqueantes)
        self._main_bloques = list(estado.bloques_acero)
        self._main_enemigos = list(estado.enemigos)
        self._main_hierba = list(estado.hierba_alta)
        estado.paredes.clear()
        estado.bloqueantes.clear()
        estado.bloques_acero.clear()
        estado.enemigos.clear()
        estado.hierba_alta.clear()

    def _restaurar_entidades_principales(self, estado):
        """Restaura las entidades del nivel principal removidas al activar la arena"""
        for lista_name in ['_main_paredes', '_main_bloqueantes', '_main_bloques', '_main_enemigos', '_main_hierba']:
            saved = getattr(self, lista_name, None)
            if saved is None:
                continue
            attr_map = {
                '_main_paredes': 'paredes',
                '_main_bloqueantes': 'bloqueantes',
                '_main_bloques': 'bloques_acero',
                '_main_enemigos': 'enemigos',
                '_main_hierba': 'hierba_alta',
            }
            estado_lista = getattr(estado, attr_map[lista_name])
            for e in saved:
                if e not in estado_lista:
                    estado_lista.append(e)
            setattr(self, lista_name, [])

    def activar_con_entrada(self, boss, punto_entrada, snake, estado):
        """Activa la arena con un jefe y punto de entrada"""
        if boss is None:
            print("Error: No se puede activar la arena sin un jefe")
            return

        self.activa = True
        self.boss = boss
        if hasattr(boss, 'z'):
            boss.z = self.z

        boss.x = self.x + self.ancho // 2 - boss.ancho // 2
        boss.y = self.y + 60
        boss.centro_x = boss.x + boss.ancho // 2
        boss.centro_y = boss.y + boss.alto // 2

        if estado:
            estado.proyectiles_necesarios = boss.proyectiles_necesarios

        self.punto_entrada = punto_entrada
        self._primera_vez = False
        self.estado_entrada = "ENTRANDO"
        self.tiempo_entrada = 0
        self.entrada_completa = False
        self.warning_alpha = 0

        # Aislar: salvar y limpiar entidades del nivel principal
        self._salvar_entidades_principales(estado)

        # Inyectar paredes de la arena
        for p in self.paredes:
            estado.paredes.append(p)

        # Categorizar y agregar entidades de la arena al estado
        self._bloqueantes_arena = []
        self._bloques_arena = []
        self._hierba_arena = []
        self._enemigos_arena = []
        for e in self.entidades:
            self._categorizar_entidad(e, estado)

        if snake and estado:
            pos_x = self.x + 60
            pos_y = self.y + self.alto - 60
            # Traducir el cuerpo completo a la entrada de la arena
            cabeza = snake.body[0]
            dx = pos_x - cabeza[0]
            dy = pos_y - cabeza[1]
            print(f"[ARENA] Traduciendo {len(snake.body)} segmentos por (dx={dx}, dy={dy})")
            for segmento in snake.body:
                segmento[0] += dx
                segmento[1] += dy
            # Reducir a 1 segmento y ponerlo dormido
            snake.iniciar_dormido((pos_x, pos_y))
            print(f"[ORM] Orm enroscado en entrada: ({pos_x}, {pos_y})")

    def activar_combate(self, snake, estado):
        """Activa la pelea con el boss desde dentro de la arena (standalone level)"""
        if not self.boss or not self.boss.vivo:
            return
        self.activa = True
        if estado:
            estado.proyectiles_necesarios = self.boss.proyectiles_necesarios
        self.estado_entrada = "ALERTA"
        self.tiempo_entrada = 0
        self.entrada_completa = False
        self.warning_alpha = 0

    def desactivar(self, estado=None):
        """Desactiva la arena y restaura las entidades del nivel principal"""
        if estado:
            # Remover entidades de la arena de las listas del estado
            for p in self.paredes:
                if p in estado.paredes:
                    estado.paredes.remove(p)
            for e in self._bloqueantes_arena:
                if e in estado.bloqueantes:
                    estado.bloqueantes.remove(e)
            for e in self._bloques_arena:
                if e in estado.bloques_acero:
                    estado.bloques_acero.remove(e)
            for e in self._hierba_arena:
                if e in estado.hierba_alta:
                    estado.hierba_alta.remove(e)
            for e in self._enemigos_arena:
                if e in estado.enemigos:
                    estado.enemigos.remove(e)
            # Restaurar entidades del nivel principal
            self._restaurar_entidades_principales(estado)
        self._bloqueantes_arena = []
        self._bloques_arena = []
        self._hierba_arena = []
        self._enemigos_arena = []
        self.activa = False
        self.boss = None
        self.estado_entrada = "INACTIVO"
        self.entrada_completa = False
        self.punto_entrada = None
        self._primera_vez = False

    def actualizar_entrada(self, snake, estado=None):
        """Actualiza la secuencia de entrada"""
        if not self.activa or self.boss is None or not self.boss.vivo:
            return

        if self.estado_entrada == "ENTRANDO":
            if not self._primera_vez:
                self._primera_vez = True
            self.estado_entrada = "ALERTA"
            self.tiempo_entrada = 0

        elif self.estado_entrada == "ALERTA":
            self.tiempo_entrada += 1
            self.warning_alpha = min(255, self.warning_alpha + 5)
            if self.tiempo_entrada >= 18:
                self.estado_entrada = "ACTIVO"
                self.entrada_completa = True
                self.warning_alpha = 255
                print("¡La pelea comienza!")

        elif self.estado_entrada == "ACTIVO":
            if self.boss:
                self.boss.mover()

    def dibujar(self, pantalla, offset_x=0, offset_y=0):
        if not self.activa:
            if self.boss and self.boss.vivo:
                self.boss.dibujar(pantalla, offset_x, offset_y)
            return

        if self.boss and self.estado_entrada != "INACTIVO":
            self.boss.dibujar_ui(pantalla, self.ui_x, self.ui_y)

        # Solo dibujar fondo y entidades propias cuando es subzona
        if not self.es_nivel_completo:
            from engine.configs.colors import FOREST_BG
            pygame.draw.rect(pantalla, FOREST_BG,
                            (self.x + offset_x, self.y + offset_y, self.ancho, self.alto))
            for e in self.entidades:
                e.dibujar(pantalla, offset_x, offset_y)
            for p in self.paredes:
                p.dibujar(pantalla, offset_x, offset_y)

        if self.estado_entrada == "ALERTA":
            surf_warning = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
            surf_warning.fill((0, 0, 0, min(180, self.warning_alpha // 2)))
            pantalla.blit(surf_warning, (0, 0))

            fuente = pygame.font.SysFont("Arial", 48, bold=True)
            if pygame.time.get_ticks() % 500 < 250:
                texto1 = fuente.render("⚔️ ¡PREPÁRATE!", True, (255, 200, 50))
            else:
                texto1 = fuente.render("⚔️ ¡PREPÁRATE!", True, (255, 100, 0))
            rect1 = texto1.get_rect(center=(ANCHO//2, ALTO//2 - 40))
            pantalla.blit(texto1, rect1)

            fuente2 = pygame.font.SysFont("Arial", 32)
            segundos = max(1, 3 - self.tiempo_entrada // 6)
            texto2 = fuente2.render(f"{segundos}", True, BLANCO)
            rect2 = texto2.get_rect(center=(ANCHO//2, ALTO//2 + 40))
            pantalla.blit(texto2, rect2)

        if self.boss and self.estado_entrada != "INACTIVO":
            self.boss.dibujar(pantalla, offset_x, offset_y)

    def colision_con_borde(self, posicion):
        """Verifica si una posición está dentro de la arena"""
        if not self.activa:
            return False
        x, y = posicion
        margen = TAMANO_CELDA // 2
        return (x < self.limite_izquierdo + margen or
                x > self.limite_derecho - TAMANO_CELDA - margen or
                y < self.limite_superior + margen or
                y > self.limite_inferior - TAMANO_CELDA - margen)

    def en_pelea(self):
        return self.activa and self.estado_entrada == "ACTIVO" and self.boss is not None

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.ancho, self.alto)
