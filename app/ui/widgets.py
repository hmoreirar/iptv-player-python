import math

from PySide6.QtCore import (
    QEasingCurve,
    QPropertyAnimation,
    QRect,
    QSize,
    Qt,
    QTimer,
    Signal,
)
from PySide6.QtGui import (
    QColor,
    QFont,
    QFontMetrics,
    QIcon,
    QPainter,
    QPainterPath,
    QPen,
)
from PySide6.QtWidgets import (
    QGraphicsOpacityEffect,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QSlider,
    QStyle,
    QStyledItemDelegate,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.ui.icons import icon
from app.ui.theme import Colors

CHANNEL_ROLE = Qt.ItemDataRole.UserRole
CURRENT_ROLE = Qt.ItemDataRole.UserRole + 1
COUNT_ROLE = Qt.ItemDataRole.UserRole + 2
STAR_COLOR = QColor(Colors.accent)
MUTED_COLOR = QColor(Colors.muted_2)
TEXT_COLOR = QColor(Colors.text)
LIVE_COLOR = QColor(Colors.live)


def _font(size, weight=QFont.Weight.Normal, mono=False):
    font = QFont()
    font.setPointSizeF(size)
    font.setWeight(weight)

    if mono:
        font.setFamilies(["DejaVu Sans Mono", "monospace"])

    return font


def _star_path(rect):
    path = QPainterPath()
    center = rect.center()
    outer = min(rect.width(), rect.height()) / 2
    inner = outer * 0.45

    for point in range(10):
        angle = math.radians(-90 + point * 36)
        radius = outer if point % 2 == 0 else inner
        x = center.x() + math.cos(angle) * radius
        y = center.y() + math.sin(angle) * radius

        if point == 0:
            path.moveTo(x, y)
        else:
            path.lineTo(x, y)

    path.closeSubpath()

    return path


class ChannelDelegate(QStyledItemDelegate):
    def __init__(self, favorites, parent=None):
        super().__init__(parent)
        self.favorites = favorites

    def sizeHint(self, option, index):
        return QSize(0, 56)

    def paint(self, painter, option, index):
        channel = index.data(CHANNEL_ROLE)

        if not channel:
            return

        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = option.rect.adjusted(4, 2, -4, -2)
        current = bool(index.data(CURRENT_ROLE))
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)

        if current:
            painter.setBrush(QColor(Colors.surface_3))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 7, 7)
        elif selected or hovered:
            painter.setBrush(QColor(Colors.surface_2))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 7, 7)

        number_rect = QRect(rect.left() + 12, rect.top(), 34, rect.height())
        painter.setFont(_font(8.5, QFont.Weight.Bold, mono=True))
        painter.setPen(QColor(Colors.accent if current else Colors.muted_2))
        painter.drawText(
            number_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
            f"{index.row() + 1:02d}",
        )

        logo_rect = QRect(rect.left() + 54, rect.top() + 13, 40, 30)
        channel_icon = index.data(Qt.ItemDataRole.DecorationRole)

        if isinstance(channel_icon, QIcon) and not channel_icon.isNull():
            channel_icon.paint(painter, logo_rect)
        else:
            painter.setBrush(QColor(Colors.surface_2))
            painter.setPen(QPen(QColor(Colors.border), 1))
            painter.drawRoundedRect(logo_rect, 5, 5)
            initial = (channel.get("name") or "?")[:1].upper()
            painter.setFont(_font(11, QFont.Weight.Bold))
            painter.setPen(QColor(Colors.muted))
            painter.drawText(logo_rect, Qt.AlignmentFlag.AlignCenter, initial)

        star_rect = QRect(rect.right() - 38, rect.top() + 18, 20, 20)
        text_right = star_rect.left() - 8
        text_rect = QRect(logo_rect.right() + 11, rect.top() + 9, text_right - logo_rect.right() - 11, 20)
        name = channel.get("name") or "Canal"
        metrics = QFontMetrics(_font(10))
        painter.setFont(_font(10, QFont.Weight.DemiBold))
        painter.setPen(QColor(Colors.text if not current else Colors.text))
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            metrics.elidedText(name, Qt.TextElideMode.ElideRight, text_rect.width()),
        )

        group = channel.get("group") or "Sin categoria"
        group_width = text_rect.width() - (66 if current else 0)
        group_rect = QRect(text_rect.left(), rect.top() + 29, group_width, 16)
        group_metrics = QFontMetrics(_font(8.5))
        group_text = group_metrics.elidedText(
            group, Qt.TextElideMode.ElideRight, group_rect.width()
        )
        painter.setFont(_font(8.5))
        painter.setPen(QColor(Colors.muted))
        painter.drawText(
            group_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            group_text,
        )

        if current:
            live_x = group_rect.left() + group_metrics.horizontalAdvance(
                group_text
            ) + 8
            painter.setFont(_font(7, QFont.Weight.Bold))
            painter.setPen(LIVE_COLOR)
            painter.drawText(
                QRect(live_x, group_rect.top(), 54, group_rect.height()),
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
                "EN VIVO",
            )

        favorite = self.favorites.is_favorite(channel)
        painter.setPen(
            QPen(STAR_COLOR if favorite else MUTED_COLOR, 1.4)
        )
        painter.setBrush(STAR_COLOR if favorite else Qt.BrushStyle.NoBrush)
        painter.drawPath(_star_path(star_rect))

        painter.restore()


class CategoryDelegate(QStyledItemDelegate):
    def sizeHint(self, option, index):
        return QSize(0, 34)

    def paint(self, painter, option, index):
        painter.save()
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        rect = option.rect.adjusted(0, 1, 0, -1)
        selected = bool(option.state & QStyle.StateFlag.State_Selected)
        hovered = bool(option.state & QStyle.StateFlag.State_MouseOver)

        if selected:
            painter.setBrush(QColor(Colors.surface_3))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 6, 6)
        elif hovered:
            painter.setBrush(QColor(Colors.surface_2))
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawRoundedRect(rect, 6, 6)

        count = index.data(COUNT_ROLE)

        if count is not None:
            count_rect = QRect(rect.right() - 45, rect.top(), 34, rect.height())
            painter.setFont(_font(8, QFont.Weight.Medium, mono=True))
            painter.setPen(
                QColor(Colors.accent if selected else Colors.muted_2)
            )
            painter.drawText(
                count_rect,
                Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignRight,
                str(count),
            )

        name = index.data(Qt.ItemDataRole.DisplayRole) or ""
        text_rect = QRect(
            rect.left() + 10,
            rect.top(),
            rect.width() - 60,
            rect.height(),
        )
        metrics = QFontMetrics(_font(9.5, QFont.Weight.DemiBold if selected else QFont.Weight.Normal))
        painter.setFont(
            _font(
                9.5,
                QFont.Weight.DemiBold if selected else QFont.Weight.Normal,
            )
        )
        painter.setPen(QColor(Colors.text if selected else Colors.muted))
        painter.drawText(
            text_rect,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignLeft,
            metrics.elidedText(name, Qt.TextElideMode.ElideRight, text_rect.width()),
        )

        painter.restore()


class ChannelListWidget(QListWidget):
    play_requested = Signal(dict)
    favorite_toggled = Signal(dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setUniformItemSizes(True)
        self.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setFrameShape(QListWidget.Shape.NoFrame)
        self._star_press = False

    def _star_rect(self, rect):
        return QRect(rect.right() - 44, rect.top(), 44, rect.height())

    def mousePressEvent(self, event):
        self._star_press = False

        if event.button() == Qt.MouseButton.LeftButton:
            index = self.indexAt(event.position().toPoint())

            if index.isValid():
                rect = self.visualRect(index)

                if self._star_rect(rect).contains(event.position().toPoint()):
                    channel = index.data(CHANNEL_ROLE)

                    if channel:
                        self._star_press = True
                        self.favorite_toggled.emit(channel)
                        event.accept()
                        return

        super().mousePressEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton and not self._star_press:
            index = self.indexAt(event.position().toPoint())

            if index.isValid():
                channel = index.data(CHANNEL_ROLE)

                if channel:
                    self.play_requested.emit(channel)

        super().mouseReleaseEvent(event)

    def keyPressEvent(self, event):
        if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
            item = self.currentItem()

            if item is not None:
                channel = item.data(CHANNEL_ROLE)

                if channel:
                    self.play_requested.emit(channel)
                    event.accept()
                    return

        super().keyPressEvent(event)

    def set_current_url(self, url):
        for row in range(self.count()):
            item = self.item(row)
            channel = item.data(CHANNEL_ROLE)
            current = bool(channel and channel.get("url") == url)
            item.setData(CURRENT_ROLE, current)

        self.viewport().update()


class CategoryListWidget(QListWidget):
    category_activated = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setMouseTracking(True)
        self.setUniformItemSizes(True)
        self.setVerticalScrollMode(QListWidget.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setFrameShape(QListWidget.Shape.NoFrame)
        self.itemClicked.connect(self._on_clicked)

    def _on_clicked(self, item):
        group = item.data(CHANNEL_ROLE)

        if group:
            self.category_activated.emit(group)

    def populate(self, counts):
        self.clear()

        for group, count in counts:
            item = QListWidgetItem(group)
            item.setData(CHANNEL_ROLE, group)
            item.setData(COUNT_ROLE, count)
            self.addItem(item)

    def filter_text(self, text):
        term = text.strip().lower()

        for row in range(self.count()):
            item = self.item(row)
            item.setHidden(bool(term and term not in item.text().lower()))

    def select_group(self, group):
        self.clearSelection()

        if group is None:
            return

        for row in range(self.count()):
            item = self.item(row)

            if item.data(CHANNEL_ROLE) == group:
                item.setSelected(True)
                self.scrollToItem(item, QListWidget.ScrollHint.EnsureVisible)
                return


class ElidedLabel(QLabel):
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self._full_text = text

    def setText(self, text):
        self._full_text = text
        self._apply_elide()

    def full_text(self):
        return self._full_text

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._apply_elide()

    def _apply_elide(self):
        if not self._full_text:
            super().setText("")
            return

        width = max(10, self.width())
        text = self.fontMetrics().elidedText(
            self._full_text,
            Qt.TextElideMode.ElideRight,
            width,
        )
        super().setText(text)


class NowPlayingBar(QWidget):
    play_toggled = Signal()
    mute_toggled = Signal()
    volume_changed = Signal(int)
    favorite_toggled = Signal()
    fullscreen_toggled = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NowPlaying")
        self.setFixedHeight(66)
        self._channel = None
        self._paused = False

        layout = QHBoxLayout(self)
        layout.setContentsMargins(14, 8, 10, 8)
        layout.setSpacing(10)

        self.number = QLabel("---")
        self.number.setObjectName("ChannelNumber")
        self.number.setFixedWidth(36)
        layout.addWidget(self.number)

        info = QVBoxLayout()
        info.setContentsMargins(0, 0, 0, 0)
        info.setSpacing(1)

        self.name = ElidedLabel("Sin canal")
        self.name.setObjectName("ChannelName")

        group_row = QHBoxLayout()
        group_row.setContentsMargins(0, 0, 0, 0)
        group_row.setSpacing(7)

        self.live = QLabel("EN VIVO")
        self.live.setObjectName("LiveBadge")
        self.live.hide()

        self.group = QLabel("Elige un canal de la lista")
        self.group.setObjectName("ChannelGroup")

        group_row.addWidget(self.live)
        group_row.addWidget(self.group)
        group_row.addStretch()

        info.addWidget(self.name)
        info.addLayout(group_row)
        layout.addLayout(info, stretch=1)

        self.play_button = self._icon_button("play", "Reproducir / pausar", 34)
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.play_toggled)

        self.mute_button = self._icon_button("volume", "Silenciar", 32)
        self.mute_button.clicked.connect(self.mute_toggled)

        self.volume = QSlider(Qt.Orientation.Horizontal)
        self.volume.setRange(0, 100)
        self.volume.setValue(100)
        self.volume.setFixedWidth(104)
        self.volume.valueChanged.connect(self.volume_changed)

        self.favorite_button = self._icon_button(
            "star", "Guardar en favoritos (F)", 32
        )
        self.favorite_button.setEnabled(False)
        self.favorite_button.clicked.connect(self.favorite_toggled)

        self.fullscreen_button = self._icon_button(
            "fullscreen", "Pantalla completa (F11)", 32
        )
        self.fullscreen_button.clicked.connect(self.fullscreen_toggled)

        layout.addWidget(self.play_button)
        layout.addWidget(self.mute_button)
        layout.addWidget(self.volume)
        layout.addSpacing(4)
        layout.addWidget(self.favorite_button)
        layout.addWidget(self.fullscreen_button)

    def _icon_button(self, name, tooltip, size):
        button = QToolButton()
        button.setIcon(icon(name, Colors.text, 18))
        button.setIconSize(QSize(18, 18))
        button.setFixedSize(size, size)
        button.setToolTip(tooltip)
        button.setAccessibleName(tooltip)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        return button

    def set_channel(self, channel, favorite=False, paused=False, muted=False):
        self._channel = channel

        if channel is None:
            self.number.setText("---")
            self.name.setText("Sin canal")
            self.group.setText("Elige un canal de la lista")
            self.live.hide()
            self.play_button.setEnabled(False)
            self.favorite_button.setEnabled(False)
            self.set_favorite(False)
            self.set_paused(False)
            return

        self.number.setText(f"{channel.get('number', 0):03d}")
        self.name.setText(channel.get("name") or "Canal")
        self.group.setText(channel.get("group") or "Sin categoria")
        self.live.show()
        self.play_button.setEnabled(True)
        self.favorite_button.setEnabled(True)
        self.set_favorite(favorite)
        self.set_paused(paused)
        self.set_muted(muted)

    def set_number(self, number):
        self.number.setText(f"{number:03d}")

    def set_favorite(self, favorite):
        self.favorite_button.setIcon(
            icon(
                "star_filled" if favorite else "star",
                Colors.accent if favorite else Colors.muted,
                18,
            )
        )
        self.favorite_button.setToolTip(
            "Quitar de favoritos (F)" if favorite else "Guardar en favoritos (F)"
        )

    def set_paused(self, paused):
        self._paused = paused
        self.play_button.setIcon(
            icon("play" if paused else "pause", Colors.text, 18)
        )
        self.play_button.setToolTip(
            "Reanudar (Space)" if paused else "Pausar (Space)"
        )

    def set_muted(self, muted):
        self.mute_button.setIcon(
            icon("volume_off" if muted else "volume", Colors.text, 18)
        )
        self.mute_button.setToolTip(
            "Activar sonido (M)" if muted else "Silenciar (M)"
        )


class Toast(QLabel):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("Toast")
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.hide()

        self._effect = QGraphicsOpacityEffect(self)
        self._effect.setOpacity(1.0)
        self.setGraphicsEffect(self._effect)

        self._animation = QPropertyAnimation(self._effect, b"opacity", self)
        self._animation.setDuration(180)
        self._animation.setEasingCurve(QEasingCurve.Type.OutCubic)

        self._timer = QTimer(self)
        self._timer.setSingleShot(True)
        self._timer.timeout.connect(self._fade_out)

    def show_message(self, text, duration=2600):
        self.setText(text)
        self.adjustSize()
        self._effect.setOpacity(1.0)
        self.show()
        self.raise_()
        self._timer.start(duration)

    def _fade_out(self):
        self._animation.stop()
        self._animation.setStartValue(self._effect.opacity())
        self._animation.setEndValue(0.0)
        self._animation.finished.connect(self._hide_once)
        self._animation.start()

    def _hide_once(self):
        try:
            self._animation.finished.disconnect(self._hide_once)
        except (RuntimeError, TypeError):
            pass

        self.hide()

    def place(self, parent_rect):
        self.adjustSize()
        x = parent_rect.center().x() - self.width() // 2
        y = 72
        self.move(max(12, x), y)
