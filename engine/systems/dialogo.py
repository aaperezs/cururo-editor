import json
import os

import pygame
from engine.configs import *
from engine.project_paths import data_dir, assets_dir

RUTA_DIALOGOS = data_dir("dialogos.json")

pygame.font.init()

_SPRITE_CACHE = {}
_SPRITE_H = 22
_RUTA_ASSETS = assets_dir()

def _cargar_fuente(tam, negrita=False):
    for nombre in ["Georgia", "Palatino Linotype", "Book Antiqua", None]:
        try:
            if nombre:
                f = pygame.font.SysFont(nombre, tam, bold=negrita)
            else:
                f = pygame.font.Font(None, tam)
            if f and f.render("A", True, (0,0,0)).get_width() > 0:
                return f
        except:
            continue
    return pygame.font.Font(None, tam)

FUENTE_DIALOGO = _cargar_fuente(18)
FUENTE_NOMBRE = _cargar_fuente(14)
FUENTE_HINT = _cargar_fuente(12)

def _cargar_sprite_marcador(nombre):
    if nombre in _SPRITE_CACHE:
        return _SPRITE_CACHE[nombre]
    ruta = os.path.join(_RUTA_ASSETS, nombre + ".png")
    if not os.path.exists(ruta):
        print(f"[Dialogo] Sprite no encontrado: {ruta}")
        _SPRITE_CACHE[nombre] = None
        return None
    try:
        spr = pygame.image.load(ruta).convert_alpha()
        escala = _SPRITE_H / spr.get_height()
        ancho = int(spr.get_width() * escala)
        spr = pygame.transform.scale(spr, (ancho, _SPRITE_H))
        _SPRITE_CACHE[nombre] = spr
        return spr
    except Exception as e:
        print(f"[Dialogo] Error cargando sprite {nombre}: {e}")
        _SPRITE_CACHE[nombre] = None
        return None

def _dividir_texto_con_marcadores(texto, flags=None):
    partes = []
    resto = texto
    while "{" in resto:
        idx = resto.index("{")
        if "}" not in resto[idx:]:
            partes.append(("texto", resto))
            return partes
        if idx > 0:
            partes.append(("texto", resto[:idx]))
        end = resto.index("}", idx)
        marcador = resto[idx+1:end]
        if marcador:
            if marcador.startswith("flag:"):
                flag_name = marcador[5:]
                valor = str(flags.get(flag_name, "?")) if flags else "?"
                partes.append(("texto", valor))
            else:
                partes.append(("sprite", marcador))
        resto = resto[end+1:]
    if resto:
        partes.append(("texto", resto))
    return partes

def _render_con_brillo(pantalla, texto, fuente, color_texto, color_brillo, pos):
    """Renderiza texto con efecto de brillo rúnico (glow blanco alrededor)"""
    for dx, dy in [(1,1),(-1,-1),(0,1)]:
        pantalla.blit(fuente.render(texto, True, (80, 70, 50)), (pos[0] + dx, pos[1] + dy))
    for dx, dy in [(1,0),(0,1)]:
        pantalla.blit(fuente.render(texto, True, color_brillo), (pos[0] + dx, pos[1] + dy))
    pantalla.blit(fuente.render(texto, True, color_texto), pos)


class DialogoSystem:
    def __init__(self, flags=None):
        self.activo = False
        self.lineas = []
        self.linea_actual = 0
        self.char_idx = 0
        self.terminado = False
        self.al_terminar = None
        self.dialog_id = None
        self.personaje_nombre = ""
        self.tipo = None
        self.options = []
        self.tiempo_espera = 0
        self.dialogos = self._cargar_dialogos()
        self.flags = flags or {}

    def _cargar_dialogos(self):
        try:
            with open(RUTA_DIALOGOS, "r", encoding="utf-8") as f:
                return json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            print(f"Error cargando dialogos: {e}")
            return {}

    def iniciar(self, dialog_id, tipo, al_terminar=None, nombre=""):
        if dialog_id not in self.dialogos:
            print(f"Dialogo para {dialog_id}/{tipo} no encontrado")
            if al_terminar:
                al_terminar()
            return
        grupo = self.dialogos[dialog_id]
        # Obtener nombre del JSON (campo "name") o usar el parámetro nombre
        nombre_grupo = grupo.get("name", "")
        personaje_nombre = nombre or nombre_grupo
        lineas_tipo = grupo.get(tipo, [])
        options = []
        if isinstance(lineas_tipo, dict):
            options = lineas_tipo.get("options", [])
            lineas_tipo = lineas_tipo.get("dialog") or lineas_tipo.get("flat", [])
        if not lineas_tipo:
            print(f"No hay lineas de dialogo para {dialog_id}/{tipo}")
            if al_terminar:
                al_terminar()
            return

        self.dialog_id = dialog_id
        self.personaje_nombre = personaje_nombre
        self.tipo = tipo
        self.lineas = lineas_tipo
        self.options = options
        self.linea_actual = 0
        self.char_idx = 0
        self.activo = True
        self.terminado = False
        self.al_terminar = al_terminar
        self.tiempo_espera = 0

    def iniciar_inline(self, lineas, nombre="", al_terminar=None):
        self.dialog_id = "inline"
        self.personaje_nombre = nombre
        self.tipo = "inline"
        self.lineas = lineas
        self.options = []
        self.linea_actual = 0
        self.char_idx = 0
        self.activo = True
        self.terminado = False
        self.al_terminar = al_terminar
        self.tiempo_espera = 0

    def _avanzar_char(self, linea):
        """Avanza un caracter saltando marcadores completos"""
        if self.char_idx < len(linea) and linea[self.char_idx] == "{":
            end = linea.find("}", self.char_idx)
            if end != -1:
                self.char_idx = end + 1
                return
        self.char_idx += 1

    def actualizar(self):
        if not self.activo:
            return
        if self.tiempo_espera > 0:
            self.tiempo_espera -= 1
            return
        linea = self.lineas[self.linea_actual]
        if self.char_idx < len(linea):
            self._avanzar_char(linea)

    def avanzar(self):
        if not self.activo:
            return
        linea = self.lineas[self.linea_actual]
        if self.char_idx < len(linea):
            self.char_idx = len(linea)
        elif self.linea_actual < len(self.lineas) - 1:
            self.linea_actual += 1
            self.char_idx = 0
        else:
            self.activo = False
            self.terminado = True
            cb = self.al_terminar
            self.al_terminar = None
            if cb:
                cb()

    def dibujar(self, pantalla):
        if not self.activo:
            return

        ANCHO_PANTALLA = pantalla.get_width()
        ALTO_PANTALLA = pantalla.get_height()

        caja_x = 40
        caja_y = ALTO_PANTALLA - 170
        caja_ancho = ANCHO_PANTALLA - 80
        caja_alto = 150

        pygame.draw.rect(pantalla, NEGRO, (caja_x - 4, caja_y - 4, caja_ancho + 8, caja_alto + 8))
        pygame.draw.rect(pantalla, MADERA_OSCURO, (caja_x, caja_y, caja_ancho, caja_alto))
        for i in range(0, caja_ancho, 20):
            pygame.draw.line(pantalla, MADERA, (caja_x + i, caja_y), (caja_x + i, caja_y + caja_alto), 1)
        pygame.draw.rect(pantalla, MADERA_CLARO, (caja_x + 6, caja_y + 6, caja_ancho - 12, 28))
        nombre = self.personaje_nombre if self.personaje_nombre else self.dialog_id.capitalize()
        _render_con_brillo(pantalla, nombre, FUENTE_NOMBRE, DORADO, (240, 230, 200), (caja_x + 14, caja_y + 10))

        contenido_x = caja_x + 14
        contenido_y = caja_y + 42
        ancho_disponible = caja_ancho - 28
        espacio_linea = 30

        texto_completo = self.lineas[self.linea_actual][:self.char_idx]
        partes = _dividir_texto_con_marcadores(texto_completo, self.flags)

        x_actual = contenido_x
        y_actual = contenido_y

        for tipo, valor in partes:
            if tipo == "texto":
                palabras = valor.split(" ")
                for palabra in palabras:
                    if not palabra:
                        x_actual += FUENTE_DIALOGO.size(" ")[0]
                        continue
                    ancho_palabra = FUENTE_DIALOGO.size(palabra)[0]
                    if x_actual + ancho_palabra > caja_x + caja_ancho - 14:
                        x_actual = contenido_x
                        y_actual += espacio_linea
                    _render_con_brillo(pantalla, palabra, FUENTE_DIALOGO, (220, 210, 190), (240, 230, 210), (x_actual, y_actual))
                    x_actual += ancho_palabra + FUENTE_DIALOGO.size(" ")[0]
            elif tipo == "sprite":
                spr = _cargar_sprite_marcador(valor)
                if spr:
                    if x_actual + spr.get_width() + 4 > caja_x + caja_ancho - 14:
                        x_actual = contenido_x
                        y_actual += espacio_linea
                    pantalla.blit(spr, (x_actual, y_actual + 2))
                    x_actual += spr.get_width() + 6

        if self.char_idx >= len(self.lineas[self.linea_actual]):
            if self.linea_actual < len(self.lineas) - 1:
                y_actual += espacio_linea + 6
                _render_con_brillo(pantalla, "[SPACE: Continuar]", FUENTE_HINT, DORADO, (240, 230, 200), (caja_x + caja_ancho - 180, y_actual))
            else:
                y_actual += espacio_linea + 6
                _render_con_brillo(pantalla, "[SPACE: Cerrar]", FUENTE_HINT, DORADO, (240, 230, 200), (caja_x + caja_ancho - 175, y_actual))

