# Third-party notices

IPTV Player se distribuye bajo la licencia MIT. Tambien usa componentes de
terceros con sus propias licencias.

## Qt 6 y PySide6

- Proyecto: https://www.qt.io/
- Licencia: LGPL-3.0-only, GPL-2.0-only o GPL-3.0-only.
- Uso: interfaz grafica, red, SVG y empaquetado Qt dentro de la aplicacion.
- En una distribucion binaria se mantienen las librerias Qt como componentes
  separados y se incluye este aviso.

## mpv y libmpv

- Proyecto: https://mpv.io/
- Licencia: GPL-2.0-or-later, o LGPL-2.1-or-later segun la compilacion.
- Uso: reproduccion de video y audio.
- La AppImage no incluye libmpv. Requiere `libmpv.so.2` instalado en el sistema
  (`libmpv2` en Debian/Ubuntu). El usuario instala ese componente por separado.

## python-mpv

- Proyecto: https://github.com/jaseg/python-mpv
- Licencia: GPL-2.0-or-later o LGPL-2.1-or-later.
- Uso: enlace Python con libmpv.

## requests

- Proyecto: https://requests.readthedocs.io/
- Licencia: Apache-2.0.
- Uso: descarga de playlists y metadatos.

## iptv-org

- Proyecto: https://github.com/iptv-org/iptv
- Licencia del repositorio: Unlicense.
- Uso: playlists publicas y metadatos por defecto.
- Los streams enlazados son de terceros. IPTV Player no aloja ni distribuye
  video. La disponibilidad y los derechos dependen de cada emisor.

## Logos de canales

Los logos se descargan de URLs incluidas en las playlists M3U. Pertenecen a sus
respectivos titulares y no se distribuyen con este repositorio.
