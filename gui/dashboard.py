"""
Dashboard — Main analysis screen with 6-stage AI verification
Fully in English.
"""
import threading
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QFrame, QTextEdit, QProgressBar, QTabWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QSplitter
)
from PyQt6.QtCore import Qt, QTimer, pyqtSignal, QThread, pyqtSlot
from PyQt6.QtGui import QFont, QColor, QTextCharFormat, QTextCursor

from core.market_data import MarketData
from core.indicators import compute_all_indicators
from core.news_fetcher import NewsFetcher
from core.strategy_manager import StrategyManager, BUILTIN_STRATEGIES
from core.ai_engine import MultiStageAnalyzer


# ══════════════════════════════════════════════════════════════════════════════
#  Background Worker Thread
# ══════════════════════════════════════════════════════════════════════════════

class SignalUpdater(QThread):
    market_updated   = pyqtSignal(dict)
    news_updated     = pyqtSignal(dict)
    strategy_updated = pyqtSignal(dict)
    strategy_discovered = pyqtSignal(str)
    ai_progressed    = pyqtSignal(str, str)
    ai_completed     = pyqtSignal(dict)

    def __init__(self, symbol: str):
        super().__init__()
        self.symbol       = symbol
        self.market       = MarketData()
        self.news_fetcher = NewsFetcher()
        self.strategy_mgr = StrategyManager()
        self._stop_flag   = False
        self._full_data   = {}

    def stop(self):
        self._stop_flag = True

    def run(self):
        self._fetch_market()
        self._fetch_extras()
        self._fetch_news()
        self._discover_strategies()
        self._run_strategies()
        self._run_ai()

    # ── Market Data (multi-timeframe) ──────────────────────────────────────
    def _fetch_market(self):
        try:
            frames = self.market.get_multi_timeframe(self.symbol)
            ticker = self.market.get_ticker(self.symbol)
            for tf, df in frames.items():
                ind = compute_all_indicators(df)
                ind["change_24h"] = float(ticker.get("priceChangePercent", 0))
                ind["volume_24h"] = float(ticker.get("quoteVolume", 0))
                ind["high_24h"]   = float(ticker.get("highPrice", 0))
                ind["low_24h"]    = float(ticker.get("lowPrice", 0))
                self._full_data[f"indicators_{tf}"] = ind
            self._full_data["ticker"] = ticker
            self.market_updated.emit(self._full_data.get("indicators_1h", {}))
        except Exception as e:
            self.market_updated.emit({"error": str(e)})

    # ── Extras (Order Book, F&G, CoinGecko, Global) ────────────────────────
    def _fetch_extras(self):
        for key, fn in [
            ("order_book",    lambda: self.market.get_order_book(self.symbol)),
            ("recent_trades", lambda: self.market.get_recent_trades(self.symbol)),
            ("fear_greed",    lambda: self.market.get_fear_greed()),
            ("coingecko",     lambda: self.market.get_coingecko_data(self.symbol)),
            ("global_market", lambda: self.market.get_global_market()),
        ]:
            try:
                self._full_data[key] = fn()
            except Exception:
                self._full_data[key] = {}

    # ── News ───────────────────────────────────────────────────────────────
    def _fetch_news(self):
        try:
            news = self.news_fetcher.get_news_for_symbol(self.symbol)
            self._full_data["news"] = news
            self.news_updated.emit(news)
        except Exception:
            self._full_data["news"] = {"text": "", "articles": []}

    # ── AI Strategy Discovery ──────────────────────────────────────────────
    def _discover_strategies(self):
        if self._stop_flag:
            return
        ind = self._full_data.get("indicators_1h", {})
        if not ind:
            return
        self.strategy_discovered.emit("🌐 Searching for optimal strategies online + AI generation...")

        done_event = threading.Event()

        def _progress(msg):
            if not self._stop_flag:
                self.strategy_discovered.emit(msg)

        def _done(count):
            self.strategy_discovered.emit(
                f"✅ {count} AI-generated strategies added — total: {len(self.strategy_mgr.strategies)}"
            )
            done_event.set()

        self.strategy_mgr.discover_and_add_strategies_async(
            self.symbol, ind, _progress, _done
        )
        done_event.wait(timeout=90)  # wait up to 90s

    # ── Strategy Evaluation ────────────────────────────────────────────────
    def _run_strategies(self):
        try:
            ind = self._full_data.get("indicators_1h", {})
            if ind:
                results   = self.strategy_mgr.run_all_strategies(ind)
                consensus = self.strategy_mgr.get_weighted_consensus(results)
                self._full_data["strategy_consensus"] = consensus
                self.strategy_updated.emit({"results": results, "consensus": consensus,
                                            "all_strats": self.strategy_mgr.strategies})
        except Exception as e:
            print(f"[Strategy] Error: {e}")

    # ── AI 6-Stage Analysis ────────────────────────────────────────────────
    def _run_ai(self):
        try:
            analyzer = MultiStageAnalyzer(self.symbol, self._full_data)

            def on_progress(stage, msg):
                if not self._stop_flag:
                    self.ai_progressed.emit(stage, msg)

            def on_complete(result):
                if not self._stop_flag:
                    self.ai_completed.emit(result)

            t = analyzer.run_full_analysis_async(on_progress, on_complete)
            t.join(timeout=300)
        except Exception as e:
            self.ai_progressed.emit("error", f"❌ AI Error: {e}")


# ══════════════════════════════════════════════════════════════════════════════
#  Small UI helpers
# ══════════════════════════════════════════════════════════════════════════════

class MetricCard(QFrame):
    def __init__(self, title: str, value: str = "—", color: str = "#F0F6FC", parent=None):
        super().__init__(parent)
        self.setObjectName("metricCard")
        self.setStyleSheet("""
            #metricCard {
                background:#161B22; border:1px solid #30363D; border-radius:10px;
            }
        """)
        lay = QVBoxLayout(self)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)
        self.title_lbl = QLabel(title)
        self.title_lbl.setStyleSheet("color:#8B949E; font-size:11px; background:transparent;")
        self.value_lbl = QLabel(value)
        self.value_lbl.setStyleSheet(f"color:{color}; font-size:16px; font-weight:bold; background:transparent;")
        lay.addWidget(self.title_lbl)
        lay.addWidget(self.value_lbl)

    def update_value(self, v: str, color: str = None):
        self.value_lbl.setText(v)
        if color:
            self.value_lbl.setStyleSheet(
                f"color:{color}; font-size:16px; font-weight:bold; background:transparent;"
            )


# ══════════════════════════════════════════════════════════════════════════════
#  Dashboard
# ══════════════════════════════════════════════════════════════════════════════

class Dashboard(QWidget):
    back_to_welcome = pyqtSignal()

    def __init__(self, symbol: str, parent=None):
        super().__init__(parent)
        self.symbol   = symbol
        self._updater = None
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 10)
        layout.setSpacing(10)

        # ─── Top bar ──────────────────────────────────────────────────────────
        top = QHBoxLayout()
        back = QPushButton("← Back")
        back.setFixedSize(80, 34)
        back.setStyleSheet("""
            QPushButton {
                background:#21262D; color:#8B949E;
                border:1px solid #30363D; border-radius:8px; font-size:12px;
            }
            QPushButton:hover { color:#F0F6FC; border-color:#00FFB2; }
        """)
        back.clicked.connect(self.back_to_welcome)

        pair = QLabel(f"📊  {self.symbol.replace('USDT','')}/USDT")
        pair.setStyleSheet("font-size:20px; font-weight:bold; color:#00FFB2;")

        self.refresh_btn = QPushButton("🔄  New Analysis")
        self.refresh_btn.setFixedSize(130, 34)
        self.refresh_btn.setStyleSheet("""
            QPushButton {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #1a3a2a,stop:1 #1a2a3a);
                color:#00FFB2; border:1px solid #00FFB2; border-radius:8px; font-size:12px;
            }
            QPushButton:hover { background: rgba(0,255,178,0.15); }
        """)
        self.refresh_btn.clicked.connect(self.start_analysis)

        top.addWidget(back)
        top.addWidget(pair)
        top.addStretch()
        top.addWidget(self.refresh_btn)
        layout.addLayout(top)

        # ─── Metric cards ─────────────────────────────────────────────────────
        cards_row = QHBoxLayout()
        self.price_card  = MetricCard("💰 Price",       "Loading…", "#00FFB2")
        self.change_card = MetricCard("📈 24h Change",  "—",        "#8B949E")
        self.rsi_card    = MetricCard("📊 RSI (14)",    "—",        "#F0F6FC")
        self.vol_card    = MetricCard("📦 Volume 24h",  "—",        "#8B949E")
        self.bb_card     = MetricCard("📉 Bollinger",   "—",        "#F0F6FC")
        self.macd_card   = MetricCard("〰️ MACD",        "—",        "#F0F6FC")
        self.fg_card     = MetricCard("😱 Fear/Greed",  "—/100",    "#F59E0B")
        for c in [self.price_card, self.change_card, self.rsi_card,
                  self.vol_card,   self.bb_card,     self.macd_card, self.fg_card]:
            cards_row.addWidget(c)
        layout.addLayout(cards_row)

        # ─── Main tabs ────────────────────────────────────────────────────────
        tabs = QTabWidget()
        tabs.setStyleSheet("""
            QTabWidget::pane {
                background:#161B22; border:1px solid #30363D; border-radius:10px;
            }
            QTabBar::tab {
                background:#21262D; color:#8B949E;
                border-radius:6px; padding:7px 14px; margin-right:4px; font-size:12px;
            }
            QTabBar::tab:selected {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 #00FFB2,stop:1 #00D4FF);
                color:#0D1117; font-weight:bold;
            }
            QTabBar::tab:hover:!selected { background:#30363D; color:#F0F6FC; }
        """)
        tabs.addTab(self._build_ai_tab(),       "🤖 AI Analysis")
        tabs.addTab(self._build_strategy_tab(), "📈 Strategies")
        tabs.addTab(self._build_news_tab(),     "📰 News")
        tabs.addTab(self._build_indicators_tab(),"📊 Indicators")
        layout.addWidget(tabs)

        # ─── Progress & status ────────────────────────────────────────────────
        self.progress = QProgressBar()
        self.progress.setRange(0, 0)
        self.progress.setVisible(False)
        self.progress.setFixedHeight(5)
        layout.addWidget(self.progress)

        self.status_lbl = QLabel("Press 'New Analysis' to start")
        self.status_lbl.setStyleSheet("color:#8B949E; font-size:12px;")
        layout.addWidget(self.status_lbl)

    # ── AI Tab ─────────────────────────────────────────────────────────────────
    def _build_ai_tab(self) -> QWidget:
        w = QWidget()
        lay = QHBoxLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(12)

        # Left panel — decision
        left = QFrame()
        left.setFixedWidth(255)
        left.setStyleSheet("QFrame{background:#0D1117;border:1px solid #30363D;border-radius:12px;}")
        ll = QVBoxLayout(left)
        ll.setContentsMargins(14, 14, 14, 14)
        ll.setSpacing(10)
        ll.setAlignment(Qt.AlignmentFlag.AlignTop)

        ttl = QLabel("Final Decision")
        ttl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        ttl.setStyleSheet("color:#8B949E; font-size:11px; font-weight:bold;")

        self.decision_icon = QLabel("⏳")
        self.decision_icon.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.decision_icon.setStyleSheet("font-size:46px;")

        self.decision_text = QLabel("Waiting…")
        self.decision_text.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.decision_text.setStyleSheet("font-size:22px; font-weight:bold; color:#8B949E;")

        self.conf_lbl = QLabel("Confidence: —")
        self.conf_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.conf_lbl.setStyleSheet("font-size:13px; color:#8B949E;")

        self.conf_bar = QProgressBar()
        self.conf_bar.setRange(0, 100)
        self.conf_bar.setFixedHeight(10)

        for ww in [ttl, self.decision_icon, self.decision_text, self.conf_lbl, self.conf_bar]:
            ll.addWidget(ww)
        ll.addSpacing(8)

        # 6 stage indicators
        self._stages = {}
        for key, lbl in [
            ("stage1",     "1️⃣ Technical 1h"),
            ("stage2_mtf", "2️⃣ Multi-Timeframe"),
            ("stage3",     "3️⃣ DeepSeek AI"),
            ("stage4",     "4️⃣ Llama Sentiment"),
            ("stage5",     "5️⃣ F&G + OrderBook"),
            ("stage6",     "6️⃣ Final Decision"),
        ]:
            row = QHBoxLayout()
            dot = QLabel("●")
            dot.setStyleSheet("color:#30363D; font-size:11px;")
            dot.setFixedWidth(14)
            lbl_w = QLabel(lbl)
            lbl_w.setStyleSheet("color:#8B949E; font-size:11px;")
            row.addWidget(dot); row.addWidget(lbl_w); row.addStretch()
            self._stages[key] = dot
            ll.addLayout(row)

        ll.addStretch()

        # Trade levels
        self._fg_stat   = self._stat("Fear/Greed", "—", "#F59E0B")
        self._entry_stat = self._stat("Entry",      "—")
        self._sl_stat    = self._stat("Stop Loss",  "—", "#EF4444")
        self._tp1_stat   = self._stat("Target 1",   "—", "#22C55E")
        self._tp2_stat   = self._stat("Target 2",   "—", "#16A34A")
        self._rr_stat    = self._stat("Risk:Reward","—", "#6366F1")
        for st in [self._fg_stat, self._entry_stat, self._sl_stat,
                   self._tp1_stat, self._tp2_stat, self._rr_stat]:
            ll.addWidget(st)

        lay.addWidget(left)

        # Right — log
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.setSpacing(6)

        log_hdr = QLabel("📝 Analysis Log  (6-Stage Verification)")
        log_hdr.setStyleSheet("font-size:13px; font-weight:bold; color:#F0F6FC;")
        rl.addWidget(log_hdr)

        self.ai_log = QTextEdit()
        self.ai_log.setReadOnly(True)
        self.ai_log.setStyleSheet("""
            QTextEdit {
                background:#0D1117; color:#C9D1D9;
                border:1px solid #30363D; border-radius:10px;
                font-family:'Cascadia Code','Consolas',monospace; font-size:12px; padding:10px;
            }
        """)
        rl.addWidget(self.ai_log)
        lay.addWidget(right)
        return w

    def _stat(self, label: str, value: str, color: str = "#F0F6FC") -> QFrame:
        f = QFrame()
        f.setStyleSheet("QFrame{background:#21262D;border-radius:6px;}")
        fl = QHBoxLayout(f)
        fl.setContentsMargins(8, 5, 8, 5)
        lb = QLabel(label)
        lb.setStyleSheet("color:#8B949E;font-size:11px;background:transparent;")
        vl = QLabel(value)
        vl.setStyleSheet(f"color:{color};font-size:11px;font-weight:bold;background:transparent;")
        fl.addWidget(lb); fl.addStretch(); fl.addWidget(vl)
        f._vl = vl
        return f

    # ── Strategy Tab ──────────────────────────────────────────────────────────
    def _build_strategy_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        hdr = QHBoxLayout()
        ttl = QLabel("📈 Strategy Signals — All Strategies")
        ttl.setStyleSheet("font-size:14px; font-weight:bold; color:#F0F6FC;")
        self.consensus_lbl = QLabel("Consensus: —")
        self.consensus_lbl.setStyleSheet("font-size:13px; font-weight:bold; color:#8B949E;")
        hdr.addWidget(ttl); hdr.addStretch(); hdr.addWidget(self.consensus_lbl)
        lay.addLayout(hdr)

        # Discovery log
        self.discovery_log = QTextEdit()
        self.discovery_log.setReadOnly(True)
        self.discovery_log.setFixedHeight(60)
        self.discovery_log.setStyleSheet("""
            QTextEdit {
                background:#0D1117; color:#00FFB2;
                border:1px solid #30363D; border-radius:6px;
                font-size:11px; padding:6px;
                font-family:'Consolas',monospace;
            }
        """)
        lay.addWidget(self.discovery_log)

        self.strategy_table = QTableWidget(0, 5)
        self.strategy_table.setHorizontalHeaderLabels(
            ["Strategy", "Category", "Signal", "Win Rate", "Weight"]
        )
        self.strategy_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.strategy_table.setAlternatingRowColors(True)
        self.strategy_table.verticalHeader().setVisible(False)
        self.strategy_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        lay.addWidget(self.strategy_table)
        return w

    # ── News Tab ──────────────────────────────────────────────────────────────
    def _build_news_tab(self) -> QWidget:
        w = QWidget()
        lay = QVBoxLayout(w)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(8)

        hdr = QHBoxLayout()
        ttl = QLabel("📰 Latest News & Sentiment")
        ttl.setStyleSheet("font-size:14px; font-weight:bold; color:#F0F6FC;")
        self.sentiment_lbl = QLabel("Sentiment: —")
        self.sentiment_lbl.setStyleSheet("font-size:12px; color:#8B949E;")
        self.news_source_lbl = QLabel("")
        self.news_source_lbl.setStyleSheet("font-size:11px; color:#6E7681;")
        hdr.addWidget(ttl); hdr.addStretch()
        hdr.addWidget(self.news_source_lbl); hdr.addWidget(self.sentiment_lbl)
        lay.addLayout(hdr)

        self.news_table = QTableWidget(0, 4)
        self.news_table.setHorizontalHeaderLabels(["Headline", "Source", "Time", "👍/👎"])
        self.news_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        self.news_table.setAlternatingRowColors(True)
        self.news_table.verticalHeader().setVisible(False)
        self.news_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.news_table.setWordWrap(True)
        lay.addWidget(self.news_table)
        return w

    # ── Indicators Tab ────────────────────────────────────────────────────────
    def _build_indicators_tab(self) -> QWidget:
        from PyQt6.QtWidgets import QGridLayout
        w = QWidget()
        lay = QGridLayout(w)
        lay.setContentsMargins(12, 12, 12, 12)
        lay.setSpacing(10)

        self._ind_cards = {}
        items = [
            ("RSI (14)",          "rsi",           "#6366F1"),
            ("MACD",              "macd",          "#F59E0B"),
            ("MACD Signal",       "macd_signal",   "#8B5CF6"),
            ("MACD Histogram",    "macd_hist",     "#F97316"),
            ("BB Upper",          "bb_upper",      "#EF4444"),
            ("BB Lower",          "bb_lower",      "#22C55E"),
            ("BB Mid",            "bb_mid",        "#8B949E"),
            ("EMA 20",            "ema20",         "#00FFB2"),
            ("EMA 50",            "ema50",         "#00D4FF"),
            ("EMA 200",           "ema200",        "#F59E0B"),
            ("Stoch K",           "stoch_k",       "#6366F1"),
            ("Stoch D",           "stoch_d",       "#8B5CF6"),
            ("ATR",               "atr",           "#8B949E"),
            ("Candle Pattern",    "candle_pattern","#F0F6FC"),
            ("24h Change %",      "change_24h",    "#22C55E"),
            ("24h High",          "high_24h",      "#F0F6FC"),
            ("24h Low",           "low_24h",       "#F0F6FC"),
            ("Volume 24h",        "volume_24h",    "#8B949E"),
        ]
        for idx, (name, key, color) in enumerate(items):
            card = MetricCard(name, "—", color)
            self._ind_cards[key] = card
            lay.addWidget(card, idx // 3, idx % 3)
        return w

    # ══════════════════════════════════════════════════════════════════════════
    #  Analysis control
    # ══════════════════════════════════════════════════════════════════════════

    def start_analysis(self):
        if self._updater and self._updater.isRunning():
            self._updater.stop()
            self._updater.wait(2000)

        self._clear_ui()
        self.progress.setVisible(True)
        self.refresh_btn.setEnabled(False)
        self.status_lbl.setText("🔄 Analysis running…")

        self._updater = SignalUpdater(self.symbol)
        self._updater.market_updated.connect(self._on_market)
        self._updater.news_updated.connect(self._on_news)
        self._updater.strategy_updated.connect(self._on_strategies)
        self._updater.strategy_discovered.connect(self._on_discovery)
        self._updater.ai_progressed.connect(self._on_ai_progress)
        self._updater.ai_completed.connect(self._on_ai_complete)
        self._updater.finished.connect(self._on_done)
        self._updater.start()

    def _clear_ui(self):
        self.ai_log.clear()
        self.decision_icon.setText("⏳")
        self.decision_text.setText("Analysing…")
        self.decision_text.setStyleSheet("font-size:22px;font-weight:bold;color:#8B949E;")
        self.conf_lbl.setText("Confidence: —")
        self.conf_bar.setValue(0)
        for dot in self._stages.values():
            dot.setStyleSheet("color:#30363D; font-size:11px;")
        self.strategy_table.setRowCount(0)
        self.discovery_log.clear()

    # ── Slots ─────────────────────────────────────────────────────────────────

    @pyqtSlot(dict)
    def _on_market(self, data: dict):
        if "error" in data:
            self._log(f"❌ Market data error: {data['error']}", "#EF4444"); return

        price  = data.get("price", 0)
        change = data.get("change_24h", 0)
        rsi    = data.get("rsi") or 0
        macd   = data.get("macd") or 0
        vol    = data.get("volume_24h", 0)
        bb_up  = data.get("bb_upper", 0)
        bb_lo  = data.get("bb_lower", 0)

        self.price_card.update_value(f"${price:,.4f}", "#00FFB2")
        c_col = "#22C55E" if change >= 0 else "#EF4444"
        self.change_card.update_value(f"{'+' if change>=0 else ''}{change:.2f}%", c_col)
        r_col = "#EF4444" if rsi > 70 else ("#22C55E" if rsi < 30 else "#F0F6FC")
        self.rsi_card.update_value(f"{rsi:.1f}", r_col)
        self.vol_card.update_value(f"${vol/1e6:.1f}M" if vol else "—")
        self.bb_card.update_value(f"{bb_lo:.2f} – {bb_up:.2f}" if bb_up else "—")
        self.macd_card.update_value(f"{macd:.5f}" if macd else "—")

        for key, card in self._ind_cards.items():
            val = data.get(key)
            if val is not None:
                card.update_value(f"{val:.4f}" if isinstance(val, float) else str(val))

        self._log(f"✅ Market data loaded — Price: ${price:,.4f}  |  RSI: {rsi:.1f}", "#22C55E")
        self._set_stage("stage1", True)
        self.status_lbl.setText(f"💰 Price: ${price:,.4f}  |  Fetching news…")

    @pyqtSlot(dict)
    def _on_news(self, data: dict):
        articles = data.get("articles", [])
        score    = data.get("sentiment_score", 0)
        sources  = data.get("sources", {})

        s_col  = "#22C55E" if score > 10 else ("#EF4444" if score < -10 else "#F59E0B")
        s_text = "Bullish 📈" if score > 10 else ("Bearish 📉" if score < -10 else "Neutral ⚖️")
        self.sentiment_lbl.setText(f"Sentiment: {s_text}  ({score:+.1f})")
        self.sentiment_lbl.setStyleSheet(f"font-size:12px; color:{s_col};")
        self.news_source_lbl.setText(
            f"CryptoPanic:{sources.get('cryptopanic',0)}  RSS:{sources.get('rss',0)}  "
            f"Reddit:{sources.get('reddit',0)}  Google:{sources.get('google',0)}"
        )

        self.news_table.setRowCount(0)
        for a in articles[:50]:
            row = self.news_table.rowCount()
            self.news_table.insertRow(row)
            self.news_table.setItem(row, 0, QTableWidgetItem(a.get("title", "")))
            self.news_table.setItem(row, 1, QTableWidgetItem(a.get("source", "")))
            self.news_table.setItem(row, 2, QTableWidgetItem(str(a.get("time", ""))[:16]))
            vt = f"👍{a.get('votes_positive',0)}  👎{a.get('votes_negative',0)}"
            self.news_table.setItem(row, 3, QTableWidgetItem(vt))

        self._log(
            f"📰 News loaded: {len(articles)} articles  |  Sentiment: {s_text}", "#F59E0B"
        )

    @pyqtSlot(str)
    def _on_discovery(self, msg: str):
        cursor = self.discovery_log.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        cursor.insertText(msg + "\n")
        self.discovery_log.setTextCursor(cursor)
        self.discovery_log.ensureCursorVisible()

    @pyqtSlot(dict)
    def _on_strategies(self, data: dict):
        results    = data.get("results", {})
        consensus  = data.get("consensus", {})
        all_strats = data.get("all_strats", {})

        self.strategy_table.setRowCount(0)
        for name, signal in results.items():
            row = self.strategy_table.rowCount()
            self.strategy_table.insertRow(row)

            info  = all_strats.get(name, BUILTIN_STRATEGIES.get(name, {}))
            dname = info.get("name", name)
            cat   = info.get("category", "—")
            wr    = info.get("win_rate", "?")
            wt    = info.get("weight", 1.0)

            cm = {"BUY": "#22C55E", "SELL": "#EF4444", "HOLD": "#F59E0B"}
            im = {"BUY": "🟢 BUY",  "SELL": "🔴 SELL", "HOLD": "🟡 HOLD"}

            self.strategy_table.setItem(row, 0, QTableWidgetItem(dname))
            self.strategy_table.setItem(row, 1, QTableWidgetItem(cat))

            sig_item = QTableWidgetItem(im.get(signal, signal))
            sig_item.setForeground(QColor(cm.get(signal, "#F0F6FC")))
            sig_item.setFont(QFont("Arial", 10, QFont.Weight.Bold))
            self.strategy_table.setItem(row, 2, sig_item)

            self.strategy_table.setItem(row, 3, QTableWidgetItem(f"{wr}%"))
            self.strategy_table.setItem(row, 4, QTableWidgetItem(f"{wt}"))

        dec  = consensus.get("decision", "—")
        conf = consensus.get("confidence", 0)
        buy  = consensus.get("buy_strats", 0)
        sell = consensus.get("sell_strats", 0)
        hold = consensus.get("hold_strats", 0)
        total= consensus.get("total_strats", 0)
        dc   = {"BUY": "#22C55E", "SELL": "#EF4444", "HOLD": "#F59E0B"}.get(dec, "#F0F6FC")
        self.consensus_lbl.setText(
            f"Consensus: {dec}  ({conf}%)  —  🟢{buy} / 🔴{sell} / 🟡{hold}  of {total}"
        )
        self.consensus_lbl.setStyleSheet(f"font-size:12px; font-weight:bold; color:{dc};")

    @pyqtSlot(str, str)
    def _on_ai_progress(self, stage: str, msg: str):
        if stage.endswith("_stream"):
            self._append(msg); return
        if stage.endswith("_detail"):
            self._log(msg, "#6E7681"); return

        colors = {
            "stage1": "#6366F1", "stage2_mtf": "#8B5CF6",
            "stage3": "#F59E0B", "stage4": "#22C55E",
            "stage5": "#F97316", "stage6": "#00FFB2",
            "warning": "#EF4444",
        }
        color = colors.get(stage, "#8B949E")
        self._log(msg, color)

        if "✅" in msg and stage in self._stages:
            self._set_stage(stage, True)
        elif stage in self._stages:
            self._stages[stage].setStyleSheet(f"color:{color}; font-size:11px;")

        self.status_lbl.setText(msg[:100])

    @pyqtSlot(dict)
    def _on_ai_complete(self, result: dict):
        decision = result.get("decision", "HOLD")
        conf     = result.get("confidence", 0)
        entry    = result.get("entry_price")
        sl       = result.get("stop_loss")
        tp1      = result.get("take_profit_1")
        tp2      = result.get("take_profit_2")
        rr       = result.get("risk_reward_ratio", "—")
        fg       = result.get("fear_greed", 50)
        reasoning = result.get("reasoning", "")
        sentiment_sum = result.get("sentiment_summary", "")
        key_events = result.get("key_events", [])
        warning  = result.get("warning")
        vb       = result.get("vote_breakdown", {})
        pos_news = result.get("positive_news", [])
        neg_news = result.get("negative_news", [])

        ic = {"BUY": "🟢", "SELL": "🔴", "HOLD": "🟡"}
        co = {"BUY": "#22C55E", "SELL": "#EF4444", "HOLD": "#F59E0B"}
        tx = {"BUY": "BUY ↑", "SELL": "SELL ↓", "HOLD": "HOLD ⏸"}

        self.decision_icon.setText(ic.get(decision, "⚪"))
        self.decision_text.setText(tx.get(decision, decision))
        self.decision_text.setStyleSheet(
            f"font-size:22px;font-weight:bold;color:{co.get(decision,'#F0F6FC')};"
        )
        self.conf_lbl.setText(f"Confidence: {conf}%")
        self.conf_bar.setValue(conf)

        # Update F&G card
        fc = "#22C55E" if fg < 35 else ("#EF4444" if fg > 65 else "#F59E0B")
        self.fg_card.update_value(f"{fg}/100", fc)

        # Update stat bars
        def _sv(stat, val):
            try:
                stat._vl.setText(f"${float(val):,.4f}")
            except Exception:
                stat._vl.setText(str(val))

        if entry: _sv(self._entry_stat, entry)
        if sl:    _sv(self._sl_stat,    sl)
        if tp1:   _sv(self._tp1_stat,   tp1)
        if tp2:   _sv(self._tp2_stat,   tp2)
        self._rr_stat._vl.setText(str(rr))

        # Detailed log
        self._log("\n" + "═"*55, "#30363D")
        self._log(f"🗳️  VOTE BREAKDOWN (6 stages):", "#F0F6FC")
        for sn, sd in vb.items():
            sc2 = {"BUY":"#22C55E","SELL":"#EF4444","HOLD":"#F59E0B"}.get(sd,"#8B949E")
            self._log(f"   • {sn}: {sd}", sc2)

        if reasoning:
            self._log(f"\n💡 DeepSeek Analysis:\n{reasoning}", "#C9D1D9")
        if sentiment_sum:
            self._log(f"\n🧠 Llama Sentiment:\n{sentiment_sum}", "#8B949E")
        if pos_news:
            self._log("\n✅ Positive News:", "#22C55E")
            for n in pos_news[:3]: self._log(f"   • {n}", "#22C55E")
        if neg_news:
            self._log("\n❌ Negative News:", "#EF4444")
            for n in neg_news[:3]: self._log(f"   • {n}", "#EF4444")
        if key_events:
            self._log("\n🔔 Key Events:", "#F59E0B")
            for e in key_events[:5]: self._log(f"   • {e}", "#F59E0B")
        if warning:
            self._log(f"\n⚠️  WARNING: {warning}", "#EF4444")

        for dot in self._stages.values():
            dot.setStyleSheet("color:#22C55E; font-size:11px;")

    def _on_done(self):
        self.progress.setVisible(False)
        self.refresh_btn.setEnabled(True)
        self.status_lbl.setText("✅ Analysis complete")

    # ── Logging helpers ───────────────────────────────────────────────────────
    def _log(self, msg: str, color: str = "#C9D1D9"):
        c = self.ai_log.textCursor()
        c.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor(color))
        c.insertText(f"\n{msg}", fmt)
        self.ai_log.setTextCursor(c)
        self.ai_log.ensureCursorVisible()

    def _append(self, text: str):
        c = self.ai_log.textCursor()
        c.movePosition(QTextCursor.MoveOperation.End)
        fmt = QTextCharFormat()
        fmt.setForeground(QColor("#7D8590"))
        c.insertText(text, fmt)
        self.ai_log.setTextCursor(c)
        self.ai_log.ensureCursorVisible()

    def _set_stage(self, key: str, done: bool):
        dot = self._stages.get(key)
        if dot:
            dot.setStyleSheet(
                f"color:{'#22C55E' if done else '#F59E0B'}; font-size:11px;"
            )
