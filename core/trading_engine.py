"""
Auto Trading Engine — Smart State Machine
==========================================

Two-state machine:

══ HUNTING ══════════════════════════════════════════════════════
  When NOT in a trade — scans every X seconds looking for an entry:
  - Fetches live candle data
  - Runs prediction + strategy consensus
  - If all signals say BUY → enters trade → switches to GUARDING
  - Otherwise → sleeps X seconds and scans again
  (X = candle_duration / 4, capped at 5 minutes, min 30 seconds)

══ GUARDING ═════════════════════════════════════════════════════
  When IN a trade — sleeps until 5 minutes before candle close:
  - Runs prediction: will next candle be UP or DOWN?
  - DOWN predicted  → sells → switches back to HUNTING immediately
  - Stop Loss hit   → sells → switches back to HUNTING immediately
  - Take Profit hit → sells → switches back to HUNTING immediately
  - UP predicted    → holds, waits for next candle

═══ AnomalyGuard ════════════════════════════════════════════════
  Runs in a separate thread, checks every 20 seconds.
  If flash crash / volume spike / order book collapse detected:
  → sells immediately → switches back to HUNTING
"""

import time
import threading
import logging
from enum import Enum, auto
from typing import Callable, Optional

from core.market_data import MarketData
from core.indicators import compute_all_indicators
from core.strategy_manager import StrategyManager
from core.ai_engine import MultiStageAnalyzer
from core.news_fetcher import NewsFetcher
from core.pre_candle_predictor import (
    predict_candle_direction,
    seconds_until_candle_close,
    get_candle_close_time_ms,
    TIMEFRAME_SECONDS,
    PRE_CLOSE_WINDOW,       # = 300 seconds (5 minutes)
)
from core.anomaly_guard import AnomalyGuard

logger = logging.getLogger(__name__)

PRE_CLOSE_WINDOW_SEC = PRE_CLOSE_WINDOW  # alias


# ─── States ───────────────────────────────────────────────────────────────────

class TraderState(Enum):
    HUNTING  = auto()   # Scanning for a buy opportunity
    GUARDING = auto()   # In a trade, monitoring for exit


# ─── Helpers ──────────────────────────────────────────────────────────────────

def _get_scan_interval(interval: str) -> int:
    """
    Seconds between each HUNTING scan.
    = candle_duration / 4, capped between 30s and 300s (5 min).

    Examples:
      1m  → 15s
      5m  → 75s
      15m → 225s (~3.75 min)
      1h  → 300s (5 min, capped)
      4h  → 300s (5 min, capped)
    """
    candle_sec = TIMEFRAME_SECONDS.get(interval, 3600)
    quarter    = candle_sec // 4
    return max(30, min(quarter, PRE_CLOSE_WINDOW_SEC))


def _interruptible_sleep(seconds: float, running_flag_fn: Callable[[], bool],
                         step: float = 5.0) -> bool:
    """
    Sleeps for the given duration in small steps so it can be interrupted.
    Returns True if sleep completed, False if stopped early.
    """
    deadline = time.time() + seconds
    while time.time() < deadline:
        if not running_flag_fn():
            return False
        time.sleep(min(step, max(0.1, deadline - time.time())))
    return True


# ══════════════════════════════════════════════════════════════════════════════
# AutoTrader
# ══════════════════════════════════════════════════════════════════════════════

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
        self.api_key         = api_key
        self.api_secret      = api_secret
        self.symbol          = symbol
        self.strategy_names  = strategy_names
        self.risk_pct        = risk_pct
        self.stop_loss_pct   = stop_loss_pct
        self.take_profit_pct = take_profit_pct
        self.interval        = interval
        self.use_ai          = use_ai
        self.min_confidence  = min_confidence

        self.market       = MarketData(api_key, api_secret, testnet)
        self.strategy_mgr = StrategyManager()
        self.news_fetcher = NewsFetcher()

        # State machine
        self._running      = False
        self._state        = TraderState.HUNTING
        self._thread: Optional[threading.Thread] = None

        # Current trade
        self._in_trade     = False
        self._entry_price  = 0.0
        self._open_order   = None

        # Indicators cache shared with AnomalyGuard
        self._latest_indicators: dict = {}

        # Rate-limiting for API calls
        self._last_api_call: float = 0.0
        self._min_api_gap: float   = 2.0   # seconds between API requests

        # Cumulative stats
        self._total_pnl_pct: float = 0.0
        self._trades_count:  int   = 0
        self._wins:          int   = 0

        # Anomaly Guard (runs in its own thread)
        self._anomaly_guard = AnomalyGuard(
            market_data         = self.market,
            symbol              = self.symbol,
            indicators_fn       = lambda: self._latest_indicators,
            on_anomaly_detected = self._emergency_exit,
            log_fn              = lambda m: self._log(m),
            check_interval      = 20,
        )

        # GUI callbacks
        self.on_log:    Optional[Callable[[str], None]] = None
        self.on_trade:  Optional[Callable[[dict], None]] = None
        self.on_status: Optional[Callable[[dict], None]] = None

    # ── Logging ───────────────────────────────────────────────────────────────

    def _log(self, msg: str):
        logger.info(msg)
        if self.on_log:
            self.on_log(msg)

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._state   = TraderState.HUNTING

        self._thread = threading.Thread(
            target=self._state_machine_loop, daemon=True, name="AutoTrader"
        )
        self._thread.start()
        self._anomaly_guard.start()

        scan_sec   = _get_scan_interval(self.interval)
        candle_sec = TIMEFRAME_SECONDS.get(self.interval, 3600)
        guard_sec  = max(0, candle_sec - PRE_CLOSE_WINDOW_SEC)
        gm, gs     = divmod(guard_sec, 60)
        gh, gm     = divmod(gm, 60)
        sm, ss     = divmod(scan_sec, 60)

        self._log(f"🚀 Smart AutoTrader started | {self.symbol} | Interval: {self.interval}")
        self._log(f"🔍 HUNTING: scans every {sm}m {ss}s | ⚔️ GUARDING: sleeps {gh}h{gm:02d}m then checks 5m before close")
        self._log("🛡️ AnomalyGuard active — monitoring every 20 seconds")

    def stop(self):
        self._running = False
        self._anomaly_guard.stop()
        win_rate = round(self._wins / self._trades_count * 100) if self._trades_count else 0
        self._log(
            f"⏹️ Stopped | Trades: {self._trades_count} | "
            f"Total P&L: {self._total_pnl_pct:+.2f}% | Win rate: {win_rate}%"
        )

    def is_running(self) -> bool:
        return self._running

    # ══════════════════════════════════════════════════════════════════════════
    # State Machine Loop
    # ══════════════════════════════════════════════════════════════════════════

    def _state_machine_loop(self):
        self._log(f"🔁 State machine started | {self.symbol}")

        while self._running:
            try:
                if self._state == TraderState.HUNTING:
                    self._hunting_cycle()
                else:
                    self._guarding_cycle()
            except Exception as e:
                self._log(f"❌ Loop error: {e}")
                _interruptible_sleep(15, lambda: self._running)

        self._log("🔁 State machine stopped")

    # ══════════════════════════════════════════════════════════════════════════
    # HUNTING — looking for a buy entry
    # ══════════════════════════════════════════════════════════════════════════

    def _hunting_cycle(self):
        """
        Fetch data, run prediction + strategies, decide:
        - Strong BUY signal → open trade → switch to GUARDING
        - No signal         → sleep scan_interval, try again
        """
        scan_interval = _get_scan_interval(self.interval)

        self._log(f"🔍 [HUNTING] Scanning... {self.symbol} @ {time.strftime('%H:%M:%S')}")

        df = self._safe_get_klines()
        if df is None:
            _interruptible_sleep(scan_interval, lambda: self._running)
            return

        indicators    = compute_all_indicators(df)
        current_price = float(df.iloc[-1]["close"])
        self._latest_indicators = indicators
        self._emit_status(current_price, indicators)

        # Prediction
        pred  = predict_candle_direction(df, indicators)
        arrow = "📈" if pred["prediction"] == "UP" else (
                "📉" if pred["prediction"] == "DOWN" else "➡️")
        self._log(
            f"  {arrow} Prediction: {pred['prediction']} | "
            f"Confidence: {pred['confidence']:.0f}% | {pred['reason'][:70]}"
        )

        # Strategy consensus
        consensus = self._get_consensus(indicators)
        self._log(
            f"  📊 Consensus: {consensus['decision']} ({consensus['confidence']}%) | "
            f"Buy:{consensus['buy_strats']} Sell:{consensus['sell_strats']}"
        )

        # Entry condition
        should_buy = (
            pred["prediction"] == "UP"
            and consensus["decision"] == "BUY"
            and consensus["confidence"] >= 50
        )

        if should_buy:
            self._log("🟢 Strong BUY signal! Running AI confirmation...")
            if self.use_ai:
                self._analyze_with_ai_then_buy(df, indicators, current_price)
            else:
                self._open_trade("BUY", current_price)
        else:
            sm, ss = divmod(scan_interval, 60)
            self._log(
                f"  ⏳ No entry signal ({pred['prediction']}/{consensus['decision']}) "
                f"— retrying in {sm}m {ss}s"
            )
            _interruptible_sleep(scan_interval, lambda: self._running)

    # ══════════════════════════════════════════════════════════════════════════
    # GUARDING — in a trade, watching for exit
    # ══════════════════════════════════════════════════════════════════════════

    def _guarding_cycle(self):
        """
        Sleeps until 5 minutes before candle close, then decides:
        - SL/TP hit       → sell → HUNTING
        - DOWN predicted  → sell → HUNTING
        - UP predicted    → hold, wait for next candle
        """
        secs_left = seconds_until_candle_close(self.interval)
        sleep_sec = max(0.0, secs_left - PRE_CLOSE_WINDOW_SEC)

        candle_sec = TIMEFRAME_SECONDS.get(self.interval, 3600)
        if candle_sec <= 600:
            sleep_sec = 0   # short timeframes: check immediately

        if sleep_sec > 0:
            sleep_m = int(sleep_sec // 60)
            sleep_s = int(sleep_sec % 60)
            pnl_now = 0.0
            if self._entry_price > 0:
                try:
                    mid = self.market.get_price(self.symbol)
                    pnl_now = (mid - self._entry_price) / self._entry_price * 100
                except Exception:
                    pass
            self._log(
                f"⚔️ [GUARDING] In trade @ {self._entry_price:.4f} | "
                f"Current PnL: {pnl_now:+.2f}% | "
                f"Next check in {sleep_m}m {sleep_s}s ({PRE_CLOSE_WINDOW_SEC//60}m before close)"
            )
            ok = _interruptible_sleep(sleep_sec, lambda: self._running)
            if not ok:
                return

        if not self._running:
            return

        # Live data at check time
        self._log(
            f"🔔 [GUARDING] Pre-close check | {self.symbol} @ {time.strftime('%H:%M:%S')}"
        )
        df = self._safe_get_klines()
        if df is None:
            return

        indicators    = compute_all_indicators(df)
        current_price = float(df.iloc[-1]["close"])
        self._latest_indicators = indicators
        self._emit_status(current_price, indicators)

        # Stop Loss / Take Profit
        sl = self._entry_price * (1 - self.stop_loss_pct / 100)
        tp = self._entry_price * (1 + self.take_profit_pct / 100)

        if current_price <= sl:
            self._close_trade("SELL", current_price, f"🛑 Stop Loss hit @ {sl:.4f}")
            self._state = TraderState.HUNTING
            self._log("🔍 Switched to HUNTING — searching for next opportunity...")
            return

        if current_price >= tp:
            self._close_trade("SELL", current_price, f"🎯 Take Profit hit @ {tp:.4f}")
            self._state = TraderState.HUNTING
            self._log("🔍 Switched to HUNTING — searching for next opportunity...")
            return

        # Pre-close prediction
        pred  = predict_candle_direction(df, indicators)
        arrow = "📈" if pred["prediction"] == "UP" else (
                "📉" if pred["prediction"] == "DOWN" else "➡️")
        self._log(
            f"  {arrow} Prediction: {pred['prediction']} | "
            f"Confidence: {pred['confidence']:.0f}% | {pred['reason'][:70]}"
        )

        # Strategy consensus
        consensus = self._get_consensus(indicators)
        self._log(f"  📊 Consensus: {consensus['decision']} ({consensus['confidence']}%)")

        # Exit decision
        sell_reason = None

        if pred["prediction"] == "DOWN" and pred["confidence"] >= 40:
            sell_reason = f"⏳ DOWN predicted ({pred['confidence']:.0f}%) before candle close"
        elif consensus["decision"] == "SELL" and pred["prediction"] != "UP":
            sell_reason = f"📉 SELL consensus ({consensus['confidence']}%) + no bullish prediction"

        if sell_reason:
            if self.use_ai:
                self._log("🤖 Sending standard exit signals to Ultimate Blender for verification...")
                self._analyze_with_ai_then_sell_or_hold(indicators, current_price, sell_reason)
            else:
                self._close_trade("SELL", current_price, sell_reason)
                self._state = TraderState.HUNTING
                self._log("🔍 Switched to HUNTING — looking for next buy opportunity...")
        else:
            pnl_now = (current_price - self._entry_price) / self._entry_price * 100
            self._log(
                f"  ✅ Holding position | PnL: {pnl_now:+.2f}% | "
                f"SL: {sl:.4f} | TP: {tp:.4f}"
            )

    # ══════════════════════════════════════════════════════════════════════════
    # AI Analysis
    # ══════════════════════════════════════════════════════════════════════════

    def _analyze_with_ai_then_buy(self, df, indicators, current_price: float):
        """Runs full 6-stage AI analysis by preparing full_data payload."""
        self._log("⏳ Collecting full market context for Ultimate Blender...")
        full_data = {}
        
        # 1. Market Data
        frames = self.market.get_multi_timeframe(self.symbol)
        for tf, d in frames.items():
            full_data[f"indicators_{tf}"] = compute_all_indicators(d)
            
        full_data["order_book"]    = self.market.get_order_book(self.symbol)
        full_data["fear_greed"]    = self.market.get_fear_greed()
        full_data["coingecko"]     = self.market.get_coingecko_data(self.symbol)
        full_data["global_market"] = self.market.get_global_market()
        full_data["recent_trades"] = self.market.get_recent_trades(self.symbol)
        
        # 2. News
        full_data["news"] = self.news_fetcher.get_news_for_symbol(self.symbol)
        
        # 3. Strategy Consensus
        primary_ind = full_data.get(f"indicators_{self.interval}", indicators)
        results = self.strategy_mgr.run_all_strategies(primary_ind)
        consensus = self.strategy_mgr.get_weighted_consensus(results)
        full_data["strategy_consensus"] = consensus

        analyzer = MultiStageAnalyzer(self.symbol, full_data, self.interval)

        def on_complete(result):
            ai_decision   = result["decision"]
            ai_confidence = result["confidence"]
            self._log(f"🤖 AI blender verdict: {ai_decision} | Confidence: {ai_confidence}%")

            if ai_decision == "BUY" and ai_confidence >= self.min_confidence:
                self._log(f"✅ AI confirms BUY ({ai_confidence}% ≥ {self.min_confidence}%)")
                self._open_trade("BUY", current_price)
            elif ai_decision == "SELL":
                self._log("⚠️ AI says SELL — skipping entry, resuming HUNTING...")
            else:
                self._log(f"⏸️ AI: {ai_decision} ({ai_confidence}%) — no entry, continuing scan")

        analyzer.run_full_analysis_async(
            on_progress=lambda s, m: self._log(m) if "Stage" in m or "FINAL" in m else None,
            on_complete=on_complete,
        )

    def _analyze_with_ai_then_sell_or_hold(self, indicators, current_price: float, standard_reason: str):
        """Runs full 6-stage AI analysis to decide if an exit should be approved."""
        self._log("⏳ Collecting full market context for Exit Blender...")
        full_data = {}
        
        frames = self.market.get_multi_timeframe(self.symbol)
        for tf, d in frames.items():
            full_data[f"indicators_{tf}"] = compute_all_indicators(d)
            
        full_data["order_book"]    = self.market.get_order_book(self.symbol)
        full_data["fear_greed"]    = self.market.get_fear_greed()
        full_data["coingecko"]     = self.market.get_coingecko_data(self.symbol)
        full_data["global_market"] = self.market.get_global_market()
        full_data["recent_trades"] = self.market.get_recent_trades(self.symbol)
        full_data["news"]          = self.news_fetcher.get_news_for_symbol(self.symbol)
        
        primary_ind = full_data.get(f"indicators_{self.interval}", indicators)
        results = self.strategy_mgr.run_all_strategies(primary_ind)
        consensus = self.strategy_mgr.get_weighted_consensus(results)
        full_data["strategy_consensus"] = consensus

        from core.ai_engine import MultiStageAnalyzer
        analyzer = MultiStageAnalyzer(self.symbol, full_data, self.interval)

        def on_complete(result):
            ai_decision   = result["decision"]
            ai_confidence = result["confidence"]
            self._log(f"🤖 AI Exit verdict: {ai_decision} | Confidence: {ai_confidence}%")

            if ai_decision == "SELL":
                self._log(f"✅ AI confirms standard exit! Executing SELL...")
                self._close_trade("SELL", current_price, f"{standard_reason} + AI Confirmation")
                self._state = TraderState.HUNTING
            elif ai_decision == "HOLD":
                self._log("⚠️ AI says HOLD — overriding standard exit signal! Holding strong...")
            else:
                self._log(f"⏸️ AI: {ai_decision} — ignoring exit for now...")

        analyzer.run_full_analysis_async(
            on_progress=lambda s, m: self._log(m) if "Stage" in m or "FINAL" in m else None,
            on_complete=on_complete,
        )

    # ══════════════════════════════════════════════════════════════════════════
    # Trade Execution
    # ══════════════════════════════════════════════════════════════════════════

    def _open_trade(self, side: str, price: float):
        self._log(f"📈 Opening {side} @ {price:.4f}")
        try:
            account      = self.market.get_account()
            usdt_balance = 0.0
            for bal in account.get("balances", []):
                if bal["asset"] == "USDT":
                    usdt_balance = float(bal["free"])
                    break

            trade_usd = usdt_balance * (self.risk_pct / 100)
            quantity  = trade_usd / price

            order = self.market.place_order(self.symbol, side, quantity)

            self._in_trade    = True
            self._entry_price = price
            self._open_order  = order
            self._state       = TraderState.GUARDING   # transition

            sl_price = price * (1 - self.stop_loss_pct / 100)
            tp_price = price * (1 + self.take_profit_pct / 100)

            self._log(
                f"✅ Trade opened | Qty: {quantity:.6f} | USDT: {trade_usd:.2f} | "
                f"SL: {sl_price:.4f} | TP: {tp_price:.4f}"
            )
            self._log("⚔️ Switched to GUARDING — monitoring until exit or target")

            if self.on_trade:
                self.on_trade({
                    "type":      "OPEN",
                    "side":      side,
                    "symbol":    self.symbol,
                    "price":     price,
                    "quantity":  quantity,
                    "trade_usd": trade_usd,
                    "order_id":  order.get("orderId"),
                    "sl":        sl_price,
                    "tp":        tp_price,
                    "time":      time.strftime("%Y-%m-%d %H:%M:%S"),
                })

        except Exception as e:
            self._log(f"❌ Failed to open trade: {e}")
            self._state = TraderState.HUNTING   # stay in HUNTING on failure

    def _close_trade(self, side: str, price: float, reason: str):
        self._log(f"📉 Closing trade | {reason} @ {price:.4f}")
        entry_snap = self._entry_price
        try:
            pnl = (price - entry_snap) / entry_snap * 100 if entry_snap > 0 else 0

            self._in_trade    = False
            self._entry_price = 0.0
            self._open_order  = None

            # Update stats
            self._trades_count  += 1
            self._total_pnl_pct += pnl
            if pnl > 0:
                self._wins += 1

            win_rate = round(self._wins / self._trades_count * 100) if self._trades_count else 0

            self._log(
                f"💰 PnL: {pnl:+.2f}% | "
                f"Total P&L: {self._total_pnl_pct:+.2f}% | "
                f"Win rate: {win_rate}% ({self._wins}/{self._trades_count})"
            )

            if self.on_trade:
                self.on_trade({
                    "type":        "CLOSE",
                    "side":        side,
                    "symbol":      self.symbol,
                    "price":       price,
                    "entry_price": entry_snap,
                    "pnl_pct":     round(pnl, 2),
                    "total_pnl":   round(self._total_pnl_pct, 2),
                    "win_rate":    win_rate,
                    "trades":      self._trades_count,
                    "reason":      reason,
                    "time":        time.strftime("%Y-%m-%d %H:%M:%S"),
                })

        except Exception as e:
            self._log(f"❌ Error closing trade: {e}")

    # ══════════════════════════════════════════════════════════════════════════
    # Emergency Exit — AnomalyGuard callback
    # ══════════════════════════════════════════════════════════════════════════

    def _emergency_exit(self, reason: str):
        """
        Called by AnomalyGuard when a dangerous anomaly is detected.
        Sells everything immediately and returns to HUNTING.
        """
        self._log(f"🆘🆘🆘 EMERGENCY EXIT! {reason}")

        if not self._in_trade:
            self._log("ℹ️ No open trade — nothing to close")
            return

        # Get current market price
        try:
            current_price = self.market.get_price(self.symbol)
        except Exception:
            current_price = self._entry_price

        # Execute emergency sell via API
        try:
            account    = self.market.get_account()
            base_asset = self.symbol.replace("USDT", "")
            coin_bal   = 0.0
            for bal in account.get("balances", []):
                if bal["asset"] == base_asset:
                    coin_bal = float(bal["free"])
                    break

            if coin_bal > 0:
                self.market.place_order(self.symbol, "SELL", coin_bal)
                self._log(f"✅ Emergency sell executed — {coin_bal:.6f} {base_asset} @ {current_price:.4f}")
            else:
                self._log("⚠️ No balance available for emergency sell")
        except Exception as e:
            self._log(f"❌ Emergency sell API failed: {e}")

        # Update internal state
        entry_snap    = self._entry_price
        pnl = ((current_price - entry_snap) / entry_snap * 100
               if entry_snap > 0 else 0)

        self._in_trade    = False
        self._entry_price = 0.0
        self._open_order  = None

        # Return to HUNTING immediately
        self._state = TraderState.HUNTING

        self._trades_count  += 1
        self._total_pnl_pct += pnl

        win_rate = round(self._wins / self._trades_count * 100) if self._trades_count else 0

        self._log(f"🆘 Emergency trade closed | PnL: {pnl:+.2f}%")
        self._log("🔍 Switched to HUNTING — looking for a safe re-entry...")

        if self.on_trade:
            self.on_trade({
                "type":        "EMERGENCY_CLOSE",
                "side":        "SELL",
                "symbol":      self.symbol,
                "price":       current_price,
                "entry_price": entry_snap,
                "pnl_pct":     round(pnl, 2),
                "total_pnl":   round(self._total_pnl_pct, 2),
                "win_rate":    win_rate,
                "trades":      self._trades_count,
                "reason":      f"🆘 ANOMALY: {reason}",
                "time":        time.strftime("%Y-%m-%d %H:%M:%S"),
            })

    # ══════════════════════════════════════════════════════════════════════════
    # Internal Helpers
    # ══════════════════════════════════════════════════════════════════════════

    def _get_consensus(self, indicators: dict) -> dict:
        """Runs all strategies and returns weighted consensus."""
        signals = {}
        for name in self.strategy_names:
            sig = self.strategy_mgr.apply_strategy(name, indicators)
            signals[name] = sig or "HOLD"
        return self.strategy_mgr.get_consensus(signals)

    def _safe_get_klines(self):
        """Fetches klines with error handling and rate limiting."""
        gap = time.time() - self._last_api_call
        if gap < self._min_api_gap:
            time.sleep(self._min_api_gap - gap)
        try:
            df = self.market.get_klines(self.symbol, self.interval, limit=200)
            self._last_api_call = time.time()
            return df
        except Exception as e:
            self._log(f"⚠️ Failed to fetch klines: {e}")
            self._last_api_call = time.time()
            return None

    def _emit_status(self, price: float, indicators: dict):
        """Sends current status to GUI callback."""
        if self.on_status:
            self.on_status({
                "price":       price,
                "indicators":  indicators,
                "in_trade":    self._in_trade,
                "entry_price": self._entry_price,
                "state":       self._state.name,
                "total_pnl":   self._total_pnl_pct,
                "trades":      self._trades_count,
            })
