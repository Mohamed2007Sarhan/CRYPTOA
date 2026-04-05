"""
main.py — نقطة دخول برنامج التداول الذكي
"""
import sys
import os

# تأكد من أن المسار الأساسي مُضاف
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from gui.app import MainWindow


def main():
    app = QApplication(sys.argv)
    app.setApplicationName("CryptoAI Trading Platform")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("AI Trading")

    # Font
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # High DPI
    app.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
