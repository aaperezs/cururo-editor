# Plan: Cururo Editor como herramienta para enseñar a hacer videojuegos

Estado: **PENDIENTE** (solo plan, sin implementar)

## Objetivo

Convertir el editor (hoy una herramienta potente pero con poca orientación) en una
herramienta que **guíe el aprendizaje** de desarrollo de videojuegos, tanto para
cursos formales como para talleres y auto-aprendizaje.

## Situación actual

### Lo que ya ayuda a enseñar
- Editor 100% visual: 18 pestañas (sprites, mapas, eventos, elementos, habilidades,
  items, jefes, diálogos, personajes, escenas, minijuegos, menús, audio, etc.). Se arma
  un juego casi sin escribir código.
- Feedback inmediato: `Ctrl+R` corre el juego; la pestaña Menús tiene vista previa en
  vivo; validaciones que avisan (p. ej. "tecla duplicada").
- Textos de orientación: cada pestaña vacía muestra una descripción de qué hace y cómo
  usarla (`tab.*.desc` en locales).
- Plantillas: 3 categorías (Snake RPG, Novela Visual, Vacío) + plantillas de menú
  (inventario/opciones/relaciones).

### Lo que falta
- No hay guía paso a paso ni un "primer proyecto" dirigido (el usuario se enfrenta a 18
  pestañas sin rumbo).
- La ayuda es texto estático: no hay explicaciones por campo, ni "por qué", ni concepto.
- No hay misiones/checklist que estructuren el aprendizaje (es fácil perderse).
- No hay modo principiante/avanzado: scripts y jefes aparecen igual que sprites y mapas.
- No hay galería de ejemplos más allá de los menús (mapas, eventos, items de muestra).
- No hay biblioteca de conceptos (qué es un flag, un evento, un renderer) accesible desde
  cada panel.
- No hay progreso por proyecto ("vas por la misión 3 de 5").

## Fases propuestas

### Fase 1 — Guía de inicio
- Pantalla de bienvenida con objetivos claros.
- Wizard "primer proyecto" que crea un juego mínimo y lo abre en la tarea correcta.
- Archivos: `editor/main.py`, nuevo `editor/welcome.py` (o panel), locales.

### Fase 2 — Misiones guiadas
- Checklists por categoría, p. ej. "Hacé que la serpiente recoja monedas":
  1. Crear el mapa
  2. Agregar el elemento (moneda)
  3. Crear el evento (recoger → dar puntos/sumar item)
  4. Probar el juego (`Ctrl+R`)
- Estado de progreso guardado por proyecto (via `workspace`).
- Archivos: `editor/workspace.py`, nuevo `editor/missions.py`, cada panel emite
  "misión cumplida" al guardar el dato correspondiente.

### Fase 3 — Ayuda en contexto
- Explicación "qué es / para qué sirve" en cada control y panel (tooltips o línea de
  ayuda inferior).
- Botón de ayuda por pestaña que abre la descripción ampliada.
- Archivos: `editor/widgets/*`, `editor/panels/base_panel.py`, locales.

### Fase 4 — Modo principiante/avanzado
- Ocultar paneles complejos (scripts, jefes, minijuegos) en modo novato.
- Desbloqueo gradual (aparecen a medida que se usan las más básicas).
- Archivos: `editor/categories.py`, `editor/main.py`, `workspace` (guardar modo).

### Fase 5 — Galería de ejemplos
- Objetos, eventos y mapas prefabricados para copiar y modificar (como las plantillas de
  menú de `menu_data.PLANTILLAS`).
- "Editar y probar" con un solo clic.
- Archivos: nuevos `editor/*_templates.py` o ampliación de `menu_data.PLANTILLAS`.

### Fase 6 — Biblioteca de conceptos
- Mini-docs de game design (qué es un flag, un evento, un renderer, un behavior) enlazadas
  desde cada panel.
- Archivos: `editor/locales/*.json` (textos) + un panel/navegador de ayuda.

## Preguntas abiertas (definir antes de implementar)

1. **Contexto de uso**: curso formal con alumnos (misiones con orden/progreso), taller
   puntual (tutoriales cortos de ~30 min) o auto-aprendizaje (ejemplos + ayuda en
   contexto). El diseño de Fase 2 cambia según la respuesta.
2. **Nivel de los estudiantes** (edad/experiencia): define el tono y el modo
   principiante (Fase 4).
3. **Idioma**: el editor ya soporta es/en; confirmar si hace falta otro.

## Criterios de aceptación (generales)

- Un usuario sin experiencia puede crear su primer juego funcionando siguiendo la guía.
- En cada panel, el usuario sabe qué hacer y por qué.
- El modo principiante elimina la sobrecarga de paneles avanzados.
- El progreso de misiones se conserva entre sesiones por proyecto.