"""
AI Engine — 6-Stage Verification
DeepSeek V3.2 + Llama 3.3 Nemotron with comprehensive data prompts
"""
import json
import re
import threading
from typing import Callable, Optional, Dict, Any
from openai import OpenAI
from config.settings import (
    NVIDIA_API_KEY, NVIDIA_BASE_URL,
    DEEPSEEK_MODEL, LLAMA_MODEL
)


def _get_client() -> OpenAI:
    return OpenAI(base_url=NVIDIA_BASE_URL, api_key=NVIDIA_API_KEY)


# ── DeepSeek V3.2 ─────────────────────────────────────────────────────────────

def analyze_with_deepseek(prompt: str,
                           on_chunk: Optional[Callable[[str], None]] = None,
                           on_done:  Optional[Callable[[str], None]] = None) -> str:
    client = _get_client()
    full_response = []
    try:
        completion = client.chat.completions.create(
            model=DEEPSEEK_MODEL,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
            top_p=0.95,
            max_tokens=8192,
            extra_body={"chat_template_kwargs": {"thinking": True}},
            stream=True,
        )
        for chunk in completion:
            if not getattr(chunk, "choices", None):
                continue
            delta = chunk.choices[0].delta
            reasoning = getattr(delta, "reasoning_content", None)
            if reasoning and on_chunk:
                on_chunk(f"💭 {reasoning}")
            content = delta.content
            if content:
                full_response.append(content)
                if on_chunk:
                    on_chunk(content)
    except Exception as e:
        err = f"❌ DeepSeek Error: {str(e)}"
        if on_chunk: on_chunk(err)
        if on_done:  on_done(err)
        return err
    result = "".join(full_response)
    if on_done: on_done(result)
    return result


# ── Llama 3.3 Nemotron ────────────────────────────────────────────────────────

def analyze_with_llama(prompt: str,
                        on_chunk: Optional[Callable[[str], None]] = None,
                        on_done:  Optional[Callable[[str], None]] = None) -> str:
    client = _get_client()
    full_response = []
    try:
        completion = client.chat.completions.create(
            model=LLAMA_MODEL,
            messages=[
                {"role": "system", "content": "/think\nYou are an expert financial and market sentiment analyst."},
                {"role": "user",   "content": prompt},
            ],
            temperature=0.6,
            top_p=0.95,
            max_tokens=65536,
            frequency_penalty=0,
            presence_penalty=0,
            stream=True,
        )
        for chunk in completion:
            if not getattr(chunk, "choices", None):
                continue
            content = chunk.choices[0].delta.content
            if content:
                full_response.append(content)
                if on_chunk: on_chunk(content)
    except Exception as e:
        err = f"❌ Llama Error: {str(e)}"
        if on_chunk: on_chunk(err)
        if on_done:  on_done(err)
        return err
    result = "".join(full_response)
    if on_done: on_done(result)
    return result


def _parse_json(text: str) -> dict:
    """Extract first valid JSON object from text."""
    try:
        match = re.search(r"\{[\s\S]*\}", text)
        if match:
            return json.loads(match.group())
    except Exception:
        pass
    # try full text
    try:
        return json.loads(text)
    except Exception:
        pass
    return {}


# ══════════════════════════════════════════════════════════════════════════════
# MultiStageAnalyzer — 6 مراحل تحقق
# ══════════════════════════════════════════════════════════════════════════════

class MultiStageAnalyzer:
    """
    Stage 1: Technical Indicators (1h)
    Stage 2: Multi-Timeframe Analysis (4h + 1d)
    Stage 3: DeepSeek V3.2 — Deep Technical Analysis
    Stage 4: Llama 3.3 — News & Sentiment Analysis
    Stage 5: Fear & Greed + OrderBook + Global Market
    Stage 6: Weighted Voting System + Final Decision
    """

    def __init__(self, symbol: str, full_data: Dict[str, Any]):
        self.symbol    = symbol
        self.full_data = full_data  # contains all collected data
        self.results   = {}

    # ─── Stage 1: Technical Analysis (1h) ────────────────────────────────────

    def run_stage1(self) -> dict:
        ind   = self.full_data.get("indicators_1h", {})
        score = 50
        votes = []

        rsi     = ind.get("rsi") or 50
        macd    = ind.get("macd") or 0
        sig     = ind.get("macd_signal") or 0
        e20     = ind.get("ema20") or 0
        e50     = ind.get("ema50") or 0
        e200    = ind.get("ema200") or 0
        price   = ind.get("price") or 0
        bb_up   = ind.get("bb_upper") or float("inf")
        bb_lo   = ind.get("bb_lower") or 0
        stoch_k = ind.get("stoch_k") or 50
        atr     = ind.get("atr") or 0

        # RSI
        if rsi < 25:    score += 20; votes.append("RSI Extreme Oversold 🟢")
        elif rsi < 35:  score += 12; votes.append("RSI Oversold 🟢")
        elif rsi > 75:  score -= 20; votes.append("RSI Extreme Overbought 🔴")
        elif rsi > 65:  score -= 12; votes.append("RSI Overbought 🔴")
        elif 45 < rsi < 55: votes.append("RSI Neutral ⚖️")

        # MACD
        if macd > sig:  score += 10; votes.append("MACD Bullish Cross 🟢")
        else:           score -= 10; votes.append("MACD Bearish Cross 🔴")

        # EMA
        if e20 and e50:
            if e20 > e50:  score += 8;  votes.append("EMA20 > EMA50 (Bullish) 🟢")
            else:          score -= 8;  votes.append("EMA20 < EMA50 (Bearish) 🔴")
        if e50 and e200:
            if e50 > e200: score += 10; votes.append("Golden Cross 🟢")
            else:          score -= 10; votes.append("Death Cross 🔴")
        if price and e200:
            if price > e200: score += 6; votes.append("Price above EMA200 🟢")
            else:            score -= 6; votes.append("Price below EMA200 🔴")

        # Bollinger
        if price and bb_lo and price <= bb_lo * 1.005:
            score += 8; votes.append("Price at BB Lower Band 🟢")
        elif price and bb_up != float("inf") and price >= bb_up * 0.995:
            score -= 8; votes.append("Price at BB Upper Band 🔴")

        # Stochastic
        if stoch_k < 20:  score += 6; votes.append("Stoch Oversold 🟢")
        elif stoch_k > 80: score -= 6; votes.append("Stoch Overbought 🔴")

        score = max(0, min(100, score))
        decision = "BUY" if score > 60 else ("SELL" if score < 40 else "HOLD")

        return {
            "score": score,
            "decision": decision,
            "signals": votes,
            "confidence": abs(score - 50) * 2,
        }

    # ─── Stage 2: Multi-Timeframe Analysis ───────────────────────────────────

    def run_stage2(self) -> dict:
        """Analyze 4h and 1d to confirm the major trend."""
        signals = {"BUY": 0, "SELL": 0, "HOLD": 0}
        details = []

        for tf, weight in [("4h", 1.5), ("1d", 2.0)]:
            ind = self.full_data.get(f"indicators_{tf}", {})
            if not ind:
                continue
            rsi   = ind.get("rsi") or 50
            macd  = ind.get("macd") or 0
            sig   = ind.get("macd_signal") or 0
            e20   = ind.get("ema20") or 0
            e50   = ind.get("ema50") or 0
            price = ind.get("price") or 0
            e200  = ind.get("ema200") or 0

            tf_score = 50
            if rsi < 40:            tf_score += 15
            elif rsi > 60:          tf_score -= 15
            if macd > sig:          tf_score += 10
            else:                   tf_score -= 10
            if e20 and e50:
                if e20 > e50:       tf_score += 8
                else:               tf_score -= 8
            if price and e200:
                if price > e200:    tf_score += 10
                else:               tf_score -= 10

            tf_score = max(0, min(100, tf_score))
            tf_dec   = "BUY" if tf_score > 58 else ("SELL" if tf_score < 42 else "HOLD")
            signals[tf_dec] += weight
            details.append(f"{tf}: {tf_dec} ({tf_score}/100)")

        winner = max(signals, key=signals.get)
        total  = sum(signals.values())
        conf   = round((signals[winner] / total) * 100) if total > 0 else 50
        return {
            "decision": winner,
            "confidence": conf,
            "details": details,
            "signals": signals,
        }

    # ─── Stage 3: DeepSeek Deep Technical Analysis ────────────────────────────

    def _build_deepseek_prompt(self) -> str:
        ind_1h = self.full_data.get("indicators_1h", {})
        ind_4h = self.full_data.get("indicators_4h", {})
        ind_1d = self.full_data.get("indicators_1d", {})
        ob     = self.full_data.get("order_book", {})
        trades = self.full_data.get("recent_trades", {})
        gecko  = self.full_data.get("coingecko", {})
        global_mkt = self.full_data.get("global_market", {})
        fg     = self.full_data.get("fear_greed", {})
        strat  = self.full_data.get("strategy_consensus", {})

        return f"""You are a professional cryptocurrency trading expert with 15 years of experience.
Perform a comprehensive deep analysis of {self.symbol} and make a well-reasoned trading decision.

═══ TECHNICAL DATA — 1 Hour Timeframe ═══
• Price: {ind_1h.get('price', 'N/A')} USDT
• 24h Change: {ind_1h.get('change_24h', 'N/A')}%
• 24h Volume: {ind_1h.get('volume_24h', 'N/A'):,.0f} USDT
• RSI(14): {ind_1h.get('rsi', 'N/A')}
• MACD: {ind_1h.get('macd', 'N/A')} | Signal: {ind_1h.get('macd_signal', 'N/A')} | Hist: {ind_1h.get('macd_hist', 'N/A')}
• Bollinger: ↑{ind_1h.get('bb_upper', 'N/A')} | Mid: {ind_1h.get('bb_mid', 'N/A')} | ↓{ind_1h.get('bb_lower', 'N/A')}
• EMA20: {ind_1h.get('ema20', 'N/A')} | EMA50: {ind_1h.get('ema50', 'N/A')} | EMA200: {ind_1h.get('ema200', 'N/A')}
• Stoch K: {ind_1h.get('stoch_k', 'N/A')} | D: {ind_1h.get('stoch_d', 'N/A')}
• ATR: {ind_1h.get('atr', 'N/A')}
• Candle Pattern: {ind_1h.get('candle_pattern', 'N/A')}

═══ 4 HOUR TIMEFRAME ═══
• Price: {ind_4h.get('price', 'N/A')} | RSI: {ind_4h.get('rsi', 'N/A')}
• MACD: {ind_4h.get('macd', 'N/A')} | EMA20: {ind_4h.get('ema20', 'N/A')} | EMA50: {ind_4h.get('ema50', 'N/A')}
• Bollinger: ↑{ind_4h.get('bb_upper', 'N/A')} | ↓{ind_4h.get('bb_lower', 'N/A')}

═══ DAILY TIMEFRAME ═══
• Price: {ind_1d.get('price', 'N/A')} | RSI: {ind_1d.get('rsi', 'N/A')}
• EMA50: {ind_1d.get('ema50', 'N/A')} | EMA200: {ind_1d.get('ema200', 'N/A')}
• 7d Change: {gecko.get('price_change_7d', 'N/A')}% | 30d Change: {gecko.get('price_change_30d', 'N/A')}%

═══ ORDER BOOK (Buy/Sell Pressure) ═══
• Bid Volume: {ob.get('bid_volume', 'N/A')} | Ask Volume: {ob.get('ask_volume', 'N/A')}
• Buy Pressure: {ob.get('buy_pressure', 'N/A')}% | Sell Pressure: {ob.get('sell_pressure', 'N/A')}%

═══ RECENT TRADES (50 trades) ═══
• Buy Ratio: {trades.get('buy_ratio', 'N/A')}%
• Buy Volume: {trades.get('buy_volume', 'N/A')} | Sell Volume: {trades.get('sell_volume', 'N/A')}

═══ FEAR & GREED INDEX ═══
• Value: {fg.get('value', 'N/A')}/100 — {fg.get('classification', 'N/A')}
• Trend: {fg.get('trend', 'N/A')} (Previous: {fg.get('prev_value', 'N/A')})

═══ GLOBAL MARKET ═══
• BTC Dominance: {global_mkt.get('btc_dominance', 'N/A')}%
• Market Cap 24h Change: {global_mkt.get('market_cap_change_24h', 'N/A')}%

═══ COINGECKO DEEP DATA ═══
• Market Rank: #{gecko.get('market_cap_rank', 'N/A')}
• ATH Price: {gecko.get('ath', 'N/A')} | Distance from ATH: {gecko.get('ath_change_pct', 'N/A')}%

═══ STRATEGY CONSENSUS ({strat.get('total_strats', 0)} strategies) ═══
• Decision: {strat.get('decision', 'N/A')} ({strat.get('confidence', 'N/A')}% confidence)
• BUY: {strat.get('buy_strats', 0)} | SELL: {strat.get('sell_strats', 0)} | HOLD: {strat.get('hold_strats', 0)}

═══ YOUR TASK ═══
Analyze ALL data above thoroughly. Look for:
1. Cross-timeframe confirmations and divergences
2. Indicator confluence and conflicts
3. Key support/resistance levels
4. Trend strength and momentum

Respond with STRICT JSON only (no text outside JSON):
{{
  "decision": "BUY" or "SELL" or "HOLD",
  "confidence": number 0-100,
  "entry_price": suggested entry price,
  "stop_loss": stop loss price,
  "take_profit_1": first target,
  "take_profit_2": second target,
  "risk_reward_ratio": "e.g. 2.5:1",
  "timeframe": "recommended trade timeframe",
  "trend_strength": "Strong/Moderate/Weak",
  "key_levels": {{"support": X, "resistance": Y}},
  "reasoning": "Detailed English analysis (100-200 words)",
  "key_signals": ["signal1", "signal2", "signal3", "signal4"],
  "risks": ["risk1", "risk2"],
  "warning": "Important warning if any or null"
}}"""

    # ─── Stage 4: Llama Sentiment Analysis ────────────────────────────────────

    def _build_llama_prompt(self) -> str:
        news    = self.full_data.get("news", {})
        fg      = self.full_data.get("fear_greed", {})
        gecko   = self.full_data.get("coingecko", {})
        articles = news.get("articles", [])

        news_text = ""
        for i, a in enumerate(articles[:25], 1):
            title = a.get("title", "")
            src   = a.get("source", "")
            pv    = a.get("votes_positive", 0)
            nv    = a.get("votes_negative", 0)
            news_text += f"{i}. [{src}] {title} (👍{pv} 👎{nv})\n"

        gecko_desc = gecko.get("description", "")[:300]

        return f"""You are a sentiment analyst specializing in cryptocurrency markets.

Analyze the following data for {self.symbol} and evaluate market sentiment:

═══ LATEST NEWS ({len(articles)} articles) ═══
{news_text if news_text else 'No news available'}

═══ CURRENT SENTIMENT ═══
• Fear & Greed Index: {fg.get('value', 50)}/100 — {fg.get('classification', 'Neutral')}
• Index Trend: {fg.get('trend', 'Stable')}
• CryptoPanic Community Score: {news.get('sentiment_score', 0):+.1f}

═══ COIN DESCRIPTION ═══
{gecko_desc}

═══ YOUR TASK ═══
1. Analyze news headlines — look for: major events, partnerships, hacks, regulation
2. Evaluate trader/community sentiment
3. Identify positive and negative news and their potential impact
4. Compare current sentiment with Fear & Greed Index
5. Look for sentiment divergence from price action

Respond with STRICT JSON only:
{{
  "overall_sentiment": "BULLISH" or "BEARISH" or "NEUTRAL",
  "sentiment_score": number -100 to 100,
  "decision": "BUY" or "SELL" or "HOLD",
  "confidence": number 0-100,
  "positive_news": ["positive headline 1", "positive headline 2"],
  "negative_news": ["negative headline 1", "negative headline 2"],
  "key_events": ["event1", "event2", "event3"],
  "community_mood": "brief description of community mood",
  "fear_greed_interpretation": "interpretation of F&G index",
  "summary": "Detailed English summary (80-150 words)",
  "warning": "Warning about dangerous news if any or null"
}}"""

    # ─── Stage 5: Fear & Greed + OrderBook Analysis ───────────────────────────

    def run_stage5(self) -> dict:
        """Analyze extra market signals: Fear & Greed, Order Book, Global Market."""
        fg     = self.full_data.get("fear_greed", {})
        ob     = self.full_data.get("order_book", {})
        trades = self.full_data.get("recent_trades", {})
        global_mkt = self.full_data.get("global_market", {})

        score  = 50
        signals = []

        # Fear & Greed
        fg_val = fg.get("value", 50)
        if fg_val < 20:   score += 15; signals.append(f"Extreme Fear ({fg_val}) — Historic buy opportunity 🟢")
        elif fg_val < 35: score += 8;  signals.append(f"Fear ({fg_val}) — Buy zone 🟢")
        elif fg_val > 80: score -= 15; signals.append(f"Extreme Greed ({fg_val}) — Consider selling 🔴")
        elif fg_val > 65: score -= 8;  signals.append(f"Greed ({fg_val}) — Be cautious 🔴")
        else:             signals.append(f"Neutral F&G ({fg_val}) ⚖️")

        # Order Book Pressure
        buy_pressure = ob.get("buy_pressure", 50)
        if buy_pressure > 65:   score += 8;  signals.append(f"Strong buy pressure: {buy_pressure}% 🟢")
        elif buy_pressure < 35: score -= 8;  signals.append(f"Strong sell pressure: {100-buy_pressure}% 🔴")

        # Recent Trades
        buy_ratio = trades.get("buy_ratio", 50)
        if buy_ratio > 60:   score += 5; signals.append(f"Recent buy ratio: {buy_ratio}% 🟢")
        elif buy_ratio < 40: score -= 5; signals.append(f"Recent sell ratio: {100-buy_ratio}% 🔴")

        # Global Market
        mkt_change = global_mkt.get("market_cap_change_24h", 0)
        if mkt_change > 3:    score += 6;  signals.append(f"Global market rising {mkt_change}% 🟢")
        elif mkt_change < -3: score -= 6;  signals.append(f"Global market falling {mkt_change}% 🔴")

        score   = max(0, min(100, score))
        decision = "BUY" if score > 58 else ("SELL" if score < 42 else "HOLD")
        return {
            "score":    score,
            "decision": decision,
            "signals":  signals,
            "confidence": abs(score - 50) * 2,
            "fear_greed_value": fg_val,
            "buy_pressure": buy_pressure,
        }

    # ─── Stage 6: Weighted Final Decision ─────────────────────────────────────

    def make_final_decision(self,
                             s1: dict, s2: dict,
                             s3_raw: dict, s4_raw: dict,
                             s5: dict, strategy_consensus: dict) -> dict:
        """
        Advanced weighted voting system:
        - S1 Technical (1h):       weight 1.0
        - S2 Multi-TF:             weight 1.8  (major trend confirmation)
        - S3 DeepSeek:             weight 2.5  (AI technical analysis)
        - S4 Llama:                weight 1.5  (AI sentiment)
        - S5 Market Extras:        weight 1.2
        - Strategy Consensus:      weight 1.5  (20+ strategies)
        """
        votes = {"BUY": 0.0, "SELL": 0.0, "HOLD": 0.0}

        def _add(decision: str, confidence: float, weight: float):
            conf_norm = min(confidence / 100, 1.0)
            votes[decision] = votes.get(decision, 0) + weight * conf_norm

        # S1
        _add(s1["decision"],                        s1.get("confidence", 50),   1.0)
        # S2
        _add(s2["decision"],                        s2.get("confidence", 50),   1.8)
        # S3 DeepSeek
        _add(s3_raw.get("decision", "HOLD"),        s3_raw.get("confidence", 0),2.5)
        # S4 Llama
        _add(s4_raw.get("decision", "HOLD"),        s4_raw.get("confidence", 0),1.5)
        # S5
        _add(s5["decision"],                        s5.get("confidence", 50),   1.2)
        # Strategy consensus
        _add(strategy_consensus.get("decision","HOLD"),
             strategy_consensus.get("confidence",50), 1.5)

        total  = sum(votes.values())
        winner = max(votes, key=votes.get)
        raw_conf = (votes[winner] / total * 100) if total > 0 else 50

        # Calculate gap bonus (larger gap between 1st and 2nd = higher confidence)
        sorted_v = sorted(votes.values(), reverse=True)
        gap = sorted_v[0] - sorted_v[1] if len(sorted_v) > 1 else 0
        gap_bonus = min(gap / total * 50, 20)

        final_confidence = min(int(raw_conf + gap_bonus), 97)

        # Reduce confidence if AI had errors
        if "❌" in str(s3_raw) or "❌" in str(s4_raw):
            final_confidence = min(final_confidence, 60)

        # Entry, SL, TP from DeepSeek — fallback to ATR-based
        price = self.full_data.get("indicators_1h", {}).get("price", 0) or 0
        atr   = self.full_data.get("indicators_1h", {}).get("atr", 0) or 0

        entry  = s3_raw.get("entry_price") or price
        sl     = s3_raw.get("stop_loss")   or (price * 0.98 if winner == "BUY" else price * 1.02)
        tp1    = s3_raw.get("take_profit_1") or (price * 1.04 if winner == "BUY" else price * 0.96)
        tp2    = s3_raw.get("take_profit_2") or (price * 1.08 if winner == "BUY" else price * 0.92)

        # ATR-based SL/TP if DeepSeek didn't provide them
        if atr and price:
            if not s3_raw.get("stop_loss"):
                sl  = price - 2 * atr if winner == "BUY" else price + 2 * atr
                tp1 = price + 3 * atr if winner == "BUY" else price - 3 * atr
                tp2 = price + 5 * atr if winner == "BUY" else price - 5 * atr

        return {
            "decision":           winner,
            "confidence":         final_confidence,
            "votes":              votes,
            "vote_breakdown": {
                "technical_1h":     s1["decision"],
                "multi_timeframe":  s2["decision"],
                "deepseek_ai":      s3_raw.get("decision", "?"),
                "llama_sentiment":  s4_raw.get("decision", "?"),
                "market_extras":    s5["decision"],
                "strategies":       strategy_consensus.get("decision", "?"),
            },
            "entry_price":        entry,
            "stop_loss":          sl,
            "take_profit_1":      tp1,
            "take_profit_2":      tp2,
            "risk_reward_ratio":  s3_raw.get("risk_reward_ratio", "2:1"),
            "trend_strength":     s3_raw.get("trend_strength", "—"),
            "key_levels":         s3_raw.get("key_levels", {}),
            "reasoning":          s3_raw.get("reasoning", ""),
            "key_signals":        (s3_raw.get("key_signals", []) +
                                   s5["signals"][:2]),
            "sentiment_summary":  s4_raw.get("summary", ""),
            "positive_news":      s4_raw.get("positive_news", []),
            "negative_news":      s4_raw.get("negative_news", []),
            "key_events":         s4_raw.get("key_events", []),
            "warning":            s3_raw.get("warning") or s4_raw.get("warning"),
            "fear_greed":         s5.get("fear_greed_value", 50),
            "buy_pressure":       s5.get("buy_pressure", 50),
            "s1_score":           s1["score"],
            "s5_score":           s5["score"],
        }

    # ─── Run All 6 Stages ─────────────────────────────────────────────────────

    def run_full_analysis_async(self,
                                on_progress: Callable[[str, str], None],
                                on_complete: Callable[[dict], None]):
        def _worker():
            # ── Stage 1 ──
            on_progress("stage1", "🔍 Stage 1: Analyzing technical indicators (1h)…")
            s1 = self.run_stage1()
            self.results["stage1"] = s1
            on_progress("stage1", f"✅ Stage 1: {s1['decision']}  |  Score: {s1['score']}/100  |  Signals: {len(s1['signals'])}")
            for sig in s1["signals"][:6]:
                on_progress("stage1_detail", f"   • {sig}")

            # ── Stage 2 ──
            on_progress("stage2_mtf", "📊 Stage 2: Multi-timeframe analysis (4h + 1d)…")
            s2 = self.run_stage2()
            self.results["stage2"] = s2
            on_progress("stage2_mtf", f"✅ Stage 2: {s2['decision']}  ({s2['confidence']}% confidence)")
            for d in s2.get("details", []):
                on_progress("stage2_detail", f"   • {d}")

            # ── Stage 3: DeepSeek ──
            on_progress("stage3", "🤖 Stage 3: DeepSeek V3.2 — Deep technical analysis…")
            ds_raw = analyze_with_deepseek(
                self._build_deepseek_prompt(),
                on_chunk=lambda c: on_progress("stage3_stream", c),
            )
            s3 = _parse_json(ds_raw)
            if not s3:
                s3 = {"decision": "HOLD", "confidence": 40, "reasoning": ds_raw[:300]}
            self.results["stage3"] = s3
            on_progress("stage3", f"✅ Stage 3 DeepSeek: {s3.get('decision','?')}  ({s3.get('confidence','?')}% confidence)  |  R:R = {s3.get('risk_reward_ratio','?')}")

            # ── Stage 4: Llama ──
            on_progress("stage4", "📰 Stage 4: Llama 3.3 — News & sentiment analysis…")
            llama_raw = analyze_with_llama(
                self._build_llama_prompt(),
                on_chunk=lambda c: on_progress("stage4_stream", c),
            )
            s4 = _parse_json(llama_raw)
            if not s4:
                s4 = {"decision": "HOLD", "confidence": 40, "summary": llama_raw[:300]}
            self.results["stage4"] = s4
            on_progress("stage4", f"✅ Stage 4 Llama: {s4.get('decision','?')}  |  Sentiment: {s4.get('overall_sentiment','?')}  ({s4.get('sentiment_score','?')})")

            # ── Stage 5 ──
            on_progress("stage5", "⚖️ Stage 5: Fear & Greed + Order Book + Global market…")
            s5 = self.run_stage5()
            self.results["stage5"] = s5
            on_progress("stage5", f"✅ Stage 5: {s5['decision']}  |  F&G: {s5['fear_greed_value']}/100  |  Buy pressure: {s5['buy_pressure']}%")

            # ── Stage 6 ──
            on_progress("stage6", "🔮 Stage 6: Weighted voting — computing final decision…")
            strat_consensus = self.full_data.get("strategy_consensus", {})
            final = self.make_final_decision(s1, s2, s3, s4, s5, strat_consensus)
            self.results["stage6"] = final

            dec  = final["decision"]
            conf = final["confidence"]
            on_progress("stage6", f"✅ FINAL DECISION: {dec}  ({conf}% confidence)")

            vb = final.get("vote_breakdown", {})
            vote_summary = " | ".join(f"{k}: {v}" for k, v in vb.items())
            on_progress("stage6_detail", f"   🗳️ {vote_summary}")

            if final.get("warning"):
                on_progress("warning", f"⚠️ WARNING: {final['warning']}")

            on_complete(final)

        t = threading.Thread(target=_worker, daemon=True)
        t.start()
        return t
