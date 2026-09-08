import os
import sys

os.environ["SDL_VIDEODRIVER"] = "dummy"
os.environ["SDL_AUDIODRIVER"] = "dummy"

from engine.entities.snake import Snake
from engine.entities.objeto_colision import ObjetoBloqueante
from engine.configs import LONGITUD_INICIAL, TAMANO_CELDA as T


class _Estado:
    def __init__(self):
        self.bloqueantes = []
        self.bloques_acero = []
        self.paredes = []


def _hacer_snake(n=5):
    """Orm de n segmentos subiendo: cabeza (4,1), (4,2), luego (3,2),(2,2)..."""
    s = Snake(4 * T, 1 * T)
    body = [[4 * T, 1 * T], [4 * T, 2 * T]]
    x = 3
    while len(body) < n:
        body.append([x * T, 2 * T])
        x -= 1
    s.body = body
    s.direccion = "ARRIBA"
    s.siguiente_direccion = "ARRIBA"
    s.enroscado = False
    s.etapa = 0
    s.creciendo = False
    s.dormido = False
    s.longitud = n
    s.largo_original = 0
    return s


def _estado_con_pared():
    e = _Estado()
    e.bloqueantes = [ObjetoBloqueante(4 * T, 0 * T)]
    return e


def _celdas(snake):
    return [[seg[0] // T, seg[1] // T] for seg in snake.body]


def _desenroscar(snake):
    """Presiona una dirección perpendicular permitida para desenroscar."""
    snake.siguiente_direccion = snake.direcciones_permitidas[0]
    snake._manejar_enroscado()


def _ciclo_completo(snake, estado):
    """Chocar contra la pared -> enroscar -> coil hasta el mínimo -> desenroscar -> restaurar."""
    estado.bloqueantes[0].manejar_colision(snake, estado)
    assert snake.enroscado
    while snake.enroscado and snake.etapa == 1 and len(snake.body) > 1:
        snake._procesar_enroscamiento()
    _desenroscar(snake)
    pasos = 0
    while snake.creciendo and pasos < 200:
        snake._desplazar_estandar()
        pasos += 1


def test_enroscar_contra_pared_no_rebota_el_cuerpo():
    s = _hacer_snake(5)
    s.mover(desplazar=True)  # la cabeza entra a la pared (0,4) y la cola se descarta

    e = _estado_con_pared()
    e.bloqueantes[0].manejar_colision(s, e)

    assert s.enroscado
    # Sin rebote: el cuerpo queda compacto bajo la cabeza, nada en la fila 3.
    celdas = _celdas(s)
    assert celdas == [[4, 1], [4, 2], [3, 2], [2, 2]], celdas
    assert all(y < 3 for _, y in celdas), celdas


def test_enroscamiento_sigue_reduciendo_en_el_lugar():
    s = _hacer_snake(5)
    s.mover(desplazar=True)

    e = _estado_con_pared()
    e.bloqueantes[0].manejar_colision(s, e)

    s._procesar_enroscamiento()
    celdas = _celdas(s)
    assert celdas == [[4, 1], [4, 2], [3, 2]], celdas
    assert all(y < 3 for _, y in celdas), celdas


def test_colision_no_cambia_longitud_ni_escamas():
    s = _hacer_snake(7)
    s.mover(desplazar=True)

    e = _estado_con_pared()
    e.bloqueantes[0].manejar_colision(s, e)

    assert s.longitud == 7
    assert s.get_escamas() == 7 - LONGITUD_INICIAL


def test_escamas_constantes_en_ciclos_repetidos():
    s = _hacer_snake(7)
    e = _estado_con_pared()

    for _ in range(3):
        s._no_enroscar_hasta = 0
        _ciclo_completo(s, e)
        assert s.longitud == 7, s.longitud
        assert s.get_escamas() == 7 - LONGITUD_INICIAL, s.get_escamas()
        assert len(s.body) == 7, len(s.body)


def test_re_enroscado_a_mitad_de_restauracion_no_pierde_escamas():
    s = _hacer_snake(7)
    e = _estado_con_pared()

    # Ciclo 1: chocar, coil mínimo, desenroscar pero restaurar SOLO 2 pasos.
    s._no_enroscar_hasta = 0
    e.bloqueantes[0].manejar_colision(s, e)
    while s.enroscado and s.etapa == 1 and len(s.body) > 1:
        s._procesar_enroscamiento()
    _desenroscar(s)
    s._desplazar_estandar()
    s._desplazar_estandar()
    assert s.creciendo
    assert len(s.body) < 7

    # Re-enroscado a mitad de la restauración: no debe perder escamas.
    s._no_enroscar_hasta = 0
    _ciclo_completo(s, e)

    assert s.longitud == 7, s.longitud
    assert s.get_escamas() == 7 - LONGITUD_INICIAL, s.get_escamas()
    assert len(s.body) == 7, len(s.body)

