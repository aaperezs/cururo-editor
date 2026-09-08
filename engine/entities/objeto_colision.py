# entities/objeto_colision.py
import pygame
from engine.configs import *
from engine.utils.sprite_manager import obtener as obtener_sprite


class ObjetoColision:
    """Clase base para todos los objetos con los que se puede colisionar"""

    def __init__(self, x, y, ancho=TAMANO_CELDA, alto=TAMANO_CELDA, z=Z_MAPA_PRINCIPAL):
        self.x = x
        self.y = y
        self.ancho = ancho
        self.alto = alto
        self.z = z
        self.visible = True
        self.activo = True
        self.solid = True
        self.properties = {}

    def colisiona_con(self, cabeza_x, cabeza_y, z_jugador=0):
        """Verifica si colisiona con una posición (cabeza de la serpiente)"""
        if not self.activo or not self.visible:
            return False
        if not self.solid:
            return False
        if self.z != z_jugador:
            return False
        return (cabeza_x == self.x and cabeza_y == self.y)

    def manejar_colision(self, snake, estado):
        """Maneja la colisión - CADA OBJETO DEFINE SU PROPIO COMPORTAMIENTO"""
        # Por defecto: no hace nada (debe ser sobrescrito)
        pass

    def dibujar(self, pantalla, offset_x=0, offset_y=0):
        """Dibuja el objeto - Sobrescribir en clases hijas"""
        pass


class ObjetoBloqueante(ObjetoColision):
    """Objeto que BLOQUEA el paso de la serpiente (ej: rocas, NPCs, árboles)"""

    def __init__(self, x, y, ancho=TAMANO_CELDA, alto=TAMANO_CELDA):
        super().__init__(x, y, ancho, alto)
        self.tipo = ""
        self.rotura = 0
        self.animation = ""
        self.sprite_id = ""

    def dibujar(self, pantalla, offset_x=0, offset_y=0):
        from engine.systems.animation import get_anim_sprite, get_anim_glow
        ox = self.x + offset_x
        oy = self.y + offset_y
        sprite_id = self.sprite_id
        if self.animation:
            sprite_id = get_anim_sprite(self.animation) or sprite_id
        if not sprite_id:
            return
        sprite = obtener_sprite(sprite_id)
        if not sprite:
            return
        if self.animation:
            glow = get_anim_glow(self.animation)
            if glow:
                color = tuple(glow.get("color", [255, 255, 0]))
                radius = glow.get("radius", 8)
                alpha = glow.get("alpha", 80)
                gcx = ox + TAMANO_CELDA // 2
                gcy = oy + TAMANO_CELDA // 2
                for r in range(radius, 1, -2):
                    surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
                    pygame.draw.circle(surf, (*color, alpha), (r + 2, r + 2), r)
                    pantalla.blit(surf, (gcx - r - 2, gcy - r - 2))
        pantalla.blit(sprite, (ox, oy))

    def colisiona_con(self, cabeza_x, cabeza_y, z_jugador=0):
        if not self.activo or not self.visible:
            return False
        if not self.solid:
            return False
        return (cabeza_x == self.x and cabeza_y == self.y)

    def es_obstaculo(self):
        return self.activo

    def get_rect(self):
        if not self.activo:
            return None
        import pygame
        return pygame.Rect(self.x, self.y, self.ancho, self.alto)

    def golpear(self, snake=None, estado=None, damage=1, attack_type=""):
        if not self.activo or not getattr(self, 'destructible', False):
            return False
        self.rotura += damage
        hp = getattr(self, 'destructible_hp', 1) - damage
        self.destructible_hp = hp
        if estado:
            estado.stack_manager.on_hit(self.x, self.y, self.z, damage=damage, attack_type=attack_type)
        if hp <= 0:
            self.activo = False
            self.visible = False
            if estado:
                from engine.systems.event_bus import EventoObjetoDestruido
                estado.event_bus.publicar(EventoObjetoDestruido(self, (self.x, self.y), "bloqueante"))
                estado.stack_manager.on_entity_destroyed(self.x, self.y, "bloqueante")
                # Remove the grid tile so the ground underneath shows
                gx = self.x // TAMANO_CELDA
                gy = self.y // TAMANO_CELDA
                estado.remove_tile_sprite(gx, gy, self.z)
            return True
        # Change to cracked sprite if configured
        cracked = getattr(self, 'cracked_sprite', '')
        if cracked and estado:
            gx = self.x // TAMANO_CELDA
            gy = self.y // TAMANO_CELDA
            estado.replace_tile_sprite(gx, gy, cracked, self.z)
            # Clear cracked_sprite so it only triggers once
            self.cracked_sprite = ''
        return False

    def manejar_colision(self, snake, estado):
        if not self.activo:
            return

        # La cabeza ya entró a la celda bloqueada en el mover(). Para
        # enroscarse en el lugar, hay que devolverla a la celda de donde
        # venía (body[1] siempre es la posición previa de la cabeza) y
        # consumir un segmento. Antes se desplazaba TODO el cuerpo por
        # (dx, dy), lo que "rebotaba" la orm una celda más lejos de la
        # pared (la cola caía a la fila siguiente).
        # Ojo: este pop es SOLO visual; la longitud (escamas) permanente
        # no cambia por enroscarse (se restaura al desenroscar).
        if snake.body and len(snake.body) > 1:
            snake.body.pop(0)

        snake.estado_actual = estado
        snake.enroscar(
            posicion=snake.body[0] if snake.body else None,
            duracion=20,
            estado=estado
        )
        return "bloqueado"


class ObjetoPeligroso(ObjetoColision):
    """Objeto que MATA a la serpiente (ej: paredes, puas, lava)"""

    def __init__(self, x, y, ancho=TAMANO_CELDA, alto=TAMANO_CELDA, z=Z_MAPA_PRINCIPAL):
        super().__init__(x, y, ancho, alto, z)

    def colisiona_con(self, cabeza_x, cabeza_y, z_jugador=0):
        if not self.activo or not self.visible:
            return False
        return (self.x <= cabeza_x < self.x + self.ancho and
                self.y <= cabeza_y < self.y + self.alto)

    def manejar_colision(self, snake, estado):
        estado.game_over = True
        estado.death_cause = f"Objeto peligroso ({type(self).__name__})"
        from engine.managers.colision_manager import mostrar_mensaje
        mostrar_mensaje("¡Has muerto!", 60)
        estado.particles.crear_explosion(
            snake.body[0][0] + TAMANO_CELDA//2,
            snake.body[0][1] + TAMANO_CELDA//2,
            30, ROJO
        )
        return "mata"
