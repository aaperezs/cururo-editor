# managers/comida_manager.py
import pygame
from engine.configs import *
from engine.entities.food import Food
from engine.utils.helpers import generar_comida_normal


class ComidaManager:
    def __init__(self, estado):
        self.estado = estado

    def actualizar(self):
        """Actualiza la lógica de la comida"""
        estado = self.estado

        arena_activa = estado.arena_boss.activa
        boss_vivo = estado.arena_boss.boss is not None and estado.arena_boss.boss.vivo
        comida_disponible = not arena_activa or not boss_vivo

        if not comida_disponible:
            return False

        if not estado.comida:
            return False

        cabeza = estado.snake.get_cabeza()
        if not cabeza:
            return False

        cabeza_rect = pygame.Rect(cabeza[0], cabeza[1], TAMANO_CELDA, TAMANO_CELDA)
        comida_rect = pygame.Rect(estado.comida.x, estado.comida.y, TAMANO_CELDA, TAMANO_CELDA)

        if cabeza_rect.colliderect(comida_rect):
            self._comer_comida()
            return True

        return False

    def _comer_comida(self):
        """Maneja el consumo de comida"""
        estado = self.estado
        cabeza = estado.snake.get_cabeza()
        fx = cabeza[0] + TAMANO_CELDA // 2 if cabeza else ANCHO // 2
        fy = cabeza[1] - 20 if cabeza else ALTO // 2

        if estado.comida.tipo == COMIDA_NORMAL:
            estado.snake.crecer(1)
            estado.text_service.spawn("+1", fx, fy, 30, VERDE_CLARO)
        elif estado.comida.tipo == COMIDA_MANA:
            if estado.habilidades.recargar_pp(cantidad=1):
                estado.text_service.spawn("+PP", fx, fy, 30, MORADO)
            else:
                estado.snake.crecer(1)
                estado.text_service.spawn("+1", fx, fy, 30, VERDE_CLARO)
        elif estado.comida.tipo == COMIDA_ESPECIAL:
            estado.snake.crecer(3)
            estado.text_service.spawn("+3", fx, fy, 40, DORADO)

        if getattr(estado, 'no_comida_spawn', False):
            estado.comida = None
            return

        x, y = generar_comida_normal(
            estado.snake.body,
            list(estado.bloqueantes) + list(estado.bloques_acero) + list(estado.paredes),
            estado.zonas_restringidas,
            estado.nivel_ancho,
            estado.nivel_alto,
            getattr(estado, 'suelos', [])
        )
        estado.comida = Food.generar_en_posicion(x, y)
        print(f"Nueva comida en: ({x}, {y})")

    def comida_disponible(self):
        """Verifica si la comida está disponible en el mapa"""
        estado = self.estado
        arena_activa = estado.arena_boss.activa
        boss_vivo = estado.arena_boss.boss is not None and estado.arena_boss.boss.vivo
        return not arena_activa or not boss_vivo
