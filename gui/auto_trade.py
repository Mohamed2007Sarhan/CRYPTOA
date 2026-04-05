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
        # Interval selector
        from PyQt6.QtWidgets import QComboBox
        self.interval_combo = QComboBox()
        self.interval_combo.addItems(["1m","5m","15m","30m","1h","2h","4h","6h","12h","1d"])
        self.interval_combo.setCurrentText("1h")
        self.interval_combo.setStyleSheet("""
            QComboBox{background:#21262D;color:#F0F6FC;border:1px solid #30363D;
                      border-radius:8px;padding:6px;font-size:12px;}
            QComboBox::drop-down{border:none;}
            QComboBox QAbstractItemView{background:#21262D;color:#F0F6FC;border:1px solid #30363D;}
        """)
        self.interval_combo.currentTextChanged.connect(self._update_timing_label)
        self.max_trades_spin = self._spin(1, 100, 10, "max trades")
        fl = QFormLayout()
        fl.addRow("Interval:",   self.interval_combo)
        fl.addRow("Max trades:", self.max_trades_spin)
        cl.addLayout(fl)

        # عرض توقيت الفحص
        self._timing_label = QLabel()
        self._timing_label.setStyleSheet("color:#8B949E;font-size:11px;padding:4px 0;")
        self._timing_label.setWordWrap(True)
        cl.addWidget(self._timing_label)
        self._update_timing_label("1h")
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
        self._total_card  = self._stat_card("Trades",   "0")
        self._win_card    = self._stat_card("Win Rate", "—")
        self._pnl_card    = self._stat_card("Total P&L", "—",    "#22C55E")
        self._state_card  = self._stat_card("Mode",     "Idle",  "#8B949E")
        for c in [self._total_card, self._win_card, self._pnl_card, self._state_card]:
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
        from core.strategy_manager import BUILTIN_STRATEGIES

        interval = self.interval_combo.currentText()
        # استخدام كل الاستراتيجيات المدمجة
        all_strategies = list(BUILTIN_STRATEGIES.keys())

        self._trader = AutoTrader(
            symbol           = self.symbol,
            api_key          = api_key,
            api_secret       = api_secret,
            testnet          = self.testnet_cb.isChecked(),
            risk_pct         = self.risk_spin.value(),
            stop_loss_pct    = self.sl_spin.value(),
            take_profit_pct  = self.tp_spin.value(),
            interval         = interval,
            strategy_names   = all_strategies,
            use_ai           = True,
            min_confidence   = 65,
        )
        self._trader.on_log    = lambda m: self._log(m)
        self._trader.on_trade  = self._on_trade
        self._trader.on_status = self._on_status
        self._trader.start()

        # تحديث عرض التوقيت
        from core.pre_candle_predictor import TIMEFRAME_SECONDS, PRE_CLOSE_WINDOW
        candle_sec  = TIMEFRAME_SECONDS.get(interval, 3600)
        check_every = max(candle_sec - PRE_CLOSE_WINDOW, 60)
        m, s = divmod(check_every, 60)
        h, m = divmod(m, 60)
        self._log(f"   ⏰ Scans every {h}h {m:02d}m (5m before each candle)", "#8B949E")

    def _stop(self):
        if self._trader:
            self._trader.stop()
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.progress.setVisible(False)
        self._status_card._vl.setText("Stopped")
        self._status_card._vl.setStyleSheet("color:#EF4444;font-size:18px;font-weight:bold;")
        self._log("⏹  AutoTrader stopped", "#EF4444")

    def _update_timing_label(self, interval: str):
        """يعرض معلومة متى سيتم المسح القادم."""
        try:
            from core.trading_engine import _get_scan_interval, PRE_CLOSE_WINDOW_SEC
            from core.pre_candle_predictor import TIMEFRAME_SECONDS
            candle_sec  = TIMEFRAME_SECONDS.get(interval, 3600)
            scan_sec    = _get_scan_interval(interval)
            guard_sec   = max(0, candle_sec - PRE_CLOSE_WINDOW_SEC)
            sm, ss      = divmod(scan_sec, 60)
            gm, gs      = divmod(guard_sec, 60)
            gh, gm      = divmod(gm, 60)
            self._timing_label.setText(
                f"🔍 HUNT: Every {sm}m {ss}s  |  ⚔️ GUARD: Sleeps {gh}h {gm:02d}m → Scans 5m before {interval}"
            )
        except Exception:
            pass

    def _on_trade(self, trade: dict):
        t_type     = trade.get("type", "")
        price      = trade.get("price", 0)
        qty        = trade.get("quantity", 0)
        pnl        = trade.get("pnl_pct", 0)
        total_pnl  = trade.get("total_pnl", 0)
        trades_n   = trade.get("trades", 0)
        win_rate   = trade.get("win_rate", 0)
        reason     = trade.get("reason", "")

        if t_type == "OPEN":
            self._log(f"🟢 BUY {qty:.6f} {self.symbol} @ {price:.4f}", "#22C55E")
            self._state_card._vl.setText("⚔️ GUARD")
            self._state_card._vl.setStyleSheet("color:#F59E0B;font-size:16px;font-weight:bold;")

        elif t_type == "CLOSE":
            color = "#22C55E" if pnl >= 0 else "#EF4444"
            self._log(
                f"{'🟢' if pnl >= 0 else '🔴'} CLOSE @ {price:.4f} "
                f"| PnL: {pnl:+.2f}% | {reason}",
                color,
            )
            self._state_card._vl.setText("🔍 HUNT")
            self._state_card._vl.setStyleSheet("color:#00FFB2;font-size:16px;font-weight:bold;")

        elif t_type == "EMERGENCY_CLOSE":
            self._log(
                f"🆘 EMERGENCY @ {price:.4f} | PnL: {pnl:+.2f}% | {reason}",
                "#F59E0B",
            )
            self._state_card._vl.setText("🔍 HUNT")
            self._state_card._vl.setStyleSheet("color:#00FFB2;font-size:16px;font-weight:bold;")

        # تحديث بطاقات الإحصاء
        self._total_card._vl.setText(str(trades_n))
        pnl_color = "#22C55E" if total_pnl >= 0 else "#EF4444"
        self._pnl_card._vl.setText(f"{total_pnl:+.2f}%")
        self._pnl_card._vl.setStyleSheet(f"color:{pnl_color};font-size:18px;font-weight:bold;")
        self._win_card._vl.setText(f"{win_rate}%")

    def _on_status(self, status: dict):
        """تحديث الحالة من trading_engine."""
        state_name = status.get("state", "")
        if not self._trader:
            return
        if state_name == "HUNTING" and not status.get("in_trade"):
            self._state_card._vl.setText("🔍 HUNT")
            self._state_card._vl.setStyleSheet("color:#00FFB2;font-size:16px;font-weight:bold;")
        elif state_name == "GUARDING":
            self._state_card._vl.setText("⚔️ GUARD")
            self._state_card._vl.setStyleSheet("color:#F59E0B;font-size:16px;font-weight:bold;")
