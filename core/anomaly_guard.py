"""
Anomaly Guard
=============
Continuous background monitor that detects dangerous market conditions
and triggers an emergency exit before capital is lost.

Monitors for:
  1. Flash Crash      — rapid price drop > X% in a short window
  2. Volume Spike     — massive volume surge with simultaneous price drop
  3. Order Book       — buy pressure collapse or abnormally wide spread
  4. RSI Cliff        — RSI collapses rapidly (panic selling)
  5. EMA200 Break     — price breaks below EMA200 by dangerous margin
"""

import time
import threading
import logging
from typing import Callable, Optional
from collections import deque

logger = logging.getLogger(__name__)


# ─── Thresholds (adjustable) ──────────────────────────────────────────────────
ANOMALY_CONFIG = {
    # Flash crash: price drops by this % within a short window
    "flash_crash_pct":       2.5,   # % drop to trigger
    "flash_crash_window":    3,     # number of recent readings to compare

    # Volume spike: current volume vs rolling average
    "volume_spike_ratio":    4.0,   # current / avg >= 4x
    "volume_spike_min_drop": 1.0,   # minimum % price drop to confirm danger

    # Order book spread: (ask - bid) / bid > threshold → low liquidity
    "spread_pct_threshold":  1.5,   # %

    # Buy pressure collapse
    "buy_pressure_danger":   25.0,  # if buy pressure < 25% → danger

    # RSI cliff: RSI drops by this many points in a short window
    "rsi_cliff_drop":        15,    # RSI points
    "rsi_cliff_window":      4,     # number of recent readings

    # Price below EMA200 by dangerous margin
    "ema200_break_pct":      1.5,   # % below EMA200 to trigger
}


class AnomalyGuard:
    """
    Continuous safety monitor. Runs in a dedicated thread.
    Calls on_anomaly_detected(reason: str) when danger is detected.

    Usage:
        guard = AnomalyGuard(
            market_data         = self.market,
            symbol              = self.symbol,
            indicators_fn       = lambda: current_indicators,
            on_anomaly_detected = self._emergency_exit,
            log_fn              = self._log,
        )
        guard.start()
        # ...
        guard.stop()
    """

    def __init__(self,
                 market_data,
                 symbol: str,
                 indicators_fn: Callable[[], dict],
                 on_anomaly_detected: Callable[[str], None],
                 log_fn: Optional[Callable[[str], None]] = None,
                 check_interval: int = 20):
        """
        Args:
            market_data:          MarketData instance
            symbol:               Trading pair (e.g. BTCUSDT)
            indicators_fn:        callable → latest indicators dict
            on_anomaly_detected:  callable(reason) — fires on danger
            log_fn:               optional log callback
            check_interval:       seconds between checks (default: 20s)
        """
        self.market          = market_data
        self.symbol          = symbol
        self._get_indicators = indicators_fn
        self.on_anomaly      = on_anomaly_detected
        self._log_fn         = log_fn
        self.check_interval  = check_interval

        self._running = False
        self._thread: Optional[threading.Thread] = None

        # Rolling history for trend detection
        self._price_history:  deque = deque(maxlen=20)
        self._rsi_history:    deque = deque(maxlen=20)
        self._volume_history: deque = deque(maxlen=20)

        # Cooldown — prevents repeated alerts for the same event
        self._last_alert_time: float = 0.0
        self._alert_cooldown:  float = 180.0   # 3 minutes between alerts

    # ── Public API ─────────────────────────────────────────────────────────────

    def start(self):
        if self._running:
            return
        self._running = True
        self._thread  = threading.Thread(target=self._run, daemon=True, name="AnomalyGuard")
        self._thread.start()
        self._log("🛡️ [AnomalyGuard] Safety monitor started")

    def stop(self):
        self._running = False
        self._log("🛡️ [AnomalyGuard] Safety monitor stopped")

    def is_running(self) -> bool:
        return self._running

    # ── Internal loop ──────────────────────────────────────────────────────────

    def _log(self, msg: str):
        logger.info(msg)
        if self._log_fn:
            self._log_fn(msg)

    def _run(self):
        while self._running:
            try:
                self._check_cycle()
            except Exception as e:
                self._log(f"⚠️ [AnomalyGuard] Check error: {e}")
            time.sleep(self.check_interval)

    def _check_cycle(self):
        """One full safety check iteration."""
        indicators = {}
        try:
            indicators = self._get_indicators() or {}
        except Exception:
            pass

        price  = float(indicators.get("price") or 0)
        rsi    = float(indicators.get("rsi") or 50)
        volume = float(indicators.get("volume_24h") or 0)

        if price > 0:
            self._price_history.append(price)
        if rsi:
            self._rsi_history.append(rsi)
        if volume:
            self._volume_history.append(volume)

        # Need at least a few data points before triggering
        if len(self._price_history) < 3:
            return

        anomaly = (
            self._check_flash_crash()
            or self._check_volume_spike(indicators)
            or self._check_order_book_anomaly()
            or self._check_rsi_cliff()
            or self._check_ema200_break(indicators)
        )

        if anomaly:
            self._fire_alert(anomaly)

    # ─── Individual Checks ────────────────────────────────────────────────────

    def _check_flash_crash(self) -> Optional[str]:
        """Detects rapid price drops within the recent window."""
        window    = ANOMALY_CONFIG["flash_crash_window"]
        threshold = ANOMALY_CONFIG["flash_crash_pct"]

        if len(self._price_history) < window:
            return None

        recent   = list(self._price_history)[-window:]
        high_p   = max(recent)
        low_p    = recent[-1]   # current price (latest reading)

        if high_p <= 0:
            return None

        drop_pct = ((high_p - low_p) / high_p) * 100
        if drop_pct >= threshold:
            return (
                f"Flash Crash! -{drop_pct:.1f}% in last {window * self.check_interval}s "
                f"({high_p:.4f} → {low_p:.4f})"
            )
        return None

    def _check_volume_spike(self, indicators: dict) -> Optional[str]:
        """Detects massive volume surge while price drops."""
        if len(self._volume_history) < 5:
            return None

        avg_vol = sum(list(self._volume_history)[:-1]) / max(len(self._volume_history) - 1, 1)
        cur_vol = self._volume_history[-1]

        if avg_vol <= 0:
            return None

        spike_ratio = ANOMALY_CONFIG["volume_spike_ratio"]
        min_drop    = ANOMALY_CONFIG["volume_spike_min_drop"]

        if cur_vol >= avg_vol * spike_ratio:
            prices = list(self._price_history)
            if len(prices) >= 3:
                drop_pct = ((prices[-3] - prices[-1]) / prices[-3]) * 100
                if drop_pct >= min_drop:
                    return (
                        f"Volume Spike! {cur_vol/avg_vol:.1f}x avg volume "
                        f"with -{drop_pct:.1f}% price drop (heavy sell-off)"
                    )
        return None

    def _check_order_book_anomaly(self) -> Optional[str]:
        """Checks order book for buy pressure collapse or wide spread."""
        try:
            ob           = self.market.get_order_book(self.symbol, limit=10)
            buy_pressure = ob.get("buy_pressure", 50)
            bid_vol      = ob.get("bid_volume", 0)
            ask_vol      = ob.get("ask_volume", 0)

            # Buy pressure collapse
            if buy_pressure <= ANOMALY_CONFIG["buy_pressure_danger"]:
                return (
                    f"Buy Pressure Collapsed! Sells dominate {100 - buy_pressure:.0f}% "
                    f"(Bids={bid_vol:.1f} vs Asks={ask_vol:.1f})"
                )

            # Abnormally wide spread = low liquidity
            bids = ob.get("bids", [])
            asks = ob.get("asks", [])
            if bids and asks:
                best_bid = bids[0][0]
                best_ask = asks[0][0]
                if best_bid > 0:
                    spread_pct = ((best_ask - best_bid) / best_bid) * 100
                    if spread_pct > ANOMALY_CONFIG["spread_pct_threshold"]:
                        return (
                            f"Spread Too Wide: {spread_pct:.2f}% — "
                            f"low liquidity / possible manipulation"
                        )
        except Exception as e:
            logger.debug(f"[AnomalyGuard] Order book check failed: {e}")
        return None

    def _check_rsi_cliff(self) -> Optional[str]:
        """Detects rapid RSI collapse (panic selling)."""
        window   = ANOMALY_CONFIG["rsi_cliff_window"]
        min_drop = ANOMALY_CONFIG["rsi_cliff_drop"]

        if len(self._rsi_history) < window:
            return None

        recent   = list(self._rsi_history)[-window:]
        high_rsi = max(recent[:-1])   # peak RSI in window
        cur_rsi  = recent[-1]

        if high_rsi - cur_rsi >= min_drop and cur_rsi < 40:
            return (
                f"RSI Cliff! Dropped from {high_rsi:.0f} to {cur_rsi:.0f} "
                f"in {window * self.check_interval}s — panic sell detected"
            )
        return None

    def _check_ema200_break(self, indicators: dict) -> Optional[str]:
        """Detects price breaking below EMA200 by a dangerous margin."""
        price  = float(indicators.get("price") or 0)
        ema200 = float(indicators.get("ema200") or 0)

        if not price or not ema200:
            return None

        threshold = ANOMALY_CONFIG["ema200_break_pct"]
        drop_pct  = ((ema200 - price) / ema200) * 100

        if drop_pct >= threshold:
            return (
                f"EMA200 Broken! Price {price:.4f} is {drop_pct:.1f}% "
                f"below EMA200 {ema200:.4f} — danger zone"
            )
        return None

    # ─── Alert Handler ────────────────────────────────────────────────────────

    def _fire_alert(self, reason: str):
        """
        Fires the emergency callback.
        Has a cooldown to prevent multiple alerts for the same event.
        """
        now = time.time()
        if now - self._last_alert_time < self._alert_cooldown:
            self._log(f"🔕 [AnomalyGuard] Alert cooldown active — {reason[:60]}...")
            return

        self._last_alert_time = now
        self._log(f"🆘 [AnomalyGuard] ANOMALY DETECTED: {reason}")
        self._log("🆘 [AnomalyGuard] Triggering emergency exit to protect capital!")

        try:
            self.on_anomaly(reason)
        except Exception as e:
            self._log(f"❌ [AnomalyGuard] Emergency exit callback failed: {e}")

    # ─── Manual Check ─────────────────────────────────────────────────────────

    def force_check(self, indicators: dict) -> Optional[str]:
        """
        Runs a single synchronous check (no threading).
        Returns anomaly reason string or None.
        """
        price  = float(indicators.get("price") or 0)
        rsi    = float(indicators.get("rsi") or 50)
        volume = float(indicators.get("volume_24h") or 0)

        if price > 0:
            self._price_history.append(price)
        if rsi:
            self._rsi_history.append(rsi)
        if volume:
            self._volume_history.append(volume)

        if len(self._price_history) < 3:
            return None

        return (
            self._check_flash_crash()
            or self._check_volume_spike(indicators)
            or self._check_rsi_cliff()
            or self._check_ema200_break(indicators)
        )
