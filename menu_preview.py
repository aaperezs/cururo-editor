# Vista previa del menú editado usando los renderers reales del runtime (orm).
#
# El editor agrega la raíz del runtime (orm/) a sys.path al cargar el proyecto,
# por lo que estos imports resuelven si el proyecto es compatible. Si el runtime
# no está disponible, la vista previa muestra un aviso en vez de fallar.

import pygame


def _import_runtime():
    """Importa los módulos del runtime. Devuelve None si no están disponibles."""
    try:
        from systems.ui.components.inventory_menu import InventoryMenu
        from entities.inventario import Inventario
        from systems.habilidades import SistemaHabilidades
        from configs import ALTO, ANCHO
        return InventoryMenu, Inventario, SistemaHabilidades, (ANCHO, ALTO)
    except Exception:
        return None


class _MenuAdapter:
    """Expone la API de MenuSystem que usan los renderers, apuntando al menú en memoria."""

    def __init__(self, menu, apartado_idx, seleccion):
        self._menu = menu
        self.apartado_actual = apartado_idx
        self.seleccion = seleccion

    @property
    def apartados(self):
        return self._menu.get("apartados", [])

    def _ap(self):
        a = self.apartados
        if 0 <= self.apartado_actual < len(a):
            return a[self.apartado_actual]
        return None

    @property
    def apartado_id(self):
        ap = self._ap()
        return ap.get("id") if ap else None

    @property
    def apartado_tipo(self):
        ap = self._ap()
        return ap.get("tipo", "lista") if ap else None

    @property
    def apartado_config(self):
        ap = self._ap()
        return ap if ap else {}

    @property
    def titulo(self):
        return self._menu.get("titulo", "")


class _InventarioFake:
    items = []
    slots = []

    def es_consumible(self, iid):
        return True

    def get_config(self, iid):
        return {}

    def cantidad(self, iid):
        return 0

    def get_equipado(self, slot):
        return None


class _HabilidadesFake:
    inventario = []
    habilidades = {}
    habilidad_equipada = None


class _EstadoPreview:
    """Estado simulado con los atributos que tocan los renderers del menú."""

    def __init__(self, menu, apartado_idx=0, seleccion=0):
        self.menu = _MenuAdapter(menu, apartado_idx, seleccion)
        self.flags = {}
        self.inventario = _InventarioFake()
        self.habilidades = _HabilidadesFake()
        rt = _import_runtime()
        if rt:
            _, Inventario, SistemaHabilidades, _ = rt
            try:
                self.inventario = Inventario()
            except Exception:
                pass
            try:
                self.habilidades = SistemaHabilidades()
            except Exception:
                pass


class MenuPreview:
    """Dibuja el menú actual como se verá en el juego en una surface dada."""

    def __init__(self):
        self._menu_ui = None
        self._tam = (800, 600)

    def _ensure(self):
        if self._menu_ui is not None:
            return True
        rt = _import_runtime()
        if not rt:
            return False
        InventoryMenu, _, _, tam = rt
        self._tam = tam
        self._menu_ui = InventoryMenu(
            pygame.font.Font(None, 22),
            pygame.font.Font(None, 34),
            pygame.font.Font(None, 18),
        )
        return True

    def tamanio(self):
        return self._tam

    def dibujar(self, surface, menu, apartado_idx=0, seleccion=0):
        if not self._ensure():
            self._dibujar_no_disponible(surface)
            return
        estado = _EstadoPreview(menu, apartado_idx, seleccion)
        self._menu_ui.draw(surface, estado)

    def _dibujar_no_disponible(self, surface):
        surface.fill((20, 25, 30))
        pygame.draw.rect(surface, (60, 70, 85), surface.get_rect(), 2)
        txt = pygame.font.Font(None, 22).render(
            "Vista previa no disponible (runtime orm no cargado)", True, (150, 160, 170))
        rect = txt.get_rect(center=surface.get_rect().center)
        surface.blit(txt, rect)
