from PySide6.QtCore import QEvent, QObject, QPropertyAnimation, QSize, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QPainter, QPen
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
    QWidget,
)

VOLUME_STEP = 5
BANNER_HIDE_MS = 3000
SIDEBAR_HIDE_MS = 4000
NUMBER_TIMEOUT_MS = 1500


class ChannelBanner(QWidget):
    """Banner inferior: info del canal, volumen, entrada numérica."""

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


class ChannelSidebar(QWidget):
    """Sidebar lateral estilo smart TV con lista de canales."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        header = QLabel("  Canales")
        header.setStyleSheet(
            "color: #ffffff; font-size: 16px; font-weight: bold; "
            "padding: 12px 16px; background-color: rgba(0, 0, 0, 0.85);"
        )
        layout.addWidget(header)

        self.channel_list = QListWidget()
        self.channel_list.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.channel_list.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        self.channel_list.setStyleSheet(
            """
            QListWidget {
                background-color: rgba(0, 0, 0, 0.82);
                border: none;
                color: #ffffff;
                font-size: 14px;
                outline: none;
                padding: 4px 0;
            }
            QListWidget::item {
                padding: 10px 16px;
                border-bottom: 1px solid rgba(255, 255, 255, 0.06);
            }
            QListWidget::item:selected {
                background-color: rgba(60, 130, 246, 0.6);
            }
            """
        )
        layout.addWidget(self.channel_list)

        self._hide_timer = QTimer(self)
        self._hide_timer.setSingleShot(True)
        self._hide_timer.timeout.connect(self.fade_out)

        self.setStyleSheet(
            """
            ChannelSidebar {
                background-color: rgba(0, 0, 0, 0.0);
                border-radius: 0px 8px 8px 0px;
            }
            """
        )

    def populate(self, channels, current_index, logo_loader=None):
        self.channel_list.clear()
        for i, ch in enumerate(channels):
            num = i + 1
            item = QListWidgetItem(f"  {num:>3}   {ch['name']}")
            item.setData(Qt.ItemDataRole.UserRole, ch)
            item.setSizeHint(QSize(0, 42))
            self.channel_list.addItem(item)

            logo = ch.get("logo", "")
            if logo and logo_loader:
                logo_loader.load(item, logo)

        self._select_index(current_index)

    def _select_index(self, index):
        if 0 <= index < self.channel_list.count():
            self.channel_list.setCurrentRow(index)
            self.channel_list.scrollToItem(
                self.channel_list.currentItem(),
                QListWidget.ScrollHint.EnsureVisible,
            )

    def update_selection(self, index):
        self._select_index(index)
        self.show()
        self.raise_()
        self._hide_timer.start(SIDEBAR_HIDE_MS)

    def show_and_start_hide_timer(self):
        self.show()
        self.raise_()
        self._hide_timer.start(SIDEBAR_HIDE_MS)

    def fade_out(self):
        self.hide()

    def place(self, video_width, video_height):
        if video_width <= 0 or video_height <= 0:
            return
        width = min(320, int(video_width * 0.28))
        self.setGeometry(0, 0, width, video_height)


class TVMode(QObject):
    """Modo TV estilo smart TV.

    Controles:
      - Flechas arriba/abajo: navegar canales (sidebar visible)
      - Flechas izquierda/derecha: volumen
      - 0-9: entrada numérica de canal
      - Enter: confirmar número / toggle sidebar
      - Backspace: canal anterior
      - M: mute
      - Tab: toggle sidebar
      - Escape: cerrar sidebar / salir
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

        self.sidebar = ChannelSidebar(self.video)
        self.sidebar.hide()

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

        self._place_widgets()
        self.sidebar.populate(channels, self._current_index, logo_loader)

        self.video.installEventFilter(self)
        self.video.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        self.video.setFocus()

        self._show_banner()
        self.sidebar.show_and_start_hide_timer()

    def exit(self):
        if not self.active:
            return

        self.active = False

        self._number_timer.stop()

        self.video.removeEventFilter(self)
        self.video.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.video.unsetCursor()

        self.banner.hide()
        self.sidebar.hide()

        self.exited.emit()

    # =========================
    # EVENTOS
    # =========================

    def eventFilter(self, obj, event):
        if not self.active:
            return False

        event_type = event.type()

        if event_type == QEvent.Type.Resize:
            self._place_widgets()
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
                self._toggle_sidebar()
            return True

        if key == Qt.Key.Key_Backspace:
            self._go_to_previous()
            return True

        if key == Qt.Key.Key_M:
            self.mute_requested.emit()
            return True

        if key == Qt.Key.Key_Tab:
            self._toggle_sidebar()
            return True

        if key == Qt.Key.Key_Escape:
            if self.sidebar.isVisible():
                self.sidebar.hide()
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
            self.sidebar.update_selection(self._current_index)
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
        slider = None
        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, "volume_slider"):
                slider = widget.volume_slider
                break

        volume = slider.value() if slider else 0
        self.banner.show_volume(volume)

    # =========================
    # SIDEBAR
    # =========================

    def _toggle_sidebar(self):
        if self.sidebar.isVisible():
            self.sidebar.hide()
            self.video.setCursor(Qt.CursorShape.BlankCursor)
        else:
            self.sidebar.show_and_start_hide_timer()
            self.video.setCursor(Qt.CursorShape.ArrowCursor)

    # =========================
    # POSICIONAMIENTO
    # =========================

    def _place_widgets(self):
        vw = self.video.width()
        vh = self.video.height()

        if vw <= 0 or vh <= 0:
            return

        self.sidebar.place(vw, vh)

        banner_w = min(400, int(vw * 0.35))
        banner_h = 90
        self.banner.setGeometry(20, vh - banner_h - 20, banner_w, banner_h)
