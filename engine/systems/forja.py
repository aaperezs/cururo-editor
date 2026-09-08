import pygame
from engine.configs import ALTO, ANCHO, BLANCO, DORADO, GRIS, MADERA, MADERA_CLARO, MADERA_OSCURO, VERDE_CLARO


class SistemaForja:
    """Menú de forja para fabricar equipamiento"""

    def __init__(self, estado):
        self.estado = estado
        from engine.repositories import RepositorioRecetas
        self._repo = RepositorioRecetas()
        self.seleccion = 0
        self.mensaje = ""
        self.tiempo_mensaje = 0

    def get_recetas_disponibles(self):
        """Devuelve recetas que se pueden fabricar"""
        materiales = self.estado.inventario.get_materiales()
        disponibles = []
        for rid in self._repo.get_todas():
            if self._repo.puede_fabricar(rid, materiales):
                disponibles.append(rid)
        return disponibles

    def fabricar_seleccion(self):
        """Intenta fabricar la receta seleccionada"""
        recetas = list(self._repo.get_todas().keys())
        if not recetas or self.seleccion >= len(recetas):
            return
        rid = recetas[self.seleccion]
        resultado = self.estado.inventario.fabricar(rid)
        if resultado:
            receta = self._repo.get_receta(rid)
            self.mensaje = f"¡{receta['nombre']} forjado!"
            self.tiempo_mensaje = 90
        else:
            self.mensaje = "No tienes suficientes materiales"
            self.tiempo_mensaje = 60

    def actualizar(self):
        if self.tiempo_mensaje > 0:
            self.tiempo_mensaje -= 1
            if self.tiempo_mensaje == 0:
                self.mensaje = ""

    def dibujar(self, pantalla):
        """Dibuja el menú de forja"""
        overlay = pygame.Surface((ANCHO, ALTO), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 200))
        pantalla.blit(overlay, (0, 0))

        cx, cy = ANCHO // 2, 60
        ancho_panel = 500
        alto_panel = 480

        # Panel principal
        pygame.draw.rect(pantalla, MADERA_OSCURO, (cx - ancho_panel // 2 - 4, cy - 4, ancho_panel + 8, alto_panel + 8))
        pygame.draw.rect(pantalla, MADERA, (cx - ancho_panel // 2, cy, ancho_panel, alto_panel))

        # Título
        fuente = pygame.font.SysFont("Georgia", 28)
        titulo = fuente.render("🏭 FORJA RÚNICA", True, DORADO)
        pantalla.blit(titulo, (cx - titulo.get_width() // 2, cy + 10))

        # Materiales disponibles
        fuente_mat = pygame.font.SysFont("Arial", 16)
        materiales = self.estado.inventario.get_materiales()
        y_mat = cy + 50
        texto_mat = fuente_mat.render("Materiales:", True, BLANCO)
        pantalla.blit(texto_mat, (cx - ancho_panel // 2 + 20, y_mat))
        y_mat += 22
        for mid, cant in materiales.items():
            txt = fuente_mat.render(f"  • {mid}: {cant}", True, (200, 200, 150))
            pantalla.blit(txt, (cx - ancho_panel // 2 + 30, y_mat))
            y_mat += 18

        # Línea divisoria
        pygame.draw.line(pantalla, MADERA_CLARO, (cx - ancho_panel // 2 + 20, y_mat + 5),
                         (cx + ancho_panel // 2 - 20, y_mat + 5), 1)
        y_rec = y_mat + 15

        # Recetas
        fuente_rec = pygame.font.SysFont("Arial", 15)
        recetas = list(self._repo.get_todas().items())
        materiales_disp = self.estado.inventario.get_materiales()

        for i, (rid, receta) in enumerate(recetas):
            y = y_rec + i * 50
            puede = self._repo.puede_fabricar(rid, materiales_disp)
            color = VERDE_CLARO if puede else GRIS
            seleccionado = (i == self.seleccion)

            if seleccionado:
                pygame.draw.rect(pantalla, (60, 80, 60), (cx - ancho_panel // 2 + 10, y - 2, ancho_panel - 20, 44))

            # Nombre
            nombre = fuente_rec.render(receta["nombre"], True, DORADO if puede else GRIS)
            pantalla.blit(nombre, (cx - ancho_panel // 2 + 20, y))

            # Requisitos
            reqs = receta.get("requiere", {})
            req_parts = [f"{mat}:{cant}" for mat, cant in reqs.items()]
            req_txt = fuente_rec.render("  →  " + "  ".join(req_parts), True, color)
            pantalla.blit(req_txt, (cx - ancho_panel // 2 + 180, y))

            # Descripción
            desc = receta.get("descripcion", "")
            desc_txt = pygame.font.SysFont("Arial", 12).render(desc, True, (180, 180, 160))
            pantalla.blit(desc_txt, (cx - ancho_panel // 2 + 25, y + 22))

        # Mensaje
        if self.tiempo_mensaje > 0:
            fuente_msg = pygame.font.SysFont("Arial", 18, bold=True)
            msg = fuente_msg.render(self.mensaje, True, DORADO)
            pantalla.blit(msg, (cx - msg.get_width() // 2, cy + alto_panel - 40))

        # Instrucciones
        fuente_inst = pygame.font.SysFont("Arial", 14)
        instrucciones = fuente_inst.render("↑↓: Navegar  |  ENTER: Forjar  |  ESC: Salir", True, GRIS)
        pantalla.blit(instrucciones, (cx - instrucciones.get_width() // 2, cy + alto_panel - 20))
