# managers/combate_manager.py - COMPLETO
import random

import pygame
from engine.configs import *


class CombateManager:
    def __init__(self, estado, mostrar_mensaje, perder_segmentos):
        self.estado = estado
        self.mostrar_mensaje = mostrar_mensaje
        self.perder_segmentos = perder_segmentos

    def actualizar_enemigos(self):
        """Actualiza los enemigos y maneja colisiones"""
        estado = self.estado

        if estado.arena_boss.activa and estado.boss and estado.boss.vivo:
            return False

        # --- ACTUALIZAR ENEMIGOS ---
        for enemigo in estado.enemigos[:]:
            if not enemigo.vivo:
                continue

            if not enemigo.aturdido:
                objetos_solidos = estado.bloques_acero + estado.bloqueantes + estado.paredes
                enemigo.mover(objetos=objetos_solidos)
            else:
                enemigo.actualizar_aturdimiento()

            enemigo_rect = enemigo.get_rect()
            cabeza = estado.snake.get_cabeza()

            if not cabeza:
                continue

            cabeza_rect = pygame.Rect(cabeza[0], cabeza[1], TAMANO_CELDA, TAMANO_CELDA)

            if cabeza_rect.colliderect(enemigo_rect):
                if estado.snake.invencible:
                    continue

                # Verificar si tiene Manto de Oscuridad activo
                habilidad_equipada = estado.habilidades.get_habilidad_equipada()
                tiene_manto = (habilidad_equipada and
                              habilidad_equipada.get("efecto") == "manto" and
                              estado.habilidades.get_pp_actual() > 0)

                if tiene_manto:
                    # CON MANTO: El enemigo muere
                    enemigo.vivo = False
                    estado.stack_manager.on_entity_destroyed(enemigo.x_inicial, enemigo.y_inicial, "enemigo")
                    # Process drops
                    drops = getattr(enemigo, "drops", [])
                    current_ability = estado.habilidades.habilidad_equipada
                    for drop in drops:
                        prob = drop.get("prob", 100)
                        if random.randint(1, 100) > prob:
                            continue
                        req_ability = drop.get("ability", "")
                        if req_ability and req_ability != current_ability:
                            continue
                        item_id = drop.get("item", "")
                        if item_id and hasattr(estado, "inventario"):
                            estado.inventario.agregar_item(item_id, 1)
                    estado.particles.crear_explosion(
                        enemigo.x + TAMANO_CELDA//2,
                        enemigo.y + TAMANO_CELDA//2,
                        15, MORADO
                    )
                    estado.habilidades.usar_habilidad()
                else:
                    # SIN MANTO: La serpiente recibe daño
                    dano = random.randint(2, 4)

                    # Verificar si tiene 3 segmentos (muerte instantánea)
                    if estado.snake.get_longitud() <= 3:
                        estado.game_over = True
                        estado.death_cause = f"Enemigo melee con {estado.snake.get_longitud()} segs"
                        self.mostrar_mensaje("¡Has muerto!", 60)
                        estado.particles.crear_explosion(
                            cabeza[0] + TAMANO_CELDA//2,
                            cabeza[1] + TAMANO_CELDA//2,
                            30, ROJO
                        )
                        return True

                    if self.perder_segmentos(dano):
                        return True

                    # Aturdir al enemigo
                    enemigo.aturdir()

                    estado.particles.crear_explosion(
                        enemigo.x + TAMANO_CELDA//2,
                        enemigo.y + TAMANO_CELDA//2,
                        5, GRIS
                    )
                    break

        # --- NUEVO: VERIFICAR PROYECTILES DE SHOOTERS ---
        cabeza = estado.snake.get_cabeza()
        if cabeza:
            cabeza_rect = pygame.Rect(cabeza[0], cabeza[1], TAMANO_CELDA, TAMANO_CELDA)
            for enemigo in estado.enemigos:
                if hasattr(enemigo, 'get_proyectiles') and enemigo.vivo:
                    for proyectil in enemigo.get_proyectiles()[:]:
                        proy_rect = pygame.Rect(
                            proyectil["x"] - proyectil["radio"],
                            proyectil["y"] - proyectil["radio"],
                            proyectil["radio"] * 2,
                            proyectil["radio"] * 2
                        )
                        if cabeza_rect.colliderect(proy_rect):
                            # Daño a la serpiente
                            if not estado.snake.invencible:
                                # Verificar si tiene 3 segmentos (muerte instantánea)
                                if estado.snake.get_longitud() <= 3:
                                    estado.game_over = True
                                    estado.death_cause = f"Proyectil con {estado.snake.get_longitud()} segs"
                                    self.mostrar_mensaje("¡Has muerto!", 60)
                                    estado.particles.crear_explosion(
                                        cabeza[0] + TAMANO_CELDA//2,
                                        cabeza[1] + TAMANO_CELDA//2,
                                        30, ROJO
                                    )
                                    return True

                                dano = random.randint(1, 2)
                                if self.perder_segmentos(dano):
                                    return True
                                enemigo.proyectiles.remove(proyectil)
                                estado.particles.crear_explosion(proyectil["x"], proyectil["y"], 5, ROJO)
                            break

        return False

    def actualizar_jefe(self):
        """Actualiza la lógica del jefe"""
        estado = self.estado

        if not estado.arena_boss.activa or not estado.boss or not estado.boss.vivo:
            return False

        estado.arena_boss.actualizar_entrada(estado.snake, estado)

        # Keep camera centered on arena while arena is active
        if estado.arena_boss.activa and not estado.arena_boss.es_nivel_completo:
            arena = estado.arena_boss
            centro = (arena.x + arena.ancho // 2, arena.y + arena.alto // 2)
            min_cx = arena.x + arena.ancho - ANCHO
            max_cx = arena.x
            if min_cx > max_cx:
                cx = (min_cx + max_cx) // 2
            else:
                cx = max(min_cx, min(centro[0] - ANCHO // 2, max_cx))
            min_cy = arena.y + arena.alto - ALTO
            max_cy = arena.y
            if min_cy > max_cy:
                cy = (min_cy + max_cy) // 2
            else:
                cy = max(min_cy, min(centro[1] - ALTO // 2, max_cy))
            estado.camera.x = cx
            estado.camera.y = cy
            estado.camera.seguir(centro)

        if not estado.arena_boss.en_pelea():
            return False

        estado.boss.mover()

        cabeza = estado.snake.get_cabeza()
        if not cabeza:
            return False

        # Limitar dentro de la arena (bordes y paredes)
        if estado.arena_boss.colision_con_borde(cabeza):
            if cabeza[0] < estado.arena_boss.limite_izquierdo:
                estado.snake.body[0][0] = estado.arena_boss.limite_izquierdo
            elif cabeza[0] >= estado.arena_boss.limite_derecho:
                estado.snake.body[0][0] = estado.arena_boss.limite_derecho - TAMANO_CELDA
            if cabeza[1] < estado.arena_boss.limite_superior:
                estado.snake.body[0][1] = estado.arena_boss.limite_superior
            elif cabeza[1] >= estado.arena_boss.limite_inferior:
                estado.snake.body[0][1] = estado.arena_boss.limite_inferior - TAMANO_CELDA
        # Colision con paredes de la arena
        for p in estado.arena_boss.paredes:
            if p.activo and p.colisiona_con(cabeza[0], cabeza[1]):
                resultado = p.manejar_colision(estado.snake, estado)
                if resultado == "mata":
                    return True

        # Proyectiles
        cabeza_rect = pygame.Rect(cabeza[0], cabeza[1], TAMANO_CELDA, TAMANO_CELDA)
        self._manejar_proyectiles(cabeza_rect)

        # Colisión con jefe
        if estado.boss.vivo and cabeza_rect.colliderect(estado.boss.get_rect()):
            if not estado.snake.invencible:
                dano = random.randint(3, 6)
                if self.perder_segmentos(dano):
                    return True

        return False

    def _manejar_proyectiles(self, cabeza_rect):
        """Maneja la colisión con proyectiles del jefe"""
        estado = self.estado

        for proyectil in estado.boss.proyectiles[:]:
            proy_rect = pygame.Rect(
                proyectil["x"] - proyectil["radio"],
                proyectil["y"] - proyectil["radio"],
                proyectil["radio"] * 2,
                proyectil["radio"] * 2
            )

            if cabeza_rect.colliderect(proy_rect):
                self._manejar_proyectil(proyectil)

    def _manejar_proyectil(self, proyectil):
        """Maneja un proyectil individual"""
        estado = self.estado

        if proyectil["comestible"]:
            estado.proyectiles_comidos += 1
            estado.boss.proyectiles_comidos = estado.proyectiles_comidos
            estado.boss.proyectiles.remove(proyectil)
            estado.particles.crear_explosion(proyectil["x"], proyectil["y"], 15, DORADO)
            estado.snake.brillo = 30

            needed = getattr(estado.boss, 'proyectiles_necesarios', estado.proyectiles_necesarios)
            if estado.proyectiles_comidos >= needed:
                estado.proyectiles_comidos = 0
                estado.boss.proyectiles_comidos = 0
                danio = getattr(estado.boss, 'damage_per_cycle', 20)
                if estado.boss.recibir_danio(danio):
                    self._derrotar_jefe()
                else:
                    estado.particles.crear_explosion(estado.boss.x, estado.boss.y, 20, ROJO)
        else:
            if not estado.snake.invencible:
                dano = random.randint(2, 4)
                if self.perder_segmentos(dano):
                    return True
                estado.boss.proyectiles.remove(proyectil)
                estado.particles.crear_explosion(proyectil["x"], proyectil["y"], 10, ROJO)

        return False

    def _derrotar_jefe(self):
        """Maneja la derrota del jefe - delega a eventos post-boss"""
        estado = self.estado
        if getattr(estado, '_jefe_derrotado', False):
            return
        estado._jefe_derrotado = True

        boss_id = estado.boss.tipo if estado.boss else "tronco"

        # Efectos visuales inmediatos
        estado.particles.crear_explosion(estado.boss.x, estado.boss.y, 30, DORADO)
        estado.snake.brillo = 0
        estado.boss.vivo = False
        print(f"Jefe {estado.boss.nombre} marcado como muerto")

        # Disparar eventos post-boss (diálogo, skill unlock, demo, etc.)
        estado.stack_manager.on_boss_defeated(boss_id)
