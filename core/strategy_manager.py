"""
Strategy Manager — Fixed Logic + AI-Powered Discovery
Module-level enrich + check functions so booleans work correctly.
"""
import json
import re
import threading
import requests
from pathlib import Path
from typing import Dict, List, Optional, Callable
from config.settings import STRATEGIES_DIR, NVIDIA_API_KEY, NVIDIA_BASE_URL, DEEPSEEK_MODEL


# ══════════════════════════════════════════════════════════════════════════════
# ENRICHMENT — compute all boolean flags at module level
# ══════════════════════════════════════════════════════════════════════════════

def enrich_indicators(ind: dict) -> dict:
    """Compute boolean/derived flags from raw indicator values."""
    e       = dict(ind)
    price   = float(e.get("price") or 0)
    e20     = float(e.get("ema20") or 0)
    e50     = float(e.get("ema50") or 0)
    e200    = float(e.get("ema200") or 0)
    macd    = float(e.get("macd") or 0)
    sig     = float(e.get("macd_signal") or 0)
    macd_h  = float(e.get("macd_hist") or 0)
    atr     = float(e.get("atr") or 0)
    bb_up   = float(e.get("bb_upper") or 0)
    bb_lo   = float(e.get("bb_lower") or 0)
    bb_mid  = float(e.get("bb_mid") or 0)
    rsi     = float(e.get("rsi") or 50)
    stoch_k = float(e.get("stoch_k") or 50)
    stoch_d = float(e.get("stoch_d") or 50)
    change  = float(e.get("change_24h") or 0)
    vol     = float(e.get("volume_24h") or 0)

    # ── Trend ──
    e["trending_up"]        = e20 > e50 > e200 if (e20 and e50 and e200) else False
    e["trending_down"]      = e20 < e50 < e200 if (e20 and e50 and e200) else False
    e["ema20_above_ema50"]  = e20 > e50 if (e20 and e50) else False
    e["ema20_below_ema50"]  = e20 < e50 if (e20 and e50) else False
    e["ema50_above_ema200"] = e50 > e200 if (e50 and e200) else False
    e["ema50_below_ema200"] = e50 < e200 if (e50 and e200) else False
    e["price_above_ema200"] = price > e200 if (price and e200) else False
    e["price_below_ema200"] = price < e200 if (price and e200) else False
    e["price_above_ema50"]  = price > e50  if (price and e50)  else False
    e["price_below_ema50"]  = price < e50  if (price and e50)  else False
    e["price_above_ema20"]  = price > e20  if (price and e20)  else False

    # ── RSI ──
    e["rsi_oversold"]       = rsi < 30
    e["rsi_near_oversold"]  = rsi < 40
    e["rsi_overbought"]     = rsi > 70
    e["rsi_near_overbought"]= rsi > 60
    e["rsi_bullish"]        = rsi > 50
    e["rsi_bearish"]        = rsi < 50
    e["rsi_neutral"]        = 45 <= rsi <= 55
    e["rsi_extreme_oversold"]   = rsi < 20
    e["rsi_extreme_overbought"] = rsi > 80

    # ── MACD ──
    e["macd_bullish"]       = macd > sig
    e["macd_bearish"]       = macd < sig
    e["macd_above_zero"]    = macd > 0
    e["macd_below_zero"]    = macd < 0
    e["macd_hist_rising"]   = macd_h > 0
    e["macd_hist_falling"]  = macd_h < 0
    e["macd_strong_bull"]   = macd > sig and macd_h > 0 and macd > 0
    e["macd_strong_bear"]   = macd < sig and macd_h < 0 and macd < 0

    # ── Bollinger Bands ──
    e["near_bb_lower"]      = price <= bb_lo * 1.015 if (price and bb_lo) else False
    e["near_bb_upper"]      = price >= bb_up * 0.985 if (price and bb_up) else False
    e["below_bb_lower"]     = price < bb_lo if (price and bb_lo) else False
    e["above_bb_upper"]     = price > bb_up if (price and bb_up) else False
    e["near_bb_mid_bull"]   = price > bb_mid if (price and bb_mid) else False
    e["near_bb_mid_bear"]   = price < bb_mid if (price and bb_mid) else False
    bb_width = (bb_up - bb_lo) / bb_mid if bb_mid else 0
    e["bb_squeeze"]         = bb_width < 0.03  # tight bands = breakout coming

    # ── Stochastic ──
    e["stoch_oversold"]     = stoch_k < 20
    e["stoch_overbought"]   = stoch_k > 80
    e["stoch_bullish_cross"]= stoch_k > stoch_d and stoch_k < 50
    e["stoch_bearish_cross"]= stoch_k < stoch_d and stoch_k > 50

    # ── Momentum ──
    e["strong_momentum_up"] = change > 3
    e["momentum_up"]        = change > 1
    e["momentum_down"]      = change < -1
    e["strong_momentum_down"]= change < -3

    # ── Combined ──
    e["strong_bull_signal"] = (
        e["rsi_bullish"] and e["macd_bullish"] and e["ema20_above_ema50"]
    )
    e["strong_bear_signal"] = (
        e["rsi_bearish"] and e["macd_bearish"] and e["ema20_below_ema50"]
    )
    e["dip_buy_signal"] = (
        e["near_bb_lower"] and e["rsi_near_oversold"] and e["macd_hist_rising"]
    )
    e["peak_sell_signal"] = (
        e["near_bb_upper"] and e["rsi_near_overbought"] and e["macd_hist_falling"]
    )
    e["golden_cross"] = e["ema50_above_ema200"] and e["price_above_ema200"]
    e["death_cross"]  = e["ema50_below_ema200"] and e["price_below_ema200"]

    return e


def check_rule(rule: dict, enriched: dict) -> bool:
    """Return True if ALL conditions in rule are satisfied by enriched indicators."""
    if not rule:
        return False
    for key, condition in rule.items():
        val = enriched.get(key)
        if isinstance(condition, bool):
            # boolean flag check
            if val is None:
                val = False
            if condition and not bool(val):
                return False
            if not condition and bool(val):
                return False
        elif isinstance(condition, dict):
            if val is None:
                return False
            if "lt" in condition  and not (val < condition["lt"]):  return False
            if "gt" in condition  and not (val > condition["gt"]):  return False
            if "lte" in condition and not (val <= condition["lte"]): return False
            if "gte" in condition and not (val >= condition["gte"]): return False
        elif isinstance(condition, str):
            # Legacy string shortcuts
            m = {"above_signal": "macd_bullish", "below_signal": "macd_bearish",
                 "lower_band":   "near_bb_lower",  "upper_band": "near_bb_upper",
                 "20_above_50":  "ema20_above_ema50","20_below_50":"ema20_below_ema50",
                 "50_above_200": "ema50_above_ema200","50_below_200":"ema50_below_ema200"}
            flag = m.get(condition)
            if flag and not enriched.get(flag, False):
                return False
    return True


# ══════════════════════════════════════════════════════════════════════════════
# BUILT-IN STRATEGIES — 20 strategies using boolean flags
# ══════════════════════════════════════════════════════════════════════════════

BUILTIN_STRATEGIES: Dict[str, dict] = {

    # ─── Oversold / Overbought ────────────────────────────────────────────────
    "RSI_Extreme": {
        "name": "RSI Extreme Reversal",
        "description": "Buy extreme oversold, sell extreme overbought",
        "category": "Reversal", "weight": 1.5, "win_rate": 64,
        "rules": {"buy":  {"rsi_extreme_oversold": True},
                  "sell": {"rsi_extreme_overbought": True}},
    },
    "RSI_Standard": {
        "name": "RSI Standard",
        "description": "Classic RSI < 30 buy, > 70 sell",
        "category": "Reversal", "weight": 1.2, "win_rate": 61,
        "rules": {"buy":  {"rsi_oversold": True},
                  "sell": {"rsi_overbought": True}},
    },
    "RSI_Momentum": {
        "name": "RSI Momentum",
        "description": "Trade RSI momentum cross above/below 50",
        "category": "Momentum", "weight": 1.0, "win_rate": 57,
        "rules": {"buy":  {"rsi_bullish": True, "macd_bullish": True},
                  "sell": {"rsi_bearish": True, "macd_bearish": True}},
    },

    # ─── MACD ────────────────────────────────────────────────────────────────
    "MACD_Cross": {
        "name": "MACD Line Crossover",
        "description": "MACD crosses signal line",
        "category": "Momentum", "weight": 1.3, "win_rate": 58,
        "rules": {"buy":  {"macd_bullish": True},
                  "sell": {"macd_bearish": True}},
    },
    "MACD_Strong": {
        "name": "MACD Strong Signal",
        "description": "MACD bullish/bearish AND above/below zero",
        "category": "Momentum", "weight": 1.6, "win_rate": 63,
        "rules": {"buy":  {"macd_strong_bull": True},
                  "sell": {"macd_strong_bear": True}},
    },
    "MACD_Zero_Cross": {
        "name": "MACD Zero Line Cross",
        "description": "MACD crosses zero line with histogram confirmation",
        "category": "Trend", "weight": 1.4, "win_rate": 61,
        "rules": {"buy":  {"macd_above_zero": True, "macd_hist_rising": True},
                  "sell": {"macd_below_zero": True, "macd_hist_falling": True}},
    },

    # ─── Bollinger Bands ─────────────────────────────────────────────────────
    "BB_Bounce": {
        "name": "Bollinger Band Bounce",
        "description": "Price near lower/upper band",
        "category": "Mean Reversion", "weight": 1.3, "win_rate": 62,
        "rules": {"buy":  {"near_bb_lower": True},
                  "sell": {"near_bb_upper": True}},
    },
    "BB_Breakout": {
        "name": "Bollinger Breakout",
        "description": "Price breaks outside bands",
        "category": "Breakout", "weight": 1.1, "win_rate": 54,
        "rules": {"buy":  {"above_bb_upper": True, "macd_bullish": True},
                  "sell": {"below_bb_lower": True, "macd_bearish": True}},
    },
    "BB_Squeeze_Break": {
        "name": "BB Squeeze Breakout",
        "description": "Tight bands indicate breakout coming",
        "category": "Volatility", "weight": 1.5, "win_rate": 60,
        "rules": {"buy":  {"bb_squeeze": True, "macd_bullish": True, "rsi_bullish": True},
                  "sell": {"bb_squeeze": True, "macd_bearish": True, "rsi_bearish": True}},
    },

    # ─── EMA Trend ────────────────────────────────────────────────────────────
    "EMA_20_50": {
        "name": "EMA 20/50 Cross",
        "description": "Fast EMA crosses slow EMA",
        "category": "Trend", "weight": 1.3, "win_rate": 58,
        "rules": {"buy":  {"ema20_above_ema50": True},
                  "sell": {"ema20_below_ema50": True}},
    },
    "Golden_Death_Cross": {
        "name": "Golden/Death Cross",
        "description": "EMA50 vs EMA200 — major trend signal",
        "category": "Trend", "weight": 2.0, "win_rate": 66,
        "rules": {"buy":  {"golden_cross": True},
                  "sell": {"death_cross": True}},
    },
    "Trend_Following": {
        "name": "Full Trend Following",
        "description": "Price above all EMAs = bullish trend",
        "category": "Trend", "weight": 1.8, "win_rate": 64,
        "rules": {"buy":  {"trending_up": True, "price_above_ema200": True},
                  "sell": {"trending_down": True, "price_below_ema200": True}},
    },

    # ─── Stochastic ──────────────────────────────────────────────────────────
    "Stochastic_Extreme": {
        "name": "Stochastic Extreme",
        "description": "Stoch K below 20 or above 80",
        "category": "Reversal", "weight": 1.1, "win_rate": 59,
        "rules": {"buy":  {"stoch_oversold": True},
                  "sell": {"stoch_overbought": True}},
    },
    "Stochastic_Cross": {
        "name": "Stochastic Bullish/Bearish Cross",
        "description": "K crosses D in oversold/overbought zone",
        "category": "Reversal", "weight": 1.3, "win_rate": 61,
        "rules": {"buy":  {"stoch_bullish_cross": True},
                  "sell": {"stoch_bearish_cross": True}},
    },

    # ─── Combined / Multi-indicator ───────────────────────────────────────────
    "Dip_Buy": {
        "name": "Dip Buy Signal",
        "description": "BB lower + oversold RSI + rising MACD histogram",
        "category": "Combined", "weight": 2.0, "win_rate": 69,
        "rules": {"buy":  {"dip_buy_signal": True},
                  "sell": {"peak_sell_signal": True}},
    },
    "Triple_Confirmation": {
        "name": "Triple Confirmation",
        "description": "RSI + MACD + EMA all agree",
        "category": "Combined", "weight": 2.2, "win_rate": 72,
        "rules": {"buy":  {"strong_bull_signal": True},
                  "sell": {"strong_bear_signal": True}},
    },
    "RSI_MACD_Combo": {
        "name": "RSI + MACD Combo",
        "description": "Both RSI near oversold AND MACD bullish",
        "category": "Combined", "weight": 1.7, "win_rate": 66,
        "rules": {"buy":  {"rsi_near_oversold": True, "macd_bullish": True},
                  "sell": {"rsi_near_overbought": True, "macd_bearish": True}},
    },
    "Momentum_Surge": {
        "name": "Momentum Surge",
        "description": "Price momentum + trend alignment",
        "category": "Momentum", "weight": 1.4, "win_rate": 62,
        "rules": {"buy":  {"momentum_up": True, "macd_bullish": True, "price_above_ema50": True},
                  "sell": {"momentum_down": True, "macd_bearish": True, "price_below_ema50": True}},
    },
    "BB_RSI_Combo": {
        "name": "BB + RSI Mean Reversion",
        "description": "BB bounce confirmed by RSI reversal zone",
        "category": "Combined", "weight": 1.8, "win_rate": 67,
        "rules": {"buy":  {"near_bb_lower": True, "rsi_near_oversold": True},
                  "sell": {"near_bb_upper": True, "rsi_near_overbought": True}},
    },
    "Smart_Trend": {
        "name": "Smart Trend Entry",
        "description": "Wait for pullback in trend using all indicators",
        "category": "Trend", "weight": 1.9, "win_rate": 68,
        "rules": {
            "buy":  {"ema20_above_ema50": True, "price_above_ema200": True,
                     "rsi": {"lte": 55}, "macd_bullish": True},
            "sell": {"ema20_below_ema50": True, "price_below_ema200": True,
                     "rsi": {"gte": 45}, "macd_bearish": True},
        },
    },
}


# ══════════════════════════════════════════════════════════════════════════════
# ONLINE STRATEGY DISCOVERY — fetch + AI generate
# ══════════════════════════════════════════════════════════════════════════════

# Known public strategy resources (raw JSON parseable or text)
STRATEGY_REPOS = [
    "https://raw.githubusercontent.com/freqtrade/freqtrade-strategies/main/user_data/strategies/berlinguyinca/GodStraNew.py",
    "https://raw.githubusercontent.com/freqtrade/freqtrade-strategies/main/README.md",
]


def fetch_strategy_descriptions() -> str:
    """Fetch strategy descriptions from public resources."""
    texts = []
    for url in STRATEGY_REPOS:
        try:
            r = requests.get(url, timeout=10)
            if r.ok:
                texts.append(r.text[:2000])
        except Exception:
            pass
    return "\n\n".join(texts) if texts else ""


def ai_generate_strategies(symbol: str, indicators: dict,
                            on_progress: Optional[Callable] = None) -> List[dict]:
    """
    Ask DeepSeek to generate 5 optimal custom strategies
    for the specific coin + current market conditions.
    Returns list of strategy dicts.
    """
    from openai import OpenAI
    client = OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_API_KEY)

    rsi    = indicators.get("rsi", 50)
    macd   = indicators.get("macd", 0)
    sig    = indicators.get("macd_signal", 0)
    price  = indicators.get("price", 0)
    e20    = indicators.get("ema20", 0)
    e50    = indicators.get("ema50", 0)
    change = indicators.get("change_24h", 0)
    bb_up  = indicators.get("bb_upper", 0)
    bb_lo  = indicators.get("bb_lower", 0)

    prompt = f"""You are a professional algorithmic trading strategy designer.

Generate 5 optimal trading strategies specifically for {symbol} based on current market:
- RSI: {rsi} | MACD: {macd:.4f} vs Signal: {sig:.4f}
- Price: {price} | EMA20: {e20} | EMA50: {e50}
- 24h Change: {change}% | BB: {bb_lo:.2f}–{bb_up:.2f}

Each strategy must use ONLY these available indicator conditions:
NUMERIC: rsi (0-100), stoch_k (0-100), macd, macd_signal, macd_hist, atr
BOOLEAN: rsi_oversold, rsi_overbought, rsi_bullish, rsi_bearish,
         macd_bullish, macd_bearish, macd_strong_bull, macd_strong_bear,
         near_bb_lower, near_bb_upper, ema20_above_ema50, ema20_below_ema50,
         trending_up, trending_down, dip_buy_signal, peak_sell_signal,
         strong_bull_signal, strong_bear_signal, golden_cross, death_cross

Return ONLY valid JSON array, no other text:
[
  {{
    "name": "Strategy Name",
    "description": "Brief description",
    "category": "Trend|Reversal|Momentum|Breakout",
    "weight": 1.5,
    "win_rate": 65,
    "rules": {{
      "buy":  {{"indicator_name": true_or_numeric_condition}},
      "sell": {{"indicator_name": true_or_numeric_condition}}
    }}
  }},
  ... (5 total)
]

Focus on strategies that work well for current market conditions ({symbol} {'is bearish' if change < 0 else 'is bullish'}, RSI={'oversold' if rsi < 40 else 'overbought' if rsi > 60 else 'neutral'}).
"""
    if on_progress:
        on_progress("Asking AI to generate optimal strategies...")
    result_text = []
    try:
        completion = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.5,
            max_tokens=3000,
            stream=True,
        )
        for chunk in completion:
            if not getattr(chunk, "choices", None):
                continue
            c = chunk.choices[0].delta.content
            if c:
                result_text.append(c)
    except Exception as e:
        if on_progress:
            on_progress(f"AI strategy generation error: {e}")
        return []

    raw = "".join(result_text)
    try:
        match = re.search(r"\[[\s\S]*\]", raw)
        if match:
            strategies = json.loads(match.group())
            return strategies if isinstance(strategies, list) else []
    except Exception as e:
        if on_progress:
            on_progress(f"Strategy parse error: {e}")
    return []


# ══════════════════════════════════════════════════════════════════════════════
# STRATEGY MANAGER CLASS
# ══════════════════════════════════════════════════════════════════════════════

class StrategyManager:
    def __init__(self):
        STRATEGIES_DIR.mkdir(parents=True, exist_ok=True)
        self.strategies: Dict[str, dict] = {}
        self._ai_generated: Dict[str, dict] = {}
        self._load_all()

    def _load_all(self):
        self.strategies.update(BUILTIN_STRATEGIES)
        self._load_from_files()

    def _load_from_files(self):
        for f in STRATEGIES_DIR.glob("*.json"):
            try:
                with open(f, "r", encoding="utf-8") as fp:
                    data = json.load(fp)
                    self.strategies[f.stem] = data
            except Exception as e:
                print(f"[Strategy] Load error {f}: {e}")

    def save_strategy(self, name: str, data: dict):
        path = STRATEGIES_DIR / f"{name}.json"
        with open(path, "w", encoding="utf-8") as fp:
            json.dump(data, fp, ensure_ascii=False, indent=2)
        self.strategies[name] = data

    def get_strategy(self, name: str) -> Optional[dict]:
        return self.strategies.get(name)

    def list_strategies(self) -> List[str]:
        return list(self.strategies.keys())

    def get_all(self) -> Dict[str, dict]:
        return self.strategies

    def apply_strategy(self, strategy_name: str, indicators: dict) -> str:
        """Apply one strategy. Returns BUY / SELL / HOLD."""
        strategy = self.strategies.get(strategy_name)
        if not strategy:
            return "HOLD"
        rules    = strategy.get("rules", {})
        enriched = enrich_indicators(indicators)   # ← KEY FIX

        if check_rule(rules.get("buy", {}), enriched):
            return "BUY"
        if check_rule(rules.get("sell", {}), enriched):
            return "SELL"
        return "HOLD"

    def run_all_strategies(self, indicators: dict) -> Dict[str, str]:
        """Run all strategies once against the same enriched indicators."""
        enriched = enrich_indicators(indicators)
        results  = {}
        for name, strategy in self.strategies.items():
            rules = strategy.get("rules", {})
            if check_rule(rules.get("buy", {}), enriched):
                results[name] = "BUY"
            elif check_rule(rules.get("sell", {}), enriched):
                results[name] = "SELL"
            else:
                results[name] = "HOLD"
        return results

    def get_weighted_consensus(self, strategy_results: Dict[str, str]) -> dict:
        """Weighted vote — heavier strategies count more."""
        weights = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}
        counts  = {"BUY": 0,   "SELL": 0,   "HOLD": 0}

        for name, decision in strategy_results.items():
            w = self.strategies.get(name, {}).get("weight", 1.0)
            weights[decision] = weights.get(decision, 0) + w
            counts[decision]  = counts.get(decision, 0) + 1

        total_w = sum(weights.values()) or 1
        winner  = max(weights, key=weights.get)
        confidence = round((weights[winner] / total_w) * 100)

        return {
            "decision":     winner,
            "confidence":   confidence,
            "weights":      {k: round(v, 2) for k, v in weights.items()},
            "counts":       counts,
            "total_strats": len(strategy_results),
            "buy_strats":   counts["BUY"],
            "sell_strats":  counts["SELL"],
            "hold_strats":  counts["HOLD"],
        }

    # alias
    def get_consensus(self, results):
        return self.get_weighted_consensus(results)

    def discover_and_add_strategies_async(self,
                                          symbol: str,
                                          indicators: dict,
                                          on_progress: Callable[[str], None],
                                          on_done: Callable[[int], None]):
        """
        Background task:
        1. Fetch strategy texts from public repos
        2. Ask AI to generate 5 custom strategies for symbol
        3. Add them to self.strategies
        """
        def _worker():
            on_progress("🌐 Fetching strategy resources from GitHub...")
            web_text = fetch_strategy_descriptions()
            if web_text:
                on_progress(f"✅ Fetched {len(web_text)} chars of strategy data")

            on_progress("🤖 Asking AI to generate optimal strategies for this coin...")
            new_strats = ai_generate_strategies(symbol, indicators, on_progress)

            added = 0
            for s in new_strats:
                name = "AI_" + s.get("name", "Unknown").replace(" ", "_")
                self.strategies[name] = s
                added += 1
                on_progress(f"  ✅ Added: {s.get('name','?')} (weight={s.get('weight','?')})")

            on_progress(f"🎯 Discovery complete — {added} AI strategies added (total: {len(self.strategies)})")
            on_done(added)

        threading.Thread(target=_worker, daemon=True).start()
