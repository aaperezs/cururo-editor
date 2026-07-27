# Cururo Editor

Editor visual Pygame para el juego Orm: La Serpiente Enroscada.

**Entry point:** `main.py` | **Ventana:** 1100×700 | **Paneles:** 8

---

## AI Agent — Quick Reference

### Directorio Clave

| Ruta | Qué es |
|------|--------|
| `main.py` | `EditorApp` — loop principal, `MenuManager` con TabBar + 5 paneles |
| `project.py` | Sistema de proyectos (Project class, path resolution) |
| `project_dialog.py` | Diálogo de selección de proyecto al inicio |
| `i18n.py` | Internacionalización ES/EN (singleton) |
| `sprite_editor.py` | `SpriteEditorPanel` — editor de píxeles 20×20 con zoom |
| `map_editor.py` | Editor de mapas con capas dinámicas (1-5) |
| `event_editor.py` | Editor de stacks (eventos por tile) |
| `element_tab.py` | `ElementTab` — editor de elementos (behaviors + propiedades, rename) |
| `elements.py` | CRUD loader para `data/elementos.json` |
| `behaviors.py` | Definiciones de 12 behaviors con schemas de propiedades |
| `animations.py` | CRUD para `data/animations.json` (animaciones + glow) |
| `widgets/animation_panel.py` | `AnimationPanel` — editor visual de animaciones |
| `boss_tab.py` | `BossTab` — editor de jefes con fases colapsables |
| `boss_data.py` | CRUD para `data/bosses.json` |
| `boss_fight_types.py` | Schemas de fight types con parámetros por fase |
| `map_tab.py` | Modelo de datos del mapa (`MapTab`, `LayerState`) |
| `sprite_registry.py` | Catálogo visual de 28 sprites (solo metadatos) |
| `panels/` | Paneles base (`BasePanel`) |
| `widgets/` | Sistema de widgets UI (20 widgets) |
| `tools/` | Herramientas de dibujo (pencil, eraser, bucket, eyedropper) |
| `locales/` | `es.json` / `en.json` (~130 claves cada uno) |

### Widget System

```
Widget (rect, visible, enabled, handle_event, draw)
  └── Container (children[], add, remove, clear)
        ├── Button, Label, Panel, Canvas
        ├── Slider, ColorPicker, Palette
        ├── TabBar, LayerPanel, Scrollable
        ├── TextInput, TextArea, Dropdown
        ├── PropertyEditor, EventEditorWidget
        ├── Dialog (modal), MenuManager
        └── BasePanel (posicionamiento automático y=30)
```

**Handle event:** `Container` propaga a hijos en orden inverso (z-index)
**Draw:** `Container` dibuja hijos en orden directo

### Panel System

Todos los paneles heredan de `BasePanel` (`editor/panels/base_panel.py`):
- Ocupan todo el espacio disponible del MenuManager (sin offset de TabBar)
- `set_size(w, h)` redimensiona y reconstruye la UI del panel
- Cada panel recibe dimensiones completas del padre

`MenuManager` (`editor/widgets/menu_manager.py`):
- Menú estilo Windows: Archivo, Editar, Arte, Herramientas, Ejecutar, Ayuda
- Secciones colapsables con MenuDropdown, atajos de teclado
- `register_tab(label_key, panel_class)`, `get_active_panel()`, `handle_event()`/`draw()`
- Locale keys: `tab.sprites`, `tab.elements`, `tab.abilities`, `tab.items`, `tab.bosses`, `tab.maps`, `tab.events`, `tab.animations`
- Atajos: Ctrl+1 Sprites, Ctrl+2 Mapas, Ctrl+3 Animaciones, Ctrl+R Ejecutar, Ctrl+S Guardar

### Cómo crear una animación

1. Ir a **Arte → Animaciones** (Ctrl+3)
2. Nueva → poner nombre, frames (sprite IDs), intervalo
3. Activar **Aurea** para efecto de brillo: elegir color (predefinidos o RGB), radio, alpha
4. Guardar
5. En el elemento deseado, escribir el nombre de la animación en la propiedad `Animacion`

### Cómo renombrar un elemento

1. En Elementos, seleccionar el elemento a renombrar
2. Click **Renombrar** en la barra de herramientas
3. Ingresar el nuevo ID
4. El sistema actualiza `elementos.json` y todos los mapas que referencian el ID anterior

### Cómo agregar una pestaña nueva

1. Crear clase que herede de `BasePanel` en `editor/panels/`
2. Agregar locale key `tab.<name>` en `editor/locales/*.json`
3. Registrar en `editor/main.py` vía `PANEL_CLASSES` + `_crear_menu()`

### Cómo agregar una herramienta de dibujo nueva

1. Crear clase con `on_mouse_down(surface, pos, color)`, `on_mouse_move(...)`, `on_mouse_up(...)`
2. Sin atributo `color` si no necesita sync con color picker (ej: EraserTool)
3. Agregar a la toolbar en `sprite_editor.py`

### Cómo agregar un behavior nuevo

1. Agregar entrada en `BEHAVIORS` en `behaviors.py` con `label` + `properties` schema
2. El editor de elementos renderiza las propiedades automáticamente
3. (Opcional) Factory en `orm/levels/level_parser.py` para runtime

### Documentación Relacionada

- `TECH-DESIGN.md` — Arquitectura detallada (widgets, mapas, elementos, bosses, multi-tile)
- `../orm/README.md` — Guía del juego Orm
- `../orm/GDD.md` — Game Design Document del juego
