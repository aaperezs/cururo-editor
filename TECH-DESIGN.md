# Cururo Editor — Documento de Diseño Técnico

## 1. Arquitectura General

El editor es una aplicación Pygame que trabaja sobre **proyectos**. Cada proyecto es un directorio con un archivo `cururo.json` que lo identifica. Al iniciar, el editor muestra un diálogo para seleccionar o crear un proyecto.

### Estructura del Editor

```
editor/                          ← Mismo nivel que los proyectos
├── main.py                      # Punto de entrada: EditorApp (ventana 1100×700)
├── project.py                   # Sistema de proyectos (Project class, path resolution)
├── project_dialog.py            # Diálogo de selección de proyecto al inicio
├── i18n.py                      # Internacionalización ES/EN
├── sprite_editor.py             # Panel editor de sprites (pestaña 1)
├── map_editor.py                # Panel editor de mapas (pestaña 2)
├── event_editor.py              # Panel editor de eventos (pestaña 3)
├── element_tab.py               # Panel editor de elementos (pestaña 4)
├── elements.py                  # CRUD loader para data/elementos.json (usa project path)
├── behaviors.py                 # Definiciones de behaviors con schemas de propiedades
├── boss_tab.py                  # Panel editor de jefes (pestaña 5)
├── boss_data.py                 # CRUD loader para data/bosses.json (usa project path)
├── boss_fight_types.py          # Definiciones de fight types con schemas de fase
├── map_tab.py                   # Modelo de datos del mapa (MapTab, LayerState)
├── sprite_map.py                # Utilidades de sprites para mapas
├── sprite_registry.py           # Registro maestro de sprites (solo catálogo visual)
│
├── tools/               # Herramientas de dibujo
│   ├── pencil.py        # Lápiz
│   ├── eraser.py        # Borrador (transparencia)
│   ├── bucket.py        # Balde (flood fill)
│   └── eyedropper.py    # Gotero
│
├── widgets/             # Sistema de widgets UI
│   ├── base.py          # Widget, Container
│   ├── button.py
│   ├── label.py
│   ├── panel.py
│   ├── canvas.py        # Lienzo de dibujo/pintura
│   ├── color_picker.py  # Selector de color
│   ├── layer_panel.py   # Panel de capas dinámicas
│   ├── slider.py        # Slider horizontal
│   ├── palette.py       # Paleta de sprites (resuelve elemento_id → sprite_id)
│   ├── tab_bar.py       # Barra de pestañas
│   ├── scrollable.py    # Área scrollable
│   ├── event_editor_widget.py  # Editor de eventos por tile
│   ├── text_input.py    # Campo de texto
│   └── dialog.py        # Diálogo modal
│
├── locales/             # Archivos de traducción
│   ├── es.json
│   └── en.json
│
└── data/                # Datos del juego (raíz del proyecto)
    └── elementos.json   # 28 elementos con sprite_id, behavior, properties
```

### Flujo de eventos
```
pygame.event.get()
  → EditorApp.run()
    → TabBar.handle_event()
    → panel_activo.handle_event()
      → Container.handle_event() (propaga a hijos en orden inverso)
        → Widget.handle_event()
```

### Flujo de dibujado
```
EditorApp.run()
  → panel_activo.draw(screen)
    → Container.draw() (dibuja hijos en orden)
      → Widget.draw()
```

---

## 2. Sistema de Proyectos

### Archivo de manifiesto
Cada proyecto tiene un `cururo.json` en su raíz:
```json
{
  "name": "Orm: La Serpiente Enroscada",
  "id": "orm",
  "version": "1.0.0"
}
```

### Diálogo de apertura (`project_dialog.py`)
Al iniciar, `main.py` escanea el directorio padre en busca de proyectos (directorios con `cururo.json`). Muestra un diálogo Pygame con la lista:
- Navegación con flechas + Enter, o click directo
- ESC para salir
- Si se pasa un argumento CLI (`python main.py ruta/al/proyecto`), lo abre directamente

### Project class (`project.py`)
```python
class Project:
    root: str                          # Ruta absoluta al directorio del proyecto
    name: str                          # Nombre visible (desde cururo.json)
    project_id: str                    # ID único (desde cururo.json)
    
    def data_path(*parts)              # → root/data/...
    def assets_path(*parts)            # → root/assets/...
    def levels_path(*parts)            # → root/levels/...
    def stacks_path(*parts)            # → root/levels/mapas_stacks/...
```

### Resolución de rutas
- `set_current_project(path)`: establece el proyecto activo y agrega su raíz a `sys.path` (para imports de Python del proyecto)
- `get_current_project()`: retorna el `Project` actual (o `None`)
- Todos los módulos del editor que leen datos del proyecto (`elements.py`, `boss_data.py`, `map_editor.py`, `event_editor.py`, `sprite_editor.py`) usan `get_current_project()` para resolver rutas

### Flujo de inicio
1. `editor/main.py` se ejecuta
2. Escanea `python/` en busca de proyectos con `cururo.json`
3. Muestra `ProjectDialog` con la lista
4. Usuario selecciona "Orm: La Serpiente Enroscada"
5. `set_current_project("python/orm")` agrega `orm/` a sys.path
6. Editor carga elementos, bosses y demás datos del proyecto
7. Editor funciona sobre `orm/` hasta que se cierra

---

## 3. Sistema de Widgets

### Jerarquía base (`editor/widgets/base.py`)

```
Widget
  ├── rect: pygame.Rect
  ├── parent: Widget
  ├── visible: bool
  ├── enabled: bool
  ├── handle_event(event) → bool
  ├── draw(surface)
  └── get_abs_rect() → pygame.Rect

Container(Widget)
  ├── children: list[Widget]
  ├── add(child)     # child.parent = self
  ├── remove(child)
  ├── clear()
  └── reversed(children) → handle_event en orden inverso (z-index)
```

### Canvas (`editor/widgets/canvas.py`)

Lienzo de dibujo paramétrico usado tanto en el editor de sprites como en mapas.

| Propiedad | Descripción |
|-----------|-------------|
| `_surface` | Superficie Pygame a editar |
| `_zoom` | Factor de zoom (2-40) |
| `_tool` | Herramienta activa (PencilTool, EraserTool, etc.) |
| `_offset_x/y` | Centrado automático del contenido en el viewport |
| `_show_grid` | Overlay de grid |

**Draw:** Itera píxeles de `_surface`, escala cada uno como rectángulo. Píxeles con `alpha=0` dibujan patrón checker; `0<alpha<255` mezclan color + checker; `alpha=255` dibujan color sólido.

**Eventos:**
- `MOUSEBUTTONDOWN (botón 1)`: Solo si `r.collidepoint(event.pos)`
- `MOUSEMOTION`: Solo si `r.collidepoint` y botón presionado
- `MOUSEBUTTONUP`: Siempre llama a `on_mouse_up()` del tool (resetea estado), pero **retorna False** para no bloquear otros widgets
- Rueda del mouse: zoom +/-2

### LayerPanel (`editor/widgets/layer_panel.py`)

Panel de capas dinámicas para el editor de mapas.

| Elemento | Descripción |
|----------|-------------|
| Toggle box | Click → toggle visibilidad de la capa |
| Nombre (Z=N) | Click → activa esa capa (cambia `tab.active_z`) |
| Slider | Click-arrastre → cambia opacidad de la capa |
| Botón X | Elimina capa (solo si Z≠0) |
| Botón + Capa | Agrega nueva capa (hasta MAX_LAYERS=5) |

**Estados:** `_layers: list[int]` (orden ascendente), `_active_z`, `_slider_dragging`, `_opacity_{z}` (atributos dinámicos)

**Método `sync_state(tab)`**: Lee `tab.layer_order` y `tab.layers[z].opacity` → sincroniza atributos `_opacity_{z}`. Limpia atributos huérfanos con `_cleanup_opacity_attrs()`.

### Slider (`editor/widgets/slider.py`)

Slider horizontal genérico.

| Propiedad | Descripción |
|-----------|-------------|
| `min` / `max` | Rango de valores |
| `value` | Valor actual |
| `label` | Texto mostrado a la izquierda |
| `callback` | Disparado al cambiar valor |

**Draw:** Track (barra), thumb (cuadrado de 8px), label, porcentaje.

---

## 4. Herramientas de Dibujo

### Interfaz común
Toda herramienta implementa estos 3 métodos (llamados por Canvas):

```python
def on_mouse_down(self, surface, pos, color): ...
def on_mouse_move(self, surface, pos, color): ...
def on_mouse_up(self, surface, pos, color): ...
```

### PencilTool (`editor/tools/pencil.py`)
- Dibuja píxeles individuales y líneas (Bresenham) entre posiciones
- Heredado por EraserTool originalmente, ahora clase independiente
- Atributo `color: tuple` (RGBA con opacidad incluida)

### EraserTool (`editor/tools/eraser.py`)
- **No tiene atributo `color`** → el `hasattr` en `sprite_editor.py` saltea el sync del color picker
- Siempre escribe `(0, 0, 0, 0)` en el píxel (transparencia total)
- Algoritmo de línea Bresenham propio (independiente de PencilTool)

### BucketTool (`editor/tools/bucket.py`)
- Flood fill (BFS) desde la posición del click
- Reemplaza píxeles del color objetivo con `self.color` (RGBA)

### EyedropperTool (`editor/tools/eyedropper.py`)
- Lee el píxel en la posición del click
- Dispara callback `on_pick(color_rgba)`
- No dibuja nada (no modifica la superficie)
- **No tiene atributo `color`**

### Flujo de actualización de color
```python
# sprite_editor.py handle_event()
if hasattr(self._current_tool, 'color'):
    r, g, b = self._color_picker.selected_color
    self._current_tool.color = (r, g, b, self._opacity_slider.value)
```

---

## 5. Editor de Sprites

### Panel (`editor/sprite_editor.py: SpriteEditorPanel`)

```
┌────────────────────────────────────────┐
│  ┌──────────┐  ┌──────────────┐ ┌────┐ │
│  │ Lapiz    │  │              │ │Nuev│ │
│  │ Borrador │  │   Canvas     │ │Abr │ │
│  │ Balde    │  │ (zoom×10)    │ │Guar│ │
│  │ Gotero   │  │              │ │    │ │
│  │          │  │              │ │pre │ │
│  │ [color]  │  │              │ │    │ │
│  │ [picker] │  │              │ │lis │ │
│  │ Op: 100% │  │              │ │... │ │
│  │ [=====o] │  └──────────────┘ └────┘ │
│  └──────────┘                           │
└────────────────────────────────────────┘
```

### Opacidad
- Slider de 0-255 en el panel de herramientas
- El color del lápiz se convierte de RGB a RGBA usando el slider
- El canvas dibuja semi-transparencia mezclando color + checker

### Undo/Redo
- `_undo_stack` / `_redo_stack`: listas de `pygame.Surface.copy()`
- Se guarda snapshot en cada `MOUSEBUTTONDOWN` (antes del dibujo)
- Ctrl+Z: pop undo, push current a redo, restaurar
- Ctrl+Shift+Z / Ctrl+Y: pop redo, push current a undo, restaurar
- Máximo 50 estados

---

## 6. Editor de Mapas

### Modelo de Datos (`editor/map_tab.py`)

#### MapTab
```python
MapTab
  ├── map_id: str
  ├── dirty: bool
  ├── undo_stack / redo_stack: list[snapshot]
  ├── layers: dict[int, LayerState]    # {0: LayerState, 1: LayerState, ...}
  ├── stacks: dict[tuple, dict]        # {(gx, gy): stack_data}
  ├── active_z: int                    # capa actual de pintado
  ├── spawn_pos: tuple | None          # (gx, gy)
  ├── spawn_z: int
  │
  ├── add_layer() → z | None           # Agrega siguiente Z disponible (hasta MAX_LAYERS=5)
  ├── remove_layer(z) → bool           # Elimina capa (no Z=0)
  ├── layer_order → list[int]          # sorted(layers.keys())
  ├── push_undo()                      # Snapshot completo
  ├── undo() / redo() → bool
  └── snapshot() → dict                # Clona todas las capas + stacks + estado
```

#### LayerState
```python
LayerState
  ├── grid: dict[tuple, str]    # {(gx, gy): sprite_id}
  ├── ancho: int
  ├── alto: int
  ├── visible: bool
  ├── opacity: int (0-100)
  └── clone() → LayerState      # deepcopy de grid
```

### Formato de Archivos

Cada capa se guarda como archivo JSON independiente:

```
levels/mapas/{map_id}.json       → Z=0 (sin sufijo, backward compat)
levels/mapas/{map_id}_z1.json    → Z=1
levels/mapas/{map_id}_z2.json    → Z=2
levels/mapas/{map_id}_z3.json    → Z=3
levels/mapas/{map_id}_z4.json    → Z=4
levels/mapas/{map_id}_meta.json  → spawn point + metadatos
levels/mapas_stacks/{map_id}_stacks.json  → eventos por tile
```

**JSON v2 (por capa):**
```json
{
  "version": 2,
  "ancho": 40,
  "alto": 30,
  "grid": {
    "x,y": "sprite_id"
  }
}
```

### Carga de Mapas (map_editor.py: _load_map_into_tab)

1. Cargar Z=0 (base) desde `{map_id}.json`
2. Escanear y cargar `{map_id}_z1.json` ... `{map_id}_z4.json` si existen
3. Cargar stacks desde `mapas_stacks/{map_id}_stacks.json` (con migración auto de formato legacy `capas` → `eventos`)
4. Cargar meta desde `{map_id}_meta.json` (spawn point)
5. Si no hay spawn en meta, escanear grids de todas las capas en busca de sprite `inicio`

### Pintado (map_editor.py)

- `_start_paint_drag()`, `_paint_drag_to()`, `_handle_map_click()`, `_handle_map_right_click()`
- Siempre operan sobre `tab.layers.get(tab.active_z)`
- Botón 1: coloca sprite seleccionado
- Botón 3: borra sprite (o restaura último)
- Auto-sincronización de spawn al colocar/borrar `inicio`

### Renderizado de Grid (map_editor.py: _draw_grid)

```python
for z in tab.layer_order:   # Ascendente (0 abajo, 4 arriba)
    ls = tab.layers.get(z)
    if not ls or not ls.visible or ls.opacity <= 0:
        continue
    alpha = ls.opacity * 2.55
    for (gx, gy) in ls.grid:
        # frustum culling, blit con alpha
```

---

## 7. Sistema de Eventos (Stacks)

### Formato de Datos
```json
{
  "pos": [x, y],
  "z_layer": 0,
  "eventos": [
    {
      "trigger": "contact" | "interact",
      "condiciones": [
        {"tipo": "has_item", "params": {"item": "...", "cantidad_min": 1}}
      ],
      "acciones": [
        {"tipo": "show_message", "params": {"mensaje": "..."}}
      ]
    }
  ]
}
```

### Runtime: StackManager (`systems/stack_manager.py`)

- `process_events(x, y, trigger)`: Busca stack en la posición, evalúa condiciones, ejecuta acciones
- `_check_conditions(condiciones, ctx)`: Evalúa lista AND de condiciones
- `_ejecutar_acciones(acciones, ctx)`: Ejecuta acciones secuencialmente
- Compatibilidad backward: formato legacy `capas` se auto-convierte a `eventos`

### Condiciones (9 tipos + escamas)

| Tipo | Params | Descripción |
|------|--------|-------------|
| `has_ability` | `ability`, `nivel_min` | Tiene habilidad con nivel mínimo |
| `not_has_ability` | `ability` | No tiene habilidad |
| `has_ability_equipped` | `ability` | Habilidad equipada |
| `not_has_ability_equipped` | `ability` | No tiene equipada |
| `has_pp` | `min` | PP actual >= min |
| `has_item` | `item`, `cantidad_min` | Tiene N items (>= cantidad_min) |
| `not_has_item` | `item`, `cantidad` | No tiene N items (< cantidad) |
| `has_escamas` | `min` | Escamas del snake >= min (usa `snake.get_escamas()`) |
| `not_has_escamas` | `cantidad` | Escamas del snake < cantidad |
| `has_flag` | `flag` | Flag global activado |
| `not_has_flag` | `flag` | Flag global desactivado |

### Acciones (11 tipos)

| Tipo | Params | Descripción |
|------|--------|-------------|
| `show_message` | `mensaje` | Muestra mensaje temporal |
| `replace_sprite` | `sprite_id` | Cambia sprite del tile (en `tile_overrides`) |
| `spawn_entity` | `sprite_id`, `offset_x`, `offset_y`, `z` | Spawnea entidad |
| `start_dialogue` | `dialogo_id` | Inicia diálogo |
| `change_map` | `nivel` | Cambia de nivel |
| `give_item` | `item`, `cantidad` | Da item al inventario |
| `remove_item` | `item`, `cantidad` | Quita item del inventario |
| `consume_pp` | `cantidad` | Consume PP |
| `set_flag` | `flag` | Activa flag global |
| `clear_flag` | `flag` | Desactiva flag global |

### Bugs Fixeados (Julio 2026)

- `Inventario.cantidad()` no existía → roto `has_item`/`not_has_item`. Agregado.
- `Inventario.remover_item()` no existía (método real `consumir_item`). Agregado alias.
- `GameState.flags` no inicializado → `set_flag`/`clear_flag`/`has_flag`/`not_has_flag` crasheaban. Agregado `self.flags = {}`.
- `stack_manager.py`: eventos con `once: false` se marcaban como `"finalizado"` en `_event_states` y el filtro en `load_stacks` los eliminaba al recargar nivel. Fix: solo marcar `"finalizado"` si `once: true`, y solo filtrar si `once: true` AND estado `"finalizado"`.

---

## 8. Sistema de Elementos

Inspirado en RPG Maker: los sprites son solo arte visual; los **elementos** (`data/elementos.json`) definen qué hace cada cosa en el juego.

### Arquitectura

```
editor/element_tab.py  →  editor/elements.py  →  data/elementos.json
                                                      ↓
                              levels/level_parser.py  (factory por behavior)
                              systems/stack_manager.py (spawn_from_element)
```

### Comportamiento (Behavior)

Archivo: `editor/behaviors.py`

Cada behavior define un schema de propiedades que el editor renderiza como campos dinámicos (bool, choice, int, text).

```python
BEHAVIORS = {
    "block_breakable": {
        "label": "Bloque rompible",
        "properties": {
            "health": {"label": "Vida", "type": "int", "default": 1},
            "damage": {"label": "Daño", "type": "int", "default": 1},
            "drops": {"label": "Suelta ítems", "type": "bool", "default": True},
        }
    },
    ...
}
```

12 behaviors definidos: `decoration`, `block`, `block_breakable`, `block_pushable`, `block_indestructible`, `tall_grass`, `tree`, `wall`, `gate`, `chest`, `enemy_melee`, `enemy_shooter`, `food`, `spawn`.

### Editor Tab (element_tab.py)

4ta pestaña del Cururo Editor. Layout:

```
┌────────────────────────────────────────────────┐
│ [Nuevo] [Clonar] [Eliminar] [Guardar]  Toolbar │
├──────────────┬─────────────────────────────────┤
│ Lista        │  ID: roca                       │
│ de           │  Nombre: [Roca          ]       │
│ elementos    │  Sprite: [▼ roca        ]  [img]│
│ (scroll)     │  Behavior: [▼ block_breakable]  │
│              │  ───────────────────────────     │
│              │  Propiedades:                    │
│              │    Vida:    [5    ]              │
│              │    Daño:    [1    ]              │
│              │    Drops:   [Sí]                 │
├──────────────┴─────────────────────────────────┤
```

- **Toolbar**: botones en un Panel superior (como las otras pestañas)
- **Lista**: panel izquierdo (240px) con scroll, renderizado manual en `draw()`
- **Editor**: panel derecho con widgets dinámicos reconstruidos en `_rebuild_properties()`
- **Propiedades dinámicas**: se crean/destruyen widgets al cambiar de behavior

### Elements CRUD (elements.py)

```python
def get_all_elements() -> list[str]        # IDs ordenados
def get_element(eid) -> dict | None        # Por ID
def set_element(eid, data)                 # Crear/actualizar
def delete_element(eid)                    # Eliminar
def create_element(eid, sprite_id, name, behavior, properties)
```

Carga `data/elementos.json` en memoria al importar. Las escrituras persisten inmediatamente al archivo.

### Factory Pattern (level_parser.py)

El `LevelParser` reemplazó el antiguo switch de entidades por **fábricas registradas por behavior**:

```python
FACTORY_MAP = {
    "block_breakable": create_breakable_block,
    "block_pushable": create_pushable_block,
    "wall": create_wall,
    "gate": create_gate,
    "enemy_melee": create_enemy_melee,
    ...
}
```

Cada factory recibe las propiedades del elemento (`element["properties"]`) y construye la entidad con esos parámetros. El sprite se resuelve desde `element["sprite_id"]` → `SPRITE_REGISTRY` → archivo PNG.

### Migración desde SPRITE_REGISTRY

Antes: `SPRITE_REGISTRY` tenía `entity` (clase Python hardcodeada) y el `LevelParser` usaba un switch gigante.

Ahora:
- `SPRITE_REGISTRY` es solo catálogo visual (`file`, `display`, `char`)
- `data/elementos.json` tiene 28 elementos con `sprite_id`, `behavior`, `properties`
- El `LevelParser` itera elementos y usa `FACTORY_MAP[behavior]`
- El editor de mapas (`palette.py`) resuelve `element_id → sprite_id` para mostrar la paleta

### Cómo agregar un behavior nuevo
1. Agregar entrada en `BEHAVIORS` en `editor/behaviors.py`
2. Crear factory class/función en `levels/level_parser.py`
3. Registrar en `FACTORY_MAP`
4. (Opcional) Crear elemento en `data/elementos.json` o desde el editor

---

## 9. Sistema de Jefes (Boss Fight)

### Arquitectura

```
editor/boss_fight_types.py  →  editor/boss_data.py  →  data/bosses.json
                                                          ↓
                              entities/boss.py  (Boss._phase_config)
                              managers/combate_manager.py
```

### Fight Types (`editor/boss_fight_types.py`)

Similar a `behaviors.py`: cada fight type define un schema de parámetros por fase.

```python
BOSS_FIGHT_TYPES = {
    "orbital": {
        "label": "Orbital",
        "phase_params": {
            "speed_mult": {"type": "float", "default": 1.0, "label": "Mult. velocidad"},
            "attack_cooldown": {"type": "int", "default": 60, "label": "Cooldown (frames)"},
            "projectile_speed": {"type": "float", "default": 2.0, "label": "Vel. proyectil"},
            "projectile_count_bonus": {"type": "int", "default": 0, "label": "Proyectiles extra"},
            "comestible_chance": {"type": "float", "default": 0.6, "label": "Prob. comestible"},
            ...
        },
        "visual_schema": {
            "trunk_color": {"type": "color", "default": [95, 60, 28], "label": "Color tronco"},
            "eye_color": {"type": "color", "default": [150, 200, 80], "label": "Color ojos"},
            ...
        }
    }
}
```

### Datos (`data/bosses.json`)

Cada entrada tiene:
- `fight_type`: tipo de pelea (define qué parámetros aplican)
- `phases`: array de N fases, ordenadas por `hp_threshold` descendente
- Cada fase: `{hp_threshold, params, visual}`
- Parámetros globales: `vida_maxima`, `proyectiles_necesarios`, `damage_per_cycle`, `color_barra`, `icono`

### Runtime (`entities/boss.py`)

`Boss._phase_config()` busca la fase activa según la vida actual:

```python
@property
def _phase_config(self):
    ratio = self.vida / self.vida_maxima
    for p in self.phases:
        if ratio >= p["hp_threshold"]:
            return p
    return self.phases[-1]
```

`_apply_phase()` sincroniza `self.fase`, `self.velocidad_actual`, `self.tiempo_entre_ataques`, `self.radio` desde la config de fase actual.

`recibir_danio()` llama a `_apply_phase()` después de cada golpe, permitiendo transiciones suaves de fase.

### Editor Tab (`editor/boss_tab.py`)

5ta pestaña con:
- **Lista**: todos los bosses, click para seleccionar
- **Toolbar**: Nuevo, Clonar, Eliminar, Guardar
- **Campos globales**: nombre, fight type (dropdown), vida, proyectiles necesarios, daño/ciclo, icono
- **Fases**: lista colapsable. Cada fase muestra threshold + parámetros dinámicos según fight type
- **Add/Delete phase**: botón +/- por fase

### Cómo agregar un fight type nuevo
1. Agregar entrada en `BOSS_FIGHT_TYPES` en `editor/boss_fight_types.py` con `phase_params` y `visual_schema`
2. El editor renderiza los parámetros automáticamente
3. (Opcional) Implementar la lógica de movimiento/ataque en `entities/boss.py` o una subclase

---

## 10. Sprite Registry

Archivo: `editor/sprite_registry.py`

Registro centralizado de todos los sprites disponibles en el editor (solo catálogo visual, sin lógica de juego).

```python
SPRITE_REGISTRY = {
    "pared": {
        "file": "pared",
        "display": "Pared",
        "char": "*"
    },
    "inicio": {
        "file": "spawn_hero",
        "display": "Inicio",
        "char": "I"
    },
    ...
}
```

28 sprites registrados. Cada entrada mapea a:
- `file`: nombre del archivo PNG (sin extensión) en `assets/`
- `display`: nombre mostrado en la paleta
- `char`: carácter legacy para mapas `.txt`

> **Nota:** Las propiedades `entity` fueron eliminadas — la lógica de juego ahora vive en `data/elementos.json` + behaviors.

---

## 11. Internacionalización

Archivo: `editor/i18n.py`

Sistema simple de traducción con singleton:

```python
class I18n:
    _instancia = None
    
    @classmethod
    def instancia(cls): ...  # Singleton
    
    def set_lang(self, lang): ...  # "es" | "en"
    
    def t(self, key): ...  # Traduce clave del JSON
    
    def fuente(self, size, bold=False): ...
```

Los archivos de locale están en `editor/locales/{lang}.json` con ~130 claves cada uno.

---

## 12. Flujo de Trabajo Principal

### Nuevo Mapa
1. Click "Nuevo mapa" → diálogo con ancho/alto
2. Se crea `MapTab` con Z=0 (visible, opacidad 100)
3. Se crea tab en `_map_tab_bar`
4. Paleta de sprites poblada desde `SPRITE_REGISTRY`

### Editar Mapa
1. Seleccionar sprite de la paleta
2. Click en canvas → coloca sprite en capa activa
3. Agregar capas con "+ Capa" (hasta 5)
4. Cambiar capa activa → click en nombre de capa
5. Ajustar visibilidad/opacidad por capa

### Guardar Mapa
1. Itera `tab.layers`: por cada capa con grid no vacío, escribe `{id}_z{z}.json`
2. Si la capa está vacía y su archivo existe, lo elimina
3. Guarda stacks en `mapas_stacks/{id}_stacks.json`
4. Escanea todas las capas buscando sprite `inicio` para meta
5. Escribe `{id}_meta.json` con spawn

### Editar Sprite
1. Abrir sprite desde lista de assets
2. Seleccionar herramienta (lápiz/borrador/balde/gotero)
3. Ajustar opacidad (solo lápiz)
4. Dibujar sobre canvas expandido
5. Undo/Redo con Ctrl+Z/Y
6. Guardar PNG

### Editar Eventos
1. Seleccionar tile en el mapa (click con sprite seleccionado en paleta)
2. En panel de eventos, agregar trigger, condiciones, acciones
3. Guardar → se escribe `mapas_stacks/{id}_stacks.json`

### Editar Elementos
1. Ir a pestaña "Elementos"
2. Hacer click en un elemento de la lista → se carga en el panel derecho
3. Modificar nombre, sprite, behavior o propiedades
4. Click "Guardar" → persiste en `data/elementos.json`
5. "Nuevo" crea elemento con behavior `decoration` y primer sprite disponible
6. "Clonar" duplica el elemento seleccionado
7. "Eliminar" borra el elemento

### Editar Jefe
1. Ir a pestaña "Jefes"
2. Click en un jefe de la lista → se carga en el panel derecho con campos y fases
3. Modificar nombre, fight type, stats globales
4. En "Fases", click en fase para expandir/colapsar
5. Ajustar threshold y parámetros por fase (velocidad, cooldown, proyectiles, colores, runas)
6. Agregar/quitar fases con botones +/-
7. Click "Guardar" → persiste en `data/bosses.json`

---

## 13. Notas Técnicas

### Canvas `MOUSEBUTTONDOWN` no verifica `collidepoint`
- Bug fijo: el canvas consumía eventos de click aunque el mouse estuviera fuera de su rect
- Fix: agregar `if r.collidepoint(event.pos):` antes de procesar

### Canvas `MOUSEBUTTONUP` retorna False
- El canvas ya no consume eventos de release, permitiendo que otros widgets (botones) los reciban
- `on_mouse_up()` del tool se llama igual para resetear estado

### EraserTool sin atributo `color`
- Se omitió intencionalmente para que `hasattr(tool, 'color')` en sprite_editor.py saltee el sync
- El color picker ya no interfiere con el eraser

### Opacidad en el Canvas
- `alpha=0` → checkerboard (transparente)
- `0 < alpha < 255` → color mezclado con checker (semi-transparente)
- `alpha=255` → color sólido
- Implementado en `_draw_checker_blended()`

### Capas: Z=0 no se elimina
- `remove_layer(0)` retorna `False` inmediatamente
- `add_layer()` busca el primer Z libre en `range(1, MAX_LAYERS)`

### Cooldown de enroscamiento
- `_no_enroscar_hasta`: contador de frames de inmunidad tras desenroscarse
- Previene el ciclo infinito roca-pared (colisión → enroscar → desenroscar → colisión → ...)
- Se decrementa cada frame en `main.py`

### Renderizado de entidades ordenado por Z
- Antes: entidades dibujadas por tipo (rocas después de paredes), ignorando la propiedad `z`
- Ahora: todas las entidades se agrupan por su atributo `z` y se renderizan en orden ascendente
- Esto permite que objetos en Z superior (ej. espinas Z=2) se vean sobre objetos en Z inferior (ej. rocas Z=1)
- Implementado en `main.py` con colección en `_entity_groups` y sorted keys

### Prioridad de colisión: peligrosos antes que bloqueantes
- Antes: se verificaban rocas → bloques acero → paredes (peligrosos al final)
- Ahora: se verifican objetos peligrosos (paredes/espinas) PRIMERO → si alguno mata (`resultado == "mata"`), retorna inmediatamente sin evaluar bloqueantes
- Si no hay muerte, se evalúan rocas y bloques acero normalmente
- Fix en `colision_manager.py`

### z_layer en _make_bloqueante
- Antes: `_make_bloqueante()` no recibía `z_layer`, por lo que rocas/bloques siempre tenían `z=0` sin importar la capa del grid donde se colocaran
- Ahora: la lambda factory pasa `z` y `_make_bloqueante()` asigna `entity.z = z_layer` después de crear la entidad
- No requiere modificar los constructores de `Roca`, `BloqueAcero`, etc.

---

## 14. Pendientes / Próximos

### Sistema de Items en HUD
Poder mostrar items del inventario en pantalla (similar al contador de escamas), con:
- Editor visual del HUD en Cururo Editor
- Registro de qué items mostrar (por mapa, por evento, o global)
- Contadores sincronizados con `estado.inventario`
- Permitir condiciones `has_item` con items custom visibles en HUD

### Gate System v2
- `change_map` con parámetro de spawn position (actualmente solo usa el sprite `inicio` del destino)
- Acción `remove_stack` para eliminar el stack actual in-memory
- Persistencia de `tile_overrides` y `flags` entre sesiones (save/load)

---

## 15. Multi-Tile Sprites — Plan de Implementación

### Visión General

Soportar sprites que ocupen múltiples tiles (20×40, 40×20, 40×40). Cada sub-tile se guarda como PNG individual (ej: `arbol_a.png`, `arbol_b.png`) y se asigna a una capa Z independiente para efectos de profundidad.

### Pipeline completo

```
Sprite Editor          Elementos              Mapa                Juego
─────────────────────────────────────────────────────────────────────
Dibujar 40×20     →   Definir sub-tiles   →  Pintar en grid   →  Renderizar
Auto-split en          Asignar Z por           ocupa W×H celda    cada sub-tile
_a, _b PNGs           sub-tile                                    en su Z
                    → Asignar behavior
                      por sub-tile
```

---

### Fase 1: Sprite Editor — Tamaño variable y auto-split

#### 1a. Selector de tamaño

Agregar en `editor/sprite_editor.py` un selector en el panel derecho (combo o botones) con opciones:

| Opción | Tamaño px | Sub-tiles | Sufijos |
|--------|-----------|-----------|---------|
| 1×1 | 20×20 | 1 | (ninguno) |
| 1×2 | 20×40 | 2 | _a (arriba), _b (abajo) |
| 2×1 | 40×20 | 2 | _a (izquierda), _b (derecha) |
| 2×2 | 40×40 | 4 | _a (0,0), _b (0,1), _c (1,0), _d (1,1) |

#### 1b. Canvas

- `_surface` se crea al tamaño seleccionado (ej: 40×40 px)
- Canvas renderiza con zoom sobre ese tamaño (ya funciona)
- Grid opcional de 20×20 para guiar al diseñador

#### 1c. Auto-split al guardar

Al guardar como `arbol.png` (40×40):

```
arbol.png (40×40)
├── arbol_a.png (20×20)  — fila 0, col 0
├── arbol_b.png (20×20)  — fila 0, col 1
├── arbol_c.png (20×20)  — fila 1, col 0
└── arbol_d.png (20×20)  — fila 1, col 1
```

Al guardar como `arbol.png` (20×40):

```
arbol.png (20×40)
├── arbol_a.png (20×20)  — fila 0, col 0
└── arbol_b.png (20×20)  — fila 1, col 0
```

#### 1d. Registro de sprites

`editor/sprite_registry.py` registra automáticamente cada sub-tile como entrada individual:

```python
"arbol_a": {"file": "arbol_a", "display": "Árbol A", "char": "a"},
"arbol_b": {"file": "arbol_b", "display": "Árbol B", "char": "b"},
```

También se registra una entrada "compuesta" para que la paleta del mapa lo muestre como un solo ítem:

```python
"arbol": {"file": "arbol", "display": "Árbol", "multi": True, "tiles": ["arbol_a", "arbol_b"]}
```

---

### Fase 2: Elementos — Definición multi-tile

#### 2a. Nuevo behavior `multi_tile`

En `editor/behaviors.py`:

```python
"multi_tile": {
    "label": "Multi Tile",
    "target_list": None,  # se resuelve por sub-tile
    "properties": {
        "tile_width": {"label": "Ancho (tiles)", "type": "int", "default": 1},
        "tile_height": {"label": "Alto (tiles)", "type": "int", "default": 2},
        "tiles": {"label": "Sub-tiles", "type": "multi_tile_config"}
    }
}
```

#### 2b. Configuración de sub-tiles

Cada sub-tile en el elemento define:

```json
{
  "sprite_id": "arbol",
  "name": "Árbol Grande",
  "behavior": "multi_tile",
  "properties": {
    "tile_width": 1,
    "tile_height": 2,
    "tiles": [
      {"offset": [0, 0], "z": 2, "behavior": "decorative", "properties": {}},
      {"offset": [0, 1], "z": 0, "behavior": "bloqueante", "properties": {"solid": true}}
    ]
  }
}
```

#### 2c. Editor de elementos — pestaña "Sub-tiles"

En `editor/element_tab.py`:
- Cuando se selecciona behavior `multi_tile`, se renderiza una tabla de sub-tiles
- Cada fila: offset X, offset Y, sprite (dropdown), Z layer, behavior, propiedades
- Botones + y — para agregar/quitar sub-tiles
- Auto-generación por defecto: al elegir tile_width × tile_height, se crean los N sub-tiles con nombres secuenciales

---

### Fase 3: Map Editor — Pintado multi-celda

#### 3a. Al pintar un elemento multi-tile

En `editor/map_editor.py`:
- Cuando el elemento seleccionado en la paleta tiene `behavior: "multi_tile"`:
  - Al hacer click en celda (gx, gy), se pintan todas las celdas que ocupa
  - Cada celda guarda el element_id + offset del sub-tile
  - Se verifica que las celdas destino estén libres (o se sobreescriben)

#### 3b. Formato de almacenamiento en grid

El grid actual guarda: `"x,y": "element_id"`

Para multi-tile, se necesita saber qué sub-tile va en cada celda ocupada:

```json
{
  "version": 2,
  "ancho": 40,
  "alto": 30,
  "grid": {
    "5,10": "arbol",
    "5,11": "arbol"
  },
  "multi_tiles": {
    "arbol_5,10_5,11": {"root": [5, 10], "element_id": "arbol", "tile_width": 1, "tile_height": 2}
  }
}
```

O más simple, almacenar en cada celda ocupada el element_id con un flag de que es parte de un multi-tile:

```json
{
  "5,10": "arbol",
  "5,11": "arbol_sub"
}
```

Donde `arbol_sub` es un elemento generado automáticamente para la parte inferior.

**Decisión**: La opción más limpia es que la celda raíz guarda el element_id y las celdas hijas guardan un elemento auto-generado con nombre `{element_id}_{suffix}`. Así no se necesita un campo extra en el JSON.

Al guardar el mapa, el editor expande el multi-tile en celdas individuales con sufijos. Al cargar, el sistema reconoce los sufijos y sabe cómo renderizar.

#### 3c. Renderizado en editor

- Cada sub-tile se renderiza en su celda con el sprite correspondiente
- Overlay visual: borde alrededor del grupo multi-tile para mostrar que es una unidad
- Las capas Z se respetan en el renderizado del editor (ya funciona)

---

### Fase 4: Level Parser — Runtime

#### 4a. Parseo de multi-tiles

En `levels/level_parser.py`:
- Al encontrar un element_id con sufijo (ej: `arbol_b`), se busca el elemento base (`arbol`)
- Se determina el behavior y la Z desde la configuración del sub-tile
- Se crea la entidad correspondiente en la lista correcta y con la Z adecuada

#### 4b. Creación de entidades

Para el ejemplo del árbol 20×40:

```
arbol_a (offset [0,0], Z=2, decorative)
  → no se crea entidad (decorative, solo visual)
  → se renderiza en Z=2 (por encima del jugador)

arbol_b (offset [0,1], Z=0, bloqueante)
  → se crea ObjetoBloqueante o Arbol
  → se renderiza en Z=0 (a nivel del suelo)
  → colisiona con el jugador
```

#### 4c. Renderizado en juego

El sistema de capas Z ya existe (Z=0 a Z=4). Cada sub-tile se renderiza en su Z asignada. El jugador (que está en Z=1 o Z=0 por defecto) queda detrás de sub-tiles con Z>1.

---

### Resumen de archivos a modificar

| Archivo | Cambio |
|---------|--------|
| `editor/sprite_editor.py` | Selector de tamaño, canvas variable, auto-split al guardar |
| `editor/sprite_registry.py` | Registro de sub-tiles, soporte `multi: true` |
| `editor/behaviors.py` | Nuevo behavior `multi_tile` |
| `editor/elements.py` | CRUD con soporte de sub-tiles |
| `editor/element_tab.py` | UI para configurar sub-tiles (tabla, Z, behavior) |
| `editor/widgets/palette.py` | Mostrar preview del multi-tile completo |
| `editor/map_editor.py` | Pintado multi-celda, guardado expandido |
| `editor/map_tab.py` | Modelo de datos para multi-tiles en el mapa |
| `levels/level_parser.py` | Parseo de sub-tiles, routing por behavior individual |
| `game_state.py` | Carga de entidades multi-tile |
| `data/elementos.json` | Elementos ejemplo con multi-tile |
