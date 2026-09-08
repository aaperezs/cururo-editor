# managers/colision_manager.py
import random

from engine.configs import *


# Variable global para mostrar mensajes desde los objetos
def mostrar_mensaje(texto, duracion=60):
    global _mensaje_callback
    if _mensaje_callback:
        _mensaje_callback(texto, duracion)

class ColisionManager:
    def __init__(self, estado, perder_segmentos, mostrar_mensaje_callback):
        self.estado = estado
        self.perder_segmentos = perder_segmentos
        global _mensaje_callback
        _mensaje_callback = mostrar_mensaje_callback

    def _en_arena(self):
        estado = self.estado
        return estado.arena_boss.activa and estado.boss and estado.boss.vivo

    def verificar_colisiones(self):
        estado = self.estado
        cabeza = estado.snake.get_cabeza()

        if not cabeza:
            return False

        # La cabeza siempre colisiona con objetos aunque esté enroscada

        # --- PELIGROSOS PRIMERO (spikes, paredes que matan) ---
        # Se evaluan antes que los bloqueantes para que siempre
        # tengan prioridad aunque compartan la misma celda.
        from engine.entities.objeto_colision import ObjetoPeligroso
        from engine.entities.pared import Pared
        for pared in estado.paredes:
            if not isinstance(pared, (ObjetoPeligroso, Pared)):
                continue
            if pared.activo and pared.colisiona_con(cabeza[0], cabeza[1]):
                resultado = pared.manejar_colision(estado.snake, estado)
                if resultado == "mata":
                    return True
                return True

        # --- BLOQUEANTES (rocas, bloques, arboles) ---
        for pared in estado.paredes:
            if isinstance(pared, (ObjetoPeligroso, Pared)):
                continue
            if pared.activo and pared.colisiona_con(cabeza[0], cabeza[1]):
                pared.manejar_colision(estado.snake, estado)
                return True

        # --- VERIFICAR BLOQUEANTES ---
        for obj in estado.bloqueantes:
            if obj.activo and obj.colisiona_con(cabeza[0], cabeza[1]):
                obj.manejar_colision(estado.snake, estado)
                return True

        # --- VERIFICAR BLOQUES DE ACERO ---
        for bloque in estado.bloques_acero:
            if bloque.activo and bloque.colisiona_con(cabeza[0], cabeza[1]):
                bloque.manejar_colision(estado.snake, estado)
                return True

        return False

    def verificar_autocolision(self):
        """Verifica si la serpiente se muerde a sí misma - NUNCA mata, solo quita segs"""
        estado = self.estado

        if len(estado.snake.body) > 1 and estado.snake.body[0] in estado.snake.body[1:]:
            dano = random.randint(3, 6)
            max_perder = estado.snake.get_longitud() - 3
            if max_perder <= 0:
                return False  # ya está al mínimo, no quitar más
            if dano > max_perder:
                dano = max_perder
            perdidos = estado.snake.perder_segmentos(dano)
            if perdidos:
                from engine.entities.segmento_perdido import SegmentoPerdido
                for pos in perdidos:
                    if pos:
                        seg = SegmentoPerdido(pos[0], pos[1], estado.nivel_ancho, estado.nivel_alto)
                        estado.segmentos_perdidos.append(seg)
                mostrar_mensaje("¡Te has mordido!", 60)
            return True

        return False

    def verificar_avance_libre(self):
        """Si la serpiente está enroscada y la celda de enfrente ya no está bloqueada, avanza"""
        estado = self.estado
        snake = estado.snake
        if not snake.enroscado or snake.dormido:
            return False
        cabeza = snake.get_cabeza()
        if not cabeza:
            return False
        dx = dy = 0
        if snake.direccion == "ARRIBA":
            dy = -TAMANO_CELDA
        elif snake.direccion == "ABAJO":
            dy = TAMANO_CELDA
        elif snake.direccion == "IZQUIERDA":
            dx = -TAMANO_CELDA
        elif snake.direccion == "DERECHA":
            dx = TAMANO_CELDA
        else:
            return False
        frente_x = cabeza[0] + dx
        frente_y = cabeza[1] + dy
        if frente_x < 0 or frente_y < 0 or frente_x >= estado.nivel_ancho or frente_y >= estado.nivel_alto:
            return False
        for obj in estado.paredes:
            if obj.activo and obj.colisiona_con(frente_x, frente_y):
                return False
        for obj in estado.bloqueantes:
            if obj.activo and obj.colisiona_con(frente_x, frente_y):
                return False
        for obj in estado.bloques_acero:
            if obj.activo and obj.colisiona_con(frente_x, frente_y):
                return False
        snake._iniciar_desenroscamiento()
        return True

    def verificar_gate(self):
        """Verifica si la cabeza está en una celda con stack 'contact' y ejecuta eventos"""
        estado = self.estado
        if estado.cambiando_nivel:
            return False
        cabeza = estado.snake.get_cabeza()
        if not cabeza:
            return False
        estado.stack_manager.process_events(cabeza[0], cabeza[1], "contact", estado.snake.z)
        return False
