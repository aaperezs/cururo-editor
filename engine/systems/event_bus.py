from collections import defaultdict
from dataclasses import dataclass
from typing import Any, Callable


@dataclass
class Evento:
    """Evento base del dominio"""
    pass


@dataclass
class EventoRocaRota(Evento):
    roca: Any = None
    posicion: tuple = (0, 0)
    jugador: Any = None


@dataclass
class EventoRocaAgrietada(Evento):
    roca: Any = None
    posicion: tuple = (0, 0)


@dataclass
class EventoEnemigoDerrotado(Evento):
    enemigo: Any = None
    posicion: tuple = (0, 0)
    con_manto: bool = False


@dataclass
class EventoJefeDerrotado(Evento):
    boss: Any = None


@dataclass
class EventoJefeDanio(Evento):
    boss: Any = None
    dano: int = 0
    nueva_fase: bool = False


@dataclass
class EventoComidaRecogida(Evento):
    comida: Any = None
    jugador: Any = None


@dataclass
class EventoProyectilComido(Evento):
    proyectil: Any = None
    total_comidos: int = 0
    necesarios: int = 0


@dataclass
class EventoGateAbierto(Evento):
    gate: Any = None
    costo_pagado: int = 0


@dataclass
class EventoNivelCambiado(Evento):
    nivel_id: str = ""
    origen_id: str = None


@dataclass
class EventoObjetoDestruido(Evento):
    objeto: Any = None
    posicion: tuple = (0, 0)
    tipo: str = ""


@dataclass
class EventoGameOver(Evento):
    causa: str = ""


@dataclass
class EventoDamageInfligido(Evento):
    """Emitido cuando se aplica daño a la serpiente"""
    cantidad: int = 0
    fuente: str = ""
    posicion: tuple = (0, 0)
    letal: bool = False


@dataclass
class EventoDamageContraataque(Evento):
    """Emitido cuando el manto contraataca a un enemigo"""
    enemigo: Any = None
    damage: int = 0
    posicion: tuple = (0, 0)


Handler = Callable[['Evento'], None]


class BusEventos:
    """Bus de eventos del dominio — suscripción y publicación con tipado"""

    def __init__(self):
        self._handlers: dict[type, list[Handler]] = defaultdict(list)

    def suscribir(self, tipo_evento: type, handler: Handler):
        self._handlers[tipo_evento].append(handler)

    def desuscribir(self, tipo_evento: type, handler: Handler):
        if handler in self._handlers[tipo_evento]:
            self._handlers[tipo_evento].remove(handler)

    def publicar(self, evento: Evento):
        for handler in self._handlers[type(evento)]:
            handler(evento)

    def limpiar(self):
        self._handlers.clear()
