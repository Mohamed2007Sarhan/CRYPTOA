"""
Main Application Window — English UI
"""
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QPushButton, QFrame, QStackedWidget
)
from PyQt6.QtCore import Qt, QTimer, pyqtSlot
from PyQt6.QtGui import QFont

from gui.styles import DARK_THEME
from gui.welcome_screen import WelcomeScreen
from gui.dashboard import Dashboard
from gui.auto_trade import AutoTradeScreen
from gui.test_mode import TestModeScreen


class NavButton(QPushButton):
    def __init__(self, icon: str, label: str, parent=None):
        super().__init__(f"{icon}  {label}", parent)
        self.setCheckable(True)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        self._apply_style(False)

    def _apply_style(self, checked: bool):
        if checked:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                        stop:0 rgba(0,255,178,0.18), stop:1 rgba(0,212,255,0.12));
                    color: #00FFB2; border: none;
                    border-left: 3px solid #00FFB2;
                    padding: 12px 18px; text-align: left;
                    font-size: 13px; font-weight: bold;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #8B949E; border: none;
                    padding: 12px 18px; text-align: left; font-size: 13px;
                }
                QPushButton:hover { background: rgba(255,255,255,0.04); color: #F0F6FC; }
            """)

    def setChecked(self, c: bool):
        super().setChecked(c)
        self._apply_style(c)


class Sidebar(QFrame):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedWidth(195)
        self.setObjectName("sidebar")
        self.setStyleSheet("""
            #sidebar { background:#161B22; border-right:1px solid #30363D; }
        """)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo
        logo = QFrame()
        logo.setFixedHeight(72)
        logo.setStyleSheet("background:#0D1117; border-bottom:1px solid #30363D;")
        ll = QVBoxLayout(logo)
        ll.setAlignment(Qt.AlignmentFlag.AlignCenter)

        t = QLabel("🤖  CryptoAI")
        t.setAlignment(Qt.AlignmentFlag.AlignCenter)
        t.setStyleSheet("font-size:16px; font-weight:bold; color:#00FFB2; background:transparent;")
        s = QLabel("AI Trading Platform")
        s.setAlignment(Qt.AlignmentFlag.AlignCenter)
        s.setStyleSheet("font-size:10px; color:#8B949E; background:transparent;")
        ll.addWidget(t); ll.addWidget(s)
        layout.addWidget(logo)

        layout.addSpacing(10)

        self.btn_home     = NavButton("🏠", "Home")
        self.btn_analysis = NavButton("📊", "AI Analysis")
        self.btn_auto     = NavButton("⚡", "Auto Trade")
        self.btn_test     = NavButton("🧪", "Backtest")
        for b in [self.btn_home, self.btn_analysis, self.btn_auto, self.btn_test]:
            layout.addWidget(b)

        layout.addStretch()

        # Status footer
        footer = QFrame()
        footer.setStyleSheet("background:#0D1117; border-top:1px solid #30363D;")
        fl = QVBoxLayout(footer)
        fl.setContentsMargins(12, 10, 12, 10)

        self.live_dot = QLabel("● Live Market Data")
        self.live_dot.setStyleSheet("color:#22C55E; font-size:11px;")
        self.time_lbl = QLabel("--:--:--")
        self.time_lbl.setStyleSheet("color:#8B949E; font-size:10px;")

        fl.addWidget(self.live_dot)
        fl.addWidget(self.time_lbl)
        layout.addWidget(footer)

        self._blink = True
        timer = QTimer(self)
        timer.timeout.connect(self._tick)
        timer.start(1000)

    def _tick(self):
        import time
        self.time_lbl.setText(time.strftime("%H:%M:%S"))
        self._blink = not self._blink
        c = "#22C55E" if self._blink else "#1a4d2e"
        self.live_dot.setStyleSheet(f"color:{c}; font-size:11px;")


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("CryptoAI — AI-Powered Cryptocurrency Trading")
        self.setMinimumSize(1200, 750)
        self.resize(1440, 860)
        self._symbol = ""
        self._setup_ui()
        self._connect_nav()
        self._go_home()

    def _setup_ui(self):
        self.setStyleSheet(DARK_THEME)
        central = QWidget()
        self.setCentralWidget(central)
        main = QHBoxLayout(central)
        main.setContentsMargins(0, 0, 0, 0)
        main.setSpacing(0)

        self.sidebar = Sidebar()
        main.addWidget(self.sidebar)

        self.stack = QStackedWidget()
        main.addWidget(self.stack)

        # Pages
        self.welcome_page = WelcomeScreen()
        self.stack.addWidget(self.welcome_page)           # 0
        self.stack.addWidget(QWidget())                   # 1 placeholder dashboard
        self.stack.addWidget(QWidget())                   # 2 placeholder auto
        self.stack.addWidget(QWidget())                   # 3 placeholder test

        sb = self.statusBar()
        sb.setStyleSheet("""
            QStatusBar {
                background:#161B22; color:#8B949E;
                border-top:1px solid #30363D; font-size:12px; padding:3px 10px;
            }
        """)
        sb.showMessage("Welcome to CryptoAI — select a pair to get started")

    def _connect_nav(self):
        self.welcome_page.symbol_selected.connect(self._on_symbol)
        self.sidebar.btn_home.clicked.connect(self._go_home)
        self.sidebar.btn_analysis.clicked.connect(self._go_dashboard)
        self.sidebar.btn_auto.clicked.connect(self._go_auto)
        self.sidebar.btn_test.clicked.connect(self._go_test)

    def _set_nav(self, idx: int):
        for i, b in enumerate([self.sidebar.btn_home, self.sidebar.btn_analysis,
                                self.sidebar.btn_auto, self.sidebar.btn_test]):
            b.setChecked(i == idx)
        self.stack.setCurrentIndex(idx)

    def _go_home(self):
        self._set_nav(0)
        self.statusBar().showMessage("Select a cryptocurrency pair to begin")

    @pyqtSlot(str)
    def _on_symbol(self, symbol: str):
        self._symbol = symbol
        self._build_dashboard(symbol)
        self._go_dashboard()

    def _build_dashboard(self, symbol: str):
        old = self.stack.widget(1)
        self.stack.removeWidget(old)
        old.deleteLater()
        dash = Dashboard(symbol)
        dash.back_to_welcome.connect(self._go_home)
        self.stack.insertWidget(1, dash)
        self._dashboard = dash
        dash.start_analysis()

    def _build_auto(self, symbol: str):
        old = self.stack.widget(2)
        self.stack.removeWidget(old)
        old.deleteLater()
        page = AutoTradeScreen(symbol)
        page.back_signal.connect(self._go_dashboard)
        self.stack.insertWidget(2, page)

    def _build_test(self, symbol: str):
        old = self.stack.widget(3)
        self.stack.removeWidget(old)
        old.deleteLater()
        page = TestModeScreen(symbol)
        page.back_signal.connect(self._go_dashboard)
        self.stack.insertWidget(3, page)

    def _go_dashboard(self):
        if not self._symbol:
            self._go_home(); return
        self._set_nav(1)
        self.statusBar().showMessage(f"📊 AI Analysis Dashboard — {self._symbol}")

    def _go_auto(self):
        if not self._symbol:
            self._go_home(); return
        self._build_auto(self._symbol)
        self._set_nav(2)
        self.statusBar().showMessage(f"⚡ Auto Trading — {self._symbol}")

    def _go_test(self):
        if not self._symbol:
            self._go_home(); return
        self._build_test(self._symbol)
        self._set_nav(3)
        self.statusBar().showMessage(f"🧪 Backtest Mode — {self._symbol}")

    def closeEvent(self, event):
        if hasattr(self, "_dashboard") and hasattr(self._dashboard, "_updater"):
            u = self._dashboard._updater
            if u: u.stop()
        event.accept()
