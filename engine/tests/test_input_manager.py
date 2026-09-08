import pytest
import pygame
from engine.handlers.input_manager import InputManager


class FakeDialogo:
    def __init__(self):
        self.activo = False
        self._avanzado = False

    def avanzar(self):
        self._avanzado = True


class FakeSnake:
    def __init__(self):
        self.dormido = False
        self.despertar_bloqueado = False
        self.siguiente_direccion = ""
        self.direccion = ""

    def despertar(self):
        self.dormido = False

    def cambiar_direccion(self, d):
        if self.dormido:
            self.despertar()
            self.siguiente_direccion = d
            self.direccion = d
            return
        self.direccion = d

    def vender_segmentos(self, n):
        return True

    def pedir_prestado(self, n):
        return True

    def tiene_deuda(self):
        return False

    def get_escamas(self):
        return 0

    def get_longitud(self):
        return 3

    def set_skin(self, efecto):
        pass


class FakeHabilidades:
    def __init__(self):
        self.habilidad_equipada = None
        self.inventario = []

    def cambiar_habilidad(self, d):
        pass

    def get_habilidad_equipada(self):
        return None

    def recargar_pp(self, cantidad=1):
        return False


class FakeForja:
    def __init__(self):
        self.seleccion = 0
        self._repo = FakeRepo()

    def fabricar_seleccion(self):
        pass


class FakeRepo:
    def get_todas(self):
        return {}


class FakeVentana:
    def __init__(self):
        self.activo = False

    def avanzar(self):
        pass


class FakeStackManager:
    def process_events(self, x, y, kind, z):
        pass


class FakeMiniJuego:
    def __init__(self):
        self._handled = []

    def handle_event(self, event):
        self._handled.append(event)


class FakeMenu:
    def __init__(self):
        self.apartados = [
            {"id": "habilidades", "nombre": "Habilidades"},
            {"id": "items", "nombre": "Items"},
            {"id": "equipo", "nombre": "Equipo"},
        ]
        self.apartado_actual = 0
        self.seleccion = 0

    def abrir(self):
        self.apartado_actual = 0
        self.seleccion = 0

    @property
    def apartado_id(self):
        return self.apartados[self.apartado_actual]["id"]

    def cambiar_apartado(self, direccion=1):
        self.apartado_actual = (self.apartado_actual + direccion) % len(self.apartados)


class FakeEstado:
    def __init__(self):
        self.dialogo = FakeDialogo()
        self.ventana = FakeVentana()
        self.game_over = False
        self.mostrando_forja = False
        self.mostrando_inventario = False
        self.mostrando_trueque = False
        self.mostrando_minijuego = False
        self.mostrando_opciones = False
        self.opciones = []
        self.opcion_seleccionada = -1
        self.sistema_minijuego = FakeMiniJuego()
        self.demo_activo = False
        self.pausa = False
        self.god_mode = False
        self.mandos_bloqueados = False
        self.stack_manager = FakeStackManager()
        self.snake = FakeSnake()
        self.habilidades = FakeHabilidades()
        self.sistema_forja = FakeForja()
        self.menu = FakeMenu()
        self.mensajes_recibidos = []

    def reiniciar(self):
        self.game_over = False
        self.pausa = False


@pytest.fixture
def estado():
    return FakeEstado()


@pytest.fixture
def im(estado):
    mensajes = []
    habilidad_usada = [False]

    def mostrar_mensaje(msg, t):
        mensajes.append((msg, t))

    def mock_ejecutar_golpe():
        habilidad_usada[0] = True

    estado.ejecutar_golpe_q = mock_ejecutar_golpe

    manager = InputManager(estado, mostrar_mensaje)
    manager._mensajes = mensajes
    manager._habilidad_usada = habilidad_usada
    return manager


def _post_key(im, key):
    pygame.event.clear()
    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))
    im.process_events()


class TestInputManager:
    def test_event_clear_no_crash(self, im, estado):
        pygame.event.clear()
        im.process_events()

    def test_dialogue_advance_space(self, im, estado):
        estado.dialogo.activo = True
        _post_key(im, pygame.K_SPACE)
        assert estado.dialogo._avanzado

    def test_dialogue_advance_return(self, im, estado):
        estado.dialogo.activo = True
        _post_key(im, pygame.K_RETURN)
        assert estado.dialogo._avanzado

    def test_toggle_pause(self, im, estado):
        _post_key(im, pygame.K_p)
        assert estado.pausa is True
        _post_key(im, pygame.K_p)
        assert estado.pausa is False

    def test_toggle_godmode(self, im, estado):
        _post_key(im, pygame.K_F3)
        assert estado.god_mode is True

    def test_move_up(self, im, estado):
        _post_key(im, pygame.K_UP)
        assert estado.snake.direccion == "ARRIBA"

    def test_move_down(self, im, estado):
        _post_key(im, pygame.K_DOWN)
        assert estado.snake.direccion == "ABAJO"

    def test_move_left(self, im, estado):
        _post_key(im, pygame.K_LEFT)
        assert estado.snake.direccion == "IZQUIERDA"

    def test_move_right(self, im, estado):
        _post_key(im, pygame.K_RIGHT)
        assert estado.snake.direccion == "DERECHA"

    def test_use_skill(self, im, estado):
        _post_key(im, pygame.K_q)
        assert im._habilidad_usada[0] is True

    def test_close_forge(self, im, estado):
        estado.mostrando_forja = True
        _post_key(im, pygame.K_ESCAPE)
        assert estado.mostrando_forja is False

    def test_forge_up(self, im, estado):
        estado.mostrando_forja = True
        _post_key(im, pygame.K_UP)
        assert estado.sistema_forja.seleccion == 0

    def test_forge_down(self, im, estado):
        estado.mostrando_forja = True
        _post_key(im, pygame.K_DOWN)
        # Empty repo clamps to -1
        assert estado.sistema_forja.seleccion == -1

    def test_wake_up_snake(self, im, estado):
        estado.snake.dormido = True
        _post_key(im, pygame.K_UP)
        assert estado.snake.dormido is False

    def test_rebind(self, im, estado):
        im.rebind(pygame.K_o, "TOGGLE_PAUSE")
        _post_key(im, pygame.K_o)
        assert estado.pausa is True

    def test_get_action_name(self, im, estado):
        name = im.get_action_name("MOVE_UP")
        assert name == "up"

    def test_toggle_trade(self, im, estado):
        _post_key(im, pygame.K_t)
        assert estado.mostrando_trueque is True

    def test_toggle_inventory(self, im, estado):
        _post_key(im, pygame.K_i)
        assert estado.mostrando_inventario is True

    def test_inventory_tab_changes_apartado(self, im, estado):
        estado.mostrando_inventario = True
        _post_key(im, pygame.K_TAB)
        assert estado.menu.apartado_id == "items"
        _post_key(im, pygame.K_RIGHT)
        assert estado.menu.apartado_id == "equipo"
        _post_key(im, pygame.K_LEFT)
        assert estado.menu.apartado_id == "items"

    def test_inventory_escape_closes(self, im, estado):
        estado.mostrando_inventario = True
        _post_key(im, pygame.K_ESCAPE)
        assert estado.mostrando_inventario is False

    def test_trade_sell_1(self, im, estado):
        estado.mostrando_trueque = True
        _post_key(im, pygame.K_1)
        assert estado.mostrando_trueque is False

    def test_trade_borrow(self, im, estado):
        estado.mostrando_trueque = True
        _post_key(im, pygame.K_d)
        assert estado.mostrando_trueque is False

    def test_game_over_restart(self, im, estado):
        estado.game_over = True
        _post_key(im, pygame.K_r)
        assert estado.game_over is False

