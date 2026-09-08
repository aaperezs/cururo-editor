import json

from engine.project_paths import data_dir


class MenuSystem:
    """Menú RPG data-driven desde data/menus.json.

    Schema:
      {
        "menus": [
          {
            "id": "inventario",          # id único
            "tecla": "i",                # nombre de tecla que abre el menú
            "titulo": "INVENTARIO",      # título mostrado
            "apartados": [
              {"id": "habilidades", "nombre": "Habilidades", "tipo": "lista_habilidades"},
              {"id": "items", "nombre": "Items", "tipo": "lista_consumibles"},
              {"id": "equipo", "nombre": "Equipo", "tipo": "equipo"}
            ]
          }
        ]
      }

    Cada apartado elige un "tipo" de renderer registrado en
    systems/ui/components/inventory_panels.py (RENDERERS).

    Retro-compat: si no existe menus.json, se construye un único menú
    "inventario" (tecla I) desde data/inventario.json, igual que antes.
    """

    def __init__(self):
        self.menus = []
        self.menu_actual = None
        self.apartado_actual = 0
        self.seleccion = 0
        self.opcion_indices = {}  # item_id -> índice de opción seleccionada
        self._cargar()

    def _cargar(self):
        cfg = {}
        try:
            with open(data_dir("menus.json"), encoding="utf-8") as f:
                cfg = json.load(f)
        except FileNotFoundError:
            cfg = {}

        menus = cfg.get("menus")
        if menus:
            self.menus = menus
            self._cargar_inventario_fallback()
            return

        # Fallback: un único menú "inventario" desde data/inventario.json
        inv = {}
        try:
            with open(data_dir("inventario.json"), encoding="utf-8") as f:
                inv = json.load(f)
        except FileNotFoundError:
            inv = {}

        apartados = inv.get("apartados")
        if not apartados:
            apartados = [
                {"id": "habilidades", "nombre": "Habilidades", "tipo": "lista_habilidades"},
                {"id": "items", "nombre": "Items", "tipo": "lista_consumibles"},
                {"id": "equipo", "nombre": "Equipo", "tipo": "equipo"},
            ]
        else:
            tipos = {
                "habilidades": "lista_habilidades",
                "items": "lista_consumibles",
                "equipo": "equipo",
            }
            apartados = [
                {"id": a.get("id", "x"), "nombre": a.get("nombre", a.get("id", "x")),
                 "tipo": tipos.get(a.get("id", ""), "lista")}
                for a in apartados
            ]

        self.menus = [{
            "id": "inventario",
            "tecla": "i",
            "titulo": "INVENTARIO",
            "apartados": apartados,
        }]

        self._slots_equipo = inv.get("slots_equipo")

    def _cargar_inventario_fallback(self):
        """Lee slots_equipo de inventario.json para el Inventario (fallback)."""
        self._slots_equipo = None
        try:
            with open(data_dir("inventario.json"), encoding="utf-8") as f:
                inv = json.load(f)
            self._slots_equipo = inv.get("slots_equipo")
        except FileNotFoundError:
            pass

    # ── Apertura / navegación ──

    def abrir(self):
        """Abre el primer menú (retro-compat: inventario)."""
        if self.menus:
            self.menu_actual = self.menus[0]
        self.apartado_actual = 0
        self.seleccion = 0
        self.opcion_indices = {}

    def abrir_menu(self, menu_id):
        """Abre un menú por id. Retorna True si existe."""
        for m in self.menus:
            if m.get("id") == menu_id:
                self.menu_actual = m
                self.apartado_actual = 0
                self.seleccion = 0
                self.opcion_indices = {}
                return True
        return False

    def cerrar(self):
        self.menu_actual = None

    def menu_id_por_tecla(self, tecla):
        """Devuelve el id del menú que se abre con la tecla dada, o None."""
        for m in self.menus:
            if m.get("tecla") == tecla:
                return m.get("id")
        return None

    # ── Propiedades de compatibilidad (apuntan al menú actual) ──

    @property
    def apartados(self):
        if self.menu_actual:
            return self.menu_actual.get("apartados", [])
        return []

    @property
    def apartado_actual_id(self):
        if 0 <= self.apartado_actual < len(self.apartados):
            return self.apartados[self.apartado_actual].get("id")
        return None

    @property
    def apartado_id(self):
        return self.apartado_actual_id

    @property
    def apartado_tipo(self):
        if 0 <= self.apartado_actual < len(self.apartados):
            return self.apartados[self.apartado_actual].get("tipo", "lista")
        return None

    @property
    def apartado_nombre(self):
        if 0 <= self.apartado_actual < len(self.apartados):
            return self.apartados[self.apartado_actual].get("nombre", "")
        return ""

    @property
    def apartado_config(self):
        """Config completa del apartado activo (items, flags, etc.)."""
        if 0 <= self.apartado_actual < len(self.apartados):
            return self.apartados[self.apartado_actual]
        return {}

    @property
    def titulo(self):
        if self.menu_actual:
            return self.menu_actual.get("titulo", "")
        return ""

    @property
    def slots_equipo(self):
        slots = self._slots_equipo
        if slots:
            return [s.get("id") for s in slots]
        return ["cabeza", "cuello", "cola"]

    def cambiar_apartado(self, direccion=1):
        """Cambia de apartado en el listado (ciclo)."""
        if not self.apartados:
            return
        self.apartado_actual = (self.apartado_actual + direccion) % len(self.apartados)
        self.seleccion = 0
        self.opcion_indices = {}

    def abrir_apartado(self, apartado_id):
        """Abre un apartado del menú actual por su id. Retorna True si existe."""
        for i, ap in enumerate(self.apartados):
            if ap.get("id") == apartado_id:
                self.apartado_actual = i
                self.seleccion = 0
                self.opcion_indices = {}
                return True
        return False
