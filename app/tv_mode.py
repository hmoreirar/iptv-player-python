from PySide6.QtCore import QEvent, QObject, QSize, Qt, QTimer, Signal
from PySide6.QtWidgets import QListWidget, QListWidgetItem

SWITCH_DELAY_MS = 700
HIDE_DELAY_MS = 2000
VOLUME_STEP = 5


class TVOverlay(QListWidget):
    """Lista de canales semitransparente superpuesta al video."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setIconSize(QSize(40, 30))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(
            """
            QListWidget {
                background-color: rgba(0, 0, 0, 0.75);
                border: 1px solid rgba(255, 255, 255, 0.2);
                border-radius: 8px;
                color: #ffffff;
                font-size: 14px;
                outline: none;
            }
            QListWidget::item {
                padding: 6px 10px;
            }
            QListWidget::item:selected {
                background-color: rgba(255, 255, 255, 0.25);
            }
            """
        )


class TVMode(QObject):
    """Modo TV: video a pantalla completa con lista de canales superpuesta."""

    channel_selected = Signal(dict)
    volume_changed = Signal(int)
    exited = Signal()

    def __init__(self, video_widget, parent=None):
        super().__init__(parent)

        self.video = video_widget
        self.channels = []
        self.current_url = None
        self.logo_loader = None
        self.active = False

        self.overlay = TVOverlay(self.video)
        self.overlay.hide()

        self._switch_timer = QTimer(self)
        self._switch_timer.setSingleShot(True)
        self._switch_timer.timeout.connect(self._confirm_selection)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self._hide_overlay)

    # =========================
    # ENTRAR / SALIR
    # =========================

    def enter(self, channels, current_url, logo_loader=None):
        if self.active:
            return

        self.active = True
        self.channels = channels
        self.current_url = current_url
        self.logo_loader = logo_loader

        self._populate_overlay()
        self._place_overlay()

        self.video.installEventFilter(self)
        self.video.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.video.setFocus()

        self._show_overlay()
        self._hide_timer.start(HIDE_DELAY_MS)

    def exit(self):
        if not self.active:
            return

        self.active = False

        self._switch_timer.stop()
        self._hide_timer.stop()

        self.video.removeEventFilter(self)
        self.video.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.video.unsetCursor()

        if self.overlay:
            self.overlay.hide()

        self.exited.emit()

    # =========================
    # EVENTOS
    # =========================

    def eventFilter(self, obj, event):
        if not self.active:
            return False

        event_type = event.type()

        if event_type == QEvent.Type.Resize:
            self._place_overlay()
            return False

        if event_type == QEvent.Type.KeyPress:
            return self._handle_key(event)

        if event_type == QEvent.Type.Wheel:
            delta = event.angleDelta().y()

            if delta:
                self._move(1 if delta > 0 else -1)
                event.accept()
                return True

        return False

    def _handle_key(self, event):
        key = event.key()

        if key == Qt.Key.Key_Up:
            self._move(-1)
            return True

        if key == Qt.Key.Key_Down:
            self._move(1)
            return True

        if key == Qt.Key.Key_Left:
            self.volume_changed.emit(-VOLUME_STEP)
            return True

        if key == Qt.Key.Key_Right:
            self.volume_changed.emit(VOLUME_STEP)
            return True

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            self._confirm_selection()
            return True

        if key == Qt.Key.Key_Escape:
            self.exit()
            return True

        return False

    # =========================
    # NAVEGACIÓN
    # =========================

    def _move(self, step):
        if not self.overlay.isVisible():
            self._show_overlay()

        row = self.overlay.currentRow()
        new_row = max(0, min(len(self.channels) - 1, row + step))

        self.overlay.setCurrentRow(new_row)

        current_item = self.overlay.currentItem()

        if current_item:
            self.overlay.scrollToItem(current_item)

        self._switch_timer.start(SWITCH_DELAY_MS)
        self._hide_timer.start(HIDE_DELAY_MS)

    def _confirm_selection(self):
        if not self.active:
            return

        channel = self._current_selection()

        if channel is None:
            return

        self.current_url = channel["url"]
        self.channel_selected.emit(channel)

        self._show_overlay()
        self._hide_timer.start(HIDE_DELAY_MS)

    def _current_selection(self):
        row = self.overlay.currentRow()

        if 0 <= row < len(self.channels):
            return self.channels[row]

        return None

    # =========================
    # OVERLAY
    # =========================

    def _populate_overlay(self):
        self.overlay.clear()

        for channel in self.channels:
            item = QListWidgetItem(channel["name"])
            item.setData(Qt.ItemDataRole.UserRole, channel)
            self.overlay.addItem(item)

            logo = channel.get("logo", "")

            if logo and self.logo_loader:
                self.logo_loader.load(item, logo)

        row = self._row_for_url(self.current_url)

        if row >= 0:
            self.overlay.setCurrentRow(row)

    def _row_for_url(self, url):
        for index, channel in enumerate(self.channels):
            if channel["url"] == url:
                return index

        return -1

    def _show_overlay(self):
        if self.overlay.isHidden():
            self.overlay.show()
            self.overlay.raise_()

        self.video.setCursor(Qt.CursorShape.ArrowCursor)

    def _hide_overlay(self):
        if self.overlay:
            self.overlay.hide()

        self.video.setCursor(Qt.CursorShape.BlankCursor)

    def _place_overlay(self):
        video_width = self.video.width()
        video_height = self.video.height()

        if video_width <= 0 or video_height <= 0:
            return

        width = min(380, int(video_width * 0.32))
        margin = 24
        top = int(video_height * 0.12)
        height = int(video_height * 0.62)

        self.overlay.setGeometry(
            video_width - width - margin,
            top,
            width,
            height,
        )
