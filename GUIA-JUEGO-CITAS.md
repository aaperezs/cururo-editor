# Guía: Juego de citas (Novela Visual)

Esta guía explica cómo crear un **juego de citas / novela visual** con el editor
**Cururo** y ejecutarlo con el runtime de Orm. El contenido se edita visualmente
en el editor y se guarda como JSON en la carpeta `data/` del proyecto.

---

## 1. Crear un proyecto de novela visual

1. Ejecuta el editor:

   ```
   python editor/main.py
   ```

2. Pulsa **Ctrl+N** (o menú *Archivo → Nuevo Proyecto*).
3. En el diálogo *Nuevo Proyecto*:
   - **Nombre**: por ejemplo `Mi Cita`.
   - **Categoría**: elige **Novela Visual**.
   - **Carpeta destino**: donde se creará la carpeta del proyecto.
4. El editor copia la plantilla `editor/templates/visual_novel/` con:
   - `cururo.json` → categoría `visual_novel`, resolución alta y pantalla de título activa.
   - `data/scenes.json`, `data/dialogos.json`, `data/personajes.json`,
     `data/assets.json`, `data/minijuegos.json`, `data/audio.json`.
   - `assets/` → un fondo de ejemplo (`fondo_ejemplo.png`), 6 retratos de un
     personaje de ejemplo (`assets/personajes/runa_*.png`) y sonidos de ejemplo.

Estructura típica de un proyecto:

```
Mi Cita/
├── cururo.json          # Configuración del proyecto (categoría, pantallas)
├── assets/              # Imágenes y sonidos (PNG/WAV/OGG/MP3)
│   └── personajes/      # Retratos: <personaje>_<expresion>.png
└── data/
    ├── assets.json      # Registro de assets (ID → archivo)
    ├── personajes.json  # Personajes y sus retratos
    ├── dialogos.json    # Diálogos + árboles de diálogo
    ├── scenes.json      # Capítulos, escenas y pantalla de título
    ├── minijuegos.json  # Minijuegos (recolección / timing / puzzle)
    └── audio.json       # Música y efectos de sonido
```

---

## 2. Paneles disponibles

Un proyecto *Novela Visual* tiene estas pestañas (en este orden):

| Pestaña | Qué contiene |
|---------|--------------|
| **Scripts** | Funciones de Python personalizadas (opcional) |
| **Diálogos** | Diálogos y su árbol de ramas |
| **Personajes** | Personajes y retratos por emoción |
| **Assets** | Imágenes y sonidos importados |
| **Escenas** | Capítulos, escenas y pantalla de título |
| **Minijuegos** | Minijuegos con premios en flags |
| **Audio** | Canciones (BGM) y efectos (SFX) |

---

## 3. Assets (imágenes y sonidos)

### Tipos de asset

| Tipo | Uso |
|------|-----|
| Fondo | Imagen de fondo a pantalla completa (`background`) |
| Personaje | Retrato de personaje (`character`) |
| CG Ilustración | Ilustración especial (p. ej. final) |
| BGM | Música de fondo |
| SFX | Efecto de sonido |

### Importar un asset

1. Pestaña **Assets** → botón *Importar*.
2. Elige el archivo e introduce **ID** y **Nombre**.
3. El archivo se copia a `assets/<id>.png` (o `.wav`/`.ogg`/`.mp3`).

### Regla de oro de los retratos

El runtime de la VN busca los retratos en la subcarpeta
`assets/personajes/` con el nombre **`<personaje>_<expresion>.png`**.
El importador copia el archivo en la raíz de `assets/`, así que para que un
retrato se vea en el juego:

- Coloca el PNG en `assets/personajes/`, por ejemplo
  `assets/personajes/ana_feliz.png`, **o**
- importa el asset normal y luego mueve el archivo a `assets/personajes/`
  (y, si quieres, corrige el campo `archivo` a `personajes/ana_feliz.png`).

Expresiones soportadas: `normal`, `feliz`, `triste`, `enojado`, `sonrojado`,
`sorpresa`. No hace falta tener todas, pero el ejemplo incluye las 6.

> El fondo inicial con el que arranca el juego es `assets/fondo_ejemplo.png`.
> Puedes reemplazar ese archivo o cambiar de fondo al inicio con la acción
> `cambiar_fondo`.

---

## 4. Personajes

En la pestaña **Personajes** crea cada personaje de la cita:

- **ID**: identificador sin espacios (ej. `ana`). Coincide con la parte de
  `assets/personajes/ana_*.png`.
- **Nombre**: nombre visible en los diálogos (ej. *Ana*).
- **Retratos**: asigna a cada emoción el retrato correspondiente.

---

## 5. Diálogos y árbol de diálogo

Los diálogos son el corazón del juego. Cada diálogo tiene un **ID con formato
`personaje/contexto`**, por ejemplo `ana/saludo` o `ana/parque`.

1. Pestaña **Diálogos** → *Nuevo diálogo*: ID `ana/saludo`, título *Saludo*.
2. Pulsa el botón **Árbol** para abrir el editor de árbol.
3. El nodo de entrada es `start`. Ve añadiendo nodos y conectándolos con el
   campo *Siguiente*.

> **Importante:** el runtime de la VN solo ejecuta los diálogos que tienen un
> **árbol de diálogo** (`nodes`). Un diálogo sin árbol no mostrará nada.

### Tipos de nodo

| Tipo | Campos | Comportamiento |
|------|--------|----------------|
| **Diálogo** | `Texto`, `Quien` (hablante; vacío usa el personaje del diálogo), `Siguiente` | Muestra un texto y espera **ESPACIO/ENTER** |
| **Opción** | Varias opciones (cada una con texto y destino) | Muestra el menú de opciones; el jugador elige con ↑/↓ + ENTER |
| **Condición** | `flag`, `operador`, `valor`, `Siguiente` (si se cumple) y `Siguiente (false)` | Ramifica según un flag |
| **Acción** | `Acción` (desplegable) + `Params (flag=valor)` + `Siguiente` | Ejecuta una acción y continúa |
| **Salto** | `Destino` (`personaje/contexto`) | Salta a otro diálogo; vacío termina la conversación |

Ejemplo de árbol de cita:

```
start ──► (dialogo) "¡Hola! ¿Vamos al parque?" ──► (opcion)
  opción "Sí, claro"          ──► +afecto ──► (dialogo) "¡Qué bien!" ──► ...
  opción "Mejor otro día"     ──► (dialogo) "Qué pena..." ──► ...
```

---

## 6. Acciones disponibles

En un nodo **Acción** elige el tipo y escribe los parámetros como
`clave=valor,clave2=valor2`.

| Acción | Params | Ejemplo |
|--------|--------|---------|
| `cambiar_fondo` | `sprite_id`, `modo` (fill/fit/center) | `sprite_id=fondo_parque,modo=fill` |
| `mostrar_personaje` | `personaje_id`, `posicion` (izquierda/centro/derecha), `expresion` | `personaje_id=ana,posicion=centro,expresion=feliz` |
| `ocultar_personaje` | `personaje_id` | `personaje_id=ana` |
| `ocultar_todos_personajes` | *(sin parámetros)* | |
| `play_bgm` | `asset_id`, `fade_ms` | `asset_id=bgm_cafe,fade_ms=500` |
| `stop_bgm` | `fade_ms` | `fade_ms=300` |
| `play_sfx` | `asset_id` | `asset_id=sfx_click` |
| `set_bgm_volume` | `volumen` (0.0–1.0) | `volumen=0.6` |
| `set_sfx_volume` | `volumen` (0.0–1.0) | `volumen=0.8` |
| `set_flag` | `flag`, `valor` | `flag=afecto_ana,valor=true` |
| `add_flag` | `flag`, `cantidad` | `flag=afecto_ana,cantidad=2` |
| `clear_flag` | `flag` | `flag=afecto_ana` |
| `iniciar_minijuego` | `minijuego_id` | `minijuego_id=cita_bowling` |
| `ir_a_escena` | `capitulo`, `escena` | `capitulo=1,escena=2` |
| `run_script` | `function_name`, `args` | `function_name=mi_funcion,args=1` |
| `fin_demo` | *(sin parámetros)* | Termina la partida |

---

## 7. Escenas y pantalla de título

En la pestaña **Escenas**:

- **Capítulos** contienen **escenas**. Cada escena apunta a un diálogo con el
  campo **`dialogo_id`** (ej. `ana/saludo`).
- La **primera escena del primer capítulo** es donde arranca el juego.
- Para encadenar escenas usa la acción `ir_a_escena` con
  `capitulo=<indice>,escena=<indice>` (empiezan en 0).
- **Título:** en la misma pestaña, sección *Título*, activa el título y
  configura fondo, título y subtítulo. Aparecerá la pantalla "Presiona ENTER".
  (La plantilla ya trae `screens.enabled=true` con `items=["title"]`.)

> Nota técnica: en esta fase el runtime de la VN solo usa el `dialogo_id` de
> cada escena. El tipo de escena de la pestaña es informativo; los minijuegos y
> cambios de escena se lanzan desde el árbol de diálogo con acciones.

---

## 8. Minijuegos

1. Pestaña **Minijuegos** → crea un minijuego con un **ID** (ej. `cita_bowling`).
2. Tipo: **recolección**, **timing** o **puzzle**.
3. En **flags_resultado** (JSON) define los flags que se aplican al terminar,
   por ejemplo `{"afecto_ana": 5}`.
4. En el árbol de diálogo, un nodo **Acción** con `iniciar_minijuego` y
   `minijuego_id=cita_bowling`. Al terminar, el runtime aplica
   `flags_resultado` a los flags y vuelve al diálogo.

---

## 9. Audio

1. Pestaña **Assets**: importa la canción/efecto con tipo **BGM** o **SFX**.
2. Pestaña **Audio**: registra el audio (ID, asset asociado, *loop* para BGM).
3. Desde el árbol usa las acciones `play_bgm`, `stop_bgm`, `play_sfx`.

---

## 10. Mecánicas de simulación de citas (flags)

Los **flags** son variables que acompañan al jugador durante toda la partida y
son la base de la simulación:

- **Afecto:** suma puntos con `add_flag` en cada opción buena,
  `flag=afecto_ana,cantidad=1`. Resta con cantidades negativas o `clear_flag`.
- **Condiciones:** el nodo **Condición** ramifica la historia según un flag.
  Operadores: `==`, `!=`, `>`, `<`, `>=`, `<=`.
- **Mostrar valores:** en el texto de un nodo **Diálogo** escribe
  `{flag:afecto_ana}` para insertar el valor actual de ese flag.
- **Finales:** elige a quién ganar encadenando `ir_a_escena` hacia una escena
  final, o termina con `fin_demo`.

---

## 11. Scripts (opcional)

La pestaña **Scripts** permite definir funciones de Python personalizadas que
puedes invocar desde el árbol con la acción `run_script`
(`function_name=<nombre>,args=<argumentos>`).

---

## 12. Probar y exportar

- **Ctrl+R** *(Ejecutar)*: lanza `python orm/main.py --project <raiz>` en una
  consola nueva con el proyecto seleccionado.
- **Ctrl+E** *(Exportar)*: genera un ejecutable (puede tardar varios minutos).

### Controles del juego (runtime)

| Tecla | Acción |
|-------|--------|
| ESPACIO / ENTER | Avanzar texto / elegir opción |
| ↑ / ↓ | Navegar por las opciones |
| ENTER | Empezar desde la pantalla de título |
| ESC | Salir del juego |

---

## 13. Limitaciones conocidas

- El fondo de la escena inicial es `fondo_ejemplo` (fijo en el runtime); para
  otra imagen, reemplaza `assets/fondo_ejemplo.png` o usa `cambiar_fondo` al
  comienzo del primer diálogo.
- Los retratos deben vivir en `assets/personajes/<personaje>_<expresion>.png`
  (el runtime no busca retratos en la raíz de `assets/`).
- Cada escena apunta a un diálogo con `personaje/contexto`; ese diálogo debe
  tener árbol de diálogo.
