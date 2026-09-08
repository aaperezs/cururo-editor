import pytest
import pygame

from engine.systems import user_prefs
from engine.systems.stack_manager import StackManager
from engine.systems.ui.components.inventory_panels import PanelLista


class FakeAudio:
    def __init__(self):
        self.bgm = None
        self.sfx = None

    def set_bgm_volume(self, v):
        self.bgm = v

    def set_sfx_volume(self, v):
        self.sfx = v


class FakeEstado:
    def __init__(self):
        self.audio = FakeAudio()


@pytest.fixture
def prefs_tmp(tmp_path, monkeypatch):
    """Redirige user_prefs a un archivo temporal (no toca data/ del repo)."""
    monkeypatch.setattr(user_prefs, "prefs_path",
                        lambda: str(tmp_path / "user_prefs.json"))
    return tmp_path


def _sm():
    return StackManager(FakeEstado())


class TestSetResolution:
    def test_aplica_y_persiste(self, prefs_tmp):
        sm = _sm()
        sm._ejecutar_accion("set_resolution", {"ancho": 800, "alto": 600}, 0, 0, 0)
        prefs = user_prefs.load()
        assert prefs["resolution"] == "800x600"

    def test_params_invalidos_no_cambian_prefs(self, prefs_tmp):
        sm = _sm()
        sm._ejecutar_accion("set_resolution", {"ancho": 0, "alto": 0}, 0, 0, 0)
        prefs = user_prefs.load()
        assert prefs["resolution"] == "auto"

    def test_sin_params_no_rompe(self, prefs_tmp):
        sm = _sm()
        sm._ejecutar_accion("set_resolution", {}, 0, 0, 0)
        prefs = user_prefs.load()
        assert prefs["resolution"] == "auto"


class TestSetVolume:
    def test_aplica_y_persiste(self, prefs_tmp):
        sm = _sm()
        sm._ejecutar_accion("set_volume", {"volumen": 0.5}, 0, 0, 0)
        assert sm.estado.audio.bgm == 0.5
        assert sm.estado.audio.sfx == 0.5
        prefs = user_prefs.load()
        assert prefs["bgm_volume"] == 0.5
        assert prefs["sfx_volume"] == 0.5

    def test_sin_audio_no_rompe(self, prefs_tmp):
        sm = StackManager(FakeEstado())
        del sm.estado.audio
        sm._ejecutar_accion("set_volume", {"volumen": 0.3}, 0, 0, 0)
        prefs = user_prefs.load()
        assert prefs["bgm_volume"] == 0.7  # default, no cambió


class TestDisplaySetWindowSize:
    def test_recrea_ventana(self):
        import display
        display.setup((800, 600))
        display.set_window_size((640, 480))
        assert display._real is not None
        assert display._real.get_size() == display._tamano_ventana((640, 480))

    def test_fullscreen_noop(self):
        import display
        display.setup((800, 600), fullscreen=True)
        antes = display._real
        display.set_window_size((640, 480))
        assert display._real is antes


class FakeMenu:
    def __init__(self):
        self.opcion_indices = {}
        self.seleccion = 0


class FakeEstadoMenu:
    def __init__(self):
        self.menu = FakeMenu()


ITEMS_RES = [
    {
        "id": "resolucion",
        "nombre": "Resolución",
        "opciones": [
            {"nombre": "1280x720", "params": {"ancho": 1280, "alto": 720}},
            {"nombre": "800x600", "params": {"ancho": 800, "alto": 600}},
        ],
        "accion": {"tipo": "set_resolution", "params": {}},
    }
]

ITEMS_VOL = [
    {
        "id": "volumen",
        "nombre": "Volumen",
        "opciones": [
            {"nombre": "0%", "params": {"volumen": 0.0}},
            {"nombre": "25%", "params": {"volumen": 0.25}},
            {"nombre": "100%", "params": {"volumen": 1.0}},
        ],
        "accion": {"tipo": "set_volume", "params": {}},
    }
]


def _panel(items):
    return PanelLista(None, None, config={"items": items})


class TestPanelListaOpciones:
    def test_accion_mergea_params_de_opcion(self):
        estado = FakeEstadoMenu()
        accion = _panel(ITEMS_RES).accion_seleccionada(estado)
        assert accion["tipo"] == "set_resolution"
        assert accion["params"]["ancho"] == 1280
        assert accion["params"]["alto"] == 720

    def test_match_resolucion_persistida(self, prefs_tmp):
        user_prefs.save({"resolution": "800x600", "fullscreen": False})
        estado = FakeEstadoMenu()
        panel = _panel(ITEMS_RES)
        assert panel._indice_opcion(ITEMS_RES[0], estado) == 1
        assert estado.menu.opcion_indices["resolucion"] == 1

    def test_match_volumen_persistido(self, prefs_tmp):
        user_prefs.save({"bgm_volume": 0.25, "sfx_volume": 0.25})
        estado = FakeEstadoMenu()
        panel = _panel(ITEMS_VOL)
        assert panel._indice_opcion(ITEMS_VOL[0], estado) == 1

    def test_sin_match_vuelve_0(self, prefs_tmp):
        user_prefs.save({"resolution": "auto", "fullscreen": False})
        estado = FakeEstadoMenu()
        panel = _panel(ITEMS_RES)
        assert panel._indice_opcion(ITEMS_RES[0], estado) == 0

    def test_sin_opciones_devuelve_accion_plana(self):
        items = [{"id": "x", "nombre": "X",
                  "accion": {"tipo": "show_message", "params": {"mensaje": "hola"}}}]
        estado = FakeEstadoMenu()
        accion = _panel(items).accion_seleccionada(estado)
        assert accion == {"tipo": "show_message", "params": {"mensaje": "hola"}}


class TestMenuOpcionIndices:
    def test_reset_en_abrir(self):
        from systems.menu import MenuSystem
        menu = MenuSystem()
        menu.opcion_indices["x"] = 3
        menu.abrir()
        assert menu.opcion_indices == {}

    def test_reset_en_cambiar_apartado(self):
        from systems.menu import MenuSystem
        menu = MenuSystem()
        menu.abrir()
        menu.opcion_indices["x"] = 3
        menu.cambiar_apartado(1)
        assert menu.opcion_indices == {}


class FakeStack:
    def __init__(self):
        self.calls = []

    def ejecutar_ahora(self, accion):
        self.calls.append(accion)


class FakeMenuCiclo:
    def __init__(self, items):
        self.apartados = [{"id": "video", "nombre": "Video", "tipo": "lista",
                           "items": items}]
        self.apartado_actual = 0
        self.seleccion = 0
        self.opcion_indices = {}

    @property
    def apartado_tipo(self):
        return self.apartados[self.apartado_actual].get("tipo", "lista")

    @property
    def apartado_config(self):
        return self.apartados[self.apartado_actual]

    def cambiar_apartado(self, direccion=1):
        self.apartado_actual = (self.apartado_actual + direccion) % len(self.apartados)
        self.seleccion = 0
        self.opcion_indices = {}


class FakeEstadoCiclo:
    def __init__(self, items):
        self.menu = FakeMenuCiclo(items)
        self.mostrando_inventario = True
        self.stack_manager = FakeStack()
        self.mostrando_minijuego = False
        self.mostrando_opciones = False
        self.opciones = []
        self.opcion_seleccionada = -1
        self.dialogo = type("D", (), {"activo": False})()
        self.ventana = type("V", (), {"activo": False})()
        self.game_over = False
        self.mostrando_forja = False
        self.mostrando_trueque = False


def _post_key(im, key):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
    im.process_events()


class TestInputCicloOpciones:
    def test_right_cicla_opcion_y_aplica(self):
        from handlers.input_manager import InputManager
        estado = FakeEstadoCiclo(ITEMS_RES)
        im = InputManager(estado, lambda m, t: None)
        _post_key(im, pygame.K_RIGHT)
        assert estado.menu.opcion_indices["resolucion"] == 1
        assert estado.stack_manager.calls
        accion = estado.stack_manager.calls[-1]
        assert accion["params"]["ancho"] == 800
        assert accion["params"]["alto"] == 600

    def test_left_cicla_en_negativo(self):
        from handlers.input_manager import InputManager
        estado = FakeEstadoCiclo(ITEMS_RES)
        im = InputManager(estado, lambda m, t: None)
        _post_key(im, pygame.K_LEFT)
        assert estado.menu.opcion_indices["resolucion"] == 1  # mod len(2)

    def test_sin_opciones_cambia_apartado(self):
        from handlers.input_manager import InputManager
        items = [{"id": "x", "nombre": "X",
                  "accion": {"tipo": "show_message", "params": {"mensaje": "hola"}}}]
        estado = FakeEstadoCiclo(items)
        im = InputManager(estado, lambda m, t: None)
        _post_key(im, pygame.K_RIGHT)
        # un solo apartado: cicla a 0, no aplica acción
        assert estado.menu.apartado_actual == 0
        assert not estado.stack_manager.calls

    def test_primer_press_left_desde_persistido_no_ultimo(self, prefs_tmp):
        """Persistido 960x720 (índice 1 de 3): LEFT debe ir a 800x600 (0), no al último."""
        from handlers.input_manager import InputManager
        items = [{
            "id": "resolucion",
            "nombre": "Resolución",
            "opciones": [
                {"nombre": "800x600", "params": {"ancho": 800, "alto": 600}},
                {"nombre": "960x720", "params": {"ancho": 960, "alto": 720}},
                {"nombre": "1280x720", "params": {"ancho": 1280, "alto": 720}},
            ],
            "accion": {"tipo": "set_resolution", "params": {}},
        }]
        user_prefs.save({"resolution": "960x720", "fullscreen": False})
        estado = FakeEstadoCiclo(items)
        im = InputManager(estado, lambda m, t: None)
        _post_key(im, pygame.K_LEFT)
        assert estado.menu.opcion_indices["resolucion"] == 0
        accion = estado.stack_manager.calls[-1]
        assert accion["params"]["ancho"] == 800
        assert accion["params"]["alto"] == 600

    def test_ciclo_sin_id_usa_fallback_key(self, prefs_tmp):
        """Ítem sin `id`: el ciclo cachea con key sintético y aplica."""
        from handlers.input_manager import InputManager
        items = [{
            "nombre": "Resolución",
            "opciones": [
                {"nombre": "800x600", "params": {"ancho": 800, "alto": 600}},
                {"nombre": "960x720", "params": {"ancho": 960, "alto": 720}},
            ],
            "accion": {"tipo": "set_resolution", "params": {}},
        }]
        user_prefs.save({"resolution": "960x720", "fullscreen": False})
        estado = FakeEstadoCiclo(items)
        im = InputManager(estado, lambda m, t: None)
        _post_key(im, pygame.K_LEFT)
        assert estado.menu.opcion_indices["@0"] == 0
        accion = estado.stack_manager.calls[-1]
        assert accion["params"]["ancho"] == 800
