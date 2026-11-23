import locale

locale.setlocale(locale.LC_NUMERIC, "C")

import mpv

from PySide6.QtCore import QObject, Signal


class MPVPlayer(QObject):
    error_occurred = Signal(str)
    file_loaded = Signal()

    def __init__(self, wid):
        super().__init__()

        # Qt puede restaurar el locale del sistema; libmpv aborta si
        # LC_NUMERIC no es "C", así que hay que fijarlo justo antes de
        # crear la instancia de mpv.
        locale.setlocale(locale.LC_NUMERIC, "C")

        self.player = mpv.MPV(
            wid=str(wid),
            vo="xv",
            hwdec="auto",
            osc="no",
            input_default_bindings=False,
            input_vo_keyboard=False,
        )

        @self.player.event_callback("end-file")
        def _on_end_file(event):
            data = event.data

            if data is not None and (
                getattr(data, "reason", None) == mpv.MpvEventEndFile.ERROR
            ):
                self.error_occurred.emit(
                    "No se pudo reproducir el canal.\n"
                    "Verifica la URL o tu conexión a internet."
                )

        @self.player.event_callback("file-loaded")
        def _on_file_loaded(event):
            self.file_loaded.emit()

    def play(self, url, headers=None):
        self._set_headers(headers)
        self.player.play(url)

    def _set_headers(self, headers):
        fields = [f"{key}: {value}" for key, value in (headers or {}).items()]

        try:
            self.player.http_header_fields = fields
        except Exception:
            try:
                self.player.command(
                    "set",
                    "http-header-fields",
                    ",".join(fields),
                )
            except Exception:
                pass

    def stop(self):
        self.player.stop()

    def toggle_pause(self):
        self.player.pause = not self.player.pause

    def is_paused(self):
        return bool(self.player.pause)

    def set_volume(self, volume):
        self.player.volume = max(0, min(100, int(volume)))

    def get_volume(self):
        return int(self.player.volume)

    def toggle_mute(self):
        self.player.mute = not self.player.mute

    def is_muted(self):
        return bool(self.player.mute)

    def destroy(self):
        self.player.terminate()
