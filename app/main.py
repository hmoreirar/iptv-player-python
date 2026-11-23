import os
import sys
from collections import Counter
from pathlib import Path
from urllib.parse import urlparse

os.environ.setdefault("QT_QPA_PLATFORM", "xcb")

from PySide6.QtCore import QEvent, QPoint, QSettings, QSize, Qt, QTimer, QUrl
from PySide6.QtGui import QIcon, QPixmap, QShortcut
from PySide6.QtNetwork import QNetworkAccessManager, QNetworkReply, QNetworkRequest
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QLineEdit,
    QListWidgetItem,
    QMainWindow,
    QMenu,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from app.favorites import FavoritesStore
from app.m3u.iptv_org import (
    DEFAULT_PLAYLIST_URL,
    MetadataWorker,
    build_playlist_url,
    metadata_label,
)
from app.m3u.loader import PlaylistLoader
from app.player.mpv_player import MPVPlayer
from app.tv_mode import TVMode
from app.ui.icons import icon
from app.ui.theme import Colors, apply_theme
from app.ui.widgets import (
    CHANNEL_ROLE,
    CURRENT_ROLE,
    CategoryDelegate,
    CategoryListWidget,
    ChannelDelegate,
    ChannelListWidget,
    ElidedLabel,
    NowPlayingBar,
    Toast,
)

FAVORITES = "__favoritos__"

LARGE_PLAYLIST = 1000
SEARCH_DEBOUNCE_MS = 180
LOGO_DEBOUNCE_MS = 120
AUTO_SKIP_LIMIT = 10
AUTO_SKIP_DELAY_MS = 700
LOADED_STABLE_MS = 8000


class LogoLoader:
    """Descarga logos de canales de forma asíncrona y los aplica a los items."""

    def __init__(self):
        self.nam = QNetworkAccessManager()
        self.nam.finished.connect(self._on_finished)
        self._pending = {}
        self._inflight = {}
        self._cache = {}

    def load(self, item, url):
        if not url:
            return

        if url in self._cache:
            self._apply(item, self._cache[url])
            return

        if url in self._inflight:
            if item not in self._inflight[url]:
                self._inflight[url].append(item)
            return

        reply = self.nam.get(QNetworkRequest(QUrl(url)))
        self._pending[reply] = url
        self._inflight[url] = [item]

    def _apply(self, item, channel_icon):
        try:
            item.setIcon(channel_icon)
        except RuntimeError:
            pass

    def _on_finished(self, reply):
        url = self._pending.pop(reply, None)
        items = self._inflight.pop(url, [])
        data = reply.readAll()
        reply.deleteLater()

        if url is None or reply.error() != QNetworkReply.NoError:
            return

        pixmap = QPixmap()
        if not pixmap.loadFromData(data):
            return

        channel_icon = QIcon(pixmap)
        self._cache[url] = channel_icon

        for item in items:
            self._apply(item, channel_icon)


class MetadataDialog(QDialog):
    """Selector con busqueda para listas grandes."""

    def __init__(self, title, items, parent=None):
        super().__init__(parent)

        self.setWindowTitle(title)
        self.resize(460, 520)
        self._items = items

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(10)

        self.search = QLineEdit()
        self.search.setPlaceholderText("Buscar...")
        self.search.addAction(
            icon("search", Colors.muted, 16),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.search.textChanged.connect(self._filter)
        layout.addWidget(self.search)

        self.list = CategoryListWidget()
        self.list.setItemDelegate(CategoryDelegate(self.list))
        self.list.itemDoubleClicked.connect(lambda _item: self._accept_selection())
        layout.addWidget(self.list, stretch=1)

        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._accept_selection)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self._populate("")
        self.search.setFocus()

    def _populate(self, term):
        self.list.clear()

        for item in self._items:
            label = metadata_label(item)

            if term and term not in label.lower():
                continue

            entry = QListWidgetItem(label)
            entry.setData(CHANNEL_ROLE, item["code"])
            self.list.addItem(entry)

        if self.list.count():
            self.list.setCurrentRow(0)

    def _filter(self, text):
        self._populate(text.strip().lower())

    def _accept_selection(self):
        if self.selected_code() is None:
            return

        self.accept()

    def selected_code(self):
        item = self.list.currentItem()
        return item.data(CHANNEL_ROLE) if item else None


class IPTVPlayer(QMainWindow):
    def __init__(self):
        super().__init__()

        self.setWindowTitle("IPTV Player")
        self.resize(1280, 800)
        self.setMinimumSize(1100, 700)

        icon_path = Path(__file__).resolve().parent / "ui" / "assets" / "iptv-player.svg"

        if not icon_path.exists():
            icon_path = (
                Path(__file__).resolve().parent
                / "app"
                / "ui"
                / "assets"
                / "iptv-player.svg"
            )

        self.setWindowIcon(QIcon(str(icon_path)))

        self.settings = QSettings("IPTVPlayer", "IPTVPlayer")
        self.favorites_store = FavoritesStore(self.settings)

        self.channels = []
        self.current_filter = None
        self.search_term = ""
        self.current_url = None
        self.current_channel = None
        self.current_number = 0
        self.loader = None
        self.player = None
        self.logo_loader = LogoLoader()
        self.playlist_history = []
        self._pending_warning = None
        self._metadata_cache = {}
        self._metadata_workers = {}
        self._consecutive_errors = 0
        self._retired_loaders = []

        self._search_timer = QTimer(self)
        self._search_timer.setSingleShot(True)
        self._search_timer.timeout.connect(self._apply_filters)

        self._logo_timer = QTimer(self)
        self._logo_timer.setSingleShot(True)
        self._logo_timer.timeout.connect(self._load_visible_logos)

        self._stable_timer = QTimer(self)
        self._stable_timer.setSingleShot(True)
        self._stable_timer.timeout.connect(self._reset_error_counter)

        self.setup_ui()
        self._load_settings()

        QTimer.singleShot(900, self._auto_load_last)

    # =========================
    # INTERFAZ
    # =========================

    def setup_ui(self):
        root = QWidget()
        root.setObjectName("Root")
        self.setCentralWidget(root)
        self.root = root

        self.root_layout = QVBoxLayout(root)
        self.root_layout.setContentsMargins(0, 0, 0, 0)
        self.root_layout.setSpacing(0)

        self.topbar = self._build_topbar()
        self.root_layout.addWidget(self.topbar)

        body = QWidget()
        self.body_layout = QHBoxLayout(body)
        self.body_layout.setContentsMargins(16, 14, 16, 16)
        self.body_layout.setSpacing(12)

        self.root_layout.addWidget(body, stretch=1)

        self.sidebar = self._build_sidebar()
        self.center = self._build_center()
        self.channel_panel = self._build_channel_panel()

        self.body_layout.addWidget(self.sidebar)
        self.body_layout.addWidget(self.center, stretch=1)
        self.body_layout.addWidget(self.channel_panel)

        self.toast = Toast(root)

        self.tv_mode = TVMode(self.video, self)
        self.tv_mode.channel_selected.connect(self.on_tv_channel_selected)
        self.tv_mode.volume_changed.connect(self.on_tv_volume_changed)
        self.tv_mode.mute_requested.connect(self.toggle_mute)
        self.tv_mode.favorite_requested.connect(self._toggle_current_favorite)
        self.tv_mode.exited.connect(self.on_tv_exited)

        self.shortcuts = [
            QShortcut("Space", self, self.toggle_play_pause),
            QShortcut("M", self, self.toggle_mute),
            QShortcut("F11", self, self.toggle_fullscreen),
            QShortcut("Escape", self, self._on_escape),
            QShortcut("Ctrl+F", self, self._focus_search),
            QShortcut("/", self, self._focus_search),
        ]
        self.favorite_shortcut = QShortcut(
            "F", self, self._toggle_current_favorite
        )
        self.shortcuts.append(self.favorite_shortcut)

        self.search.installEventFilter(self)

    def _build_topbar(self):
        bar = QWidget()
        bar.setObjectName("TopBar")
        bar.setFixedHeight(60)

        layout = QHBoxLayout(bar)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(10)

        brand = QLabel("IPTV")
        brand.setObjectName("Brand")
        brand.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred)
        brand_accent = QLabel("Player")
        brand_accent.setObjectName("BrandAccent")
        brand_accent.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Preferred
        )

        layout.addWidget(brand)
        layout.addWidget(brand_accent)
        layout.addSpacing(14)

        self.search = QLineEdit()
        self.search.setObjectName("Search")
        self.search.setPlaceholderText("Buscar canal...")
        self.search.setClearButtonEnabled(True)
        self.search.setFixedWidth(380)
        self.search.addAction(
            icon("search", Colors.muted, 16),
            QLineEdit.ActionPosition.LeadingPosition,
        )
        self.search.textChanged.connect(self.on_search_changed)
        layout.addWidget(self.search)
        layout.addStretch(1)

        self.loading_label = QLabel("")
        self.loading_label.setObjectName("SourceLabel")
        self.loading_label.hide()
        layout.addWidget(self.loading_label)

        open_button = QPushButton("Abrir")
        open_button.setIcon(icon("folder", Colors.muted, 16))
        open_button.setIconSize(QSize(16, 16))
        open_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )

        open_menu = QMenu(open_button)
        local_action = open_menu.addAction(
            icon("folder", Colors.muted, 16),
            "Archivo M3U...",
        )
        url_action = open_menu.addAction(
            icon("link", Colors.muted, 16),
            "Desde URL...",
        )
        local_action.triggered.connect(self.open_m3u)
        url_action.triggered.connect(self.open_m3u_url)
        open_button.setMenu(open_menu)
        layout.addWidget(open_button)

        self.iptv_button = QPushButton("IPTV-org")
        self.iptv_button.setIcon(icon("grid", Colors.muted, 16))
        self.iptv_button.setIconSize(QSize(16, 16))
        self.iptv_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.iptv_button.clicked.connect(self.show_iptv_org_menu)
        layout.addWidget(self.iptv_button)

        self.tv_button = QPushButton("Modo TV")
        self.tv_button.setObjectName("PrimaryButton")
        self.tv_button.setIcon(icon("tv", Colors.accent_text, 16))
        self.tv_button.setIconSize(QSize(16, 16))
        self.tv_button.setSizePolicy(
            QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed
        )
        self.tv_button.clicked.connect(self.toggle_tv_mode)
        layout.addWidget(self.tv_button)

        return bar

    def _build_sidebar(self):
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(208)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(12, 14, 12, 12)
        layout.setSpacing(5)

        section = QLabel("BIBLIOTECA")
        section.setObjectName("SectionLabel")
        layout.addWidget(section)

        self.nav_all = self._nav_button("Todos", "grid")
        self.nav_favorites = self._nav_button("Favoritos", "star")
        self.nav_history = self._nav_button("Historial", "history")

        self.nav_all.clicked.connect(self.show_all)
        self.nav_favorites.clicked.connect(self.show_favorites)
        self.nav_history.clicked.connect(self.show_history)

        layout.addWidget(self.nav_all)
        layout.addWidget(self.nav_favorites)
        layout.addWidget(self.nav_history)
        layout.addSpacing(6)

        self.auto_skip_check = QCheckBox("Saltar canales con error")
        self.auto_skip_check.setToolTip(
            "En Modo TV, pasa al canal siguiente cuando falla la reproduccion."
        )
        self.auto_skip_check.stateChanged.connect(self._save_auto_skip)
        layout.addWidget(self.auto_skip_check)

        layout.addSpacing(10)

        categories_row = QHBoxLayout()
        categories_row.setContentsMargins(0, 0, 0, 0)

        categories_title = QLabel("CATEGORIAS")
        categories_title.setObjectName("SectionLabel")
        self.categories_count = QLabel("0")
        self.categories_count.setObjectName("CountLabel")

        categories_row.addWidget(categories_title)
        categories_row.addStretch()
        categories_row.addWidget(self.categories_count)
        layout.addLayout(categories_row)

        self.category_search = QLineEdit()
        self.category_search.setObjectName("CategorySearch")
        self.category_search.setPlaceholderText("Filtrar categorias")
        self.category_search.textChanged.connect(self._filter_categories)
        layout.addWidget(self.category_search)

        self.category_list = CategoryListWidget()
        self.category_list.setItemDelegate(CategoryDelegate(self.category_list))
        self.category_list.category_activated.connect(self.filter_by_group)
        layout.addWidget(self.category_list, stretch=1)

        source = QFrame()
        source.setObjectName("SourceCard")
        source_layout = QVBoxLayout(source)
        source_layout.setContentsMargins(10, 8, 8, 8)
        source_layout.setSpacing(2)

        source_header = QHBoxLayout()
        source_header.setContentsMargins(0, 0, 0, 0)
        source_title = QLabel("FUENTE")
        source_title.setObjectName("SectionLabel")

        self.refresh_button = QToolButton()
        self.refresh_button.setIcon(icon("refresh", Colors.muted, 14))
        self.refresh_button.setIconSize(QSize(14, 14))
        self.refresh_button.setToolTip("Actualizar playlist actual")
        self.refresh_button.setAccessibleName("Actualizar playlist")
        self.refresh_button.clicked.connect(self._refresh_current_playlist)

        source_header.addWidget(source_title)
        source_header.addStretch()
        source_header.addWidget(self.refresh_button)
        source_layout.addLayout(source_header)

        self.source_name = ElidedLabel("Sin playlist")
        self.source_name.setObjectName("SourceName")
        source_layout.addWidget(self.source_name)

        layout.addWidget(source)

        return sidebar

    def _nav_button(self, text, icon_name):
        button = QPushButton(text)
        button.setIcon(icon(icon_name, Colors.muted, 17))
        button.setIconSize(QSize(17, 17))
        button.setCheckable(True)
        button.setCursor(Qt.CursorShape.PointingHandCursor)
        button.setFixedHeight(36)
        button.setStyleSheet(
            f"""
            QPushButton {{
                background: transparent;
                border: none;
                border-radius: 7px;
                color: {Colors.muted};
                font-size: 13px;
                padding: 6px 10px;
                text-align: left;
            }}
            QPushButton:hover {{
                background: {Colors.surface_2};
                color: {Colors.text};
            }}
            QPushButton:checked {{
                background: {Colors.surface_3};
                color: {Colors.text};
                font-weight: 700;
            }}
            QPushButton:focus {{
                border: 1px solid {Colors.accent};
            }}
            """
        )
        return button

    def _build_center(self):
        center = QWidget()
        self.center_layout = QVBoxLayout(center)
        self.center_layout.setContentsMargins(0, 0, 0, 0)
        self.center_layout.setSpacing(12)

        self.video = QWidget()
        self.video.setMinimumHeight(320)
        self.video.setAttribute(Qt.WidgetAttribute.WA_NativeWindow)
        self.video.setStyleSheet("background-color: #000000;")

        stage = QWidget()
        stage.setObjectName("VideoStage")
        stage_layout = QVBoxLayout(stage)
        stage_layout.setContentsMargins(1, 1, 1, 1)
        stage_layout.setSpacing(0)
        stage_layout.addWidget(self.video)

        self.center_layout.addWidget(stage, stretch=1)

        self.now_bar = NowPlayingBar()
        self.now_bar.play_toggled.connect(self.toggle_play_pause)
        self.now_bar.mute_toggled.connect(self.toggle_mute)
        self.now_bar.volume_changed.connect(self.on_volume_changed)
        self.now_bar.favorite_toggled.connect(self._toggle_current_favorite)
        self.now_bar.fullscreen_toggled.connect(self.toggle_fullscreen)
        self.center_layout.addWidget(self.now_bar)

        return center

    def _build_channel_panel(self):
        panel = QWidget()
        panel.setObjectName("ChannelPanel")
        panel.setFixedWidth(344)

        layout = QVBoxLayout(panel)
        layout.setContentsMargins(10, 14, 10, 12)
        layout.setSpacing(8)

        header = QHBoxLayout()
        header.setContentsMargins(2, 0, 2, 0)

        title = QLabel("CANALES")
        title.setObjectName("SectionLabel")

        self.channel_count = QLabel("0")
        self.channel_count.setObjectName("CountLabel")

        header.addWidget(title)
        header.addStretch()
        header.addWidget(self.channel_count)
        layout.addLayout(header)

        self.scope_label = QLabel("Todos")
        self.scope_label.setObjectName("SourceLabel")
        layout.addWidget(self.scope_label)

        self.channel_list = ChannelListWidget()
        self.channel_list.setItemDelegate(
            ChannelDelegate(self.favorites_store, self.channel_list)
        )
        self.channel_list.play_requested.connect(self._play_channel)
        self.channel_list.favorite_toggled.connect(self._toggle_favorite)
        self.channel_list.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.channel_list.customContextMenuRequested.connect(
            self.on_context_menu
        )
        self.channel_list.verticalScrollBar().valueChanged.connect(
            self._schedule_visible_logos
        )
        layout.addWidget(self.channel_list, stretch=1)

        self.empty_state = QWidget()
        empty_layout = QVBoxLayout(self.empty_state)
        empty_layout.setContentsMargins(18, 0, 18, 40)
        empty_layout.addStretch()

        self.empty_title = QLabel("Sin canales")
        self.empty_title.setObjectName("EmptyTitle")
        self.empty_title.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.empty_body = QLabel("Abre una playlist para empezar.")
        self.empty_body.setObjectName("EmptyBody")
        self.empty_body.setWordWrap(True)
        self.empty_body.setAlignment(Qt.AlignmentFlag.AlignCenter)

        empty_layout.addWidget(self.empty_title)
        empty_layout.addWidget(self.empty_body)
        empty_layout.addStretch()

        layout.addWidget(self.empty_state, stretch=1)
        self.empty_state.hide()

        return panel

    # =========================
    # ATAJOS Y BUSQUEDA
    # =========================

    def _focus_search(self):
        self.search.setFocus()
        self.search.selectAll()

    def eventFilter(self, obj, event):
        if obj is self.search:
            if event.type() == QEvent.Type.FocusIn:
                for shortcut in getattr(self, "shortcuts", []):
                    shortcut.setEnabled(False)
            elif event.type() == QEvent.Type.FocusOut:
                for shortcut in getattr(self, "shortcuts", []):
                    shortcut.setEnabled(True)

        return super().eventFilter(obj, event)

    def on_search_changed(self, text):
        self.search_term = text.strip().lower()
        self._search_timer.start(SEARCH_DEBOUNCE_MS)

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

    def _start_loading(self, source, is_url, force_refresh=False):
        if self.loader and self.loader.isRunning():
            self.loader.abort()

            if not self.loader.wait(3000):
                retired = self.loader
                self._retired_loaders.append(retired)
                retired.finished.connect(
                    lambda loader=retired: self._release_loader(loader)
                )

            self.loader = None

        self.loading_label.setText("Cargando...")
        self.loading_label.show()
        self._pending_warning = None

        self._pending_source = source
        self._pending_is_url = is_url

        self.loader = PlaylistLoader(source, is_url, force_refresh=force_refresh)
        self.loader.loaded.connect(self._on_load_finished)
        self.loader.failed.connect(self._on_load_failed)
        self.loader.warning.connect(self._on_loader_warning)
        self.loader.finished.connect(
            lambda loader=self.loader: self._release_loader(loader)
        )
        self.loader.start()

    def _release_loader(self, loader):
        if loader in self._retired_loaders:
            self._retired_loaders.remove(loader)

        if loader is self.loader:
            self.loader = None

        loader.deleteLater()

    def _on_loader_warning(self, message):
        self._pending_warning = message

    def _on_load_finished(self, channels):
        self.loading_label.hide()

        source = self._pending_source
        is_url = self._pending_is_url
        warning = self._pending_warning
        self._pending_source = None
        self._pending_is_url = None
        self._pending_warning = None

        self.channels = channels
        self.current_filter = self._initial_filter(channels)
        self.search_term = ""
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)
        self.category_search.clear()

        self._save_playlist_source(source, is_url)
        self._rebuild_categories()
        self._apply_filters()
        self._update_nav_state()
        self._update_source_label(source, is_url)

        if warning:
            self.toast.show_message(warning, 4200)

    def _initial_filter(self, channels):
        if len(channels) <= LARGE_PLAYLIST:
            return None

        groups = Counter()

        for channel in channels:
            for group in channel.get("groups") or [channel["group"]]:
                groups[group] += 1

        for preferred in (
            "News",
            "Entertainment",
            "Movies",
            "Sports",
            "Documentary",
            "Kids",
            "Music",
        ):
            if preferred in groups:
                return preferred

        if groups:
            return sorted(groups)[0]

        return None

    def _on_load_failed(self, error):
        self.loading_label.hide()
        self._pending_source = None
        self._pending_is_url = None
        self._pending_warning = None

        self.toast.show_message(
            f"No se pudo cargar la playlist: {str(error)[:140]}",
            5200,
        )

    # =========================
    # CATEGORIAS
    # =========================

    def _rebuild_categories(self):
        counts = Counter()

        for channel in self.channels:
            for group in channel.get("groups") or [channel["group"]]:
                counts[group] += 1

        ordered = sorted(counts.items(), key=lambda item: item[0].lower())

        self.category_list.populate(ordered)
        self.categories_count.setText(str(len(ordered)))
        self.category_list.select_group(self.current_filter)

    def _filter_categories(self, text):
        self.category_list.filter_text(text)

    def _sync_category_selection(self):
        group = None if self.current_filter in (None, FAVORITES) else self.current_filter
        self.category_list.select_group(group)

    def _update_nav_state(self):
        self.nav_all.setChecked(self.current_filter is None)
        self.nav_favorites.setChecked(self.current_filter == FAVORITES)

        total = len(self.channels)
        self.nav_all.setText(f"Todos  {total}" if total else "Todos")

        favorite_count = self.favorites_store.count()
        self.nav_favorites.setText(
            f"Favoritos  {favorite_count}" if favorite_count else "Favoritos"
        )

        self.scope_label.setText(
            "Favoritos"
            if self.current_filter == FAVORITES
            else self.current_filter or "Todos"
        )

    def filter_by_group(self, group):
        self.current_filter = group
        self._reset_search()
        self._sync_category_selection()
        self._update_nav_state()
        self._apply_filters()

    def show_all(self):
        self.current_filter = None
        self._reset_search()
        self._sync_category_selection()
        self._update_nav_state()
        self._apply_filters()

    def show_favorites(self):
        self.current_filter = FAVORITES
        self._reset_search()
        self._sync_category_selection()
        self._update_nav_state()
        self._apply_filters()

    def _reset_search(self):
        self.search_term = ""
        self._search_timer.stop()
        self.search.blockSignals(True)
        self.search.clear()
        self.search.blockSignals(False)

    # =========================
    # FILTROS Y LISTA
    # =========================

    def _current_channels(self):
        if self.current_filter == FAVORITES:
            filtered = self.favorites_store.merge(self.channels)
        elif self.search_term:
            filtered = self.channels
        elif self.current_filter:
            filtered = [
                channel
                for channel in self.channels
                if self.current_filter
                in (channel.get("groups") or [channel["group"]])
            ]
        else:
            filtered = self.channels

        if self.search_term:
            filtered = [
                channel
                for channel in filtered
                if self.search_term in channel["name"].lower()
            ]

        return filtered

    def _apply_filters(self):
        channels = self._current_channels()
        self._populate_list(channels)
        self._update_empty_state(len(channels))
        self._update_nav_state()

        if self.search_term:
            self.scope_label.setText("Busqueda")
            self.category_list.clearSelection()
        elif self.current_filter == FAVORITES:
            self.scope_label.setText("Favoritos")
        else:
            self.scope_label.setText(self.current_filter or "Todos")
            self._sync_category_selection()

        if self.current_channel is not None:
            for index, channel in enumerate(channels, start=1):
                if channel.get("url") == self.current_channel.get("url"):
                    self.current_number = index
                    self.now_bar.set_number(index)
                    break

    def _populate_list(self, channels):
        self.channel_list.setUpdatesEnabled(False)

        try:
            self.channel_list.clear()

            for channel in channels:
                item = QListWidgetItem(channel["name"])
                item.setData(CHANNEL_ROLE, channel)

                if self.current_channel and (
                    channel.get("url") == self.current_channel.get("url")
                ):
                    item.setData(CURRENT_ROLE, True)

                self.channel_list.addItem(item)
        finally:
            self.channel_list.setUpdatesEnabled(True)

        self.channel_count.setText(str(len(channels)))

        if self.current_channel is not None:
            self.channel_list.set_current_url(self.current_channel.get("url"))

        self._schedule_visible_logos()

    def _update_empty_state(self, count):
        if count:
            self.channel_list.show()
            self.empty_state.hide()
            return

        self.channel_list.hide()
        self.empty_state.show()

        if self.current_filter == FAVORITES:
            if self.search_term:
                self.empty_title.setText("Sin resultados")
                self.empty_body.setText(
                    "Prueba otro nombre o limpia la busqueda para ver la lista."
                )
            else:
                self.empty_title.setText("Sin favoritos")
                self.empty_body.setText(
                    "Marca un canal con la estrella del panel o con la tecla F."
                )
        elif self.search_term:
            self.empty_title.setText("Sin resultados")
            self.empty_body.setText(
                "Prueba otro nombre o limpia la busqueda para ver la lista."
            )
        elif not self.channels:
            self.empty_title.setText("Sin playlist")
            self.empty_body.setText(
                "Abre un archivo M3U o carga IPTV-org desde la barra superior."
            )
        else:
            self.empty_title.setText("Categoria vacia")
            self.empty_body.setText(
                "Esta categoria no tiene canales. Elige otra en la barra lateral."
            )

    def _schedule_visible_logos(self, *_args):
        self._logo_timer.start(LOGO_DEBOUNCE_MS)

    def _load_visible_logos(self):
        viewport = self.channel_list.viewport()
        top = self.channel_list.indexAt(QPoint(0, 0))
        bottom = self.channel_list.indexAt(
            QPoint(0, max(0, viewport.height() - 1))
        )

        if not top.isValid():
            return

        start = top.row()
        end = bottom.row() if bottom.isValid() else start

        for row in range(max(0, start - 1), min(self.channel_list.count(), end + 2)):
            item = self.channel_list.item(row)

            if item is None:
                continue

            channel = item.data(CHANNEL_ROLE)

            if not channel:
                continue

            logo = channel.get("logo", "")

            if logo:
                self.logo_loader.load(item, logo)

    # =========================
    # FAVORITOS
    # =========================

    def _toggle_current_favorite(self):
        if self.current_channel is None:
            return

        self._toggle_favorite(self.current_channel)

    def _toggle_favorite(self, channel):
        added = self.favorites_store.toggle(channel)

        if self.current_channel and (
            channel.get("url") == self.current_channel.get("url")
        ):
            self.now_bar.set_favorite(added)

        self.channel_list.viewport().update()
        self._update_nav_state()

        name = channel.get("name") or "Canal"
        message = (
            f"Anadido a favoritos: {name}"
            if added
            else f"Quitado de favoritos: {name}"
        )
        self.toast.show_message(message)

        if self.tv_mode.active:
            self.tv_mode.show_status(
                "Guardado en favoritos" if added else "Quitado de favoritos",
                name,
            )

        if self.current_filter == FAVORITES:
            self._apply_filters()
        elif self.favorites_store.count() == 0:
            self.channel_list.viewport().update()

    def toggle_favorite(self, channel):
        self._toggle_favorite(channel)

    def on_context_menu(self, position):
        item = self.channel_list.itemAt(position)

        if item is None:
            return

        channel = item.data(CHANNEL_ROLE)

        if channel is None:
            return

        menu = QMenu(self)
        favorite = self.favorites_store.is_favorite(channel)

        favorite_action = menu.addAction(
            icon("star_filled" if favorite else "star", Colors.accent, 16),
            "Quitar de favoritos" if favorite else "Guardar en favoritos",
        )
        play_action = menu.addAction(icon("play", Colors.muted, 16), "Reproducir")

        chosen = menu.exec(self.channel_list.mapToGlobal(position))

        if chosen == favorite_action:
            self._toggle_favorite(channel)
        elif chosen == play_action:
            self._play_channel(channel)

    # =========================
    # REPRODUCCION
    # =========================

    def _play_channel(self, channel):
        if channel is None or self.player is None:
            return

        self.current_url = channel["url"]
        self.current_channel = channel
        self.current_number = self._channel_number(channel)
        self._stable_timer.stop()

        self.now_bar.set_channel(
            channel,
            favorite=self.favorites_store.is_favorite(channel),
            paused=False,
            muted=self.player.is_muted(),
        )
        self.now_bar.set_number(self.current_number)
        self.channel_list.set_current_url(channel["url"])

        self.player.play(channel["url"], channel.get("headers"))

    def _channel_number(self, channel):
        for index, candidate in enumerate(self._current_channels(), start=1):
            if candidate.get("url") == channel.get("url"):
                return index

        return 0

    def play_selected_channel(self, item):
        channel = item.data(CHANNEL_ROLE)

        if channel is None:
            return

        if self.current_url == channel["url"]:
            return

        self._play_channel(channel)

    def toggle_play_pause(self):
        if self.current_url is None or self.player is None:
            return

        self.player.toggle_pause()
        paused = self.player.is_paused()
        self.now_bar.set_paused(paused)

    def on_volume_changed(self, value):
        if self.player is not None:
            self.player.set_volume(value)

        self.settings.setValue("player/volume", value)

    def toggle_mute(self):
        if self.player is None:
            return

        self.player.toggle_mute()
        self.now_bar.set_muted(self.player.is_muted())

    def toggle_fullscreen(self):
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

    def _on_escape(self):
        if self.tv_mode.active:
            self.tv_mode.exit()
            return

        if self.isFullScreen():
            self.showNormal()

    # =========================
    # MODO TV
    # =========================

    def toggle_tv_mode(self):
        if self.tv_mode.active:
            self.tv_mode.exit()
        else:
            self.enter_tv_mode()

    def enter_tv_mode(self):
        channels = self._current_channels()

        if not channels:
            self.toast.show_message("Primero carga una playlist con canales.")
            return

        if len(channels) > LARGE_PLAYLIST:
            reply = QMessageBox.question(
                self,
                "Modo TV",
                f"Hay {len(channels)} canales en la vista actual.\n\n"
                "Navegar con las flechas sera lento. Se recomienda elegir "
                "una categoria o usar favoritos antes de entrar.\n\n"
                "¿Continuar de todos modos?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.No,
            )

            if reply != QMessageBox.StandardButton.Yes:
                return

        self._consecutive_errors = 0
        self.favorite_shortcut.setEnabled(False)
        self._set_ui_visible(False)
        self._set_tv_layout(True)
        self.showFullScreen()
        self.raise_()
        self.activateWindow()
        self.tv_mode.enter(channels, self.current_url, self.logo_loader)

    def on_tv_exited(self):
        self.showNormal()
        self._set_tv_layout(False)
        self._set_ui_visible(True)
        self.favorite_shortcut.setEnabled(True)
        self._stable_timer.stop()
        self._consecutive_errors = 0

    def on_tv_channel_selected(self, channel):
        self._play_channel(channel)

    def on_tv_volume_changed(self, delta):
        value = max(0, min(100, self.now_bar.volume.value() + delta))
        self.now_bar.volume.setValue(value)
        self.tv_mode.show_volume(value)

    def _set_ui_visible(self, visible):
        for widget in (
            self.topbar,
            self.sidebar,
            self.channel_panel,
            self.now_bar,
        ):
            widget.setVisible(visible)

    def _set_tv_layout(self, tv_mode_active):
        if tv_mode_active:
            self.body_layout.setContentsMargins(0, 0, 0, 0)
            self.body_layout.setSpacing(0)
            self.center_layout.setContentsMargins(0, 0, 0, 0)
            self.center_layout.setSpacing(0)
        else:
            self.body_layout.setContentsMargins(16, 14, 16, 16)
            self.body_layout.setSpacing(12)
            self.center_layout.setContentsMargins(0, 0, 0, 0)
            self.center_layout.setSpacing(12)

    def on_playback_error(self, message):
        if self.tv_mode.active:
            self.tv_mode.show_error(message)

            if (
                self.auto_skip_check.isChecked()
                and self._consecutive_errors < AUTO_SKIP_LIMIT
            ):
                self._consecutive_errors += 1
                QTimer.singleShot(AUTO_SKIP_DELAY_MS, self._auto_skip_next)

            return

        self.now_bar.group.setText("Error de reproduccion")
        self.now_bar.live.hide()
        self.now_bar.play_button.setEnabled(False)
        self.toast.show_message("No se pudo reproducir el canal. Prueba otro.")

    def _auto_skip_next(self):
        if self.tv_mode.active:
            self.tv_mode.next_channel()

    def _on_file_loaded(self):
        self._stable_timer.start(LOADED_STABLE_MS)

    def _reset_error_counter(self):
        self._consecutive_errors = 0

    # =========================
    # IPTV-ORG
    # =========================

    def show_iptv_org_menu(self):
        menu = QMenu(self)
        all_action = menu.addAction("Todos los canales")
        countries_action = menu.addAction("Por pais...")
        categories_action = menu.addAction("Por categoria...")
        languages_action = menu.addAction("Por idioma...")
        menu.addSeparator()
        refresh_action = menu.addAction("Actualizar playlist actual")

        position = self.iptv_button.mapToGlobal(
            QPoint(0, self.iptv_button.height())
        )
        chosen = menu.exec(position)

        if chosen is None:
            return

        if chosen == all_action:
            self._start_loading(DEFAULT_PLAYLIST_URL, is_url=True)
        elif chosen == countries_action:
            self._request_iptv_metadata("countries", "Pais")
        elif chosen == categories_action:
            self._request_iptv_metadata("categories", "Categoria")
        elif chosen == languages_action:
            self._request_iptv_metadata("languages", "Idioma")
        elif chosen == refresh_action:
            self._refresh_current_playlist()

    def _request_iptv_metadata(self, kind, title):
        cached = self._metadata_cache.get(kind)

        if cached:
            self._prompt_iptv_metadata(kind, title, cached)
            return

        if kind in self._metadata_workers:
            return

        self.loading_label.setText("Cargando opciones...")
        self.loading_label.show()

        worker = MetadataWorker(kind)
        worker.loaded.connect(self._on_metadata_loaded)
        worker.failed.connect(self._on_metadata_failed)
        worker.finished.connect(lambda w=worker: w.deleteLater())
        self._metadata_workers[kind] = worker
        worker.start()

    def _on_metadata_loaded(self, kind, items):
        self._metadata_workers.pop(kind, None)

        self.loading_label.hide()
        self._metadata_cache[kind] = items
        title = {
            "countries": "Pais",
            "categories": "Categoria",
            "languages": "Idioma",
        }.get(kind, kind)

        self._prompt_iptv_metadata(kind, title, items)

    def _on_metadata_failed(self, kind, error):
        self._metadata_workers.pop(kind, None)

        self.loading_label.hide()
        self.toast.show_message(
            f"No se pudo obtener la lista: {str(error)[:120]}",
            5000,
        )

    def _prompt_iptv_metadata(self, kind, title, items):
        if not items:
            self.toast.show_message("La lista de opciones esta vacia.")
            return

        dialog = MetadataDialog(f"IPTV-org - {title}", items, self)

        if dialog.exec() != QDialog.DialogCode.Accepted:
            return

        code = dialog.selected_code()

        if not code:
            return

        try:
            url = build_playlist_url(kind, code)
        except ValueError as error:
            self.toast.show_message(str(error))
            return

        self._start_loading(url, is_url=True)

    def _refresh_current_playlist(self):
        source = self._last_source or self._default_source

        if not source:
            return

        is_url = self._last_is_url if self._last_source else True
        self._start_loading(source, is_url=is_url, force_refresh=True)

    # =========================
    # HISTORIAL
    # =========================

    def show_history(self):
        if not self.playlist_history:
            self.toast.show_message("No hay playlists en el historial.")
            return

        items = list(self.playlist_history)

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

    # =========================
    # PERSISTENCIA
    # =========================

    def _load_settings(self):
        geometry = self.settings.value("window/geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)

        volume = self.settings.value("player/volume", 100, type=int)
        self.now_bar.volume.setValue(volume)

        auto_skip = self.settings.value(
            "player/auto_skip_errors", False, type=bool
        )
        self.auto_skip_check.setChecked(auto_skip)

        self._default_source = (
            self.settings.value("playlist/default_source", DEFAULT_PLAYLIST_URL)
            or DEFAULT_PLAYLIST_URL
        )
        self._last_source = self.settings.value("playlist/last_source", "")
        self._last_is_url = self.settings.value(
            "playlist/last_is_url", False, type=bool
        )
        self.playlist_history = self.settings.value(
            "playlist/history", [], type=list
        )

        if self._last_source:
            self._update_source_label(self._last_source, self._last_is_url)

        self._update_nav_state()

    def _save_settings(self):
        self.settings.setValue("window/geometry", self.saveGeometry())
        self.settings.setValue("player/volume", self.now_bar.volume.value())
        self.settings.setValue(
            "player/auto_skip_errors", self.auto_skip_check.isChecked()
        )
        self.settings.setValue("playlist/history", self.playlist_history)
        self.favorites_store.save()

    def _save_auto_skip(self, _state):
        if not hasattr(self, "settings"):
            return

        self.settings.setValue(
            "player/auto_skip_errors",
            self.auto_skip_check.isChecked(),
        )

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

    def _update_source_label(self, source, is_url):
        if not source:
            self.source_name.setText("Sin playlist")
            self.source_name.setToolTip("")
            return

        if is_url:
            parsed = urlparse(source)
            name = Path(parsed.path).name or parsed.netloc or source
        else:
            name = Path(source).name or source

        self.source_name.setText(name)
        self.source_name.setToolTip(source)

    def _auto_load_last(self):
        if self._last_source:
            answer = QMessageBox.question(
                self,
                "Cargar ultima playlist",
                f"¿Cargar la ultima playlist?\n\n{self._last_source}",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )

            if answer == QMessageBox.StandardButton.Yes:
                self._start_loading(
                    self._last_source,
                    is_url=self._last_is_url,
                )

            return

        if not self.playlist_history and self._default_source:
            self._start_loading(self._default_source, is_url=True)

    # =========================
    # EVENTOS
    # =========================

    def showEvent(self, event):
        super().showEvent(event)

        if self.player is None:
            self.player = MPVPlayer(self.video.winId())
            self.player.error_occurred.connect(self.on_playback_error)
            self.player.file_loaded.connect(self._on_file_loaded)
            self.now_bar.set_muted(self.player.is_muted())

    def resizeEvent(self, event):
        super().resizeEvent(event)

        if hasattr(self, "toast"):
            self.toast.place(self.root.rect())

    def closeEvent(self, event):
        self._save_settings()

        if self.loader and self.loader.isRunning():
            self.loader.abort()
            self.loader.wait(3000)

        for loader in list(self._retired_loaders):
            if loader.isRunning():
                loader.wait(3000)

        for worker in self._metadata_workers.values():
            if worker.isRunning():
                worker.wait(3000)

        if self.player:
            self.player.destroy()

        event.accept()


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("iptv-player")
    app.setApplicationDisplayName("IPTV Player")
    app.setOrganizationName("IPTVPlayer")
    app.setDesktopFileName("iptv-player")
    apply_theme(app)

    window = IPTVPlayer()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
