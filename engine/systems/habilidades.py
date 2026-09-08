# systems/habilidades.py - CON HABILIDAD BASE
import pygame
from engine.configs import *


class SistemaHabilidades:
    def __init__(self):
        self.habilidades = {}
        self.habilidad_equipada = None
        self.inventario = []

        # Inicializar todas las habilidades
        for hid, config in HABILIDADES.items():
            self.habilidades[hid] = {
                "desbloqueada": False,
                "pp_actual": config["pp_max"],
                "pp_max": config["pp_max"],
                "nombre": config["nombre"],
                "descripcion": config["descripcion"],
                "color": config["color"],
                "tecla": config["tecla"],
                "efecto": config["efecto"]
            }

        # --- NUEVO: Desbloquear habilidad BASE desde el inicio ---
        self.habilidades[HabilidadID.BASE]["desbloqueada"] = True
        self.inventario.append(HabilidadID.BASE)
        self.habilidad_equipada = HabilidadID.BASE

    def desbloquear_habilidad(self, hid):
        """Desbloquea una habilidad y la añade al inventario"""
        if hid in self.habilidades and not self.habilidades[hid]["desbloqueada"]:
            self.habilidades[hid]["desbloqueada"] = True
            self.habilidades[hid]["pp_actual"] = self.habilidades[hid]["pp_max"]
            if hid not in self.inventario:
                self.inventario.append(hid)
            # No cambiamos automáticamente a la nueva habilidad
            # El jugador decide con TAB
            return True
        return False

    def equipar_habilidad(self, hid):
        """Equipa una habilidad"""
        if hid in self.habilidades and self.habilidades[hid]["desbloqueada"]:
            self.habilidad_equipada = hid
            return True
        return False

    def usar_habilidad(self):
        """Usa la habilidad equipada - RETORNA el efecto"""
        if not self.habilidad_equipada:
            if MOSTRAR_LOGS: print(f"[HAB] FALLO: habilidad_equipada = None (inventario={self.inventario})")
            return None

        habilidad = self.habilidades[self.habilidad_equipada]

        if habilidad["efecto"] == "base":
            if MOSTRAR_LOGS: print(f"[HAB] FALLO: efecto='base' (hid={self.habilidad_equipada})")
            return None

        if not habilidad["desbloqueada"]:
            if MOSTRAR_LOGS: print(f"[HAB] FALLO: {self.habilidad_equipada} no desbloqueada")
            return None

        if habilidad["pp_actual"] <= 0:
            if MOSTRAR_LOGS: print(f"[HAB] FALLO: {self.habilidad_equipada} PP=0")
            return None

        habilidad["pp_actual"] -= 1
        if MOSTRAR_LOGS: print(f"[HAB] OK: {self.habilidad_equipada} PP restante={habilidad['pp_actual']}")
        return habilidad["efecto"]

    def recargar_pp(self, hid=None, cantidad=1):
        """Recarga PP de una habilidad"""
        if hid is None:
            hid = self.habilidad_equipada

        if hid and hid in self.habilidades:
            habilidad = self.habilidades[hid]
            if habilidad["efecto"] != "base":  # La base no tiene PP
                habilidad["pp_actual"] = min(
                    habilidad["pp_actual"] + cantidad,
                    habilidad["pp_max"]
                )
                return True
        return False

    def get_efecto_equipado(self):
        """Devuelve el efecto de la habilidad equipada (para la skin)"""
        if self.habilidad_equipada:
            return self.habilidades[self.habilidad_equipada]["efecto"]
        return "base"

    def get_habilidad_equipada(self):
        if self.habilidad_equipada:
            return self.habilidades[self.habilidad_equipada]
        return None

    def get_pp_actual(self):
        if self.habilidad_equipada:
            return self.habilidades[self.habilidad_equipada]["pp_actual"]
        return 0

    def get_pp_max(self):
        if self.habilidad_equipada:
            return self.habilidades[self.habilidad_equipada]["pp_max"]
        return 0

    def tiene_habilidad(self, hid):
        return hid in self.habilidades and self.habilidades[hid]["desbloqueada"]

    def cambiar_habilidad(self, direccion=1):
        """Cambia a la siguiente habilidad en el inventario (ciclo)"""
        if not self.inventario:
            return False

        idx = 0
        if self.habilidad_equipada in self.inventario:
            idx = self.inventario.index(self.habilidad_equipada)

        idx = (idx + direccion) % len(self.inventario)
        self.habilidad_equipada = self.inventario[idx]
        print(f"Habilidad cambiada a: {self.habilidad_equipada}")  # DEBUG
        return True

    def dibujar_ui(self, pantalla):
        if not self.habilidad_equipada:
            return
        hab = self.habilidades[self.habilidad_equipada]
        if hab["efecto"] == "base":
            return

        color = hab["color"]
        pp_act = hab["pp_actual"]
        pp_max = hab["pp_max"]

        px, py = 8, 38

        # Fondo
        seg_w, seg_h, gap = 10, 14, 2
        total_w = pp_max * (seg_w + gap) + 30
        surf = pygame.Surface((total_w, seg_h + 8), pygame.SRCALPHA)
        surf.fill((5, 10, 20, 200))
        pantalla.blit(surf, (px, py))
        pygame.draw.rect(pantalla, (40, 60, 80), (px, py, total_w, seg_h + 8), 1)

        # Runa diamante
        runa = [(px + 8, py + 8), (px + 13, py + 4), (px + 18, py + 8), (px + 13, py + 12)]
        pygame.draw.polygon(pantalla, color, runa)

        # Barra segmentada
        bx = px + 26
        by = py + 5
        for s in range(pp_max):
            sx = bx + s * (seg_w + gap)
            if s < pp_act:
                pygame.draw.rect(pantalla, color, (sx, by, seg_w, seg_h))
                pygame.draw.rect(pantalla, (255, 255, 255, 60), (sx, by, seg_w, seg_h // 3))
            else:
                pygame.draw.rect(pantalla, (20, 25, 35), (sx, by, seg_w, seg_h))
            pygame.draw.rect(pantalla, (60, 70, 85), (sx, by, seg_w, seg_h), 1)

        # Tecla
        tecla = hab["tecla"].upper()
        ts = pygame.font.SysFont("Arial", 13).render(tecla, True, (130, 150, 170))
        pantalla.blit(ts, (bx + pp_max * (seg_w + gap) + 6, py + 4))
