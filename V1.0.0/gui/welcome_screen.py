"""
Welcome Screen — Crypto pair selection
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QLineEdit, QGridLayout, QFrame, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QFont
from config.settings import TOP_CRYPTO_PAIRS


class CryptoCard(QPushButton):
    def __init__(self, symbol: str, parent=None):
        super().__init__(parent)
        self.symbol = symbol
        self.setFixedSize(130, 70)
        self.setCursor(Qt.CursorShape.PointingHandCursor)
        base = symbol.replace("USDT", "")
        self.setText(f"{base}\n{symbol}")
        self._apply_style(False)

    def _apply_style(self, selected: bool):
        if selected:
            self.setStyleSheet("""
                QPushButton {
                    background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                        stop:0 #00FFB2, stop:1 #00D4FF);
                    color: #0D1117; border: none; border-radius: 10px;
                    font-weight: bold; font-size: 13px;
                }
            """)
        else:
            self.setStyleSheet("""
                QPushButton {
                    background-color: #21262D;
                    color: #F0F6FC; border: 1px solid #30363D;
                    border-radius: 10px; font-size: 12px;
                }
                QPushButton:hover {
                    background-color: #2D333B; border: 1px solid #00FFB2;
                }
            """)

    def set_selected(self, s: bool):
        self._apply_style(s)


class WelcomeScreen(QWidget):
    symbol_selected = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.selected_symbol = ""
        self._cards = {}
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(50, 30, 50, 30)
        layout.setSpacing(20)

        # ─── Header ──────────────────────────────────────────────────────────
        header = QFrame()
        header.setObjectName("welcomeHeader")
        header.setStyleSheet("""
            #welcomeHeader {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #0D1117, stop:0.5 #161B22, stop:1 #0D1117);
                border: 1px solid #30363D; border-radius: 16px;
            }
        """)
        h_layout = QVBoxLayout(header)
        h_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        h_layout.setContentsMargins(20, 24, 20, 24)
        h_layout.setSpacing(8)

        icon_lbl = QLabel("🤖")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setStyleSheet("font-size:52px; background:transparent;")

        title = QLabel("AI Crypto Trading Platform")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet("font-size:28px; font-weight:bold; color:#00FFB2; background:transparent;")

        sub = QLabel("Powered by DeepSeek V3.2 + Llama 3.3 Nemotron  |  6-Stage Verification")
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet("font-size:13px; color:#8B949E; background:transparent;")

        h_layout.addWidget(icon_lbl)
        h_layout.addWidget(title)
        h_layout.addWidget(sub)
        layout.addWidget(header)

        # ─── Question ─────────────────────────────────────────────────────────
        q = QLabel("🎯  What would you like to trade?")
        q.setAlignment(Qt.AlignmentFlag.AlignCenter)
        q.setStyleSheet("font-size:18px; font-weight:bold; color:#F0F6FC;")
        layout.addWidget(q)

        # ─── Search ───────────────────────────────────────────────────────────
        search_row = QHBoxLayout()
        icon = QLabel("🔍")
        icon.setStyleSheet("font-size:18px; color:#8B949E;")
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search or type a symbol  (e.g.  BTC, ETH, SOL)…")
        self.search_input.setStyleSheet("""
            QLineEdit {
                background:#21262D; color:#F0F6FC;
                border:1px solid #30363D; border-radius:10px;
                padding:12px 16px; font-size:14px;
            }
            QLineEdit:focus { border:1px solid #00FFB2; background:#1C2128; }
        """)
        self.search_input.textChanged.connect(self._on_search)
        self.search_input.returnPressed.connect(self._on_enter)
        search_row.addWidget(icon)
        search_row.addWidget(self.search_input)
        layout.addLayout(search_row)

        # ─── Grid ─────────────────────────────────────────────────────────────
        pop = QLabel("⚡  Most Traded Pairs")
        pop.setStyleSheet("font-size:13px; color:#8B949E; font-weight:bold;")
        layout.addWidget(pop)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setMaximumHeight(220)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        grid_widget = QWidget()
        self.grid_layout = QGridLayout(grid_widget)
        self.grid_layout.setSpacing(10)
        self.grid_layout.setContentsMargins(4, 4, 4, 4)
        self._populate_grid(TOP_CRYPTO_PAIRS)
        scroll.setWidget(grid_widget)
        layout.addWidget(scroll)

        # ─── Selected display ─────────────────────────────────────────────────
        self.sel_frame = QFrame()
        self.sel_frame.setStyleSheet("""
            QFrame { background:#161B22; border:1px solid #30363D; border-radius:12px; }
        """)
        sel_layout = QHBoxLayout(self.sel_frame)
        self.sel_lbl = QLabel("No pair selected")
        self.sel_lbl.setStyleSheet("font-size:14px; color:#8B949E;")
        self.sel_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sel_layout.addWidget(self.sel_lbl)
        layout.addWidget(self.sel_frame)

        # ─── Start Button ─────────────────────────────────────────────────────
        self.start_btn = QPushButton("🚀  Start AI Analysis")
        self.start_btn.setFixedHeight(52)
        self.start_btn.setEnabled(False)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00FFB2,stop:1 #00D4FF);
                color:#0D1117; border:none; border-radius:12px;
                font-size:16px; font-weight:bold;
            }
            QPushButton:hover { background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00FFD4,stop:1 #00EAFF); }
            QPushButton:disabled { background:#21262D; color:#8B949E; }
        """)
        self.start_btn.clicked.connect(self._on_start)
        layout.addWidget(self.start_btn)

    def _populate_grid(self, pairs):
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        self._cards.clear()
        cols = 6
        for i, sym in enumerate(pairs):
            card = CryptoCard(sym)
            card.clicked.connect(lambda _, s=sym: self._select(s))
            self.grid_layout.addWidget(card, i // cols, i % cols)
            self._cards[sym] = card

    def _on_search(self, text):
        if not text:
            self._populate_grid(TOP_CRYPTO_PAIRS)
            return
        text = text.upper().strip()
        filtered = [p for p in TOP_CRYPTO_PAIRS if text in p]
        if not filtered:
            custom = text if text.endswith("USDT") else text + "USDT"
            filtered = [custom]
        self._populate_grid(filtered)

    def _on_enter(self):
        text = self.search_input.text().upper().strip()
        if text:
            sym = text if text.endswith("USDT") else text + "USDT"
            self._select(sym)

    def _select(self, symbol: str):
        for card in self._cards.values():
            card.set_selected(False)
        if symbol in self._cards:
            self._cards[symbol].set_selected(True)

        self.selected_symbol = symbol
        base = symbol.replace("USDT", "")
        self.sel_frame.setStyleSheet("""
            QFrame {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,
                    stop:0 rgba(0,255,178,0.08), stop:1 rgba(0,212,255,0.08));
                border:1px solid #00FFB2; border-radius:12px;
            }
        """)
        self.sel_lbl.setStyleSheet("font-size:16px; font-weight:bold; color:#00FFB2;")
        self.sel_lbl.setText(f"✅  Selected: {base} / USDT  ({symbol})")
        self.start_btn.setEnabled(True)

    def _on_start(self):
        if self.selected_symbol:
            self.symbol_selected.emit(self.selected_symbol)
