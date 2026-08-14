# IPTV Player Python

Reproductor de IPTV de escritorio construido con PySide6 y mpv.

## Caracteristicas

- Carga de playlists M3U locales y por URL
- Busqueda y filtrado por categorias
- Favoritos (memoria de la sesion)
- Modo TV a pantalla completa con navegacion por teclado
- Carga asincrona de canales y logos
- Parser M3U robusto con soporte de URLs relativas

## Dependencias del sistema

### Ubuntu / Debian

```bash
sudo apt update
sudo apt install -y mpv libmpv-dev python3-dev python3-venv
```

### Fedora

```bash
sudo dnf install -y mpv libmpv-devel python3-devel
```

### macOS (Homebrew)

```bash
brew install mpv
```

### Windows

Instalar [mpv](https://mpv.io/installation/) y agregarlo al PATH del sistema.

## Instalacion

```bash
git clone git@github.com:hmoreirar/iptv-player-python.git
cd iptv-player-python
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Ejecucion

```bash
python -m app.main
```

## Uso

1. Abrir una playlist con el boton **Abrir M3U** (archivo local) o **Abrir URL** (desde Internet).
2. Seleccionar un canal de la lista o buscar por nombre.
3. Usar los controles de reproduccion (play/pause, volumen, pantalla completa).
4. Navegar por categorias usando el panel lateral.
5. Agregar canales a favoritos con clic derecho > Añadir a favoritos.
6. Entrar al Modo TV con el boton correspondiente. Navegar con flechas del teclado o rueda del raton. Salir con Escape.

## Estructura del proyecto

```
iptv-player-python/
  app/
    main.py          # Ventana principal
    tv_mode.py       # Modo TV con overlay
    m3u/
      parser.py      # Parser de playlists M3U
      loader.py      # Carga asincrona de playlists
    player/
      mpv_player.py  # Wrapper de mpv
  requirements.txt
```

## Licencia

MIT
