# entities/snake/movimiento.py
from engine.configs import *

_DIR_OPUESTA = {
    "ARRIBA": "ABAJO",
    "ABAJO": "ARRIBA",
    "IZQUIERDA": "DERECHA",
    "DERECHA": "IZQUIERDA",
}

_DESPLAZAMIENTO = {
    "ARRIBA": (0, -TAMANO_CELDA),
    "ABAJO": (0, TAMANO_CELDA),
    "IZQUIERDA": (-TAMANO_CELDA, 0),
    "DERECHA": (TAMANO_CELDA, 0),
}


class MovimientoMixin:

    # ── Público ───────────────────────────────────────────

    def mover(self, desplazar=True):
        self._actualizar_invencible()

        if self.dormido:
            return

        if self.enroscado and self.etapa > 0:
            self._manejar_enroscado()
            return

        if not desplazar:
            return

        self._desplazar_estandar()

    def cambiar_direccion(self, nueva_direccion):
        if self.dormido:
            self._despertar_y_direccionar(nueva_direccion)
            return

        if self.enroscado and nueva_direccion not in self.direcciones_permitidas:
            return

        if _DIR_OPUESTA.get(nueva_direccion) != self.direccion:
            self.siguiente_direccion = nueva_direccion

    # ── Movimiento enroscado ──────────────────────────────

    def _manejar_enroscado(self):
        if self.siguiente_direccion in self.direcciones_permitidas:
            self.direccion = self.siguiente_direccion
            self._iniciar_desenroscamiento()
        else:
            self._procesar_enroscamiento()

    # ── Movimiento estándar ───────────────────────────────

    def _actualizar_invencible(self):
        if self.invencible:
            self.tiempo_invencible -= 1
            if self.tiempo_invencible <= 0:
                self.invencible = False

    def _desplazar_estandar(self):
        self.direccion = self.siguiente_direccion
        self.body.insert(0, self._calcular_nueva_cabeza())
        self._gestionar_crecimiento()

    def _calcular_nueva_cabeza(self):
        cabeza = self.body[0].copy()
        dx, dy = _DESPLAZAMIENTO.get(self.direccion, (0, 0))
        cabeza[0] += dx
        cabeza[1] += dy
        return cabeza

    def _gestionar_crecimiento(self):
        if not self.creciendo:
            self.body.pop()
            return

        if self.segmentos_a_restaurar > 0:
            self.segmentos_a_restaurar -= 1
        if self.segmentos_a_restaurar <= 0:
            self.creciendo = False
            self.largo_original = len(self.body)

    # ── Despertar ─────────────────────────────────────────

    def _despertar_y_direccionar(self, nueva_direccion):
        self.despertar()
        self.siguiente_direccion = nueva_direccion
        self.direccion = nueva_direccion
