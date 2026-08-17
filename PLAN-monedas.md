# Plan: Sistema de Monedas (contadores de primera clase)

Estado: ✅ Aprobado por el usuario. Implementación en curso.
Última actualización: fase de migración de orm a la moneda "escamas".

## Objetivo

Las escamas (y cualquier otra moneda de cualquier juego: rupias, oro, pokedollar,
nivel de amistad...) pasan a ser **contadores de primera clase** definibles desde
el editor. Un juego puede tener 1 o N monedas; cada una es una entidad propia.

## Modelo de datos

`data/monedas.json`:

```json
{
  "monedas": [
    {
      "id": "escamas",
      "label": "Escamas",
      "valor_inicial": 0,
      "icono": "\u25c6",
      "color": [210, 185, 100],
      "principal": true
    }
  ]
}
```

| campo | uso |
|---|---|
| `id` | referencia interna (condiciones/acciones) |
| `label` | lo que se muestra en el juego |
| `valor_inicial` | cantidad inicial (default 0) |
| `icono` | visual (HUD/inventario futuros) |
| `color` | visual (HUD futuro) — [r, g, b] |
| `principal` | moneda de pago por defecto — **máx 1 por juego** |

Reglas:
- Máximo **una** moneda `principal` (el editor la garantiza al marcar una).
- `id` único; `label` requerido.
- Convive con los flags: moneda = se gasta y se muestra; flag = estado del mundo.

## A. Motor (orm)

1. `data/monedas.json` nueva (definición). Template snake_rpg idéntico.
2. `repositories/repositorio_monedas.py` (carga de definiciones).
3. `game_state.monedas` = contador actual `{id: cantidad}`, inicializado con
   `valor_inicial` de cada definición.
4. `systems/stack_manager.py`:
   - Condición genérica `has_moneda` (moneda, operador, valor).
   - Acciones genéricas `give_moneda` / `remove_moneda` (moneda, cantidad).
   - Migración legacy en carga: `escamas`/`has_escamas`/`not_has_escamas` →
     `has_moneda` (moneda="escamas"); `remove_escamas` → `remove_moneda`.
   - Los stack files no se editan (se migran en carga, patrón existente).
   - La moneda `escamas` sigue ligada a `snake.get_escamas()`/`perder_escamas()`
     (shim, cero regresión). Otras monedas = contador genérico.
5. UI (HUD / game over / trueque) sin cambios: leen `snake.get_escamas()`,
   que coincide con el valor de la moneda "escamas" bajo el shim.

## B. Editor

1. `monedas_data.py`: CRUD de `data/monedas.json` + `validar_monedas`
   (ids únicos, label requerido, única principal).
2. `monedas_panel.py` (MonedasTab): lista + formulario
   (id, label, valor_inicial, icono, color, principal con auto-desmarcado).
3. Registro: `categories.py` (panel `monedas`), `main.py` (PANELES), locales
   `tab.monedas.*`.
4. `widgets/event_editor_widget.py`:
   - condición `escamas` → `has_moneda` (params: moneda, operador, valor);
   - acción `remove_escamas` → `give_moneda` + `remove_moneda` (moneda, cantidad);
   - dropdown `moneda` en `_get_param_options` (patrón del dropdown `item`);
   - locales es/en (`event.condition.has_moneda`, `event.action.give_moneda`,
     `event.action.remove_moneda`).
5. `actions_data.py` (acciones de items de menú): agregar `give_moneda` /
   `remove_moneda` (útil para menús tipo tienda).

## C. Datos

- `orm/data/monedas.json` (nueva): "escamas" principal (label "Escamas",
  valor_inicial 0, icono ◆, color ámbar [210,185,100]).
- `editor/templates/snake_rpg/data/monedas.json`: idéntica (seed de proyectos).
- Se crea como archivo nuevo; no se toca `data/` existente del usuario.

## Temas aparte (fuera de esta fase)

1. Desacoplar "escamas" del largo de la snake (cómo la comida recarga la moneda).
2. `recetas.json` usa "escamas" como material de crafteo.
3. HUD configurable (editor visual del HUD).

## Verificación

- Tests orm nuevos: init de monedas, `has_moneda`/`give_moneda`/`remove_moneda`,
  migración de aliases legacy; regresión de los 86 actuales.
- Test headless del MonedasTab (CRUD + única principal) y del event editor
  (dropdown de monedas).
- `py_compile` de todo.
