import os
import sys

os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

from PySide6.QtCore import QSize, Qt, QUrl, QSettings, QTimer, QShortcut
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from app.m3u.loader import PlaylistLoader
from app.player.mpv_player import MPVPlayer
from app.tv_mode import TVMode

FAVORITES = "__favoritos__"


class LogoLoader:
    """Descarga logos de canales de forma asíncrona y los aplica a los items."""

    def __init__(self):
        self.nam = QNetworkAccessManager()
        self.nam.finished.connect(self._on_finished)
        self._pending = {}
        self._cache = {}

    def load(self, item, url):
        if not url:
            return

        if url in self._cache:
            try:
                item.setIcon(self._cache[url])
            except RuntimeError:
                pass
            return

        reply = self.nam.get(QNetworkRequest(QUrl(url)))
        self._pending[reply] = (item, url)

    def _on_finished(self, reply):
        item, url = self._pending.pop(reply, None)
        data = reply.readAll()
        reply.deleteLater()

        if item is None or reply.error() != QNetworkReply.NoError:
            return

        pixmap = QPixmap()
        if pixmap.loadFromData(data):
            icon = QIcon(pixmap)
            self._cache[url] = icon
            try:
                item.setIcon(icon)
            except RuntimeError:
                pass


class IPTVPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("IPTV Player")
        self.resize(1200, 700)

        self.settings = QSettings("IPTVPlayer", "IPTVPlayer")

        self.channels = []
        self.current_filter = None
        self.search_term = ""
        self.favorites = set()
        self.current_url = None
        self.loader = None
        self.player = None
        self.logo_loader = LogoLoader()
        self.category_buttons = {}
        self.playlist_history = []

        self.setup_ui()
        self._load_settings()

        QTimer.singleShot(1000, self._auto_load_last)

    # =========================
    # INTERFAZ
    # =========================

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # -------------------------
        # BARRA LATERAL
        # -------------------------

        sidebar = QWidget()
        sidebar.setFixedWidth(240)
        self.sidebar = sidebar

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(15, 15, 15, 15)

        title = QLabel("IPTV Player")
        title.setStyleSheet("font-size: 22px; font-weight: bold;")

        open_button = QPushButton("📂 Abrir M3U")
        open_button.clicked.connect(self.open_m3u)

        url_button = QPushButton("🌐 Abrir URL")
        url_button.clicked.connect(self.open_m3u_url)

        self.loading_label = QLabel("⏳ Cargando playlist...")
        self.loading_label.setVisible(False)

        favorites_button = QPushButton("⭐ Favoritos")
        favorites_button.clicked.connect(self.show_favorites)

        all_button = QPushButton("📺 Todos")
        all_button.clicked.connect(self.show_all)

        self.tv_button = QPushButton("🖥️ Modo TV")
        self.tv_button.setCheckable(True)
        self.tv_button.clicked.connect(self.toggle_tv_mode)

        history_button = QPushButton("🕐 Historial")
        history_button.clicked.connect(self.show_history)

        sidebar_layout.addWidget(title)
        sidebar_layout.addSpacing(20)
        sidebar_layout.addWidget(open_button)
        sidebar_layout.addWidget(url_button)
        sidebar_layout.addWidget(self.loading_label)
        sidebar_layout.addSpacing(20)
        sidebar_layout.addWidget(history_button)
        sidebar_layout.addWidget(favorites_button)
        sidebar_layout.addWidget(all_button)
        sidebar_layout.addWidget(self.tv_button)
        sidebar_layout.addSpacing(10)

        categories_title = QLabel("Categorías")
        categories_title.setStyleSheet("font-weight: bold; color: #888;")
        sidebar_layout.addWidget(categories_title)

        self.category_container = QWidget()
        self.category_layout = QVBoxLayout(self.category_container)
        self.category_layout.setContentsMargins(0, 0, 0, 0)
        self.category_layout.setSpacing(4)

        scroll = QScrollArea()
        scroll.setWidget(self.category_container)
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)

        sidebar_layout.addWidget(scroll, stretch=1)

        # -------------------------
        # CONTENIDO PRINCIPAL
        # -------------------------

        content = QWidget()

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(15, 15, 15, 15)
        self.content_layout = content_layout
        self._content_margins = content_layout.contentsMargins()
        self._content_spacing = content_layout.spacing()

        self.search = QLineEdit()
        self.search.setPlaceholderText("🔍 Buscar canal...")
        self.search.textChanged.connect(self.on_search_changed)

        # Reproductor

        self.video = QWidget()
        self.video.setMinimumHeight(450)
        self.video.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.video.setStyleSheet(
            """
            QWidget {
                background-color: #111111;
            }
            """
        )

        # Controles

        controls = QWidget()
        self.controls_bar = controls

        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        self.play_button = QPushButton("▶ Reproducir")
        self.play_button.setEnabled(False)
        self.play_button.clicked.connect(self.toggle_play_pause)

        self.mute_button = QPushButton("🔊")
        self.mute_button.clicked.connect(self.toggle_mute)

        self.volume_slider = QSlider(Qt.Horizontal)
        self.volume_slider.setRange(0, 100)
        self.volume_slider.setValue(100)
        self.volume_slider.setFixedWidth(140)
        self.volume_slider.valueChanged.connect(self.on_volume_changed)

        fullscreen_button = QPushButton("⛶ Pantalla completa")
        fullscreen_button.clicked.connect(self.toggle_fullscreen)

        controls_layout.addWidget(self.play_button)
        controls_layout.addWidget(self.mute_button)
        controls_layout.addWidget(self.volume_slider)
        controls_layout.addStretch()
        controls_layout.addWidget(fullscreen_button)

        # Lista de canales

        self.channel_list = QListWidget()
        self.channel_list.setIconSize(QSize(40, 30))
        self.channel_list.itemClicked.connect(self.play_selected_channel)
        self.channel_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.channel_list.customContextMenuRequested.connect(self.on_context_menu)

        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #888;")

        content_layout.addWidget(self.search)
        content_layout.addWidget(self.video, stretch=3)
        content_layout.addWidget(controls)
        content_layout.addWidget(self.channel_list, stretch=1)
        content_layout.addWidget(self.status_label)

        # -------------------------
        # ENSAMBLAR
        # -------------------------

        main_layout.addWidget(sidebar)
        main_layout.addWidget(content)

        # -------------------------
        # MPV (init diferida - ver showEvent)
        # -------------------------

        self.player = None

        # -------------------------
        # MODO TV
        # -------------------------

        self.tv_mode = TVMode(self.video, self)
        self.tv_mode.channel_selected.connect(self.on_tv_channel_selected)
        self.tv_mode.volume_changed.connect(self.on_tv_volume_changed)
        self.tv_mode.mute_requested.connect(self.toggle_mute)
        self.tv_mode.exited.connect(self.on_tv_exited)

        # -------------------------
        # ATAJOS DE TECLADO
        # -------------------------

        QShortcut("Space", self, self.toggle_play_pause)
        QShortcut("M", self, self.toggle_mute)
        QShortcut("F11", self, self.toggle_fullscreen)
        QShortcut("Escape", self, self._on_escape)

    # =========================
    # ABRIR PLAYLISTS
    # =========================

    def open_m3u(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Abrir playlist M3U",
            "",
            "Playlist M3U (*.m3u *.m3u8);;Todos los archivos (*)",
        )

        if not file_path:
            return

        self._start_loading(file_path, is_url=False)

    def open_m3u_url(self):
        url, ok = QInputDialog.getText(
            self,
            "Abrir playlist desde Internet",
            "URL de la playlist M3U:",
        )

        if not ok or not url.strip():
            return

        self._start_loading(url.strip(), is_url=True)

    def _start_loading(self, source, is_url):
        if self.loader and self.loader.isRunning():
            self.loader.abort()
            self.loader.wait(3000)
            self.loader = None

        self.loading_label.setVisible(True)
        self.setEnabled(False)
        self.status_label.setText("")

        self._pending_source = source
        self._pending_is_url = is_url

        self.loader = PlaylistLoader(source, is_url)
        self.loader.finished.connect(self._on_load_finished)
        self.loader.failed.connect(self._on_load_failed)
        self.loader.start()

    def _on_load_finished(self, channels):
        self.setEnabled(True)
        self.loading_label.setVisible(False)

        source = self._pending_source
        is_url = self._pending_is_url
        self.loader = None
        self._pending_source = None
        self._pending_is_url = None

        self.channels = channels
        self.current_filter = None
        self.search_term = ""
        self.search.clear()

        self._save_playlist_source(source, is_url)
        self._rebuild_categories()
        self._apply_filters()

    def _on_load_failed(self, error):
        self.setEnabled(True)
        self.loading_label.setVisible(False)
        self.loader = None
        self._pending_source = None
        self._pending_is_url = None

        QMessageBox.critical(
            self,
            "Error",
            f"No se pudo cargar la playlist:\n\n{error}",
        )

    # =========================
    # CATEGORÍAS
    # =========================

    def _rebuild_categories(self):
        for button in self.category_buttons.values():
            button.deleteLater()

        self.category_buttons = {}

        while self.category_layout.count():
            child = self.category_layout.takeAt(0)

            if child.widget():
                child.widget().deleteLater()

        groups = []
        seen = set()

        for channel in self.channels:
            group = channel["group"]

            if group not in seen:
                seen.add(group)
                groups.append(group)

        for group in groups:
            button = QPushButton(f"🏷️ {group}")
            button.setCheckable(True)
            button.clicked.connect(
                lambda checked=False, g=group: self.filter_by_group(g)
            )
            self.category_layout.addWidget(button)
            self.category_buttons[group] = button

    def _update_category_buttons(self):
        for group, button in self.category_buttons.items():
            button.setChecked(self.current_filter == group)

    # =========================
    # FILTROS
    # =========================

    def filter_by_group(self, group):
        self.current_filter = group
        self._update_category_buttons()
        self._apply_filters()

    def show_all(self):
        self.current_filter = None
        self.search.clear()
        self._update_category_buttons()
        self._apply_filters()

    def show_favorites(self):
        self.current_filter = FAVORITES
        self.search.clear()
        self._update_category_buttons()
        self._apply_filters()

    def on_search_changed(self, text):
        self.search_term = text.strip().lower()
        self._apply_filters()

    def _current_channels(self):
        filtered = self.channels

        if self.current_filter == FAVORITES:
            filtered = [c for c in filtered if c["url"] in self.favorites]
        elif self.current_filter:
            filtered = [c for c in filtered if c["group"] == self.current_filter]

        if self.search_term:
            filtered = [c for c in filtered if self.search_term in c["name"].lower()]

        return filtered

    def _apply_filters(self):
        self._populate_list(self._current_channels())

    # =========================
    # LISTA
    # =========================

    def _populate_list(self, channels):
        self.channel_list.clear()

        for channel in channels:
            item = QListWidgetItem(channel["name"])
            item.setData(Qt.UserRole, channel)
            self.channel_list.addItem(item)

            logo = channel.get("logo", "")

            if logo:
                self.logo_loader.load(item, logo)

        count = len(channels)
        self.status_label.setText(
            f"{count} canal{'es' if count != 1 else ''}"
        )

    # =========================
    # FAVORITOS
    # =========================

    def toggle_favorite(self, channel):
        url = channel["url"]

        if url in self.favorites:
            self.favorites.remove(url)
            message = f"Quitado de favoritos: {channel['name']}"
        else:
            self.favorites.add(url)
            message = f"Añadido a favoritos: {channel['name']}"

        self._save_settings()
        self.status_label.setText(message)

        if self.current_filter == FAVORITES:
            self._apply_filters()

    def on_context_menu(self, position):
        item = self.channel_list.itemAt(position)

        if item is None:
            return

        channel = item.data(Qt.UserRole)

        if channel is None:
            return

        menu = QMenu(self)

        if channel["url"] in self.favorites:
            action_text = "⭐ Quitar de favoritos"
        else:
            action_text = "⭐ Añadir a favoritos"

        favorite_action = menu.addAction(action_text)
        play_action = menu.addAction("▶ Reproducir")

        chosen = menu.exec(self.channel_list.mapToGlobal(position))

        if chosen == favorite_action:
            self.toggle_favorite(channel)
        elif chosen == play_action:
            self._play_channel(channel)

    # =========================
    # REPRODUCCIÓN
    # =========================

    def _play_channel(self, channel):
        if channel is None or self.player is None:
            return

        self.current_url = channel["url"]
        self.play_button.setText("⏸ Pausa")
        self.play_button.setEnabled(True)

        self.player.play(channel["url"])
        self.status_label.setText(f"Reproduciendo: {channel['name']}")

    def play_selected_channel(self, item):
        channel = item.data(Qt.UserRole)

        if channel is None:
            return

        if self.current_url == channel["url"]:
            return

        self._play_channel(channel)

    def toggle_play_pause(self):
        if self.current_url is None or self.player is None:
            return

        self.player.toggle_pause()

        if self.player.is_paused():
            self.play_button.setText("▶ Reproducir")
        else:
            self.play_button.setText("⏸ Pausa")

    def on_volume_changed(self, value):
        if self.player is not None:
            self.player.set_volume(value)
        self.settings.setValue("player/volume", value)

    def toggle_mute(self):
        if self.player is None:
            return

        self.player.toggle_mute()

        if self.player.is_muted():
            self.mute_button.setText("🔇")
        else:
            self.mute_button.setText("🔊")

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _on_escape(self):
        if self.isFullScreen():
            self.showNormal()
        elif self.tv_button.isChecked():
            self.tv_mode.exit()

    # =========================
    # MODO TV
    # =========================

    def toggle_tv_mode(self, checked):
        if checked:
            self.enter_tv_mode()
        else:
            self.tv_mode.exit()

    def enter_tv_mode(self):
        channels = self._current_channels()

        if not channels:
            self.tv_button.setChecked(False)
            QMessageBox.information(
                self,
                "Modo TV",
                "Primero carga una playlist con canales.",
            )
            return

        self._set_ui_visible(False)
        self._set_tv_layout(True)
        self.showFullScreen()
        self.tv_mode.enter(channels, self.current_url, self.logo_loader)

    def on_tv_exited(self):
        self.tv_button.setChecked(False)
        self.showNormal()
        self._set_tv_layout(False)
        self._set_ui_visible(True)

    def on_tv_channel_selected(self, channel):
        self._play_channel(channel)

    def on_tv_volume_changed(self, delta):
        value = max(0, min(100, self.volume_slider.value() + delta))
        self.volume_slider.setValue(value)

    def _set_ui_visible(self, visible):
        for widget in (
            self.sidebar,
            self.search,
            self.controls_bar,
            self.status_label,
            self.channel_list,
        ):
            widget.setVisible(visible)

    def _set_tv_layout(self, tv_mode_active):
        if tv_mode_active:
            self.content_layout.setContentsMargins(0, 0, 0, 0)
            self.content_layout.setSpacing(0)
        else:
            self.content_layout.setContentsMargins(self._content_margins)
            self.content_layout.setSpacing(self._content_spacing)

    def on_playback_error(self, message):
        self.current_url = None
        self.play_button.setText("▶ Reproducir")
        self.play_button.setEnabled(False)

        QMessageBox.warning(self, "Error de reproducción", message)

    # =========================
    # PERSISTENCIA
    # =========================

    def _load_settings(self):
        geometry = self.settings.value("window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)

        volume = self.settings.value("player/volume", 100, type=int)
        self.volume_slider.setValue(volume)

        favorites = self.settings.value("favorites/urls", [], type=list)
        self.favorites = set(favorites)

        self._last_source = self.settings.value("playlist/last_source", "")
        self._last_is_url = self.settings.value("playlist/last_is_url", False, type=bool)
        self.playlist_history = self.settings.value("playlist/history", [], type=list)

    def _save_settings(self):
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("player/volume", self.volume_slider.value())
        self.settings.setValue("favorites/urls", list(self.favorites))
        self.settings.setValue("playlist/history", self.playlist_history)

    def _save_playlist_source(self, source, is_url):
        self._last_source = source
        self._last_is_url = is_url
        self.settings.setValue("playlist/last_source", source)
        self.settings.setValue("playlist/last_is_url", is_url)

        entry = f"{'[URL] ' if is_url else ''}{source}"
        if entry in self.playlist_history:
            self.playlist_history.remove(entry)
        self.playlist_history.insert(0, entry)
        self.playlist_history = self.playlist_history[:10]
        self.settings.setValue("playlist/history", self.playlist_history)

    # =========================
    # HISTORIAL
    # =========================

    def show_history(self):
        if not self.playlist_history:
            QMessageBox.information(
                self,
                "Historial",
                "No hay playlists en el historial.",
            )
            return

        items = []
        for entry in self.playlist_history:
            items.append(entry)

        item, ok = QInputDialog.getItem(
            self,
            "Historial de Playlists",
            "Selecciona una playlist:",
            items,
            0,
            False,
        )

        if ok and item:
            is_url = item.startswith("[URL] ")
            source = item[6:] if is_url else item
            self._start_loading(source, is_url=is_url)

    def _auto_load_last(self):
        if not self._last_source:
            return

        reply = QMessageBox.question(
            self,
            "Cargar última playlist",
            f"¿Deseas cargar la última playlist?\n\n{self._last_source}",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.Yes,
        )

        if reply == QMessageBox.Yes:
            self._start_loading(self._last_source, is_url=self._last_is_url)

    # =========================
    # INICIALIZACIÓN DIFERIDA
    # =========================

    def showEvent(self, event):
        super().showEvent(event)

        if self.player is None:
            self.player = MPVPlayer(self.video.winId())
            self.player.error_occurred.connect(self.on_playback_error)

    # =========================
    # CERRAR APLICACIÓN
    # =========================

    def closeEvent(self, event):
        self._save_settings()

        if self.loader and self.loader.isRunning():
            self.loader.abort()
            self.loader.wait(3000)

        if self.player:
            self.player.destroy()

        event.accept()


def main():
    app = QApplication(sys.argv)

    window = IPTVPlayer()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
