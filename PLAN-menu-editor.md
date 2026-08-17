# Plan: Mejoras al Editor de Menús (MenuTab)

> Archivo de referencia. Estado: Fases 1 y 3 implementadas (2026-08-17).

## 1. Contexto y definición

El editor de menús (`editor/menu_panel.py` + `editor/menu_data.py`) permite definir las
pantallas de menú del juego (inventario, opciones, relaciones…) sin tocar código.

**Modelo de datos** (`data/menus.json`):

```
menu -> { id, tecla, titulo, apartados[] }
apartado -> { id, nombre, tipo, config? }
config -> { items[] }  (tipos lista/opciones)
       -> { flags[] }  (tipo stats_flags)
item -> { id, nombre, descripcion, accion {tipo, params} }
```

**Tipos de renderer actuales** (`TIPO_OPTIONS`): lista_habilidades, lista_consumibles,
equipo, lista, opciones, controles, stats_flags.

**Acciones**: formato `stack_manager` (`{tipo, params}`). El dispatcher de menú
(`input_manager._ejecutar_accion_menu`) maneja `equipar_habilidad`, `usar_item`,
`equipar_slot`, `desequipar_slot`; el resto va a `stack_manager.ejecutar_ahora`
(show_message, give_item, set_flag, add_flag, clear_flag, change_map, iniciar_dialogo,
dialogo_inline, dialogo_tree, spawn_entity, remove_sprite, replace_sprite, etc.).

**Estado actual**: CRUD completo y funcional (verificado headless). Punto débil: el
contenido de items/config se edita como **JSON crudo**, no hay preview, y faltan
validaciones.

## 2. Fases priorizadas

### Fase 1 — Editor visual de items y acciones (ALTA prioridad) ✅ Implementada

**Problema**: hoy los items de un apartado `lista`/`opciones` y las flags de
`stats_flags` se editan pegando JSON en un `UITextEntryLine`. Un creador no técnico lo
rompe fácilmente y un JSON inválido se guarda y rompe el runtime.

**Qué hacer**:
- Grilla de items (tabla) en el editor de apartado: ver lista, seleccionar, y botones
  Nuevo / Duplicar / Eliminar.
- Formulario de item por campos (no JSON): `id`, `nombre`, `descripcion`.
- Selector de **acción desde lista de acciones conocidas** (dropdown), y campos
  dinámicos de `params` según la acción elegida:
  - `show_message` -> `mensaje`
  - `give_item`/`remove_item` -> `item`, `cantidad`
  - `set_flag`/`clear_flag` -> `flag`, `valor`
  - `add_flag` -> `flag`, `cantidad`
  - `change_map` -> `nivel`, `exit_id`
  - `iniciar_dialogo`/`dialogo_tree` -> `dialogo_id`
  - `dialogo_inline` -> `lineas`, `quien`
  - acciones de menú: `usar_item`, `equipar_habilidad`, `equipar_slot`,
    `desequipar_slot` -> `item`/`habilidad`/`slot`
- Igual para flags de `stats_flags`: grilla con `id`/`nombre`/`default`.

**Archivos**: `editor/menu_panel.py` (sub-panel de items), `editor/menu_data.py`
(validación de estructura), nuevo `editor/actions_data.py` (registro de acciones
conocidas + esquema de params).

**Criterios de aceptación**:
- Crear un item con acción `show_message` sin tocar JSON genera la estructura correcta.
- Editar la acción cambia los campos de params al momento.
- Guardar siempre produce `menus.json` válido.

**Verificación**: test headless que construye/edita items y valida el JSON escrito.

**Hecho (2026-08-17)**:
- `editor/actions_data.py` creado (registro de acciones con esquema de params).
- `_build_config_editor` + `_build_item_form` + `_build_flag_form` reemplazan el JSON
  crudo: lista de items/flags con botones +/X/Dup y formulario por campos.
- Selector de acción con params dinámicos (text/int/float/bool).
- Fix del flujo add/dup/del: el formulario se reconstruye antes de guardar para no
  pisar el item nuevo con el formulario del item anterior.
- `_sel_option` helper: tolera `selected_option` como str o tuple de pygame_gui.
- Verificado headless (items con show_message/give_item/sin acción, add/dup/del,
  flags, JSON válido en disco). 86 tests del runtime siguen verdes.

---

### Fase 2 — Vista previa en vivo (ALTA prioridad) ✅ Implementada

**Problema**: no se puede ver cómo quedará el menú hasta correr el juego.

**Qué hacer**:
- Panel de preview que instancie los renderers reales del runtime
  (`orm/systems/ui/components/inventory_panels.py`) con el menú actual en memoria.
- Reutilizar `Inventario`/`InputManager` en modo simulado (o un adaptador de estado)
  para dibujar el apartado activo.
- Recargar el preview en cada cambio relevante (tipo, items, config).

**Archivos**: `editor/menu_panel.py` (panel de preview), `editor/menu_preview.py`
(nuevo, adaptador estado+renderer).

**Criterios de aceptación**:
- Cambiar el tipo del apartado actualiza el preview sin guardar.
- El preview no modifica el proyecto real (estado simulado).

**Hecho (2026-08-17)**:
- `editor/menu_preview.py` (nuevo): `MenuPreview` dibuja el menú con los renderers
  reales del runtime (`InventoryMenu.draw`) sobre una surface del tamaño del juego
  (configs.ANCHO/ALTO). `_EstadoPreview` simula el estado con un adaptador de `menu`
  apuntando al menú en memoria y usa `Inventario()`/`SistemaHabilidades()` reales del
  proyecto (con fallback a fakes para no crashear). Si el runtime no está cargado,
  muestra un aviso en lugar de fallar.
- `menu_panel.py`: botón "Vista"/"Editar" en la toolbar que alterna el modo preview.
  En modo preview se muestra la lista de apartados arriba y la vista previa (escalada
  al tamaño del panel, con proporción del juego) abajo; se re-renderiza cuando cambia
  el menú/apartado/items (firma JSON) sin guardar.
- Verificado headless: render de lista, stats_flags, habilidades, consumibles y equipo;
  el preview refleja cambios de items sin tocar disco; toggle de ida y vuelta OK.

---

### Fase 3 — Validaciones (MEDIA) ✅ Implementada

**Problema**: hoy se pueden guardar menús con teclas repetidas, ids duplicados o JSON
malformado.

**Qué hacer**:
- Tecla única entre menús (aviso y bloqueo de guardado si hay conflicto).
- Ids únicos de menú y de apartado.
- Marcar en rojo el JSON/config inválido en lugar de guardarlo.
- Título y tecla obligatorios.
- Mensaje de error/OK al guardar (ya existe `_save_btn`; añadir feedback visible).

**Archivos**: `editor/menu_panel.py`, `editor/menu_data.py`.

**Criterios de aceptación**: no se puede crear un estado inválido persistido.

**Hecho (2026-08-17)**:
- `menu_data.validar_menu(menu, todos)` devuelve `(bloqueantes, advertencias)`:
  - Bloqueantes: tecla duplicada con otro menú, ids de apartado/item/flag duplicados.
  - Advertencias: sin tecla, sin título, sin apartados.
- `_save_menu` valida antes de escribir: con bloqueantes NO guarda y muestra el error;
  con advertencias guarda y lo avisa; sin problemas muestra "✓ Guardado".
- Label de estado en la toolbar con el resultado del último guardado.
- La edición de config ya no es JSON (Fase 1), así que el punto "JSON inválido" quedó
  sin efecto.
- Verificado headless: tecla duplicada bloqueada (disco intacto), advertencia por
  título vacío, guardado OK, y tests unitarios de `validar_menu`.

---

### Fase 4 — Reordenar apartados (MEDIA)

**Problema**: hoy solo se agregan/eliminan apartados (+/X); no se puede cambiar el
orden, y el runtime los recorre en orden (TAB).

**Qué hacer**: botones ↑/↓ en la lista de apartados que reordenan `apartados[]`.

**Archivos**: `editor/menu_panel.py`.

---

### Fase 5 — Mapeo de controles (MEDIA)

**Problema**: el renderer `controles` es de solo lectura (lee `data/controles.json`);
un usuario querrá definir/remapear teclas desde el editor.

**Qué hacer**: editor de bindings (acción -> tecla) que escriba `data/controles.json`,
con preview del renderer (Fase 2) y validación de teclas duplicadas.

**Archivos**: `editor/menu_panel.py` (o sub-pestaña), nuevo `editor/controls_data.py`.

---

### Fase 6 — Más tipos de renderer / stats dinámicos (BAJA)

**Problema**: `stats_flags` solo muestra flags del estado; no hay stats con valores
(nivel, progreso, inventario…).

**Qué hacer**: definir nuevos tipos de renderer en el runtime
(`orm/systems/ui/components/inventory_panels.py`) y registrarlos en `TIPO_OPTIONS` +
`CONFIG_LABELS`. Ej.: `stats` con items `{label, valor}` donde `valor` puede ser una
referencia (`estado.<campo>` o flag).

**Archivos**: `orm/systems/ui/components/inventory_panels.py`, `orm/systems/menu.py`,
`editor/menu_panel.py`.

---

### Fase 7 — Plantillas y flujo (BAJA)

**Qué hacer**:
- Crear un menú desde plantillas completas (inventario, opciones, relaciones) en vez
  de siempre `1 apartado lista`.
- Elegir el menú inicial / orden de los menús.
- Vincular apertura de menú a eventos/escenas (acción `abrir_menu {menu_id}` en
  `stack_manager`).

**Archivos**: `editor/menu_panel.py`, `orm/systems/stack_manager.py`,
`editor/templates/snake_rpg/data/menus.json`.

## 3. Fuera de alcance (por ahora)

- Reescritura del sistema de renderers (el contrato `PanelApartado` + `RENDERERS` se
  mantiene).
- Editor visual de la apariencia (estilos/colores) de los menús.
- Soporte de múltiples proyectos simultáneos en el mismo editor.

## 4. Notas técnicas

- El registro de "acciones conocidas" debe derivarse de
  `orm/systems/stack_manager.py: _ejecutar_accion` y
  `orm/handlers/input_manager.py: _ejecutar_accion_menu` (fuente única de verdad).
- La Fase 2 (preview) depende de que el editor tenga el runtime en `sys.path` (ya se
  agrega `orm/` al cargar proyecto) y de usar `SDL_VIDEODRIVER=dummy` o una surface
  aparte para no interferir con la ventana del editor.
- Toda edición de `data/` sigue la regla: avisar antes de tocar archivos existentes;
  los archivos nuevos no pisan datos del usuario.

## 5. Orden de trabajo sugerido

1. Fase 1 (items/acciones) — base para todo lo demás. ✅
2. Fase 3 (validaciones) — junto a la Fase 1. ✅
3. Fase 2 (preview). ✅
4. Fase 4 (reordenar).
5. Fases 5-7 cuando el usuario las pida.