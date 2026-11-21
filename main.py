import os
import sys

from PySide6.QtCore import QLockFile
from PySide6.QtGui import QColor, QIcon, QPalette
from PySide6.QtWidgets import QApplication, QMessageBox

from app.config.paths import ASSETS_DIR
from app.config.theme import ACCENT, APP_QSS, BG_CARD, BG_INPUT, BG_MAIN, TEXT_DIM, TEXT_MAIN
from app.core.data_manager import DataManager
from app.core.fonts import load_app_fonts
from app.core.logging_setup import setup_logging
from app.core.recovery import load_with_recovery
from app.core.runtime import user_data_dir
from app.core.window_transition import show_prepared_window
from app.core.window_utils import setup_app_user_model_id
from app.window.main_window import MainWindow


def main():
    setup_logging()

    # Setup Windows taskbar grouping so custom icon appears
    setup_app_user_model_id("AbdulKarim.DizoClip.1.0")

    app = QApplication(sys.argv)

    lock = QLockFile(str(user_data_dir() / "dizoclip.lock"))
    lock.setStaleLockTime(0)  # a crashed run never blocks the next start
    if not lock.tryLock(100):
        QMessageBox.information(None, "DizoClip", "DizoClip is already running.")
        sys.exit(0)

    load_app_fonts()
    app.setStyle("Fusion")
    app.setApplicationName("DizoClip")
    app.setApplicationDisplayName("DizoClip")

    # Set application-level window icon for taskbar and dialogs
    ico_path = os.path.join(ASSETS_DIR, "app_logo.ico")
    png_path = os.path.join(ASSETS_DIR, "app_logo.png")
    if os.path.exists(ico_path):
        app.setWindowIcon(QIcon(ico_path))
    elif os.path.exists(png_path):
        app.setWindowIcon(QIcon(png_path))

    # Dark fusion palette
    pal = QPalette()
    pal.setColor(QPalette.Window, QColor(BG_MAIN))
    pal.setColor(QPalette.WindowText, QColor(TEXT_MAIN))
    pal.setColor(QPalette.Base, QColor(BG_INPUT))
    pal.setColor(QPalette.AlternateBase, QColor(BG_CARD))
    pal.setColor(QPalette.Text, QColor(TEXT_MAIN))
    pal.setColor(QPalette.Button, QColor(BG_CARD))
    pal.setColor(QPalette.ButtonText, QColor(TEXT_MAIN))
    pal.setColor(QPalette.ToolTipBase, QColor("#1a1e27"))
    pal.setColor(QPalette.ToolTipText, QColor(TEXT_MAIN))
    pal.setColor(QPalette.PlaceholderText, QColor(TEXT_DIM))
    pal.setColor(QPalette.Highlight, QColor(ACCENT))
    pal.setColor(QPalette.HighlightedText, QColor("#ffffff"))
    app.setPalette(pal)

    # Global stylesheet
    app.setStyleSheet(APP_QSS)

    dm = DataManager()
    datasets = load_with_recovery(dm)
    if datasets is None:
        sys.exit(1)
    win = MainWindow(data_manager=dm, datasets=datasets)

    # Show prepared window with smooth 200ms fade-in
    show_prepared_window(win, duration=200)

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
