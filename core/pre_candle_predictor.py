"""
Pre-Candle Predictor
====================
15 minutes before a candle closes, predicts the next candle direction:
  - UP   → BUY  (enter or hold)
  - DOWN → SELL (exit before close)
  - NEUTRAL → HOLD
"""

import time
import logging
from typing import Optional, Callable
import pandas as pd

logger = logging.getLogger(__name__)

# ─── Timeframe durations in seconds ───────────────────────────────────────────
TIMEFRAME_SECONDS = {
    "1m":  60,
    "3m":  180,
    "5m":  300,
    "15m": 900,
    "30m": 1800,
    "1h":  3600,
    "2h":  7200,
    "4h":  14400,
    "6h":  21600,
    "8h":  28800,
    "12h": 43200,
    "1d":  86400,
}

# 15 minutes (900 seconds) before candle close — trigger prediction
PRE_CLOSE_WINDOW = 900


def get_candle_close_time_ms(interval: str) -> int:
    """
    Calculate the next candle close time (Unix ms) for the given interval.
    Binance candles are aligned to clean boundaries (e.g. 1h → :00:00 every hour).
    """
    dur      = TIMEFRAME_SECONDS.get(interval, 3600)
    now_ms   = int(time.time() * 1000)
    dur_ms   = dur * 1000
    close_ms = ((now_ms // dur_ms) + 1) * dur_ms
    return close_ms


def seconds_until_candle_close(interval: str) -> float:
    """Seconds remaining until the current candle closes."""
    close_ms = get_candle_close_time_ms(interval)
    now_ms   = int(time.time() * 1000)
    return max(0.0, (close_ms - now_ms) / 1000.0)


# ─── Prediction Logic ──────────────────────────────────────────────────────────

def predict_candle_direction(df: pd.DataFrame, indicators: dict) -> dict:
    """
    Predict whether the next candle will be bullish or bearish using
    momentum, volume, RSI, MACD, Bollinger Bands, and EMA analysis.

    Returns:
        {
            "prediction":  "UP" | "DOWN" | "NEUTRAL",
            "confidence":  float (0-100),
            "score":       int   (raw weighted score),
            "action":      "BUY" | "SELL" | "HOLD",
            "reason":      str   (pipe-separated list of signals)
        }
    """
    scores  = []    # positive = bullish, negative = bearish
    reasons = []

    # ── 1. Candle body momentum (last 3 candles) ──────────────────────────────
    if len(df) >= 3:
        last3      = df.tail(3)
        bodies     = (last3["close"] - last3["open"]).tolist()
        bull_count = sum(1 for b in bodies if b > 0)
        bear_count = sum(1 for b in bodies if b < 0)
        if bull_count >= 2:
            scores.append(+15)
            reasons.append(f"Last 3 candles: {bull_count} bullish")
        elif bear_count >= 2:
            scores.append(-15)
            reasons.append(f"Last 3 candles: {bear_count} bearish")

    # ── 2. Volume momentum ────────────────────────────────────────────────────
    if len(df) >= 10:
        recent_vol = df["volume"].tail(3).mean()
        avg_vol    = df["volume"].tail(10).mean()
        if recent_vol > avg_vol * 1.5:
            if df["close"].iloc[-1] > df["open"].iloc[-1]:
                scores.append(+20)
                reasons.append("High volume + bullish candle")
            else:
                scores.append(-20)
                reasons.append("High volume + bearish candle (strong sell pressure)")
        elif recent_vol < avg_vol * 0.5:
            reasons.append("Low volume — weak move")

    # ── 3. RSI momentum ───────────────────────────────────────────────────────
    rsi = indicators.get("rsi") or 50
    if rsi > 60:
        scores.append(+10)
        reasons.append(f"RSI={rsi:.1f} (bullish momentum)")
    elif rsi > 50:
        scores.append(+5)
    elif rsi < 40:
        scores.append(-10)
        reasons.append(f"RSI={rsi:.1f} (weak / fear)")
    elif rsi < 50:
        scores.append(-5)

    # ── 4. MACD histogram direction ───────────────────────────────────────────
    macd_h = indicators.get("macd_hist") or 0
    if macd_h > 0:
        scores.append(+10)
        reasons.append("MACD histogram positive — bullish momentum")
    elif macd_h < 0:
        scores.append(-10)
        reasons.append("MACD histogram negative — bearish momentum")

    # ── 5. Price vs EMA20 (short-term trend) ─────────────────────────────────
    price = indicators.get("price") or 0
    ema20 = indicators.get("ema20") or 0
    if price and ema20:
        diff_pct = ((price - ema20) / ema20) * 100
        if diff_pct > 0.3:
            scores.append(+10)
            reasons.append(f"Price above EMA20 by {diff_pct:.1f}%")
        elif diff_pct < -0.3:
            scores.append(-10)
            reasons.append(f"Price below EMA20 by {abs(diff_pct):.1f}%")

    # ── 6. Bollinger Band position ────────────────────────────────────────────
    bb_upper = indicators.get("bb_upper") or 0
    bb_lower = indicators.get("bb_lower") or 0
    bb_mid   = indicators.get("bb_mid") or 0
    if price and bb_upper and bb_lower and bb_mid:
        bb_range = bb_upper - bb_lower
        if bb_range > 0:
            pos = (price - bb_lower) / bb_range   # 0 = lower band, 1 = upper band
            if pos > 0.8:
                scores.append(-15)
                reasons.append(f"Price near BB upper ({pos:.0%}) — reversal likely")
            elif pos < 0.2:
                scores.append(+15)
                reasons.append(f"Price near BB lower ({pos:.0%}) — bounce likely")

    # ── 7. Short-term rate of change ──────────────────────────────────────────
    if len(df) >= 5:
        roc = ((df["close"].iloc[-1] - df["close"].iloc[-5]) / df["close"].iloc[-5]) * 100
        if roc > 1.5:
            scores.append(+10)
            reasons.append(f"Short-term momentum ↑ {roc:.1f}%")
        elif roc < -1.5:
            scores.append(-10)
            reasons.append(f"Short-term momentum ↓ {roc:.1f}%")

    # ── Aggregate ─────────────────────────────────────────────────────────────
    total        = sum(scores)
    max_possible = 90

    raw_confidence = min(abs(total) / max_possible * 100, 100)

    if total > 10:
        prediction = "UP"
        action     = "BUY"    # enter or hold — next candle expected bullish
    elif total < -10:
        prediction = "DOWN"
        action     = "SELL"   # exit before close — next candle expected bearish
    else:
        prediction = "NEUTRAL"
        action     = "HOLD"   # unclear — no forced action
        raw_confidence = max(0, raw_confidence)

    return {
        "prediction": prediction,
        "confidence": round(raw_confidence, 1),
        "score":      total,
        "action":     action,
        "reason":     " | ".join(reasons) if reasons else "No clear signals",
    }


# ─── Pre-Candle Watcher (legacy helper, kept for compatibility) ───────────────

class PreCandleWatcher:
    """
    Can be used standalone to check pre-close windows.
    The main AutoTrader uses predict_candle_direction() directly.
    """

    def __init__(self, interval: str = "1h"):
        self.interval = interval
        self._fired_for_close: Optional[int] = None

    def check(self,
              df: pd.DataFrame,
              indicators: dict,
              log_fn: Optional[Callable[[str], None]] = None) -> Optional[str]:
        """
        Returns "SELL" if in pre-close window and prediction is DOWN,
        "BUY" if UP, otherwise None.
        """
        def _log(msg):
            if log_fn:
                log_fn(msg)
            logger.info(msg)

        secs_left = seconds_until_candle_close(self.interval)
        close_ms  = get_candle_close_time_ms(self.interval)

        if self._fired_for_close == close_ms:
            return None

        if secs_left > PRE_CLOSE_WINDOW:
            return None

        self._fired_for_close = close_ms

        m = int(secs_left // 60)
        s = int(secs_left % 60)
        _log(f"⏳ {m}m {s}s before candle close — running prediction...")

        result = predict_candle_direction(df, indicators)
        arrow  = "📈" if result["prediction"] == "UP" else (
                 "📉" if result["prediction"] == "DOWN" else "➡️")

        _log(
            f"{arrow} Pre-close prediction: {result['prediction']} "
            f"({result['confidence']:.0f}% confidence) — {result['reason']}"
        )

        if result["action"] == "SELL":
            _log("⚠️ Bearish prediction — protective sell before close!")
            return "SELL"
        if result["action"] == "BUY":
            _log("✅ Bullish prediction — holding or entering position")
            return "BUY"

        _log("➡️ Neutral prediction — no forced action")
        return None
