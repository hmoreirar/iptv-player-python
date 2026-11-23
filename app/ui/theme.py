from PySide6.QtGui import QColor, QFont, QPalette


class Colors:
    bg = "#0b0f14"
    surface = "#111820"
    surface_2 = "#17212b"
    surface_3 = "#1e2a36"
    border = "#263442"
    border_strong = "#33495c"
    text = "#eef4f8"
    muted = "#90a3b3"
    muted_2 = "#7a92a5"
    accent = "#f0b429"
    accent_text = "#1a1205"
    live = "#35d07f"
    danger = "#ff6b6b"
    focus = "#7cc4ff"


STYLE = f"""
QWidget {{
    color: {Colors.text};
    font-family: "Noto Sans", "DejaVu Sans", sans-serif;
    font-size: 13px;
}}

QMainWindow, QWidget#Root {{
    background-color: {Colors.bg};
}}

QWidget#TopBar {{
    background-color: {Colors.surface};
    border-bottom: 1px solid {Colors.border};
}}

QWidget#Sidebar {{
    background-color: {Colors.surface};
    border-right: 1px solid {Colors.border};
}}

QWidget#ChannelPanel {{
    background-color: {Colors.surface};
    border-left: 1px solid {Colors.border};
}}

QWidget#VideoStage {{
    background-color: #000000;
    border: 1px solid {Colors.border};
}}

QWidget#NowPlaying {{
    background-color: {Colors.surface};
    border: 1px solid {Colors.border};
    border-radius: 10px;
}}

QWidget#SourceCard {{
    background-color: {Colors.surface_2};
    border: 1px solid {Colors.border};
    border-radius: 8px;
}}

QLabel#Brand {{
    font-size: 17px;
    font-weight: 700;
}}

QLabel#BrandAccent {{
    color: {Colors.accent};
    font-size: 17px;
    font-weight: 700;
}}

QLabel#SourceLabel {{
    color: {Colors.muted};
    font-size: 11px;
}}

QLabel#SectionLabel {{
    color: {Colors.muted_2};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}}

QLabel#PanelTitle {{
    font-size: 13px;
    font-weight: 700;
}}

QLabel#CountLabel {{
    color: {Colors.muted_2};
    font-size: 11px;
}}

QLabel#ChannelNumber {{
    color: {Colors.accent};
    font-family: "DejaVu Sans Mono", monospace;
    font-size: 12px;
    font-weight: 700;
}}

QLabel#ChannelName {{
    font-size: 14px;
    font-weight: 600;
}}

QLabel#ChannelGroup {{
    color: {Colors.muted};
    font-size: 11px;
}}

QLabel#LiveBadge {{
    color: {Colors.live};
    font-size: 10px;
    font-weight: 700;
    letter-spacing: 1px;
}}

QLabel#EmptyTitle {{
    font-size: 14px;
    font-weight: 600;
}}

QLabel#EmptyBody {{
    color: {Colors.muted};
    font-size: 12px;
}}

QLabel#SourceName {{
    color: {Colors.text};
    font-size: 11px;
}}

QLabel#Toast {{
    background-color: {Colors.surface_3};
    border: 1px solid {Colors.border_strong};
    border-radius: 8px;
    color: {Colors.text};
    font-size: 12px;
    padding: 9px 14px;
}}

QPushButton {{
    background-color: {Colors.surface_2};
    border: 1px solid {Colors.border};
    border-radius: 7px;
    color: {Colors.text};
    font-size: 12px;
    padding: 7px 12px;
}}

QPushButton:hover {{
    background-color: {Colors.surface_3};
    border-color: {Colors.border_strong};
}}

QPushButton:pressed {{
    background-color: {Colors.border};
}}

QPushButton:focus {{
    border-color: {Colors.accent};
}}

QPushButton:disabled {{
    color: {Colors.muted_2};
    background-color: {Colors.surface};
    border-color: {Colors.border};
}}

QPushButton#PrimaryButton {{
    background-color: {Colors.accent};
    border-color: {Colors.accent};
    color: {Colors.accent_text};
    font-weight: 700;
}}

QPushButton#PrimaryButton:hover {{
    background-color: #ffc848;
    border-color: #ffc848;
}}

QPushButton#GhostButton {{
    background-color: transparent;
    border-color: transparent;
    color: {Colors.muted};
}}

QPushButton#GhostButton:hover {{
    background-color: {Colors.surface_2};
    color: {Colors.text};
}}

QToolButton {{
    background-color: transparent;
    border: 1px solid transparent;
    border-radius: 7px;
    color: {Colors.text};
    padding: 5px;
}}

QToolButton:hover {{
    background-color: {Colors.surface_2};
}}

QToolButton:pressed {{
    background-color: {Colors.surface_3};
}}

QToolButton:focus {{
    background-color: {Colors.surface_2};
    border-color: {Colors.accent};
}}

QToolButton:disabled {{
    color: {Colors.muted_2};
}}

QToolButton[nav="true"] {{
    background-color: transparent;
    border: none;
    border-radius: 7px;
    color: {Colors.muted};
    font-size: 13px;
    font-weight: 500;
    padding: 8px 10px;
    text-align: left;
}}

QToolButton[nav="true"]:hover {{
    background-color: {Colors.surface_2};
    color: {Colors.text};
}}

QToolButton[nav="true"][active="true"] {{
    background-color: {Colors.surface_3};
    color: {Colors.text};
    font-weight: 700;
}}

QLineEdit {{
    background-color: {Colors.bg};
    border: 1px solid {Colors.border};
    border-radius: 7px;
    color: {Colors.text};
    padding: 8px 10px;
    selection-background-color: {Colors.accent};
    selection-color: {Colors.accent_text};
}}

QLineEdit:focus {{
    border-color: {Colors.accent};
}}

QLineEdit#Search {{
    background-color: {Colors.surface_2};
    font-size: 13px;
    padding-left: 32px;
}}

QLineEdit#Search:focus {{
    background-color: {Colors.bg};
}}

QLineEdit#CategorySearch {{
    background-color: {Colors.surface_2};
    font-size: 11px;
    padding: 5px 8px;
}}

QListWidget {{
    background-color: transparent;
    border: none;
    outline: none;
}}

QListWidget::item {{
    border: none;
}}

QListWidget::item:selected {{
    background-color: transparent;
}}

QSlider::groove:horizontal {{
    background-color: {Colors.border};
    border-radius: 2px;
    height: 4px;
}}

QSlider::sub-page:horizontal {{
    background-color: {Colors.accent};
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background-color: {Colors.text};
    border: none;
    border-radius: 6px;
    height: 12px;
    margin: -4px 0;
    width: 12px;
}}

QSlider::handle:horizontal:hover {{
    background-color: {Colors.accent};
}}

QScrollBar:vertical {{
    background: transparent;
    border: none;
    margin: 2px;
    width: 9px;
}}

QScrollBar::handle:vertical {{
    background: {Colors.border_strong};
    border-radius: 4px;
    min-height: 28px;
}}

QScrollBar::handle:vertical:hover {{
    background: {Colors.muted_2};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QMenu {{
    background-color: {Colors.surface_2};
    border: 1px solid {Colors.border_strong};
    border-radius: 8px;
    padding: 5px;
}}

QMenu::item {{
    border-radius: 5px;
    padding: 7px 26px 7px 12px;
}}

QMenu::item:selected {{
    background-color: {Colors.surface_3};
}}

QMenu::separator {{
    background-color: {Colors.border};
    height: 1px;
    margin: 5px 8px;
}}

QCheckBox {{
    color: {Colors.muted};
    font-size: 11px;
    spacing: 7px;
}}

QCheckBox::indicator {{
    background-color: {Colors.bg};
    border: 1px solid {Colors.border_strong};
    border-radius: 4px;
    height: 14px;
    width: 14px;
}}

QCheckBox::indicator:checked {{
    background-color: {Colors.accent};
    border-color: {Colors.accent};
}}

QToolTip {{
    background-color: {Colors.surface_3};
    border: 1px solid {Colors.border_strong};
    color: {Colors.text};
    padding: 5px 8px;
}}

QMessageBox, QDialog, QInputDialog {{
    background-color: {Colors.surface};
}}

QDialog QLabel, QMessageBox QLabel {{
    color: {Colors.text};
}}

QDialogButtonBox QPushButton {{
    min-width: 72px;
}}
"""


def apply_theme(app):
    app.setStyle("Fusion")

    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(Colors.bg))
    palette.setColor(QPalette.WindowText, QColor(Colors.text))
    palette.setColor(QPalette.Base, QColor(Colors.surface))
    palette.setColor(QPalette.AlternateBase, QColor(Colors.surface_2))
    palette.setColor(QPalette.Text, QColor(Colors.text))
    palette.setColor(QPalette.Button, QColor(Colors.surface_2))
    palette.setColor(QPalette.ButtonText, QColor(Colors.text))
    palette.setColor(QPalette.Highlight, QColor(Colors.accent))
    palette.setColor(QPalette.HighlightedText, QColor(Colors.accent_text))
    palette.setColor(QPalette.ToolTipBase, QColor(Colors.surface_3))
    palette.setColor(QPalette.ToolTipText, QColor(Colors.text))
    palette.setColor(QPalette.PlaceholderText, QColor(Colors.muted_2))
    palette.setColor(QPalette.Disabled, QPalette.Text, QColor(Colors.muted_2))
    palette.setColor(
        QPalette.Disabled, QPalette.ButtonText, QColor(Colors.muted_2)
    )

    app.setPalette(palette)
    app.setStyleSheet(STYLE)

    font = QFont()
    font.setPointSize(10)
    app.setFont(font)
