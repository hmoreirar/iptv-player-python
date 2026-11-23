# Product

<!-- impeccable:product-schema 1 -->

## Platform

desktop (Linux; PySide6/Qt 6, mpv embebido). No es web, iOS ni Android.

## Users

Persona en su escritorio Linux que pone canales publicos de TV mientras usa la
maquina. Zapping frecuente con mouse y teclado, sesiones largas, a veces en
pantalla completa tipo TV. Tambien carga playlists M3U propias y mantiene una
coleccion de canales favoritos.

## Product Purpose

Reproductor IPTV de escritorio que carga playlists M3U locales o por URL y
reproduce canales dentro de la misma ventana. El exito es encontrar un canal en
segundos, cambiar rapido y volver a los favoritos sin friccion, incluso con
listas de mas de 10.000 canales.

## Positioning

Un reproductor nativo, local-first y sin cuentas: usa las playlists publicas de
iptv-org como catalogo por defecto, embebe mpv en Qt y guarda todo en el equipo.
No compite por catalogo propietario; compite por navegacion rapida y
confiabilidad sobre streams publicos que cambian y fallan.

## Operating Context

- Linux, principalmente Wayland con XWayland; la app fuerza `QT_QPA_PLATFORM=xcb`.
- mpv embebido con `vo=xv`; los streams requieren a veces User-Agent/Referer.
- Uso con mouse y teclado; Modo TV con flechas, numeros y atajos.
- Listas reales: iptv-org index con 11.452 canales, 184 grupos, 250 paises,
  30 categorias y 7.893 idiomas disponibles.
- Muchos streams estan caidos, geo-bloqueados o rotan de URL.
- Sin backend, sin cuentas, sin telemetria ni servicios de pago.

## Capabilities and Constraints

- Carga M3U local y remota; cache local de 24 h con fallback offline.
- Playlist predeterminada de iptv-org; selector por pais, categoria e idioma.
- Busqueda, filtro por categoria, favoritos e historial de playlists.
- Favoritos persistidos en QSettings; hoy por URL, con perdida al cambiar playlist.
- Modo TV a pantalla completa con sidebar de canales y banner.
- Headers HTTP por canal para streams que los exigen.
- UI en espanol. Sin emojis en codigo nuevo.
- Sin EPG, grabacion, cuentas, sincronizacion ni reproduccion de video local.
- Depende de `mpv`/`libmpv` del sistema; el empaquetado usa PyInstaller.

## Brand Commitments

- Nombre: IPTV Player.
- Voz: directa, en espanol, sin marketing ni promesas de disponibilidad.
- Identidad visual no definida todavia; la primera direccion se establece en
  este trabajo de rediseno.

## Evidence on Hand

- Playlists y metadatos publicos de iptv-org, sin licencia de contenido.
- Logos servidos por terceros; no hay assets de marca propios ni derechos sobre
  los logos de canales.
- Datos reales verificados: 11.452 canales en `index.m3u`, carga en ~0.5 s y
  cache en ~0.42 s.
- No existen testimonios, metricas de usuarios ni capturas de producto.

## Product Principles

1. Encontrar y cambiar canal gana sobre cualquier adorno.
2. La reproduccion manda: la UI se aparta y no congela la ventana.
3. Los favoritos son del usuario y sobreviven cambios de playlist o de URL.
4. Todo funciona local; la red solo aporta playlists y streams.
5. Fallar es normal: canal caido, red lenta o stream geo-bloqueado deben tener
   recuperacion visible y rapida.

## Accessibility & Inclusion

- Navegacion completa por teclado en Modo TV y atajos en modo normal.
- Contraste alto para texto sobre superficies oscuras y estados de foco visibles.
- Sin requisito formal de estandar confirmado.
