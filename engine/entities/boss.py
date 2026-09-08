import math
import random

import pygame
from engine.configs import *


def _merge_dict(base, override):
    result = dict(base)
    if override:
        result.update(override)
    return result


class Boss:
    def __init__(self, x, y, tipo="tronco", z=Z_MAPA_PRINCIPAL):
        self.x = x
        self.y = y
        self.tipo = tipo
        self.z = z
        self.ancho = TAMANO_CELDA * 3
        self.alto = TAMANO_CELDA * 3
        self.vida_maxima = 100
        self.vida = self.vida_maxima
        self.fase = 0
        self.velocidad_base = 1
        self.velocidad_actual = self.velocidad_base
        self.angulo = 0
        self.radio = 100
        self.centro_x = x
        self.centro_y = y
        self.vivo = True
        self.estado = "IDLE"
        self.tiempo_estado = 0
        self.proyectiles = []
        self.tiempo_entre_ataques = 60
        self.max_proyectiles = 3
        self.brillo = 0
        self.animacion_golpe = 0
        self.proyectiles_comidos = 0
        self.damage_per_cycle = 20
        self.fight_type = "orbital"
        self.phases = []
        self.sprite_sheet = ""
        self.sprite_rows = 1
        self.sprite_cols = 1
        self.sprite_frame_w = 60
        self.sprite_frame_h = 60
        self.sprite_interval = 12
        self._sprite_frames = None
        self._configurar_tipo(tipo)

    def _configurar_tipo(self, tipo):
        from engine.repositories import RepositorioJefes
        repo = RepositorioJefes()
        config = repo.get_config(tipo)

        self.color = tuple(config.get("color", [139, 69, 19]))
        self.color_herido = tuple(config.get("color_herido", [200, 100, 50]))
        self.nombre = config.get("nombre", tipo)
        self.vida_maxima = config.get("vida_maxima", 100)
        self.vida = self.vida_maxima
        self.color_barra = tuple(config.get("color_barra", [0, 200, 50]))
        self.icono = config.get("icono", "?")
        self.proyectiles_necesarios = config.get("proyectiles_necesarios", 3)
        self.damage_per_cycle = config.get("damage_per_cycle", 20)
        self.fight_type = config.get("fight_type", "orbital")
        self.phases = config.get("phases", [])
        self.max_proyectiles = self.proyectiles_necesarios

        self.sprite_sheet = config.get("sprite_sheet", "")
        self.sprite_rows = config.get("sprite_rows", 1)
        self.sprite_cols = config.get("sprite_cols", 1)
        self.sprite_frame_w = config.get("sprite_frame_w", self.ancho)
        self.sprite_frame_h = config.get("sprite_frame_h", self.alto)
        self.sprite_interval = config.get("sprite_interval", 12)
        if self.sprite_sheet:
            from engine.utils.sprite_sheet import cargar_hoja
            self._sprite_frames = cargar_hoja(
                self.sprite_sheet,
                self.sprite_rows,
                self.sprite_cols,
                self.sprite_frame_w,
                self.sprite_frame_h,
            )
        else:
            self._sprite_frames = None

        self._apply_phase()

    def _phase_config(self):
        if not self.phases:
            return {"params": {}, "visual": {}}
        ratio = self.vida / self.vida_maxima if self.vida_maxima > 0 else 0
        for p in self.phases:
            if ratio >= p.get("hp_threshold", 0.0):
                return p
        return self.phases[-1]

    def _phase_param(self, key, default=None):
        pcfg = self._phase_config()
        return pcfg.get("params", {}).get(key, default)

    def _phase_visual(self, key, default=None):
        pcfg = self._phase_config()
        return pcfg.get("visual", {}).get(key, default)

    def _apply_phase(self):
        pcfg = self._phase_config()
        pp = pcfg.get("params", {})
        self.velocidad_actual = self.velocidad_base * pp.get("speed_mult", 1.0)
        self.tiempo_entre_ataques = pp.get("attack_cooldown", 60)
        self.radio = pp.get("orbit_radius", 100)
        phase_index = 0
        for i, p in enumerate(self.phases):
            if p is pcfg:
                phase_index = i
                break
        self.fase = phase_index

    def mover(self):
        if not self.vivo:
            return

        self.tiempo_estado += 1

        if self.brillo > 0:
            self.brillo -= 1

        if self.animacion_golpe > 0:
            self.animacion_golpe -= 1

        pcfg = self._phase_config()
        pp = pcfg.get("params", {})
        orbit_speed = pp.get("orbit_speed", 0.02)
        radius = pp.get("orbit_radius", 100)

        self.angulo += orbit_speed * self.velocidad_actual
        self.x = self.centro_x + radius * math.cos(self.angulo)
        self.y = self.centro_y + radius * math.sin(self.angulo)

        if self.tiempo_estado > self.tiempo_entre_ataques:
            self.tiempo_estado = 0
            self.generar_proyectiles()

        self.actualizar_proyectiles()

    def generar_proyectiles(self):
        if not self.vivo:
            return

        pcfg = self._phase_config()
        pp = pcfg.get("params", {})
        count_bonus = pp.get("projectile_count_bonus", 0)
        proj_speed = pp.get("projectile_speed", 2.0)
        comestible_chance = pp.get("comestible_chance", 0.6)
        angle_spread = pp.get("angle_spread", 0.2)
        lifetime = pp.get("projectile_lifetime", 180)
        golden_r = pp.get("golden_radius", 10)
        red_r = pp.get("red_radius", 8)

        num_proyectiles = self.max_proyectiles + count_bonus
        for i in range(num_proyectiles):
            angulo = (i / num_proyectiles) * 2 * math.pi + random.uniform(-angle_spread, angle_spread)
            velocidad = proj_speed
            es_comestible = random.random() < comestible_chance

            if es_comestible:
                color = DORADO
                radio = golden_r
            else:
                color = ROJO
                radio = red_r

            proyectil = {
                "x": self.x + self.ancho // 2,
                "y": self.y + self.alto // 2,
                "dx": velocidad * math.cos(angulo),
                "dy": velocidad * math.sin(angulo),
                "radio": radio,
                "vida": lifetime,
                "color": color,
                "comestible": es_comestible,
                "pulsacion": 0
            }
            self.proyectiles.append(proyectil)

    def actualizar_proyectiles(self):
        for proyectil in self.proyectiles[:]:
            proyectil["x"] += proyectil["dx"]
            proyectil["y"] += proyectil["dy"]
            proyectil["vida"] -= 1
            proyectil["pulsacion"] += 0.05
            if proyectil["vida"] <= 0:
                self.proyectiles.remove(proyectil)

    def recibir_danio(self, cantidad):
        if not self.vivo:
            return False

        self.vida -= cantidad
        self.estado = "HERIDO"
        self.animacion_golpe = 10
        self.brillo = 20
        self._apply_phase()

        if self.vida <= 0:
            self.vivo = False
            return True
        return False

    def dibujar(self, pantalla, offset_x=0, offset_y=0):
        if not self.vivo:
            return

        escala = 1.0
        if self.animacion_golpe > 0:
            escala = 1.0 + (self.animacion_golpe / 20) * 0.1

        ancho_sprite = int(self.ancho * escala)
        alto_sprite = int(self.alto * escala)
        cx = int(self.x + self.ancho // 2) + offset_x
        cy = int(self.y + self.alto // 2) + offset_y

        herido = self.estado == "HERIDO" and self.brillo > 0 and pygame.time.get_ticks() % 100 < 50

        if self._sprite_frames:
            cols = max(1, self.sprite_cols)
            frames = self._sprite_frames
            fila = min(max(0, self.fase), len(frames) // cols - 1)
            col = (pygame.time.get_ticks() // max(1, self.sprite_interval)) % cols
            idx = fila * cols + col
            if idx < len(frames):
                frame = frames[idx]
                if frame.get_size() != (ancho_sprite, alto_sprite):
                    frame = pygame.transform.scale(frame, (ancho_sprite, alto_sprite))
                pantalla.blit(frame, (cx - ancho_sprite // 2, cy - alto_sprite // 2))
            self.dibujar_proyectiles(pantalla, offset_x, offset_y)
            return

        w3 = ancho_sprite // 2
        h3 = alto_sprite // 2

        v = self._phase_config().get("visual", {})
        if herido:
            c_tronco = (200, 160, 100)
        else:
            c_tronco = tuple(v.get("trunk_color", (95, 60, 28)))
        c_osc = (55, 32, 12)
        c_musgo = (50, 75, 35)

        tronco = [
            (cx - 14, cy - h3), (cx + 14, cy - h3),
            (cx + 18, cy - h3 + 10), (cx + 20, cy - 10),
            (cx + 24, cy + 10), (cx + 26, cy + h3 - 8),
            (cx + 22, cy + h3), (cx - 22, cy + h3),
            (cx - 26, cy + h3 - 8), (cx - 24, cy + 10),
            (cx - 20, cy - 10), (cx - 18, cy - h3 + 10),
        ]
        pygame.draw.polygon(pantalla, c_tronco, tronco)
        pygame.draw.polygon(pantalla, NEGRO, tronco, 2)

        for gx in [cx - 10, cx - 4, cx + 2, cx + 8, cx + 14]:
            pygame.draw.line(pantalla, c_osc, (gx, cy - h3 + 6), (gx, cy + h3 - 6), 1)

        for nx, ny, nr in [(cx - 12, cy + 15, 3), (cx + 10, cy - 18, 2), (cx + 8, cy + 25, 3)]:
            pygame.draw.circle(pantalla, c_osc, (nx, ny), nr)
            pygame.draw.circle(pantalla, c_tronco, (nx, ny), nr - 1)

        cima_pts = [
            (cx - 14, cy - h3), (cx - 10, cy - h3 - 4), (cx - 5, cy - h3),
            (cx - 1, cy - h3 - 3), (cx + 5, cy - h3 - 1), (cx + 10, cy - h3 - 5),
            (cx + 14, cy - h3),
        ]
        pygame.draw.polygon(pantalla, (130, 90, 45), cima_pts)
        pygame.draw.polygon(pantalla, NEGRO, cima_pts, 1)
        for ay in [cy - h3 - 1, cy - h3 - 3]:
            pygame.draw.ellipse(pantalla, (150, 110, 55), (cx - 8, ay, 16, 3), 1)

        for rx, ry, rdx, rdy in [
            (-18, cy + h3 - 4, -12, 8), (-8, cy + h3, -10, 6),
            (8, cy + h3, 10, 6), (18, cy + h3 - 4, 12, 8),
        ]:
            pygame.draw.line(pantalla, c_osc, (cx + rx, ry), (cx + rx + rdx, ry + rdy), 3)

        for vx, vl in [(cx - 8, 14), (cx, 18), (cx + 6, 12)]:
            for vi in range(vl):
                viy = cy - h3 + vi * 3
                if viy < cy + h3 - 10:
                    pygame.draw.line(pantalla, c_musgo, (vx, viy), (vx + 1, viy + 4), 1)

        for mx, my, mr in [(cx - 10, cy - 5, 4), (cx + 6, cy + 12, 5),
                            (cx - 4, cy + 22, 3), (cx + 14, cy - 12, 3)]:
            pygame.draw.circle(pantalla, c_musgo, (mx, my), mr)
        pygame.draw.ellipse(pantalla, (40, 25, 10), (cx - 8, cy + 5, 16, 8))

        for hx, hy in [(cx - 16, cy + h3 - 2), (cx + 12, cy + h3 - 3)]:
            pygame.draw.ellipse(pantalla, (190, 120, 100), (hx - 4, hy - 2, 8, 5))
            pygame.draw.line(pantalla, (210, 190, 160), (hx, hy), (hx, hy - 4), 2)

        ojo_tam = v.get("eye_size", 5)
        ojo_tam = max(3, ojo_tam)
        color_brillo = tuple(v.get("eye_color", (150, 200, 80)))

        for ox, oy in [(cx - 7, cy - 8), (cx + 7, cy - 8)]:
            pygame.draw.circle(pantalla, (10, 5, 2), (ox, oy), ojo_tam + 3)
            pygame.draw.circle(pantalla, NEGRO, (ox, oy), ojo_tam + 3, 1)
            pygame.draw.circle(pantalla, color_brillo, (ox, oy), ojo_tam)
            pygame.draw.circle(pantalla, (255, 255, 200), (ox - 1, oy - 1), ojo_tam // 2)

        boca = [(cx - 9, cy + 6), (cx - 5, cy + 3), (cx, cy + 7), (cx + 5, cy + 4), (cx + 9, cy + 6)]
        pygame.draw.lines(pantalla, (5, 2, 0), False, boca, 2)
        pygame.draw.ellipse(pantalla, (15, 8, 3), (cx - 6, cy + 6, 12, 4))

        self.dibujar_proyectiles(pantalla, offset_x, offset_y)

    def dibujar_ui(self, pantalla, x_ui, y_ui):
        if not self.vivo:
            return

        MADERA_CLARO = (100, 70, 40)
        MADERA = (75, 50, 25)
        MADERA_OSCURO = (50, 35, 15)
        RUNA_BRILLO = (200, 180, 100)
        PIEDRA = (60, 55, 50)

        barra_x = ANCHO - 42
        barra_y = 50
        barra_w = 22
        barra_h = ALTO - 160
        segmentos = min(16, max(4, self.vida_maxima // 5))
        alto_seg = barra_h // segmentos

        vida_porcentaje = max(0, self.vida / self.vida_maxima)
        seg_llenos = int(segmentos * vida_porcentaje)

        v = self._phase_config().get("visual", {})
        bar_color_override = v.get("bar_color")
        if bar_color_override:
            color_barra = tuple(bar_color_override)
        else:
            color_barra = self.color_barra

        pygame.draw.rect(pantalla, MADERA_OSCURO, (barra_x - 3, barra_y - 3, barra_w + 6, barra_h + 6))
        pygame.draw.rect(pantalla, MADERA, (barra_x - 2, barra_y - 2, barra_w + 4, barra_h + 4))
        for vy in range(barra_y - 2, barra_y + barra_h + 2, 8):
            pygame.draw.line(pantalla, MADERA_OSCURO, (barra_x - 2, vy), (barra_x + barra_w + 2, vy), 1)
        for ry, rx in [(barra_y - 2, barra_x - 2), (barra_y - 2, barra_x + barra_w),
                      (barra_y + barra_h, barra_x - 2), (barra_y + barra_h, barra_x + barra_w)]:
            pygame.draw.circle(pantalla, (140, 120, 80), (rx + 1, ry + 1), 2)

        pygame.draw.rect(pantalla, PIEDRA, (barra_x + 1, barra_y + 1, barra_w - 2, barra_h - 2))

        for i in range(segmentos):
            sy = barra_y + i * alto_seg
            if i < seg_llenos:
                t = i / segmentos
                c = (min(255, color_barra[0] + int(60 * (1 - t))),
                     min(255, color_barra[1] + int(30 * (1 - t))),
                     min(255, color_barra[2] + int(10 * t)))
                pygame.draw.rect(pantalla, c, (barra_x + 2, sy + 1, barra_w - 4, alto_seg - 1))
                if i == seg_llenos - 1 or i == 0:
                    pygame.draw.rect(pantalla, RUNA_BRILLO, (barra_x + 2, sy + 1, barra_w - 4, 2))
            else:
                pygame.draw.rect(pantalla, (35, 30, 28), (barra_x + 2, sy + 1, barra_w - 4, alto_seg - 1))
            pygame.draw.line(pantalla, (45, 40, 35), (barra_x + 1, sy), (barra_x + barra_w - 1, sy), 1)

        fuente = pygame.font.SysFont("Arial", 11, bold=True)
        for dy, txt in enumerate([self.icono, self.nombre.split(",")[0]]):
            texto = fuente.render(txt, True, (200, 190, 170))
            tx = barra_x + barra_w // 2 - texto.get_width() // 2
            ty = barra_y - 16 + dy * 14
            pantalla.blit(texto, (tx, ty))

        if self.proyectiles_necesarios > 0:
            cx = ANCHO // 2
            cy = 18
            separacion = 36
            inicio_x = cx - (self.proyectiles_necesarios - 1) * separacion // 2
            for i in range(self.proyectiles_necesarios):
                sx = inicio_x + i * separacion
                lleno = i < self.proyectiles_comidos
                radio = 10
                pygame.draw.circle(pantalla, (50, 45, 40), (sx, cy), radio)
                pygame.draw.circle(pantalla, (80, 70, 60), (sx, cy), radio, 2)
                if lleno:
                    pygame.draw.circle(pantalla, (240, 190, 30), (sx, cy), radio - 1)
                    pygame.draw.circle(pantalla, (255, 230, 120), (sx - 2, cy - 2), radio // 2)
                    pygame.draw.circle(pantalla, (200, 150, 20), (sx + 1, cy + 1), radio // 3)
                    pygame.draw.circle(pantalla, NEGRO, (sx, cy), radio, 1)

        fuente_fase = pygame.font.SysFont("Arial", 10)
        fase_color = tuple(v.get("rune_color", (100, 200, 100)))
        runa = v.get("rune", "\u00de\u00be")
        texto_fase = fuente_fase.render(f"{runa} F{self.fase + 1}", True, fase_color)
        tx = barra_x + barra_w // 2 - texto_fase.get_width() // 2
        pantalla.blit(texto_fase, (tx, barra_y + barra_h + 6))

    def dibujar_proyectiles(self, pantalla, offset_x=0, offset_y=0):
        for proyectil in self.proyectiles:
            pulsacion = abs(math.sin(proyectil["pulsacion"]))
            radio_actual = proyectil["radio"] + pulsacion * 2
            px = int(proyectil["x"]) + offset_x
            py = int(proyectil["y"]) + offset_y

            if proyectil["comestible"]:
                for g in range(3, 0, -1):
                    alpha = 80 - g * 20
                    surf = pygame.Surface((radio_actual * 4, radio_actual * 4), pygame.SRCALPHA)
                    pygame.draw.circle(surf, (255, 220, 50, alpha), (radio_actual * 2, radio_actual * 2), radio_actual + g * 3)
                    pantalla.blit(surf, (px - radio_actual * 2, py - radio_actual * 2))
                pygame.draw.circle(pantalla, (240, 190, 30), (px, py), radio_actual)
                pygame.draw.circle(pantalla, NEGRO, (px, py), radio_actual, 1)
                pygame.draw.circle(pantalla, (255, 230, 120), (px - 3, py - 3), radio_actual // 2)
                pygame.draw.circle(pantalla, (200, 150, 20), (px + 2, py + 2), radio_actual // 4)
                diam = max(3, radio_actual // 2)
                pygame.draw.polygon(pantalla, (255, 240, 180), [
                    (px, py - diam), (px + diam, py),
                    (px, py + diam), (px - diam, py)
                ])
                pygame.draw.polygon(pantalla, NEGRO, [
                    (px, py - diam), (px + diam, py),
                    (px, py + diam), (px - diam, py)
                ], 1)
            else:
                for g in range(3, 0, -1):
                    alpha = 70 - g * 20
                    surf = pygame.Surface((radio_actual * 4, radio_actual * 4), pygame.SRCALPHA)
                    pygame.draw.circle(surf, (180, 20, 20, alpha), (radio_actual * 2, radio_actual * 2), radio_actual + g * 3)
                    pantalla.blit(surf, (px - radio_actual * 2, py - radio_actual * 2))
                fire_r = radio_actual
                pygame.draw.circle(pantalla, (40, 8, 8), (px, py), fire_r)
                pygame.draw.circle(pantalla, (180, 30, 20), (px, py), fire_r - 2)
                pygame.draw.circle(pantalla, (255, 100, 30), (px, py), fire_r - 4)
                pygame.draw.circle(pantalla, (255, 220, 100), (px - 2, py - 2), fire_r // 3)
                for fi in range(4):
                    fa = fi * 90 + int(proyectil["pulsacion"] * 30) % 90
                    fr = fire_r - 1
                    fx = px + fr * math.cos(math.radians(fa))
                    fy = py + fr * math.sin(math.radians(fa))
                    pygame.draw.polygon(pantalla, (200, 60, 30), [
                        (int(fx), int(fy)),
                        (int(fx + 4 * math.cos(math.radians(fa - 120))), int(fy + 4 * math.sin(math.radians(fa - 120)))),
                        (int(fx + 4 * math.cos(math.radians(fa + 120))), int(fy + 4 * math.sin(math.radians(fa + 120)))),
                    ])

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.ancho, self.alto)
