from engine.runtime.flags import FlagsManager
from engine.systems.dialogo import DialogoSystem
from engine.systems.stack_manager import StackManager
from engine.systems.minigame import MiniJuegoManager
from engine.systems.audio_manager import AudioManager


def finalizar_minijuego(estado):
    res = estado.sistema_minijuego.get_resultado() or {}
    for k, v in res.items():
        estado.flags.set(k, v)
    estado.mostrando_minijuego = False
    estado.minijuego_id = None


class VnGameState:
    def __init__(self):
        self.flags = FlagsManager()
        self.dialogo = DialogoSystem(flags=self.flags)
        self.stack_manager = StackManager(self)
        self.sistema_minijuego = MiniJuegoManager(self)
        self.audio = AudioManager()

        self.fondo_activo = None
        self.fondo_modo = "fill"
        self.personajes_visibles = {}
        self.mostrando_opciones = False
        self.opciones = []
        self.opcion_seleccionada = -1
        self.mostrando_minijuego = False
        self.minijuego_id = None
        self.corriendo = True
        self.volver_a_menu = False
        self.cambiando_nivel = False
        self._scene_navegacion = None
