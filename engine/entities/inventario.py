import json

from engine.project_paths import data_dir
from engine.repositories import RepositorioBotin, RepositorioObjetos, RepositorioRecetas

SLOTS = ["cabeza", "cuello", "cola"]

_CONS_EFECTOS = {
    "recupera_pp": "recargar_pp",
    "crece+1": "crecer",
}


def _cargar_slots():
    """Slots de equipo desde data/inventario.json (fallback SLOTS)."""
    try:
        with open(data_dir("inventario.json"), encoding="utf-8") as f:
            cfg = json.load(f)
        slots = cfg.get("slots_equipo", [])
        if slots:
            return [s.get("id") for s in slots]
    except (FileNotFoundError, json.JSONDecodeError):
        pass
    return SLOTS


class Objeto:
    """Un objeto en el inventario (material, mineral, item)"""

    def __init__(self, id_objeto, cantidad=1):
        self.id = id_objeto
        self.cantidad = cantidad


class ObjetoEquipable:
    """Un objeto equipable con efectos"""

    def __init__(self, id_objeto, config):
        self.id = id_objeto
        self.nombre = config.get("nombre", id_objeto)
        self.slot = config.get("slot", "cabeza")
        self.descripcion = config.get("descripcion", "")
        self.rareza = config.get("rareza", "comun")
        self.efectos = config.get("efectos", [])

    def aplicar_efectos(self, snake, estado):
        """Aplica todos los efectos de este objeto"""
        for efecto in self.efectos:
            tipo = efecto.get("tipo")
            if tipo == "negar_terreno":
                for terreno in efecto.get("terrenos", []):
                    estado.terrenos_negados.add(terreno)
            elif tipo == "velocidad_extra":
                estado.velocidad_extra *= efecto.get("valor", 1.0)
            elif tipo == "regeneracion_pp":
                pass  # Se maneja por frame en el game loop
            elif tipo == "longitud_minima_extra":
                pass  # Se verifica en perder_segmentos


class Inventario:
    """Inventario del jugador — items, equipo, materiales"""

    def __init__(self):
        self._repo_objetos = RepositorioObjetos()
        self._repo_recetas = RepositorioRecetas()
        self._repo_botin = RepositorioBotin()
        self.slots = _cargar_slots()
        self.items = {}  # id -> Objeto (materiales)
        self.equipo = {}  # slot -> ObjetoEquipable
        self.equipados = set()  # ids de objetos equipados

    def agregar_item(self, id_objeto, cantidad=1):
        """Agrega un item/material al inventario"""
        if id_objeto in self.items:
            self.items[id_objeto].cantidad += cantidad
        else:
            self.items[id_objeto] = Objeto(id_objeto, cantidad)

    def tiene_item(self, id_objeto, cantidad=1):
        """Verifica si tiene cierta cantidad de un item"""
        return self.items.get(id_objeto, Objeto(id_objeto, 0)).cantidad >= cantidad

    def cantidad(self, id_objeto):
        """Retorna la cantidad de un item en el inventario"""
        return self.items.get(id_objeto, Objeto(id_objeto, 0)).cantidad

    def remover_item(self, id_objeto, cantidad=1):
        """Elimina items del inventario (alias público de consumir_item)"""
        return self.consumir_item(id_objeto, cantidad)

    def consumir_item(self, id_objeto, cantidad=1):
        """Consume items del inventario"""
        if not self.tiene_item(id_objeto, cantidad):
            return False
        self.items[id_objeto].cantidad -= cantidad
        if self.items[id_objeto].cantidad <= 0:
            del self.items[id_objeto]
        return True

    def get_config(self, id_objeto):
        """Resuelve la config de un item desde objetos.json/items.json o botin.json."""
        config = self._repo_objetos.get_objeto(id_objeto)
        if config:
            return config
        return self._repo_botin.get_evento(id_objeto)

    def es_consumible(self, id_objeto):
        """Un item es consumible si su tipo es 'consumible' o tiene efecto y no es mineral."""
        config = self.get_config(id_objeto)
        if not config:
            return False
        if config.get("tipo") == "consumible":
            return True
        return bool(config.get("efecto")) and config.get("tipo") != "mineral"

    def es_key_item(self, id_objeto):
        """Un item es un objeto clave si su tipo es 'objeto_clave'."""
        config = self.get_config(id_objeto)
        return config.get("tipo") == "objeto_clave" if config else False

    def get_key_items(self):
        """Devuelve dict {id: Objeto} de items con tipo 'objeto_clave'."""
        return {iid: obj for iid, obj in self.items.items() if self.es_key_item(iid)}

    def tiene_key_item(self, id_objeto):
        """Verifica si tiene un objeto clave específico."""
        return id_objeto in self.get_key_items()

    def usar_item(self, id_objeto, estado, cantidad=1):
        """Usa un consumible: aplica su efecto y lo consume. Retorna True si se usó."""
        if not self.es_consumible(id_objeto) or not self.tiene_item(id_objeto, cantidad):
            return False
        config = self.get_config(id_objeto)
        efecto = config.get("efecto")
        aplicado = False
        if efecto and estado:
            if efecto == "recupera_pp":
                estado.habilidades.recargar_pp(cantidad=5)
                aplicado = True
            elif efecto == "crece+1":
                estado.snake.crecer(1)
                aplicado = True
        self.consumir_item(id_objeto, cantidad)
        return aplicado or True

    def equipar(self, id_objeto):
        """Equipa un objeto del inventario"""
        config = self._repo_objetos.get_objeto(id_objeto)
        if not config:
            return False
        slot = config.get("slot")
        if slot not in self.slots:
            return False
        # Desequipar lo que haya en ese slot
        if slot in self.equipo:
            self.desequipar(slot)
        obj = ObjetoEquipable(id_objeto, config)
        self.equipo[slot] = obj
        self.equipados.add(id_objeto)
        return True

    def desequipar(self, slot):
        """Desequipa un slot"""
        if slot in self.equipo:
            self.equipados.discard(self.equipo[slot].id)
            del self.equipo[slot]

    def get_equipado(self, slot):
        """Devuelve el objeto equipado en un slot"""
        return self.equipo.get(slot)

    def aplicar_todos_efectos(self, snake, estado):
        """Aplica efectos de todos los objetos equipados"""
        estado.terrenos_negados.clear()
        estado.velocidad_extra = 1.0
        for obj in self.equipo.values():
            obj.aplicar_efectos(snake, estado)

    def get_materiales(self):
        """Devuelve dict de materiales para forja"""
        return {iid: obj.cantidad for iid, obj in self.items.items()}

    def puede_fabricar(self, id_receta):
        """Verifica si puede fabricar una receta"""
        return self._repo_recetas.puede_fabricar(id_receta, self.get_materiales())

    def fabricar(self, id_receta):
        """Intenta fabricar una receta — retorna el resultado o None"""
        if not self._repo_recetas.puede_fabricar(id_receta, self.get_materiales()):
            return None
        self._repo_recetas.consumir_materiales(id_receta, self.get_materiales())
        receta = self._repo_recetas.get_receta(id_receta)
        resultado = receta.get("resultado")
        self.agregar_item(resultado, 1)
        return resultado

