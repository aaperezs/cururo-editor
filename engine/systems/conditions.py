"""Evaluador único de condiciones (Sprint 4, bonus).

Unifica la evaluación de condiciones en stack_manager, eventos_globales
y scene_player. Soporta tres formatos:

  - Lista plana:        [{"tipo": ..., "params": ...}, ...]  => AND implícito
  - Nodo compuesto:     {"operator": "AND"|"OR", "children": [...]} => recursivo
  - Hoja simple:        {"tipo": ..., "params": ...} o {"flag": ..., "valor": ...}

El evaluador recorre la estructura y delega cada hoja a un callable `leaf`
provisto por el llamador, que conoce la semántica concreta de cada condición.
"""

from __future__ import annotations

from typing import Any, Callable


def _is_composite(node: Any) -> bool:
    return isinstance(node, dict) and "operator" in node and isinstance(node.get("children"), list)


def evaluate_condition_node(node: Any, leaf: Callable[[dict], bool]) -> bool:
    """Evalúa un nodo de condición.

    node: lista (AND implícito), dict compuesto (operator/children) u hoja.
    leaf: callable(cond_dict) -> bool que evalúa una condición simple.
    """
    if node is None or node == {}:
        return True
    if isinstance(node, list):
        return all(evaluate_condition_node(child, leaf) for child in node)
    if _is_composite(node):
        op = str(node.get("operator", "AND")).upper()
        children = node.get("children", [])
        results = [evaluate_condition_node(c, leaf) for c in children]
        if op == "OR":
            return any(results)
        return all(results)
    if isinstance(node, dict):
        return leaf(node)
    return True


def make_leaf(method, ctx=None):
    """Convierte un método (cond, ctx=None) -> bool en un leaf con ctx fijado."""
    def _leaf(cond: dict) -> bool:
        return bool(method(cond, ctx))
    return _leaf
