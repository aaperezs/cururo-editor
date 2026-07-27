# Cururo Editor — Design System

## 1. Paleta Base (Modo Oscuro)

| Token | RGBA | Uso |
|-------|------|-----|
| `COL_BG` | `(35, 40, 45)` | Fondo de panel (nivel -1) |
| `COL_BORDER` | `(55, 60, 65)` | Líneas divisorias, bordes de layout |
| `COL_CARD_BG` | `(45, 50, 58)` | Tarjeta de evento (nivel 0) |
| `COL_CARD_BORDER` | `(60, 65, 75)` | Contorno de tarjeta |
| `COL_FIELD_BG` | `(50, 55, 65)` | Inputs, dropdowns cerrados |
| `COL_FIELD_BORDER` | `(70, 75, 85)` | Borde de inputs |
| `COL_EDIT_BG` | `(60, 80, 120)` | Foco activo / cursor |
| `COL_ACCENT` | `(70, 130, 200)` | Botones primarios, hover |
| `COL_TEXT` | `(220, 220, 220)` | Texto principal |
| `COL_TEXT_DIM` | `(160, 165, 175)` | Texto secundario, labels |
| `COL_GREEN` | `(60, 120, 60)` | Éxito, toggle on |
| `COL_RED` | `(180, 60, 60)` | Destrucción, eliminar |
| `COL_OVERLAY` | `(0, 0, 0, 160)` | Fondo modal / dropdown backdrop |

## 2. Grilla de Layout

```
Padding general de panel:    10px  (r.x+10 / r.w-20)
Padding interno de tarjeta:   8px  (desde borde de card a contenido)
Altura de fila estándar:     22px
Margen entre tarjetas:       12px  (separación vertical)
Indent cond/act:             10px  + línea guía vertical 1px
Trigger dropdown ancho:      100px  (fijo)
ID label ancho:               30px  (fijo)
ID field: restante del ancho de tarjeta
```

## 3. Jerarquía de Componentes

```
Panel Background (COL_BG, nivel -1)
├── Header fijo
│   ├── Texto: "Elemento @ (x,y) (Z=0)" [COL_TEXT]
│   └── Botón [Set Spawn / Remove Spawn] (ancho completo, COL_FIELD_BG)
└── Área scrolleable
    ├── Tarjeta Evento #0 (COL_CARD_BG, nivel 0)
    │   ├── Dropdown Trigger [contact ▼] (100px, COL_ACCENT bg)
    │   ├── Checkbox [✔ Once] (14x14px, COL_GREEN si activo)
    │   ├── Botón [X] (22x22px, COL_RED solo hover)
    │   ├── ID: [_______________] (30px label + field)
    │   ├── Condiciones
    │   │   ├── [escamas ▼] [>=] [1]  [X]
    │   │   │   (indent 10px, línea guía a izquierda)
    │   │   └── [+ Condición] (COL_ACCENT en hover)
    │   ├── Acciones
    │   │   ├── [show_message ▼] [mensaje...]  [X]
    │   │   │   (same indent)
    │   │   └── [+ Acción]
    │   └── ────────────────────────────
    ├── Tarjeta Evento #1
    ├── ...
    └── [+ Agregar Evento] (COL_GREEN, ancho completo)
```

## 4. Comportamiento (Hover / Focus / Z-Index)

- **Delete X**: Fondo `COL_RED` sólido solo cuando el mouse está sobre él. Normalmente fondo transparente, texto rojo apagado.
- **+ buttons**: Texto cambia a `COL_ACCENT` en hover, resto del tiempo `COL_TEXT`.
- **Dropdown**: Renderizado al final de `draw()` para que flote sobre todas las tarjetas (z-index máximo).
- **Inline edit**: Fondo `COL_EDIT_BG` con cursor parpadeante (`|`) en campo activo.

## 5. Scrollbar (Estilo Propio)

```
Track:  COL_FIELD_BG (fondo)
Thumb:  COL_ACCENT (arrastre) / blue-400 (normal)
Ancho:  12px
Mínimo: 16px de alto
Snap:   Scroll con wheel (event.y * 20)
```

## 6. Convenciones de Código

1. Toda constante de color se define como tupla RGB en el módulo.
2. La altura de un componente se calcula en `_card_height()` y se refleja en el renderizado.
3. Todo padding es `10px` desde el borde del panel padre.
4. El orden de draw debe ser: fondo → header → cards → dropdowns flotantes.
5. `_find_click_target()` es el único punto de entrada para determinar qué se clickeó.
