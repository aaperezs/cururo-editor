import json

import pygame
from engine.configs import ALTO, ANCHO
from engine.project_paths import data_dir
from engine.utils.sprite_manager import obtener as obtener_sprite
from engine.systems.ui.components.base import dibujar_marco_madera, dibujar_runas, panel_tallado


def _cargar_slots_nombres():
    """Mapa slot_id -> nombre de equipo desde data/inventario.json."""
    try:
        with open(data_dir("inventario.json"), encoding="utf-8") as f:
            cfg = json.load(f)
        return {s.get("id"): s.get("nombre", s.get("id", ""))
                for s in cfg.get("slots_equipo", [])}
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _moneda_pago(shop_item, shop=None):
    """Moneda con la que se paga un item: principal de la tienda si está en
    el precio, si no la primera moneda del precio."""
    precio = shop_item.precio or {}
    if shop is not None:
        principal = getattr(shop, "moneda_principal", "")
        if principal in precio:
            return principal
    if precio:
        return next(iter(precio))
    return "oro"


class PanelApartado:
    """Base para un panel de apartado del menú."""

    def __init__(self, fuente, fuente_pequena, config=None):
        self.fuente = fuente
        self.fuente_pequena = fuente_pequena
        self.config = config or {}

    def item_count(self, estado):
        """Cantidad de filas seleccionables de este apartado."""
        return 0

    def accion_seleccionada(self, estado):
        """Acción {tipo, ...} de la fila seleccionada, o None."""
        return None

    def dibujar(self, pantalla, estado, area):
        raise NotImplementedError


class PanelHabilidades(PanelApartado):
    """Apartado Habilidades — mismo render que el menú original."""

    def item_count(self, estado):
        return len(estado.habilidades.inventario)

    def accion_seleccionada(self, estado):
        lista = estado.habilidades.inventario
        if 0 <= estado.menu.seleccion < len(lista):
            return {"tipo": "equipar_habilidad", "habilidad": lista[estado.menu.seleccion]}
        return None

    def dibujar(self, pantalla, estado, area):
        habilidades = estado.habilidades
        lista = habilidades.inventario
        if not lista:
            txt = self.fuente.render("No tienes habilidades desbloqueadas", True, (120, 120, 120))
            txt_rect = txt.get_rect(center=(area.centerx, area.centery))
            pantalla.blit(txt, txt_rect)
            return

        sel = estado.menu.seleccion
        paso = 62
        for i, hid in enumerate(lista):
            hab = habilidades.habilidades[hid]
            es_equipada = (hid == habilidades.habilidad_equipada)
            es_seleccion = (i == sel)
            y_pos = area.top + i * paso

            item_rect = pygame.Rect(area.left, y_pos, area.width, 54)
            if es_equipada:
                panel_tallado(pantalla, item_rect, (35, 55, 25), (180, 150, 70))
            elif es_seleccion:
                panel_tallado(pantalla, item_rect, (40, 60, 30), (120, 150, 90))
            else:
                panel_tallado(pantalla, item_rect, (25, 42, 20), (60, 70, 50))

            if es_equipada:
                pygame.draw.polygon(pantalla, (200, 170, 80), [
                    (area.left - 6, y_pos + 27 - 6),
                    (area.left - 6, y_pos + 27 + 6),
                    (area.left, y_pos + 27)
                ])

            if es_seleccion and not es_equipada:
                pygame.draw.polygon(pantalla, (140, 200, 120), [
                    (area.left + area.width + 6, y_pos + 27 - 6),
                    (area.left + area.width + 6, y_pos + 27 + 6),
                    (area.left + area.width, y_pos + 27)
                ])

            nom_color = (220, 200, 130) if es_equipada else (180, 200, 160)
            texto_nombre = self.fuente.render(hab['nombre'], True, nom_color)
            pantalla.blit(texto_nombre, (area.left + 10, y_pos + 4))

            texto_desc = self.fuente_pequena.render(hab['descripcion'], True, (140, 150, 130))
            pantalla.blit(texto_desc, (area.left + 10, y_pos + 28))

            pp_x = area.left + area.width - 110
            pp_y = y_pos + 6
            pp_w = 100
            pp_h = 10

            pygame.draw.rect(pantalla, (20, 30, 15), (pp_x, pp_y, pp_w, pp_h))
            pygame.draw.rect(pantalla, (50, 60, 40), (pp_x, pp_y, pp_w, pp_h), 1)

            if hab['pp_max'] > 0:
                fill = int((hab['pp_actual'] / hab['pp_max']) * pp_w)
                if hab['pp_actual'] > 0:
                    color_pp = (100, 180, 80) if hab['pp_actual'] > 1 else (200, 120, 40)
                    pygame.draw.rect(pantalla, color_pp, (pp_x + 1, pp_y + 1, fill - 1, pp_h - 2))

            pp_txt = self.fuente_pequena.render(f"PP {hab['pp_actual']}/{hab['pp_max']}", True, (160, 180, 140))
            pantalla.blit(pp_txt, (pp_x + pp_w + 6, pp_y - 1))

            if i < len(lista) - 1:
                sep_y = y_pos + paso - 2
                pygame.draw.line(pantalla, (40, 55, 35), (area.left + 20, sep_y), (area.left + area.width - 20, sep_y), 1)


class PanelItems(PanelApartado):
    """Apartado Items — lista de consumibles del inventario."""

    def _lista(self, estado):
        inv = estado.inventario
        return [iid for iid in inv.items if inv.es_consumible(iid)]

    def item_count(self, estado):
        return len(self._lista(estado))

    def accion_seleccionada(self, estado):
        lista = self._lista(estado)
        if 0 <= estado.menu.seleccion < len(lista):
            return {"tipo": "usar_item", "item": lista[estado.menu.seleccion]}
        return None

    def dibujar(self, pantalla, estado, area):
        inv = estado.inventario
        lista = self._lista(estado)
        if not lista:
            txt = self.fuente.render("No tienes items consumibles", True, (120, 120, 120))
            txt_rect = txt.get_rect(center=(area.centerx, area.centery))
            pantalla.blit(txt, txt_rect)
            return

        sel = estado.menu.seleccion
        paso = 62
        for i, iid in enumerate(lista):
            config = inv.get_config(iid) or {}
            cant = inv.cantidad(iid)
            es_seleccion = (i == sel)
            y_pos = area.top + i * paso

            item_rect = pygame.Rect(area.left, y_pos, area.width, 54)
            if es_seleccion:
                panel_tallado(pantalla, item_rect, (40, 60, 30), (120, 150, 90))
            else:
                panel_tallado(pantalla, item_rect, (25, 42, 20), (60, 70, 50))

            if es_seleccion:
                pygame.draw.polygon(pantalla, (140, 200, 120), [
                    (area.left + area.width + 6, y_pos + 27 - 6),
                    (area.left + area.width + 6, y_pos + 27 + 6),
                    (area.left + area.width, y_pos + 27)
                ])

            sprite_id = config.get("sprite_id", "")
            sprite = obtener_sprite(sprite_id) if sprite_id else None
            if sprite:
                icono_size = 32
                escala = min(icono_size / sprite.get_width(), icono_size / sprite.get_height())
                sw = max(1, int(sprite.get_width() * escala))
                sh = max(1, int(sprite.get_height() * escala))
                s = pygame.transform.scale(sprite, (sw, sh))
                pantalla.blit(s, (area.left + 10, y_pos + (54 - sh) // 2))
            else:
                icono = config.get("icono", "●")
                icono_txt = self.fuente.render(icono, True, (200, 190, 140))
                pantalla.blit(icono_txt, (area.left + 10, y_pos + 4))

            nombre = config.get("nombre", iid)
            texto_nombre = self.fuente.render(nombre, True, (180, 200, 160))
            pantalla.blit(texto_nombre, (area.left + 48, y_pos + 4))

            cant_txt = self.fuente_pequena.render(f"x{cant}", True, (140, 150, 130))
            pantalla.blit(cant_txt, (area.left + area.width - 70, y_pos + 8))

            texto_desc = self.fuente_pequena.render(config.get("descripcion", ""), True, (140, 150, 130))
            pantalla.blit(texto_desc, (area.left + 48, y_pos + 28))

            if i < len(lista) - 1:
                sep_y = y_pos + paso - 2
                pygame.draw.line(pantalla, (40, 55, 35), (area.left + 20, sep_y), (area.left + area.width - 20, sep_y), 1)


class PanelEquipo(PanelApartado):
    """Apartado Equipo — slots de equipo equipar/desequipar."""

    def _slots(self, estado):
        return estado.inventario.slots

    def _slot_nombre(self, slot_id):
        if not hasattr(self, "_slots_nombres"):
            self._slots_nombres = _cargar_slots_nombres()
        return self._slots_nombres.get(slot_id, slot_id)

    def item_count(self, estado):
        return len(self._slots(estado))

    def accion_seleccionada(self, estado):
        slots = self._slots(estado)
        if 0 <= estado.menu.seleccion < len(slots):
            slot_id = slots[estado.menu.seleccion]
            inv = estado.inventario
            if inv.get_equipado(slot_id):
                return {"tipo": "desequipar_slot", "slot": slot_id}
            return {"tipo": "equipar_slot", "slot": slot_id}
        return None

    def dibujar(self, pantalla, estado, area):
        inv = estado.inventario
        slots = self._slots(estado)
        if not slots:
            txt = self.fuente.render("Sin slots de equipo", True, (120, 120, 120))
            txt_rect = txt.get_rect(center=(area.centerx, area.centery))
            pantalla.blit(txt, txt_rect)
            return

        sel = estado.menu.seleccion
        paso = 62
        for i, slot_id in enumerate(slots):
            equipado = inv.get_equipado(slot_id)
            es_seleccion = (i == sel)
            y_pos = area.top + i * paso

            item_rect = pygame.Rect(area.left, y_pos, area.width, 54)
            if equipado:
                panel_tallado(pantalla, item_rect, (35, 55, 25), (180, 150, 70))
            elif es_seleccion:
                panel_tallado(pantalla, item_rect, (40, 60, 30), (120, 150, 90))
            else:
                panel_tallado(pantalla, item_rect, (25, 42, 20), (60, 70, 50))

            if equipado:
                pygame.draw.polygon(pantalla, (200, 170, 80), [
                    (area.left - 6, y_pos + 27 - 6),
                    (area.left - 6, y_pos + 27 + 6),
                    (area.left, y_pos + 27)
                ])
            elif es_seleccion:
                pygame.draw.polygon(pantalla, (140, 200, 120), [
                    (area.left + area.width + 6, y_pos + 27 - 6),
                    (area.left + area.width + 6, y_pos + 27 + 6),
                    (area.left + area.width, y_pos + 27)
                ])

            nombre_slot = self._slot_nombre(slot_id)
            col_slot = (200, 170, 80) if equipado else (160, 170, 140)
            texto_slot = self.fuente.render(nombre_slot, True, col_slot)
            pantalla.blit(texto_slot, (area.left + 10, y_pos + 4))

            if equipado:
                config = inv.get_config(equipado.id) or {}
                sprite_id = config.get("sprite_id", "")
                sprite = obtener_sprite(sprite_id) if sprite_id else None
                if sprite:
                    icono_size = 24
                    escala = min(icono_size / sprite.get_width(), icono_size / sprite.get_height())
                    sw = max(1, int(sprite.get_width() * escala))
                    sh = max(1, int(sprite.get_height() * escala))
                    s = pygame.transform.scale(sprite, (sw, sh))
                    pantalla.blit(s, (area.left + 10, y_pos + 28))
                else:
                    icono = config.get("icono", "◆")
                    icono_txt = self.fuente.render(icono, True, (200, 190, 140))
                    pantalla.blit(icono_txt, (area.left + 10, y_pos + 28))

                texto_nombre = self.fuente_pequena.render(equipado.nombre, True, (180, 200, 160))
                pantalla.blit(texto_nombre, (area.left + 48, y_pos + 28))

                texto_desc = self.fuente_pequena.render(equipado.descripcion, True, (140, 150, 130))
                pantalla.blit(texto_desc, (area.left + 48, y_pos + 42))
            else:
                texto_vacio = self.fuente_pequena.render("— Vacío —", True, (110, 120, 105))
                pantalla.blit(texto_vacio, (area.left + 48, y_pos + 28))

            if i < len(slots) - 1:
                sep_y = y_pos + paso - 2
                pygame.draw.line(pantalla, (40, 55, 35), (area.left + 20, sep_y), (area.left + area.width - 20, sep_y), 1)


# Registro por tipo de renderer (data/menus.json -> apartados[].tipo)
class PanelLista(PanelApartado):
    """Apartado Lista/Opciones — filas configurables con acciones.

    Config esperada:
      {"items": [{"id", "nombre", "descripcion", "accion": {"tipo", "params"}}]}

    Un ítem puede tener `opciones` (lista de {nombre, params}): LEFT/RIGHT
    cicla la opción y la acción se ejecuta con los params de la opción
    seleccionada (merge sobre los params estáticos de la acción).
    """

    def _items(self, estado):
        return self.config.get("items", [])

    def item_count(self, estado):
        return len(self._items(estado))

    def _match_opcion_persistida(self, it, opciones):
        """Índice de la opción que coincide con el valor persistido en user_prefs.

        - set_resolution: prefs["resolution"] ("WxH") contra params ancho/alto.
        - set_volume: prefs["bgm_volume"]/["sfx_volume"] (float) contra params["volumen"].
        Sin match -> 0.
        """
        try:
            from systems.user_prefs import load as _load_prefs
            prefs = _load_prefs()
        except Exception:
            prefs = {}
        tipo = (it.get("accion") or {}).get("tipo", "")
        for i, op in enumerate(opciones):
            params = op.get("params", {})
            if tipo == "set_resolution":
                ancho = params.get("ancho")
                alto = params.get("alto")
                if ancho is not None and alto is not None:
                    try:
                        if prefs.get("resolution") == f"{int(ancho)}x{int(alto)}":
                            return i
                    except (ValueError, TypeError):
                        pass
            elif tipo == "set_volume":
                vol = params.get("volumen")
                if vol is None:
                    continue
                try:
                    v = float(vol)
                except (ValueError, TypeError):
                    continue
                for key in ("bgm_volume", "sfx_volume"):
                    try:
                        if abs(v - float(prefs.get(key, -1))) < 1e-6:
                            return i
                    except (ValueError, TypeError):
                        pass
        return 0

    def _indice_opcion(self, it, estado):
        """Índice de la opción actual del ítem (cache en menu.opcion_indices).

        El schema recomienda `id` en cada ítem; si falta, se cachea con un
        key sintético por posición de selección (fallback).
        """
        opciones = it.get("opciones")
        if not opciones:
            return 0
        item_id = it.get("id", "")
        indices = getattr(estado.menu, "opcion_indices", {})
        key = item_id if item_id else f"@{estado.menu.seleccion}"
        if key in indices:
            return indices[key]
        idx = self._match_opcion_persistida(it, opciones)
        indices[key] = idx
        return idx

    def accion_seleccionada(self, estado):
        items = self._items(estado)
        if 0 <= estado.menu.seleccion < len(items):
            it = items[estado.menu.seleccion]
            accion = it.get("accion")
            if not accion:
                return None
            opciones = it.get("opciones")
            if opciones:
                idx = self._indice_opcion(it, estado)
                op = opciones[idx]
                return {**accion, "params": {**accion.get("params", {}), **op.get("params", {})}}
            return accion
        return None

    def dibujar(self, pantalla, estado, area):
        items = self._items(estado)
        if not items:
            txt = self.fuente.render("Sin opciones", True, (120, 120, 120))
            txt_rect = txt.get_rect(center=(area.centerx, area.centery))
            pantalla.blit(txt, txt_rect)
            return

        sel = estado.menu.seleccion
        paso = 62
        for i, it in enumerate(items):
            es_seleccion = (i == sel)
            y_pos = area.top + i * paso

            item_rect = pygame.Rect(area.left, y_pos, area.width, 54)
            if es_seleccion:
                panel_tallado(pantalla, item_rect, (40, 60, 30), (120, 150, 90))
            else:
                panel_tallado(pantalla, item_rect, (25, 42, 20), (60, 70, 50))

            if es_seleccion:
                pygame.draw.polygon(pantalla, (140, 200, 120), [
                    (area.left + area.width + 6, y_pos + 27 - 6),
                    (area.left + area.width + 6, y_pos + 27 + 6),
                    (area.left + area.width, y_pos + 27)
                ])

            nombre = it.get("nombre", it.get("id", ""))
            opciones = it.get("opciones")
            if opciones:
                idx = self._indice_opcion(it, estado)
                op = opciones[idx]
                nombre = f"{nombre}: {op.get('nombre', '')}"
            texto_nombre = self.fuente.render(nombre, True, (180, 200, 160))
            pantalla.blit(texto_nombre, (area.left + 10, y_pos + 4))

            texto_desc = self.fuente_pequena.render(it.get("descripcion", ""), True, (140, 150, 130))
            pantalla.blit(texto_desc, (area.left + 10, y_pos + 28))

            if i < len(items) - 1:
                sep_y = y_pos + paso - 2
                pygame.draw.line(pantalla, (40, 55, 35), (area.left + 20, sep_y), (area.left + area.width - 20, sep_y), 1)


class PanelControles(PanelApartado):
    """Apartado Controles — muestra el mapeo de teclas (solo lectura)."""

    _FALLBACK = [
        {"accion": "Moverse", "tecla": "Flechas"},
        {"accion": "Interactuar", "tecla": "E"},
        {"accion": "Habilidad", "tecla": "Q"},
        {"accion": "Inventario", "tecla": "I"},
        {"accion": "Forja", "tecla": "F"},
        {"accion": "Trueque", "tecla": "T"},
        {"accion": "Pausa", "tecla": "P"},
    ]

    def _controles(self):
        try:
            with open(data_dir("controles.json"), encoding="utf-8") as f:
                cfg = json.load(f)
            lista = cfg.get("controles")
            if lista:
                return lista
        except (FileNotFoundError, json.JSONDecodeError):
            pass
        return self._FALLBACK

    def item_count(self, estado):
        return 0

    def accion_seleccionada(self, estado):
        return None

    def dibujar(self, pantalla, estado, area):
        controles = self._controles()
        if not controles:
            txt = self.fuente.render("Sin controles", True, (120, 120, 120))
            txt_rect = txt.get_rect(center=(area.centerx, area.centery))
            pantalla.blit(txt, txt_rect)
            return

        paso = 40
        for i, c in enumerate(controles):
            y_pos = area.top + i * paso
            texto_accion = self.fuente.render(c.get("accion", ""), True, (180, 200, 160))
            pantalla.blit(texto_accion, (area.left + 10, y_pos))

            tecla = c.get("tecla", "")
            texto_tecla = self.fuente_pequena.render(tecla, True, (200, 190, 140))
            rect_tecla = texto_tecla.get_rect(right=area.right - 10, top=y_pos)
            pantalla.blit(texto_tecla, rect_tecla)


class PanelStatsFlags(PanelApartado):
    """Apartado Stats/Flags — muestra valores de flags del estado (solo lectura).

    Config esperada:
      {"flags": [{"id", "nombre", "default"}]}
    """

    def _flags(self):
        return self.config.get("flags", [])

    def item_count(self, estado):
        return 0

    def accion_seleccionada(self, estado):
        return None

    def dibujar(self, pantalla, estado, area):
        flags = self._flags()
        if not flags:
            txt = self.fuente.render("Sin datos", True, (120, 120, 120))
            txt_rect = txt.get_rect(center=(area.centerx, area.centery))
            pantalla.blit(txt, txt_rect)
            return

        paso = 40
        for i, f in enumerate(flags):
            y_pos = area.top + i * paso
            nombre = f.get("nombre", f.get("id", ""))
            valor = estado.flags.get(f.get("id"), f.get("default", 0))
            texto_nombre = self.fuente.render(nombre, True, (180, 200, 160))
            pantalla.blit(texto_nombre, (area.left + 10, y_pos))

            texto_valor = self.fuente.render(str(valor), True, (200, 190, 140))
            rect_valor = texto_valor.get_rect(right=area.right - 10, top=y_pos)
            pantalla.blit(texto_valor, rect_valor)


class PanelStats(PanelApartado):
    """Apartado Stats — filas {label, valor} con valor literal o referencia.

    Config esperada:
      {"stats": [{"id", "nombre", "valor"}]}
    valor: literal, "flag:<id>" (estado.flags) o "state:<campo>" (getattr estado).
    """

    def _stats(self):
        return self.config.get("stats", [])

    def item_count(self, estado):
        return len(self._stats(estado))

    def accion_seleccionada(self, estado):
        return None

    def _valor(self, estado, ref):
        if ref is None:
            return ""
        s = str(ref)
        if s.startswith("flag:"):
            return estado.flags.get(s[5:], 0)
        if s.startswith("state:"):
            return getattr(estado, s[6:], 0)
        return s

    def dibujar(self, pantalla, estado, area):
        stats = self._stats()
        if not stats:
            txt = self.fuente.render("Sin datos", True, (120, 120, 120))
            txt_rect = txt.get_rect(center=(area.centerx, area.centery))
            pantalla.blit(txt, txt_rect)
            return

        paso = 40
        sel = estado.menu.seleccion
        for i, st in enumerate(stats):
            y_pos = area.top + i * paso
            if i == sel:
                item_rect = pygame.Rect(area.left, y_pos, area.width, paso - 4)
                panel_tallado(pantalla, item_rect, (40, 60, 30), (120, 150, 90))

            nombre = st.get("nombre", st.get("id", ""))
            valor = self._valor(estado, st.get("valor"))
            texto_nombre = self.fuente.render(nombre, True, (180, 200, 160))
            pantalla.blit(texto_nombre, (area.left + 10, y_pos + 6))

            texto_valor = self.fuente.render(str(valor), True, (200, 190, 140))
            rect_valor = texto_valor.get_rect(right=area.right - 10, top=y_pos + 6)
            pantalla.blit(texto_valor, rect_valor)


class PanelObjetosClave(PanelApartado):
    """Apartado Objetos Clave — llaves, items de quest, items de progresión."""

    def _lista(self, estado):
        return list(estado.inventario.get_key_items().keys())

    def item_count(self, estado):
        return len(self._lista(estado))

    def accion_seleccionada(self, estado):
        lista = self._lista(estado)
        if 0 <= estado.menu.seleccion < len(lista):
            return {"tipo": "examinar_key_item", "item": lista[estado.menu.seleccion]}
        return None

    def dibujar(self, pantalla, estado, area):
        lista = self._lista(estado)
        if not lista:
            txt = self.fuente.render("Sin objetos clave", True, (120, 120, 120))
            txt_rect = txt.get_rect(center=(area.centerx, area.centery))
            pantalla.blit(txt, txt_rect)
            return

        sel = estado.menu.seleccion
        paso = 62
        for i, iid in enumerate(lista):
            config = estado.inventario.get_config(iid) or {}
            cant = estado.inventario.cantidad(iid)
            es_seleccion = (i == sel)
            y_pos = area.top + i * paso

            item_rect = pygame.Rect(area.left, y_pos, area.width, 54)
            if es_seleccion:
                panel_tallado(pantalla, item_rect, (40, 60, 30), (120, 150, 90))
            else:
                panel_tallado(pantalla, item_rect, (25, 42, 20), (60, 70, 50))

            if es_seleccion:
                pygame.draw.polygon(pantalla, (140, 200, 120), [
                    (area.left + area.width + 6, y_pos + 27 - 6),
                    (area.left + area.width + 6, y_pos + 27 + 6),
                    (area.left + area.width, y_pos + 27)
                ])

            sprite_id = config.get("sprite_id", "")
            sprite = obtener_sprite(sprite_id) if sprite_id else None
            if sprite:
                icono_size = 32
                escala = min(icono_size / sprite.get_width(), icono_size / sprite.get_height())
                sw = max(1, int(sprite.get_width() * escala))
                sh = max(1, int(sprite.get_height() * escala))
                s = pygame.transform.scale(sprite, (sw, sh))
                pantalla.blit(s, (area.left + 10, y_pos + (54 - sh) // 2))
            else:
                icono = config.get("icono", "🔑")
                icono_txt = self.fuente.render(icono, True, (220, 190, 80))
                pantalla.blit(icono_txt, (area.left + 10, y_pos + 4))

            nombre = config.get("nombre", iid)
            texto_nombre = self.fuente.render(nombre, True, (220, 200, 130))
            pantalla.blit(texto_nombre, (area.left + 48, y_pos + 4))

            if cant > 1:
                cant_txt = self.fuente_pequena.render(f"x{cant}", True, (180, 170, 120))
                pantalla.blit(cant_txt, (area.left + area.width - 60, y_pos + 8))

            texto_desc = self.fuente_pequena.render(config.get("descripcion", ""), True, (140, 150, 130))
            pantalla.blit(texto_desc, (area.left + 48, y_pos + 28))

            if i < len(lista) - 1:
                sep_y = y_pos + paso - 2
                pygame.draw.line(pantalla, (40, 55, 35), (area.left + 20, sep_y), (area.left + area.width - 20, sep_y), 1)


class PanelShopComprar(PanelApartado):
    """Panel de compra en tienda: muestra items disponibles con precio y stock."""

    def _items(self, estado):
        if not hasattr(estado, "shop_actual") or not estado.shop_actual:
            return []
        return estado.shop_actual.get_items_disponibles(estado)

    def item_count(self, estado):
        return len(self._items(estado))

    def accion_seleccionada(self, estado):
        items = self._items(estado)
        if 0 <= estado.menu.seleccion < len(items):
            item = items[estado.menu.seleccion]
            return {"tipo": "shop_comprar", "item_id": item.item_id, "cantidad": 1}
        return None

    def dibujar(self, pantalla, estado, area):
        items = self._items(estado)
        if not items:
            txt = self.fuente.render("No hay items disponibles", True, (120, 120, 120))
            txt_rect = txt.get_rect(center=(area.centerx, area.centery))
            pantalla.blit(txt, txt_rect)
            return

        sel = estado.menu.seleccion
        paso = 62
        for i, shop_item in enumerate(items):
            config = estado.inventario.get_config(shop_item.item_id) or {}
            es_seleccion = (i == sel)
            y_pos = area.top + i * paso

            item_rect = pygame.Rect(area.left, y_pos, area.width, 54)
            if es_seleccion:
                panel_tallado(pantalla, item_rect, (40, 60, 30), (120, 150, 90))
            else:
                panel_tallado(pantalla, item_rect, (25, 42, 20), (60, 70, 50))

            if es_seleccion:
                pygame.draw.polygon(pantalla, (140, 200, 120), [
                    (area.left + area.width + 6, y_pos + 27 - 6),
                    (area.left + area.width + 6, y_pos + 27 + 6),
                    (area.left + area.width, y_pos + 27)
                ])

            # Icono
            sprite_id = config.get("sprite_id", "")
            sprite = obtener_sprite(sprite_id) if sprite_id else None
            if sprite:
                icono_size = 32
                escala = min(icono_size / sprite.get_width(), icono_size / sprite.get_height())
                sw = max(1, int(sprite.get_width() * escala))
                sh = max(1, int(sprite.get_height() * escala))
                s = pygame.transform.scale(sprite, (sw, sh))
                pantalla.blit(s, (area.left + 10, y_pos + (54 - sh) // 2))
            else:
                icono = config.get("icono", "●")
                icono_txt = self.fuente.render(icono, True, (200, 190, 140))
                pantalla.blit(icono_txt, (area.left + 10, y_pos + 4))

            nombre = config.get("nombre", shop_item.item_id)
            texto_nombre = self.fuente.render(nombre, True, (180, 200, 160))
            pantalla.blit(texto_nombre, (area.left + 48, y_pos + 4))

            # Precio
            precio = shop_item.precio
            moneda = _moneda_pago(shop_item, estado.shop_actual)
            costo = precio.get(moneda, 0)
            moneda_cfg = estado.monedas.definir(moneda) if hasattr(estado, 'monedas') else None
            icono_moneda = moneda_cfg.get("icono", "💰") if moneda_cfg else "💰"
            precio_txt = f"{costo} {icono_moneda}"
            if len(precio) > 1:
                otros = [f"{v} {estado.monedas.definir(m).get('icono', m) if estado.monedas.definir(m) else m}" 
                        for m, v in precio.items() if m != moneda]
                if otros:
                    precio_txt += f" / {' '.join(otros)}"
            texto_precio = self.fuente_pequena.render(precio_txt, True, (200, 190, 100))
            pantalla.blit(texto_precio, (area.left + area.width - 150, y_pos + 4))

            # Stock
            if shop_item.stock_infinito:
                stock_txt = "∞"
            else:
                stock_txt = str(shop_item.stock)
            stock_color = (180, 170, 120) if shop_item.stock_infinito or shop_item.stock > 0 else (180, 80, 80)
            stock_render = self.fuente_pequena.render(f"Stock: {stock_txt}", True, stock_color)
            pantalla.blit(stock_render, (area.left + area.width - 150, y_pos + 24))

            # Descripción
            texto_desc = self.fuente_pequena.render(config.get("descripcion", ""), True, (140, 150, 130))
            pantalla.blit(texto_desc, (area.left + 48, y_pos + 28))

            # Moneda del jugador
            if hasattr(estado, 'monedas'):
                tengo = estado.monedas.get(moneda, 0)
                dinero_txt = self.fuente_pequena.render(f"Tienes: {tengo}", True, (140, 160, 140))
                pantalla.blit(dinero_txt, (area.left + area.width - 150, y_pos + 40))

            if i < len(items) - 1:
                sep_y = y_pos + paso - 2
                pygame.draw.line(pantalla, (40, 55, 35), (area.left + 20, sep_y), (area.left + area.width - 20, sep_y), 1)


class PanelShopVender(PanelApartado):
    """Panel de venta a tienda: muestra inventario del jugador con precio de compra."""

    def _items(self, estado):
        if not hasattr(estado, "shop_actual") or not estado.shop_actual:
            return []
        shop = estado.shop_actual
        items = []
        for iid in estado.inventario.items:
            config = estado.inventario.get_config(iid) or {}
            if not config:
                continue
            precio_compra = shop.get_precio_compra(iid)
            if precio_compra:
                items.append((iid, config, precio_compra))
        return items

    def item_count(self, estado):
        return len(self._items(estado))

    def accion_seleccionada(self, estado):
        items = self._items(estado)
        if 0 <= estado.menu.seleccion < len(items):
            iid, config, precio = items[estado.menu.seleccion]
            return {"tipo": "shop_vender", "item_id": iid, "cantidad": 1, "precio_compra": precio}
        return None

    def dibujar(self, pantalla, estado, area):
        items = self._items(estado)
        if not items:
            txt = self.fuente.render("No hay items vendibles aquí", True, (120, 120, 120))
            txt_rect = txt.get_rect(center=(area.centerx, area.centery))
            pantalla.blit(txt, txt_rect)
            return

        sel = estado.menu.seleccion
        paso = 62
        for i, (iid, config, precio_compra) in enumerate(items):
            es_seleccion = (i == sel)
            y_pos = area.top + i * paso

            item_rect = pygame.Rect(area.left, y_pos, area.width, 54)
            if es_seleccion:
                panel_tallado(pantalla, item_rect, (40, 60, 30), (120, 150, 90))
            else:
                panel_tallado(pantalla, item_rect, (25, 42, 20), (60, 70, 50))

            if es_seleccion:
                pygame.draw.polygon(pantalla, (140, 200, 120), [
                    (area.left + area.width + 6, y_pos + 27 - 6),
                    (area.left + area.width + 6, y_pos + 27 + 6),
                    (area.left + area.width, y_pos + 27)
                ])

            # Icono
            sprite_id = config.get("sprite_id", "")
            sprite = obtener_sprite(sprite_id) if sprite_id else None
            if sprite:
                icono_size = 32
                escala = min(icono_size / sprite.get_width(), icono_size / sprite.get_height())
                sw = max(1, int(sprite.get_width() * escala))
                sh = max(1, int(sprite.get_height() * escala))
                s = pygame.transform.scale(sprite, (sw, sh))
                pantalla.blit(s, (area.left + 10, y_pos + (54 - sh) // 2))
            else:
                icono = config.get("icono", "●")
                icono_txt = self.fuente.render(icono, True, (200, 190, 140))
                pantalla.blit(icono_txt, (area.left + 10, y_pos + 4))

            nombre = config.get("nombre", iid)
            texto_nombre = self.fuente.render(nombre, True, (180, 200, 160))
            pantalla.blit(texto_nombre, (area.left + 48, y_pos + 4))

            # Precio de compra (trueque)
            precio_txt = " / ".join([f"{v} {estado.monedas.definir(m).get('icono', m) if estado.monedas.definir(m) else m}"
                                    for m, v in precio_compra.items()])
            texto_precio = self.fuente_pequena.render(f"Vende por: {precio_txt}", True, (100, 200, 100))
            pantalla.blit(texto_precio, (area.left + area.width - 200, y_pos + 4))

            cant = estado.inventario.cantidad(iid)
            if cant > 1:
                cant_txt = self.fuente_pequena.render(f"x{cant}", True, (140, 150, 130))
                pantalla.blit(cant_txt, (area.left + area.width - 60, y_pos + 8))

            texto_desc = self.fuente_pequena.render(config.get("descripcion", ""), True, (140, 150, 130))
            pantalla.blit(texto_desc, (area.left + 48, y_pos + 28))

            if i < len(items) - 1:
                sep_y = y_pos + paso - 2
                pygame.draw.line(pantalla, (40, 55, 35), (area.left + 20, sep_y), (area.left + area.width - 20, sep_y), 1)


# Registro por tipo de renderer (data/menus.json -> apartados[].tipo)
class PanelSaveSlots(PanelApartado):
    """Panel de selección de slots de guardado."""

    def __init__(self, fuente, fuente_pequena, config=None):
        super().__init__(fuente, fuente_pequena, config)
        self._modo = (config or {}).get("config", {}).get("modo", "guardar")
        self._slots_cache = []

    def item_count(self, estado):
        if hasattr(estado, "save_system"):
            self._slots_cache = estado.save_system.manager.listar_slots()
        return len(self._slots_cache)

    def accion_seleccionada(self, estado):
        if self._modo == "cargar":
            if 0 <= estado.menu.seleccion < len(self._slots_cache):
                slot = self._slots_cache[estado.menu.seleccion]
                return {"tipo": "load_game", "slot": slot.get("slot", 1)}
        elif self._modo == "guardar":
            if 0 <= estado.menu.seleccion < len(self._slots_cache):
                slot = self._slots_cache[estado.menu.seleccion]
                estado.menu._slot_pendiente = slot.get("slot", 1)
                estado.menu.abrir_apartado("confirmar")
                return None
        return None

    def dibujar(self, pantalla, estado, area):
        if not hasattr(estado, "save_system"):
            return

        slots = estado.save_system.manager.listar_slots()
        if not slots:
            txt = self.fuente.render("No hay partidas guardadas", True, (120, 120, 120))
            txt_rect = txt.get_rect(center=(area.centerx, area.centery))
            pantalla.blit(txt, txt_rect)
            return

        sel = estado.menu.seleccion
        paso = 62
        for i, slot in enumerate(slots):
            es_seleccion = (i == sel)
            y_pos = area.top + i * paso

            item_rect = pygame.Rect(area.left, y_pos, area.width, 54)
            if es_seleccion:
                panel_tallado(pantalla, item_rect, (40, 60, 30), (120, 150, 90))
            else:
                panel_tallado(pantalla, item_rect, (25, 42, 20), (60, 70, 50))

            if es_seleccion:
                pygame.draw.polygon(pantalla, (140, 200, 120), [
                    (area.left + area.width + 6, y_pos + 27 - 6),
                    (area.left + area.width + 6, y_pos + 27 + 6),
                    (area.left + area.width, y_pos + 27)
                ])

            slot_num = slot.get("slot", i + 1)
            nivel = slot.get("nivel_id", "?")
            timestamp = slot.get("timestamp", 0)
            import time
            fecha = time.strftime("%d/%m %H:%M", time.localtime(timestamp))
            jefes = slot.get("jefes_derrotados", 0)

            titulo = f"Slot {slot_num}  —  {nivel}"
            texto_titulo = self.fuente.render(titulo, True, (180, 200, 160))
            pantalla.blit(texto_titulo, (area.left + 10, y_pos + 4))

            subtitulo = f"{fecha}  |  Jefes: {jefes}"
            texto_sub = self.fuente_pequena.render(subtitulo, True, (140, 150, 130))
            pantalla.blit(texto_sub, (area.left + 10, y_pos + 28))

            if i < len(slots) - 1:
                pygame.draw.line(pantalla, (60, 80, 50),
                                 (area.left + 8, y_pos + paso - 2),
                                 (area.left + area.width - 8, y_pos + paso - 2))


class PanelConfirmarGuardar(PanelApartado):
    """Panel de confirmación para guardar en un slot."""

    def item_count(self, estado):
        return 2  # Sí / No

    def accion_seleccionada(self, estado):
        slot = getattr(estado.menu, "_slot_pendiente", 1)
        if estado.menu.seleccion == 0:
            return {"tipo": "confirmar_guardar", "slot": slot}
        estado.menu.abrir_apartado("guardar")
        return None

    def dibujar(self, pantalla, estado, area):
        slot = getattr(estado.menu, "_slot_pendiente", "?")
        titulo = f"¿Guardar en Slot {slot}?"
        txt = self.fuente.render(titulo, True, (180, 200, 160))
        pantalla.blit(txt, (area.left + 10, area.top + 20))

        opciones = ["Sí, guardar", "Cancelar"]
        sel = estado.menu.seleccion
        for i, op in enumerate(opciones):
            y = area.top + 60 + i * 40
            color = (200, 220, 180) if i == sel else (120, 120, 120)
            prefijo = "▶ " if i == sel else "  "
            texto = self.fuente.render(f"{prefijo}{op}", True, color)
            pantalla.blit(texto, (area.left + 20, y))


class PanelConfirmarCargar(PanelApartado):
    """Panel de confirmación para cargar un slot."""

    def item_count(self, estado):
        return 2  # Sí / No

    def accion_seleccionada(self, estado):
        slot = getattr(estado.menu, "_slot_pendiente", 1)
        if estado.menu.seleccion == 0:
            return {"tipo": "confirmar_cargar", "slot": slot}
        estado.menu.abrir_apartado("cargar")
        return None

    def dibujar(self, pantalla, estado, area):
        slot = getattr(estado.menu, "_slot_pendiente", "?")
        titulo = f"¿Cargar Slot {slot}?"
        txt = self.fuente.render(titulo, True, (180, 200, 160))
        pantalla.blit(txt, (area.left + 10, area.top + 20))

        sub = self.fuente_pequena.render("Se perderá el progreso no guardado.", True, (180, 120, 100))
        pantalla.blit(sub, (area.left + 10, area.top + 50))

        opciones = ["Sí, cargar", "Cancelar"]
        sel = estado.menu.seleccion
        for i, op in enumerate(opciones):
            y = area.top + 80 + i * 40
            color = (200, 220, 180) if i == sel else (120, 120, 120)
            prefijo = "▶ " if i == sel else "  "
            texto = self.fuente.render(f"{prefijo}{op}", True, color)
            pantalla.blit(texto, (area.left + 20, y))


RENDERERS = {
    "lista_habilidades": PanelHabilidades,
    "lista_consumibles": PanelItems,
    "equipo": PanelEquipo,
    "lista": PanelLista,
    "opciones": PanelLista,
    "controles": PanelControles,
    "stats_flags": PanelStatsFlags,
    "stats": PanelStats,
    "objetos_clave": PanelObjetosClave,
    "shop_comprar": PanelShopComprar,
    "shop_vender": PanelShopVender,
    "save_slots": PanelSaveSlots,
    "save_confirmar": PanelConfirmarGuardar,
    "cargar_confirmar": PanelConfirmarCargar,
}

# Registro por id de apartado (retro-compat data/inventario.json)
PANELES_APARTADO = {
    "habilidades": RENDERERS["lista_habilidades"],
    "items": RENDERERS["lista_consumibles"],
    "equipo": RENDERERS["equipo"],
}
