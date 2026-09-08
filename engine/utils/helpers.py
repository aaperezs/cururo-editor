# utils/helpers.py
import random

from engine.configs import *


def alinear_a_grid(x, y):
    """Alinea una posición a la cuadrícula de TAMANO_CELDA"""
    x = (x // TAMANO_CELDA) * TAMANO_CELDA
    y = (y // TAMANO_CELDA) * TAMANO_CELDA
    return x, y

def posicion_en_grid(pos):
    """Verifica si una posición está alineada a la cuadrícula"""
    x, y = pos
    return x % TAMANO_CELDA == 0 and y % TAMANO_CELDA == 0

def generar_comida_normal(snake_body, obstaculos=None, zonas_restringidas=None, limite_ancho=None, limite_alto=None, suelos=None):
    """Genera comida en una posición válida (fuera de obstáculos y zonas restringidas)"""
    if obstaculos is None:
        obstaculos = []
    if zonas_restringidas is None:
        zonas_restringidas = []
    if suelos is None:
        suelos = []
    if limite_ancho is None:
        limite_ancho = ANCHO
    if limite_alto is None:
        limite_alto = ALTO

    MARGEN = TAMANO_CELDA * 2

    intentos = 0
    while intentos < 200:
        x = random.randrange(MARGEN, limite_ancho - MARGEN, TAMANO_CELDA)
        y = random.randrange(MARGEN, limite_alto - MARGEN, TAMANO_CELDA)

        x, y = alinear_a_grid(x, y)

        ocupado = False

        for suelo in suelos:
            if suelo.x == x and suelo.y == y and suelo.no_food_spawn:
                ocupado = True
                break

        if ocupado:
            intentos += 1
            continue

        for obj in obstaculos:
            if not obj.activo:
                continue
            if hasattr(obj, 'ancho') and (obj.ancho != TAMANO_CELDA or obj.alto != TAMANO_CELDA):
                if obj.x <= x < obj.x + obj.ancho and obj.y <= y < obj.y + obj.alto:
                    ocupado = True
                    break
            elif obj.x == x and obj.y == y:
                ocupado = True
                break

        if ocupado:
            continue

        if (x, y) in zonas_restringidas:
            continue

        if [x, y] not in snake_body:
            return x, y

        intentos += 1

    return (limite_ancho // 2, limite_alto // 2)

def generar_comida_cerca(snake_body, posicion_referencia, distancia_max=10, limite_ancho=None, limite_alto=None):
    """Genera comida cerca de una posición de referencia (distancia_max en celdas)"""
    ref_x, ref_y = posicion_referencia
    intentos = 0
    while intentos < 100:
        offset_x = random.randint(-distancia_max, distancia_max) * TAMANO_CELDA
        offset_y = random.randint(-distancia_max, distancia_max) * TAMANO_CELDA
        x = ref_x + offset_x
        y = ref_y + offset_y
        x = max(0, min(ANCHO - TAMANO_CELDA, x))
        y = max(0, min(ALTO - TAMANO_CELDA, y))
        x = (x // TAMANO_CELDA) * TAMANO_CELDA
        y = (y // TAMANO_CELDA) * TAMANO_CELDA
        if [x, y] not in snake_body:
            return x, y
        intentos += 1
    return generar_comida_normal(snake_body, limite_ancho=limite_ancho, limite_alto=limite_alto)

def generar_comida_dentro_arena(snake_body, arena_boss):
    """Genera comida DENTRO de la arena del jefe"""
    intentos = 0
    while intentos < 100:
        x = random.randrange(arena_boss.limite_izquierdo, arena_boss.limite_derecho, TAMANO_CELDA)
        y = random.randrange(arena_boss.limite_superior, arena_boss.limite_inferior, TAMANO_CELDA)
        if [x, y] not in snake_body:
            return x, y
        intentos += 1
    # Si no encuentra posición, devolver el centro de la arena
    return (arena_boss.x + arena_boss.ancho // 2, arena_boss.y + arena_boss.alto // 2)

def distancia(x1, y1, x2, y2):
    return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5
