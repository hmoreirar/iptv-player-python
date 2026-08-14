from PySide6.QtCore import QEvent, QObject, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QFont, QPixmap
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

VOLUME_STEP = 5
BANNER_HIDE_MS = 3000
NUMBER_TIMEOUT_MS = 1500


class ChannelBanner(QWidget):
    """Banner de información del canal en la parte inferior de la pantalla."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 0, 24, 20)

        self.channel_info = QLabel()
        self.channel_info.setStyleSheet(
            "color: #ffffff; font-size: 20px; font-weight: bold;"
        )

        self.group_label = QLabel()
        self.group_label.setStyleSheet("color: #cccccc; font-size: 14px;")

        self.volume_label = QLabel()
        self.volume_label.setStyleSheet("color: #aaaaaa; font-size: 14px;")
        self.volume_label.hide()

        self.input_label = QLabel()
        self.input_label.setStyleSheet(
            "color: #ffcc00; font-size: 28px; font-weight: bold;"
        )
        self.input_label.hide()

        layout.addWidget(self.channel_info)
        layout.addWidget(self.group_label)
        layout.addWidget(self.volume_label)
        layout.addWidget(self.input_label)

        self.setStyleSheet(
            """
            ChannelBanner {
                background-color: rgba(0, 0, 0, 0.7);
                border-radius: 10px;
            }
            """
        )

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.hide)

    def show_channel(self, index, total, channel):
        self.channel_info.setText(
            f"CH {index + 1}/{total}  —  {channel['name']}"
        )

        group = channel.get("group", "")
        self.group_label.setText(group if group else "")
        self.group_label.setVisible(bool(group))

        self.volume_label.hide()
        self.input_label.hide()

        self.show()
        self.raise_()
        self._hide_timer.start(BANNER_HIDE_MS)

    def show_volume(self, volume):
        self.volume_label.setText(f"Volumen: {volume}")
        self.volume_label.show()
        self.show()
        self.raise_()
        self._hide_timer.start(BANNER_HIDE_MS)

    def show_number_input(self, digits):
        self.input_label.setText(f"Canal: {digits}_")
        self.input_label.show()
        self.show()
        self.raise_()

    def hide_number_input(self):
        self.input_label.hide()


class TVOverlay(QListWidget):
    """Lista de canales semitransparente superpuesta al video (guía)."""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setIconSize(QSize(40, 30))
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setStyleSheet(
            """
            QListWidget {
                background-color: rgba(0, 0, 0, 0.80);
                border: 1px solid rgba(255, 255, 255, 0.15);
                border-radius: 8px;
                color: #ffffff;
                font-size: 14px;
                outline: none;
            }
            QListWidget::item {
                padding: 8px 12px;
            }
            QListWidget::item:selected {
                background-color: rgba(255, 255, 255, 0.25);
            }
            """
        )


class TVMode(QObject):
    """Modo TV: experiencia real de televisión.

    Controles:
      - Flechas arriba/abajo: canal anterior/siguiente
      - Flechas izquierda/derecha: volumen
      - 0-9: entrada numérica de canal
      - Enter: confirmar número ingresado
      - Backspace: canal anterior
      - M: mute
      - Tab: guía de canales
      - Escape: salir
    """

    channel_selected = Signal(dict)
    volume_changed = Signal(int)
    mute_requested = Signal()
    exited = Signal()

    def __init__(self, video_widget, parent=None):
        super().__init__(parent)

        self.video = video_widget
        self.channels = []
        self.current_url = None
        self.logo_loader = None
        self.active = False

        self._current_index = 0
        self._previous_index = 0
        self._number_buffer = ""

        self.banner = ChannelBanner(self.video)
        self.banner.hide()

        self.overlay = TVOverlay(self.video)
        self.overlay.hide()

        self._number_timer = QTimer(self)
        self._number_timer.setSingleShot(True)
        self._number_timer.timeout.connect(self._execute_number_input)

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

        self._current_index = self._find_current_index()
        self._previous_index = self._current_index
        self._number_buffer = ""

        self._place_banner()
        self._place_overlay()
        self._populate_overlay()

        self.video.installEventFilter(self)
        self.video.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.video.setFocus()

        self._show_banner()

    def _show_banner(self):
        if 0 <= self._current_index < len(self.channels):
            channel = self.channels[self._current_index]
            self.banner.show_channel(
                self._current_index, len(self.channels), channel
            )

    def exit(self):
        if not self.active:
            return

        self.active = False

        self._number_timer.stop()

        self.video.removeEventFilter(self)
        self.video.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.video.unsetCursor()

        self.banner.hide()
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
            self._place_banner()
            self._place_overlay()
            return False

        if event_type == QEvent.Type.KeyPress:
            return self._handle_key(event)

        if event_type == QEvent.Type.Wheel:
            delta = event.angleDelta().y()
            if delta:
                self._change_channel(1 if delta > 0 else -1)
                event.accept()
                return True

        return False

    def _handle_key(self, event):
        key = event.key()

        if key == Qt.Key.Key_Up:
            self._change_channel(-1)
            return True

        if key == Qt.Key.Key_Down:
            self._change_channel(1)
            return True

        if key == Qt.Key.Key_Left:
            self.volume_changed.emit(-VOLUME_STEP)
            self._show_volume()
            return True

        if key == Qt.Key.Key_Right:
            self.volume_changed.emit(VOLUME_STEP)
            self._show_volume()
            return True

        if key in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            if self._number_buffer:
                self._execute_number_input()
            else:
                self._toggle_guide()
            return True

        if key == Qt.Key.Key_Backspace:
            self._go_to_previous()
            return True

        if key == Qt.Key.Key_M:
            self.mute_requested.emit()
            return True

        if key == Qt.Key.Key_Tab:
            self._toggle_guide()
            return True

        if key == Qt.Key.Key_Escape:
            if self.overlay.isVisible():
                self.overlay.hide()
                self.video.setCursor(Qt.CursorShape.BlankCursor)
            else:
                self.exit()
            return True

        if Qt.Key.Key_0 <= key <= Qt.Key.Key_9:
            digit = str(key - Qt.Key.Key_0)
            self._add_digit(digit)
            return True

        return False

    # =========================
    # CAMBIO DE CANAL
    # =========================

    def _change_channel(self, step):
        if not self.channels:
            return

        self._previous_index = self._current_index

        new_index = self._current_index + step
        if new_index < 0:
            new_index = len(self.channels) - 1
        elif new_index >= len(self.channels):
            new_index = 0

        self._current_index = new_index
        self._emit_current()

    def _go_to_previous(self):
        if not self.channels:
            return

        self._current_index = self._previous_index
        self._emit_current()

    def _emit_current(self):
        if 0 <= self._current_index < len(self.channels):
            channel = self.channels[self._current_index]
            self.current_url = channel["url"]
            self._update_overlay_selection()
            self.banner.show_channel(
                self._current_index, len(self.channels), channel
            )
            self.channel_selected.emit(channel)

    def _find_current_index(self):
        if self.current_url is None:
            return 0

        for i, ch in enumerate(self.channels):
            if ch["url"] == self.current_url:
                return i

        return 0

    # =========================
    # ENTRADA NUMÉRICA
    # =========================

    def _add_digit(self, digit):
        if len(self._number_buffer) >= 3:
            self._number_buffer = ""

        self._number_buffer += digit

        self._number_timer.stop()
        self._number_timer.start(NUMBER_TIMEOUT_MS)

        self.banner.show_number_input(self._number_buffer)

    def _execute_number_input(self):
        self._number_timer.stop()

        if not self._number_buffer:
            return

        num = int(self._number_buffer)
        self._number_buffer = ""

        self.banner.hide_number_input()

        if not self.channels:
            return

        index = num - 1
        if index < 0:
            index = 0
        elif index >= len(self.channels):
            index = len(self.channels) - 1

        self._previous_index = self._current_index
        self._current_index = index
        self._emit_current()

    # =========================
    # VOLUMEN
    # =========================

    def _show_volume(self):
        from PySide6.QtWidgets import QApplication

        slider = None
        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, "volume_slider"):
                slider = widget.volume_slider
                break

        volume = slider.value() if slider else 0
        self.banner.show_volume(volume)

    # =========================
    # GUÍA DE CANALES
    # =========================

    def _toggle_guide(self):
        if self.overlay.isVisible():
            self.overlay.hide()
            self.video.setCursor(Qt.CursorShape.BlankCursor)
        else:
            self._populate_overlay()
            self.overlay.show()
            self.overlay.raise_()
            self.video.setCursor(Qt.CursorShape.ArrowCursor)

    def _populate_overlay(self):
        self.overlay.clear()

        for i, channel in enumerate(self.channels):
            num = i + 1
            item = QListWidgetItem(f"{num:>3}.  {channel['name']}")
            item.setData(Qt.ItemDataRole.UserRole, channel)
            self.overlay.addItem(item)

            logo = channel.get("logo", "")
            if logo and self.logo_loader:
                self.logo_loader.load(item, logo)

        if 0 <= self._current_index < self.overlay.count():
            self.overlay.setCurrentRow(self._current_index)
            self.overlay.scrollToItem(self.overlay.currentItem())

    def _update_overlay_selection(self):
        if self.overlay.isVisible() and 0 <= self._current_index < self.overlay.count():
            self.overlay.setCurrentRow(self._current_index)
            self.overlay.scrollToItem(self.overlay.currentItem())

    # =========================
    # POSICIONAMIENTO
    # =========================

    def _place_banner(self):
        vw = self.video.width()
        vh = self.video.height()

        if vw <= 0 or vh <= 0:
            return

        width = min(400, int(vw * 0.35))
        height = 90
        x = 20
        y = vh - height - 20

        self.banner.setGeometry(x, y, width, height)

    def _place_overlay(self):
        vw = self.video.width()
        vh = self.video.height()

        if vw <= 0 or vh <= 0:
            return

        width = min(380, int(vw * 0.32))
        margin = 24
        top = int(vh * 0.12)
        height = int(vh * 0.62)

        self.overlay.setGeometry(
            vw - width - margin,
            top,
            width,
            height,
        )
