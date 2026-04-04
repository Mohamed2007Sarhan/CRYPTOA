"""
Auto Trade Screen — English UI
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QLineEdit, QDoubleSpinBox, QCheckBox, QTextEdit,
    QGroupBox, QFormLayout, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QTextCharFormat, QTextCursor, QColor
from config.settings import DEFAULT_RISK_PERCENT, DEFAULT_STOP_LOSS_PCT, DEFAULT_TAKE_PROFIT_PCT


class AutoTradeScreen(QWidget):
    back_signal = pyqtSignal()

    def __init__(self, symbol: str, parent=None):
        super().__init__(parent)
        self.symbol  = symbol
        self._trader = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(14)

        # Top bar
        top = QHBoxLayout()
        back = QPushButton("← Back")
        back.setFixedSize(80, 34)
        back.setStyleSheet("QPushButton{background:#21262D;color:#8B949E;border:1px solid #30363D;border-radius:8px;font-size:12px;}QPushButton:hover{color:#F0F6FC;border-color:#00FFB2;}")
        back.clicked.connect(self.back_signal)
        title = QLabel(f"⚡  Auto Trading — {self.symbol}")
        title.setStyleSheet("font-size:18px;font-weight:bold;color:#F0F6FC;")
        top.addWidget(back); top.addWidget(title); top.addStretch()
        layout.addLayout(top)

        content = QHBoxLayout()

        # ─── Config panel ──────────────────────────────────────────────────
        config = QFrame()
        config.setFixedWidth(340)
        config.setStyleSheet("QFrame{background:#161B22;border:1px solid #30363D;border-radius:12px;}")
        cl = QVBoxLayout(config)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.setSpacing(14)

        cl.addWidget(self._section_title("🔑 Binance API Keys"))

        api_form = QFormLayout()
        api_form.setSpacing(8)
        self.api_key    = QLineEdit()
        self.api_secret = QLineEdit()
        self.api_key.setPlaceholderText("API Key")
        self.api_secret.setPlaceholderText("API Secret")
        self.api_secret.setEchoMode(QLineEdit.EchoMode.Password)
        for w in [self.api_key, self.api_secret]:
            w.setStyleSheet(self._input_style())
        api_form.addRow("API Key:", self.api_key)
        api_form.addRow("Secret:",  self.api_secret)
        cl.addLayout(api_form)

        self.testnet_cb = QCheckBox("Use Testnet (recommended for testing)")
        self.testnet_cb.setChecked(True)
        self.testnet_cb.setStyleSheet("color:#F59E0B; font-size:12px;")
        cl.addWidget(self.testnet_cb)

        cl.addWidget(self._sep())
        cl.addWidget(self._section_title("⚠️ Risk Management"))

        risk_form = QFormLayout()
        risk_form.setSpacing(8)
        self.risk_spin = self._spin(0.1, 20.0, DEFAULT_RISK_PERCENT, "% of balance")
        self.sl_spin   = self._spin(0.1, 20.0, DEFAULT_STOP_LOSS_PCT,  "%")
        self.tp_spin   = self._spin(0.1, 50.0, DEFAULT_TAKE_PROFIT_PCT, "%")
        risk_form.addRow("Risk per trade:", self.risk_spin)
        risk_form.addRow("Stop Loss:",      self.sl_spin)
        risk_form.addRow("Take Profit:",    self.tp_spin)
        cl.addLayout(risk_form)

        cl.addWidget(self._sep())
        cl.addWidget(self._section_title("🔄 Sessions"))
        self.max_trades_spin = self._spin(1, 100, 10, "max trades")
        fl = QFormLayout()
        fl.addRow("Max trades:", self.max_trades_spin)
        cl.addLayout(fl)
        cl.addStretch()

        # Buttons
        self.start_btn = QPushButton("🚀  Start AutoTrading")
        self.start_btn.setFixedHeight(46)
        self.start_btn.setStyleSheet("""
            QPushButton {
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00FFB2,stop:1 #00D4FF);
                color:#0D1117;border:none;border-radius:10px;font-size:14px;font-weight:bold;
            }
            QPushButton:hover{background:rgba(0,255,178,0.9);}
            QPushButton:disabled{background:#21262D;color:#8B949E;}
        """)
        self.start_btn.clicked.connect(self._start)
        self.stop_btn = QPushButton("⏹  Stop")
        self.stop_btn.setFixedHeight(40)
        self.stop_btn.setEnabled(False)
        self.stop_btn.setStyleSheet("""
            QPushButton{background:#EF4444;color:white;border:none;border-radius:10px;font-size:14px;}
            QPushButton:hover{background:#DC2626;}
            QPushButton:disabled{background:#21262D;color:#8B949E;}
        """)
        self.stop_btn.clicked.connect(self._stop)
        cl.addWidget(self.start_btn)
        cl.addWidget(self.stop_btn)
        content.addWidget(config)

        # ─── Live log panel ────────────────────────────────────────────────
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(8)

        # Stats row
        stats = QHBoxLayout()
        self._total_card  = self._stat_card("Total Trades", "0")
        self._win_card    = self._stat_card("Win Rate", "—")
        self._pnl_card    = self._stat_card("P&L", "—", "#22C55E")
        self._status_card = self._stat_card("Status", "Idle", "#8B949E")
        for c in [self._total_card, self._win_card, self._pnl_card, self._status_card]:
            stats.addWidget(c)
        rl.addLayout(stats)

        log_lbl = QLabel("📡  Live Trade Log")
        log_lbl.setStyleSheet("font-size:13px;font-weight:bold;color:#F0F6FC;")
        rl.addWidget(log_lbl)

        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("""
            QTextEdit{
                background:#0D1117;color:#C9D1D9;
                border:1px solid #30363D;border-radius:10px;
                font-family:'Consolas',monospace;font-size:12px;padding:10px;
            }
        """)
        rl.addWidget(self.log)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.progress.setFixedHeight(4)
        rl.addWidget(self.progress)

        content.addWidget(right)
        layout.addLayout(content)

    def _section_title(self, text: str) -> QLabel:
        l = QLabel(text)
        l.setStyleSheet("font-size:13px;font-weight:bold;color:#F0F6FC;")
        return l

    def _sep(self) -> QFrame:
        f = QFrame()
        f.setFrameShape(QFrame.Shape.HLine)
        f.setStyleSheet("color:#30363D;")
        return f

    def _input_style(self) -> str:
        return """
            QLineEdit{
                background:#21262D;color:#F0F6FC;
                border:1px solid #30363D;border-radius:8px;padding:8px;font-size:12px;
            }
            QLineEdit:focus{border:1px solid #00FFB2;}
        """

    def _spin(self, mn, mx, val, suffix) -> QDoubleSpinBox:
        s = QDoubleSpinBox()
        s.setRange(mn, mx); s.setValue(val); s.setSuffix(f"  {suffix}")
        s.setStyleSheet("QDoubleSpinBox{background:#21262D;color:#F0F6FC;border:1px solid #30363D;border-radius:8px;padding:6px;}")
        return s

    def _stat_card(self, title: str, value: str, color: str = "#F0F6FC") -> QFrame:
        f = QFrame()
        f.setStyleSheet("QFrame{background:#161B22;border:1px solid #30363D;border-radius:10px;}")
        fl = QVBoxLayout(f)
        fl.setContentsMargins(12, 10, 12, 10)
        tl = QLabel(title); tl.setStyleSheet("color:#8B949E;font-size:11px;")
        vl = QLabel(value); vl.setStyleSheet(f"color:{color};font-size:18px;font-weight:bold;")
        fl.addWidget(tl); fl.addWidget(vl)
        f._vl = vl
        return f

    def _log(self, msg: str, color: str = "#C9D1D9"):
        from PyQt6.QtGui import QTextCharFormat, QTextCursor, QColor
        c = self.log.textCursor()
        c.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        c.insertText(f"\n{msg}", fmt)
        self.log.setTextCursor(c)
        self.log.ensureCursorVisible()

    def _start(self):
        api_key    = self.api_key.text().strip()
        api_secret = self.api_secret.text().strip()
        if not api_key or not api_secret:
            self._log("❌ Please enter both API Key and Secret", "#EF4444")
            return
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.progress.setVisible(True)
        self._status_card._vl.setText("Running")
        self._status_card._vl.setStyleSheet("color:#22C55E;font-size:18px;font-weight:bold;")
        self._log(f"🚀 AutoTrader started — {self.symbol}", "#00FFB2")
        self._log(f"   Risk: {self.risk_spin.value()}%  |  SL: {self.sl_spin.value()}%  |  TP: {self.tp_spin.value()}%", "#8B949E")
        self._log(f"   Mode: {'Testnet' if self.testnet_cb.isChecked() else '⚠️ LIVE'}", "#F59E0B")

        from core.trading_engine import AutoTrader
        self._trader = AutoTrader(
            symbol=self.symbol,
            api_key=api_key,
            api_secret=api_secret,
            testnet=self.testnet_cb.isChecked(),
            risk_pct=self.risk_spin.value(),
            stop_loss_pct=self.sl_spin.value(),
            take_profit_pct=self.tp_spin.value(),
        )
        self._trader.on_log    = lambda m: self._log(m)
        self._trader.on_trade  = self._on_trade
        self._trader.start()

    def _stop(self):
        if self._trader:
            self._trader.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.setVisible(False)
        self._status_card._vl.setText("Stopped")
        self._status_card._vl.setStyleSheet("color:#EF4444;font-size:18px;font-weight:bold;")
        self._log("⏹  AutoTrader stopped", "#EF4444")

    def _on_trade(self, trade: dict):
        side  = trade.get("side", "")
        price = trade.get("price", 0)
        qty   = trade.get("qty", 0)
        pnl   = trade.get("pnl", 0)
        color = "#22C55E" if side == "BUY" else "#EF4444"
        self._log(
            f"{'🟢' if side=='BUY' else '🔴'} {side} {qty} {self.symbol} @ ${price:.4f}  |  P&L: {pnl:+.2f} USDT",
            color
        )
