"""
Auto Trading Engine — محرك التداول التلقائي
"""
import time
import threading
import logging
from typing import Callable, Optional
from core.market_data import MarketData
from core.indicators import compute_all_indicators
from core.strategy_manager import StrategyManager
from core.ai_engine import MultiStageAnalyzer
from core.news_fetcher import NewsFetcher

logger = logging.getLogger(__name__)


class AutoTrader:
    def __init__(self,
                 api_key: str,
                 api_secret: str,
                 symbol: str,
                 strategy_names: list,
                 risk_pct: float = 1.0,
                 stop_loss_pct: float = 2.0,
                 take_profit_pct: float = 4.0,
                 interval: str = "1h",
                 testnet: bool = False,
                 use_ai: bool = True,
                 min_confidence: int = 65,
                 ):
        self.api_key        = api_key
        self.api_secret     = api_secret
        self.symbol         = symbol
        self.strategy_names = strategy_names
        self.risk_pct       = risk_pct
        self.stop_loss_pct  = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.interval       = interval
        self.use_ai         = use_ai
        self.min_confidence = min_confidence

        self.market      = MarketData(api_key, api_secret, testnet)
        self.strategy_mgr = StrategyManager()
        self.news_fetcher = NewsFetcher()

        self._running    = False
        self._thread     = None
        self._in_trade   = False
        self._entry_price = 0.0
        self._open_order  = None

        # Callbacks
        self.on_log:    Optional[Callable[[str], None]] = None
        self.on_trade:  Optional[Callable[[dict], None]] = None
        self.on_status: Optional[Callable[[dict], None]] = None

    def _log(self, msg: str):
        logger.info(msg)
        if self.on_log:
            self.on_log(msg)

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread  = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()
        self._log(f"🚀 بدأ التداول التلقائي على {self.symbol}")

    def stop(self):
        self._running = False
        self._log("⏹️ تم إيقاف التداول التلقائي")

    def is_running(self) -> bool:
        return self._running

    def _loop(self):
        while self._running:
            try:
                self._tick()
                time.sleep(self._get_sleep_seconds())
            except Exception as e:
                self._log(f"❌ خطأ في الحلقة: {e}")
                time.sleep(30)

    def _get_sleep_seconds(self) -> int:
        mapping = {
            "1m": 60, "5m": 300, "15m": 900,
            "1h": 3600, "4h": 14400, "1d": 86400,
        }
        return mapping.get(self.interval, 3600)

    def _tick(self):
        self._log(f"🔄 فحص دوري — {self.symbol} @ {time.strftime('%H:%M:%S')}")

        # جلب البيانات
        df = self.market.get_klines(self.symbol, self.interval, limit=200)
        indicators = compute_all_indicators(df)
        current_price = float(df.iloc[-1]["close"])

        # تحديث الحالة
        if self.on_status:
            self.on_status({
                "price": current_price,
                "indicators": indicators,
                "in_trade": self._in_trade,
                "entry_price": self._entry_price,
            })

        # إذا في صفقة — تحقق من الوقف والهدف
        if self._in_trade:
            sl = self._entry_price * (1 - self.stop_loss_pct / 100)
            tp = self._entry_price * (1 + self.take_profit_pct / 100)
            if current_price <= sl:
                self._close_trade("SELL", current_price, "🛑 وقف الخسارة")
            elif current_price >= tp:
                self._close_trade("SELL", current_price, "🎯 هدف الربح")
            return

        # حساب إشارات الاستراتيجيات
        strategy_signals = {}
        for name in self.strategy_names:
            sig = self.strategy_mgr.apply_strategy(name, indicators)
            strategy_signals[name] = sig or "HOLD"

        consensus = self.strategy_mgr.get_consensus(strategy_signals)
        self._log(f"📊 إجماع الاستراتيجيات: {consensus['decision']} ({consensus['confidence']}%)")

        # إذا الإجماع يقترح صفقة وثقته كافية
        if consensus["decision"] != "HOLD" and consensus["confidence"] >= 50:
            if self.use_ai:
                self._analyze_with_ai_then_trade(df, indicators, consensus["decision"])
            else:
                self._open_trade(consensus["decision"], current_price)

    def _analyze_with_ai_then_trade(self, df, indicators, strategy_signal):
        current_price = float(df.iloc[-1]["close"])
        news = self.news_fetcher.get_news_for_symbol(self.symbol)

        analyzer = MultiStageAnalyzer(self.symbol, indicators, news["text"])

        def on_complete(result):
            ai_decision  = result["decision"]
            ai_confidence = result["confidence"]
            self._log(f"🤖 AI قرار: {ai_decision} ({ai_confidence}% ثقة)")

            # التحقق من توافق AI مع الاستراتيجية
            if ai_decision == strategy_signal or ai_decision == "HOLD":
                if ai_confidence >= self.min_confidence:
                    final_decision = strategy_signal
                    self._open_trade(final_decision, current_price)
                else:
                    self._log(f"⏸️ الثقة منخفضة ({ai_confidence}%) — لا صفقة")
            else:
                self._log(f"⚠️ تعارض: AI={ai_decision} مقابل Strategy={strategy_signal} — تجاهل")

        analyzer.run_full_analysis_async(
            on_progress=lambda s, m: self._log(m),
            on_complete=on_complete,
        )

    def _open_trade(self, side: str, price: float):
        self._log(f"📈 فتح صفقة {side} @ {price}")
        try:
            account = self.market.get_account()
            usdt_balance = 0.0
            for balance in account.get("balances", []):
                if balance["asset"] == "USDT":
                    usdt_balance = float(balance["free"])
                    break

            trade_usd = usdt_balance * (self.risk_pct / 100)
            quantity  = trade_usd / price

            order = self.market.place_order(self.symbol, side, quantity)
            self._in_trade    = True
            self._entry_price = price
            self._open_order  = order

            trade_info = {
                "type":        "OPEN",
                "side":        side,
                "symbol":      self.symbol,
                "price":       price,
                "quantity":    quantity,
                "trade_usd":   trade_usd,
                "order_id":    order.get("orderId"),
                "time":        time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            self._log(f"✅ صفقة مفتوحة — الكمية: {quantity:.6f}")
            if self.on_trade:
                self.on_trade(trade_info)

        except Exception as e:
            self._log(f"❌ فشل فتح الصفقة: {e}")

    def _close_trade(self, side: str, price: float, reason: str):
        self._log(f"📉 إغلاق الصفقة — {reason} @ {price}")
        try:
            pnl = (price - self._entry_price) / self._entry_price * 100
            trade_info = {
                "type":       "CLOSE",
                "side":       side,
                "symbol":     self.symbol,
                "price":      price,
                "entry_price": self._entry_price,
                "pnl_pct":    round(pnl, 2),
                "reason":     reason,
                "time":       time.strftime("%Y-%m-%d %H:%M:%S"),
            }
            self._in_trade    = False
            self._entry_price = 0.0
            if self.on_trade:
                self.on_trade(trade_info)

        except Exception as e:
            self._log(f"❌ خطأ في إغلاق الصفقة: {e}")
