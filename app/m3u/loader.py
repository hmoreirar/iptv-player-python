from PySide6.QtCore import QThread, Signal

from app.m3u.parser import (
    parse_m3u_file,
    parse_m3u_url,
)


class PlaylistLoader(QThread):
    finished = Signal(list)
    failed = Signal(str)

    def __init__(self, source, is_url):
        super().__init__()
        self.source = source
        self.is_url = is_url

    def run(self):
        try:
            if self.is_url:
                channels = parse_m3u_url(self.source)
            else:
                channels = parse_m3u_file(self.source)
        except Exception as error:
            self.failed.emit(str(error))
            return

        self.finished.emit(channels)
