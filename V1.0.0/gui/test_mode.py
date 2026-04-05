"""
Test Mode / Backtest Screen — English UI
"""
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QComboBox, QSpinBox, QTextEdit, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar
)
from PyQt6.QtCore import Qt, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QColor, QTextCharFormat, QTextCursor


class BacktestWorker(QThread):
    log_signal     = pyqtSignal(str, str)
    result_signal  = pyqtSignal(dict)
    done_signal    = pyqtSignal()

    def __init__(self, symbol: str, interval: str, days: int):
        super().__init__()
        self.symbol   = symbol
        self.interval = interval
        self.days     = days

    def run(self):
        try:
            from core.market_data import MarketData
            from core.indicators import compute_all_indicators
            from core.strategy_manager import StrategyManager
            from core.backtester import Backtester

            self.log_signal.emit("info", f"📥 Fetching {self.days}d of {self.interval} data for {self.symbol}…")
            md    = MarketData()
            limit = self.days * 24 if self.interval == "1h" else self.days * 6
            df    = md.get_klines(self.symbol, self.interval, limit=min(limit, 1000))
            ind   = compute_all_indicators(df)

            self.log_signal.emit("info", f"✅ Got {len(df)} candles")
            self.log_signal.emit("info", "📊 Running all strategies across historical data…")

            sm          = StrategyManager()
            bt          = Backtester(sm)                    # ← only strategy_manager
            raw_results = bt.run_all_strategies(df)         # {name: BacktestResult}

            # Convert to list-of-dicts for the UI
            strategies = []
            for name, r in raw_results.items():
                d = r.to_dict()
                d["name"]             = sm.strategies.get(name, {}).get("name", name)
                d["strategy"]         = name
                d["signal_count"]     = d.get("total_trades", 0)
                d["total_return_pct"] = d.get("total_pnl", 0)   # normalised label
                strategies.append(d)

            self.log_signal.emit("info", f"✅ Backtest complete — {len(strategies)} strategies evaluated")
            self.result_signal.emit({"strategies": strategies})
        except Exception as e:
            self.log_signal.emit("error", f"❌ Backtest error: {e}")
        finally:
            self.done_signal.emit()


class TestModeScreen(QWidget):
    back_signal = pyqtSignal()

    def __init__(self, symbol: str, parent=None):
        super().__init__(parent)
        self.symbol = symbol
        self._worker = None
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
        title = QLabel(f"🧪  Backtest Mode — {self.symbol}")
        title.setStyleSheet("font-size:18px;font-weight:bold;color:#F0F6FC;")
        top.addWidget(back); top.addWidget(title); top.addStretch()
        layout.addLayout(top)

        content = QHBoxLayout()

        # ─── Config ────────────────────────────────────────────────────────
        cfg = QFrame()
        cfg.setFixedWidth(280)
        cfg.setStyleSheet("QFrame{background:#161B22;border:1px solid #30363D;border-radius:12px;}")
        cl = QVBoxLayout(cfg)
        cl.setContentsMargins(16, 16, 16, 16)
        cl.setSpacing(12)
        cl.setAlignment(Qt.AlignmentFlag.AlignTop)

        cl.addWidget(self._ttl("⚙️ Backtest Settings"))

        def lbl(t): return QLabel(t, styleSheet="color:#8B949E;font-size:12px;")

        cl.addWidget(lbl("Timeframe:"))
        self.interval_cb = QComboBox()
        self.interval_cb.addItems(["1h", "4h", "1d", "15m"])
        self.interval_cb.setCurrentText("1h")
        self.interval_cb.setStyleSheet(self._combo_style())
        cl.addWidget(self.interval_cb)

        cl.addWidget(lbl("Period (days):"))
        self.days_spin = QSpinBox()
        self.days_spin.setRange(3, 365)
        self.days_spin.setValue(30)
        self.days_spin.setStyleSheet("QSpinBox{background:#21262D;color:#F0F6FC;border:1px solid #30363D;border-radius:8px;padding:6px;}")
        cl.addWidget(self.days_spin)

        cl.addSpacing(10)
        self.run_btn = QPushButton("▶  Run Backtest")
        self.run_btn.setFixedHeight(44)
        self.run_btn.setStyleSheet("""
            QPushButton{
                background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00FFB2,stop:1 #00D4FF);
                color:#0D1117;border:none;border-radius:10px;font-size:14px;font-weight:bold;
            }
            QPushButton:hover{background:rgba(0,255,178,0.9);}
            QPushButton:disabled{background:#21262D;color:#8B949E;}
        """)
        self.run_btn.clicked.connect(self._run)
        cl.addWidget(self.run_btn)

        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.progress.setFixedHeight(4)
        cl.addWidget(self.progress)

        cl.addStretch()

        # Summary cards
        cl.addWidget(self._ttl("📊 Summary"))
        self._best  = self._stat_card("Best Strategy", "—", "#22C55E")
        self._win_r = self._stat_card("Best Win Rate", "—", "#00FFB2")
        self._avg_r = self._stat_card("Avg Return",    "—", "#F59E0B")
        for c in [self._best, self._win_r, self._avg_r]:
            cl.addWidget(c)

        content.addWidget(cfg)

        # ─── Results panel ─────────────────────────────────────────────────
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(8)

        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane{background:#161B22;border:1px solid #30363D;border-radius:10px;}
            QTabBar::tab{background:#21262D;color:#8B949E;border-radius:6px;padding:7px 14px;margin-right:4px;font-size:12px;}
            QTabBar::tab:selected{background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00FFB2,stop:1 #00D4FF);color:#0D1117;font-weight:bold;}
        """)
        tabs.addTab(self._results_tab(), "📈 Results Table")
        tabs.addTab(self._log_tab(),     "📝 Log")
        rl.addWidget(tabs)
        content.addWidget(right)
        layout.addLayout(content)

    def _results_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 10, 10, 10)
        self.results_table = QTableWidget(0, 6)
        self.results_table.setHorizontalHeaderLabels(
            ["Strategy", "Signal Count", "Win Rate", "Total Return %", "Max Drawdown", "Sharpe"]
        )
        self.results_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.results_table.setAlternatingRowColors(True)
        self.results_table.verticalHeader().setVisible(False)
        self.results_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.results_table)
        return w

    def _log_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(10, 10, 10, 10)
        self.log = QTextEdit()
        self.log.setReadOnly(True)
        self.log.setStyleSheet("""
            QTextEdit{
                background:#0D1117;color:#C9D1D9;
                border:1px solid #30363D;border-radius:8px;
                font-family:'Consolas',monospace;font-size:12px;padding:8px;
            }
        """)
        lay.addWidget(self.log)
        return w

    def _ttl(self, t): return QLabel(t, styleSheet="font-size:13px;font-weight:bold;color:#F0F6FC;")

    def _combo_style(self):
        return "QComboBox{background:#21262D;color:#F0F6FC;border:1px solid #30363D;border-radius:8px;padding:6px;}"

    def _stat_card(self, title, val, color="#F0F6FC"):
        f = QFrame()
        f.setStyleSheet("QFrame{background:#0D1117;border:1px solid #30363D;border-radius:8px;}")
        fl = QVBoxLayout(f)
        fl.setContentsMargins(10, 8, 10, 8)
        tl = QLabel(title); tl.setStyleSheet("color:#8B949E;font-size:11px;")
        vl = QLabel(val);   vl.setStyleSheet(f"color:{color};font-size:14px;font-weight:bold;")
        fl.addWidget(tl); fl.addWidget(vl)
        f._vl = vl
        return f

    def _log_msg(self, msg: str, color: str = "#C9D1D9"):
        c = self.log.textCursor()
        c.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        c.insertText(f"\n{msg}", fmt)
        self.log.setTextCursor(c)
        self.log.ensureCursorVisible()

    def _run(self):
        if self._worker and self._worker.isRunning():
            return
        self.results_table.setRowCount(0)
        self.log.clear()
        self.run_btn.setEnabled(False)
        self.progress.setVisible(True)

        self._worker = BacktestWorker(
            self.symbol,
            self.interval_cb.currentText(),
            self.days_spin.value(),
        )
        self._worker.log_signal.connect(self._on_log)
        self._worker.result_signal.connect(self._on_result)
        self._worker.done_signal.connect(self._on_done)
        self._worker.start()

    @pyqtSlot(str, str)
    def _on_log(self, level: str, msg: str):
        colors = {"info": "#8B949E", "error": "#EF4444", "success": "#22C55E"}
        self._log_msg(msg, colors.get(level, "#C9D1D9"))

    @pyqtSlot(dict)
    def _on_result(self, results: dict):
        self.results_table.setRowCount(0)
        strategies = results.get("strategies", [])
        if not strategies:
            # flatten if dict
            strategies = [{"name": k, **v} for k, v in results.items() if isinstance(v, dict)]

        best_wr = 0; best_name = "—"; best_ret = 0
        for strat in sorted(strategies, key=lambda x: x.get("win_rate", 0), reverse=True):
            row = self.results_table.rowCount()
            self.results_table.insertRow(row)
            name   = strat.get("name", strat.get("strategy", "—"))
            sigs   = strat.get("signal_count", strat.get("trades", 0))
            wr     = strat.get("win_rate", 0)
            ret    = strat.get("total_return_pct", strat.get("pnl_pct", 0))
            dd     = strat.get("max_drawdown", 0)
            sharpe = strat.get("sharpe_ratio", 0)

            self.results_table.setItem(row, 0, QTableWidgetItem(str(name)))
            self.results_table.setItem(row, 1, QTableWidgetItem(str(sigs)))

            wr_item = QTableWidgetItem(f"{wr:.1f}%")
            wr_item.setForeground(QColor("#22C55E" if wr > 55 else "#EF4444"))
            self.results_table.setItem(row, 2, wr_item)

            ret_item = QTableWidgetItem(f"{ret:+.2f}%")
            ret_item.setForeground(QColor("#22C55E" if ret > 0 else "#EF4444"))
            self.results_table.setItem(row, 3, ret_item)

            self.results_table.setItem(row, 4, QTableWidgetItem(f"{dd:.2f}%"))
            self.results_table.setItem(row, 5, QTableWidgetItem(f"{sharpe:.2f}"))

            if wr > best_wr:
                best_wr = wr; best_name = str(name); best_ret = ret

        self._best._vl.setText(best_name[:25])
        self._win_r._vl.setText(f"{best_wr:.1f}%")
        avg = sum(s.get("total_return_pct", s.get("pnl_pct", 0)) for s in strategies) / max(len(strategies), 1)
        self._avg_r._vl.setText(f"{avg:+.2f}%")
        c = "#22C55E" if avg > 0 else "#EF4444"
        self._avg_r._vl.setStyleSheet(f"color:{c};font-size:14px;font-weight:bold;")

    def _on_done(self):
        self.run_btn.setEnabled(True)
        self.progress.setVisible(False)
        self._log_msg("✅ Backtest complete", "#22C55E")
