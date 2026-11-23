---
name: IPTV Player
description: Consola de emision nocturna para explorar y reproducir IPTV en escritorio
colors:
  ink-black: "#0b0f14"
  graphite: "#111820"
  graphite-raised: "#17212b"
  graphite-active: "#1e2a36"
  hairline: "#263442"
  hairline-strong: "#33495c"
  phosphor: "#eef4f8"
  muted: "#90a3b3"
  muted-deep: "#7a92a5"
  signal-amber: "#f0b429"
  amber-ink: "#1a1205"
  live-green: "#35d07f"
  error-red: "#ff6b6b"
typography:
  body:
    fontFamily: "Noto Sans, DejaVu Sans, sans-serif"
    fontSize: "13px"
    fontWeight: 400
  title:
    fontFamily: "Noto Sans, DejaVu Sans, sans-serif"
    fontSize: "17px"
    fontWeight: 700
  label:
    fontFamily: "Noto Sans, DejaVu Sans, sans-serif"
    fontSize: "10px"
    fontWeight: 700
    letterSpacing: "1px"
  numeric:
    fontFamily: "DejaVu Sans Mono, monospace"
    fontSize: "12px"
    fontWeight: 700
rounded:
  sm: "7px"
  md: "10px"
spacing:
  xs: "4px"
  sm: "8px"
  md: "12px"
  lg: "16px"
  xl: "24px"
components:
  button-primary:
    backgroundColor: "{colors.signal-amber}"
    textColor: "{colors.amber-ink}"
    rounded: "{rounded.sm}"
    padding: "7px 12px"
  button-secondary:
    backgroundColor: "{colors.graphite-raised}"
    textColor: "{colors.phosphor}"
    rounded: "{rounded.sm}"
    padding: "7px 12px"
  input-search:
    backgroundColor: "{colors.graphite-raised}"
    textColor: "{colors.phosphor}"
    rounded: "{rounded.sm}"
    padding: "8px 10px"
  nav-item-active:
    backgroundColor: "{colors.graphite-active}"
    textColor: "{colors.phosphor}"
    rounded: "{rounded.sm}"
    padding: "8px 10px"
  now-playing:
    backgroundColor: "{colors.graphite}"
    textColor: "{colors.phosphor}"
    rounded: "{rounded.md}"
---

# Design System: IPTV Player

## Overview

**Creative North Star: "La consola de emision nocturna"**

La interfaz se usa de noche, en un escritorio, con la TV de fondo. Por eso el
fondo es tinta azul-negro y la luz sale de la senal: ambar para el canal activo
y los favoritos, verde solo para vivo, rojo solo para error. No es un dashboard
de tarjetas: es un log de canales denso, con lineas finas y numeros tabulares.

El video ocupa el centro, pero la lista nunca desaparece. La navegacion vive en
una barra lateral compacta; el log de canales, en un panel fijo a la derecha.
Todo se puede leer de un vistazo y operar con teclado.

**Key Characteristics:**

- Tema oscuro de bajo brillo, no negro puro.
- Ambar como unica senal de estado activo.
- Filas densas de 56 px con separacion por capas tonales, no por sombras.
- Numeros de canal monoespaciados y tabulares.
- Iconos SVG de un solo trazo; cero emojis.

## Colors

Paleta restringida: grafito azulado, blanco fosforo y una sola senal ambar.

### Primary

- **Signal Amber** (#f0b429): canal en vivo, favorito guardado, foco de entrada
  y accion primaria. Es la unica saturacion fuerte de la pantalla.
- **Amber Ink** (#1a1205): texto sobre ambar; garantiza contraste en botones.

### Secondary

- **Live Green** (#35d07f): exclusivamente el estado `EN VIVO`.
- **Error Red** (#ff6b6b): exclusivamente errores de reproduccion.

### Neutral

- **Ink Black** (#0b0f14): fondo de la ventana y del escenario de video.
- **Graphite** (#111820): barra superior, barra lateral y panel de canales.
- **Graphite Raised** (#17212b): botones, tarjeta de fuente, hover.
- **Graphite Active** (#1e2a36): fila actual, seleccion y nav activo.
- **Hairline** (#263442): bordes de 1 px y separadores.
- **Hairline Strong** (#33495c): hover de borde y foco.
- **Phosphor** (#eef4f8): texto principal.
- **Muted** (#90a3b3): texto secundario y metadatos.
- **Muted Deep** (#7a92a5): etiquetas y numeros inactivos.

**The One Signal Rule.** El ambar se reserva para el canal actual, los
favoritos y la accion primaria. Si aparece en decoracion, deja de significar.

## Typography

**Body Font:** Noto Sans (fallback DejaVu Sans, sans-serif)
**Label Font:** Noto Sans, mayusculas con tracking
**Numeric Font:** DejaVu Sans Mono (fallback monospace)

**Character:** Una sans de trabajo para leer canales y controles; el mono solo
aparece donde el numero importa: canal, contador y categoria.

### Hierarchy

- **Title** (700, 17 px): marca en la barra superior.
- **Body** (400, 13 px): nombres de canal, botones y navegacion.
- **Body strong** (600, 14 px): canal actual en la barra Ahora.
- **Label** (700, 10 px, 1 px tracking, mayusculas): secciones como BIBLIOTECA,
  CATEGORIAS y CANALES.
- **Caption** (400, 11 px): grupo del canal, fuente y textos auxiliares.
- **Numeric** (700, 12 px): numero de canal y contadores.

**The Two-Voice Rule.** La UI no usa una fuente decorativa. La identidad viene
del color, la densidad y los numeros tabulares, no de una display face.

## Layout

Ventana minima 1100 x 700; tamano recomendado 1280 x 800.

- Barra superior fija de 60 px: marca, busqueda de 380 px, acciones a la derecha.
- Cuerpo con margen 16 px y gap 12 px.
- Sidebar fija de 208 px: biblioteca, salto de errores, categorias y fuente.
- Centro elastico: escenario de video + barra Ahora de 66 px.
- Panel de canales fijo de 344 px con filas de 56 px.
- En Modo TV se ocultan barra, sidebar, panel y barra Ahora; el video ocupa todo.

La busqueda global ignora la categoria activa; el filtro por categoria se aplica
cuando no hay termino de busqueda. Las categorias muestran contador porque un
canal puede pertenecer a varias.

## Elevation & Depth

Sistema plano por capas tonales. No hay sombras en la UI: la profundidad se
construye con cuatro niveles de grafito y bordes de 1 px. El unico efecto de
elevacion permitido es el contorno del foco ambar en un campo de texto.

La barra Ahora y el banner del Modo TV usan borde y fondo solido; nunca blur ni
glass. Los overlays del Modo TV pueden usar fondo opaco para no mezclarse con el
video nativo.

## Shapes

Esquinas suaves y contenidas: 7 px en botones, campos, filas y nav; 10 px en la
barra Ahora, el banner de TV y la tarjeta de fuente. Bordes de 1 px. Sin
capsulas, sin circulos decorativos, sin cortes diagonales.

Los iconos son SVG de 24 x 24, trazo 1.6-1.8, un solo lenguaje. La estrella de
favorito se dibuja como path, no como glifo.

## Components

### Buttons

- **Shape:** radio 7 px, borde 1 px, padding 7 x 12 px.
- **Primary:** ambar solido con texto Amber Ink; solo Modo TV.
- **Secondary:** Graphite Raised con texto Phosphor y borde Hairline.
- **Hover:** Graphite Active y borde Hairline Strong.
- **Focus:** contorno ambar de 1 px via el campo o shortcut, nunca glow.

### Navigation

- **Style:** filas de 36 px con icono de 17 px, texto 13 px y contador inline.
- **Default:** texto Muted, fondo transparente.
- **Hover:** fondo Graphite Raised, texto Phosphor.
- **Active:** fondo Graphite Active, texto Phosphor y peso 700.
- **Categories:** filas de 34 px, contador monoespaciado a la derecha.

### Channel List

- **Row:** 56 px, numero 01-99 en mono, logo 40 x 30 o inicial, nombre 13 px,
  grupo 11 px, estrella de 20 px, `EN VIVO` en verde para el actual.
- **Current:** fondo Graphite Active, numero ambar y `EN VIVO` en verde.
- **Hover / Selected:** fondo Graphite Raised.
- **Empty:** titulo y cuerpo centrados que explican la accion siguiente.

### Inputs

- **Style:** fondo Ink Black o Graphite Raised, borde Hairline, radio 7 px.
- **Focus:** borde ambar, sin sombra.
- **Clear:** boton nativo del campo; placeholder Muted Deep.

### Now Playing Bar

- **Shape:** 66 px de alto, radio 10 px, fondo Graphite, borde Hairline.
- **Contents:** numero ambar, nombre y grupo, play/pause, mute, volumen,
  favorito y pantalla completa.
- **State:** estrella rellena en ambar cuando el canal es favorito; `EN VIVO`
  verde solo con reproduccion activa.

### Toast

- **Shape:** radio 8 px, fondo Graphite Active, borde Hairline Strong.
- **Placement:** centrado arriba, a 72 px del borde superior; nunca tapa los
  controles de reproduccion.
- **Motion:** fade de 180 ms al desaparecer.

## Do's and Don'ts

### Do:

- **Do** reservar el ambar para canal actual, favoritos y accion primaria.
- **Do** usar numeros tabulares monoespaciados para canal y contadores.
- **Do** mantener filas de 56 px y lineas de 1 px.
- **Do** mostrar estados vacios que expliquen como seguir.
- **Do** usar iconos SVG propios de un solo trazo.
- **Do** mantener el video visible y los controles alcanzables con teclado.

### Don't:

- **Don't** usar emojis como iconos.
- **Don't** introducir sombras, glass, blur decorativo ni gradientes de texto.
- **Don't** crear tarjetas anidadas ni una grilla de tarjetas para canales.
- **Don't** usar ambar como decoracion o color de fondo de secciones.
- **Don't** mostrar modales para errores recuperables; usar el toast o el banner.
- **Don't** congelar toda la ventana mientras carga una playlist.
