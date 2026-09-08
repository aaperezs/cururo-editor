import pygame
from engine.configs import ALTO, ANCHO
from engine.systems.ui.components.base import dibujar_marco_madera, dibujar_runas, panel_tallado
from engine.systems.ui.components.inventory_panels import PANELES_APARTADO, RENDERERS


class InventoryMenu:
    def __init__(self, fuente, fuente_grande, fuente_pequena):
        self.fuente = fuente
        self.fuente_grande = fuente_grande
        self.fuente_pequena = fuente_pequena

    def _panel_activo(self, estado):
        cls = RENDERERS.get(estado.menu.apartado_tipo)
        if not cls:
            cls = PANELES_APARTADO.get(estado.menu.apartado_id)
        if not cls:
            return None
        return cls(self.fuente, self.fuente_pequena, config=estado.menu.apartado_config)

    def draw(self, pantalla, estado):
        overlay = pygame.Surface((ANCHO, ALTO))
        overlay.set_alpha(200)
        overlay.fill((10, 30, 8))
        pantalla.blit(overlay, (0, 0))

        m = 30
        w, h = ANCHO - 2*m, ALTO - 2*m

        marco_ext = pygame.Rect(m, m, w, h)
        dibujar_marco_madera(pantalla, marco_ext, (60, 40, 20), (80, 55, 30))

        int_rect = marco_ext.inflate(-12, -12)
        panel_tallado(pantalla, int_rect, (15, 38, 12), (35, 60, 25))

        col_runa = (100, 75, 40)
        dibujar_runas(pantalla, int_rect.left + 15, int_rect.top + 15, col_runa)
        dibujar_runas(pantalla, int_rect.right - 15, int_rect.top + 15, col_runa)
        dibujar_runas(pantalla, int_rect.left + 15, int_rect.bottom - 15, col_runa)
        dibujar_runas(pantalla, int_rect.right - 15, int_rect.bottom - 15, col_runa)

        tit_rect = pygame.Rect(int_rect.centerx - 180, int_rect.top + 8, 360, 36)
        panel_tallado(pantalla, tit_rect, (80, 55, 30), (120, 80, 45))
        titulo = self.fuente_grande.render(estado.menu.titulo or "INVENTARIO", True, (220, 190, 120))
        tit_rect_txt = titulo.get_rect(center=tit_rect.center)
        pantalla.blit(titulo, tit_rect_txt)

        # ── Listado lateral de apartados (estilo RPG) ──
        lado_x = int_rect.left + 15
        lado_w = 190
        y0 = int_rect.top + 56
        paso_lado = 40

        for i, ap in enumerate(estado.menu.apartados):
            es_activo = (i == estado.menu.apartado_actual)
            ap_rect = pygame.Rect(lado_x, y0 + i * paso_lado, lado_w, 32)
            if es_activo:
                panel_tallado(pantalla, ap_rect, (45, 70, 35), (180, 150, 70))
                pygame.draw.polygon(pantalla, (200, 170, 80), [
                    (lado_x - 6, ap_rect.centery - 6),
                    (lado_x - 6, ap_rect.centery + 6),
                    (lado_x, ap_rect.centery)
                ])
            else:
                panel_tallado(pantalla, ap_rect, (25, 42, 20), (60, 70, 50))
            col_txt = (220, 200, 130) if es_activo else (160, 170, 140)
            texto_ap = self.fuente.render(ap.get("nombre", ap.get("id", "")), True, col_txt)
            pantalla.blit(texto_ap, (ap_rect.left + 12, ap_rect.top + 6))

        # ── Área de contenido del apartado activo ──
        panel = self._panel_activo(estado)
        if panel is not None:
            area = pygame.Rect(lado_x + lado_w + 15, int_rect.top + 50,
                               int_rect.right - 15 - (lado_x + lado_w + 15),
                               int_rect.bottom - 60 - int_rect.top)
            panel.dibujar(pantalla, estado, area)
        else:
            txt = self.fuente.render("Apartado no registrado", True, (120, 120, 120))
            txt_rect = txt.get_rect(center=(ANCHO//2, ALTO//2))
            pantalla.blit(txt, txt_rect)

        inst = self.fuente_pequena.render(
            "TAB: Apartado   UP/DOWN: Elegir   ENTER: Usar   ESC: Cerrar", True, (100, 130, 80))
        inst_rect = inst.get_rect(center=(ANCHO//2, int_rect.bottom - 10))
        pantalla.blit(inst, inst_rect)
