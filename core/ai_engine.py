"""
AI Engine — 6-Stage Verification
DeepSeek V3.2 + Llama 3.3 Nemotron with comprehensive data prompts
"""
import json
import re
import threading
import time
import threading
import time
import threading
from typing import Callable, Optional, Dict, Any
from openai import OpenAI
import httpx
import traceback
import sys
from config.settings import (
    NVIDIA_API_KEY, NVIDIA_BASE_URL,
    DEEPSEEK_MODEL, LLAMA_MODEL
)


def _get_client() -> OpenAI:
    return OpenAI(
        base_url=NVIDIA_BASE_URL, 
        api_key=NVIDIA_API_KEY,
        timeout=httpx.Timeout(None)
    )


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
        print("\n=== DEEPSEEK ERROR ===", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("======================\n", file=sys.stderr)
        sys.stderr.flush()
        sys.stdout.flush()
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
        print("\n=== LLAMA ERROR ===", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print("===================\n", file=sys.stderr)
        sys.stderr.flush()
        sys.stdout.flush()
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

    def __init__(self, symbol: str, full_data: Dict[str, Any], primary_tf: str = "1h"):
        self.symbol     = symbol
        self.full_data  = full_data
        self.primary_tf = primary_tf
        self.results    = {}

    # ─── Stage 1: Technical Analysis ────────────────────────────────────

    def run_stage1(self) -> dict:
        ind   = self.full_data.get(f"indicators_{self.primary_tf}", {})
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
        ind_pri = self.full_data.get(f"indicators_{self.primary_tf}", {})
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

═══ TECHNICAL DATA — {self.primary_tf} Timeframe ═══
• Price: {ind_pri.get('price', 'N/A')} USDT
• 24h Change: {ind_pri.get('change_24h', 'N/A')}%
• 24h Volume: {ind_pri.get('volume_24h', 'N/A'):,.0f} USDT
• RSI(14): {ind_pri.get('rsi', 'N/A')}
• MACD: {ind_pri.get('macd', 'N/A')} | Signal: {ind_pri.get('macd_signal', 'N/A')} | Hist: {ind_pri.get('macd_hist', 'N/A')}
• Bollinger: ↑{ind_pri.get('bb_upper', 'N/A')} | Mid: {ind_pri.get('bb_mid', 'N/A')} | ↓{ind_pri.get('bb_lower', 'N/A')}
• EMA20: {ind_pri.get('ema20', 'N/A')} | EMA50: {ind_pri.get('ema50', 'N/A')} | EMA200: {ind_pri.get('ema200', 'N/A')}
• Stoch K: {ind_pri.get('stoch_k', 'N/A')} | D: {ind_pri.get('stoch_d', 'N/A')}
• ATR: {ind_pri.get('atr', 'N/A')}
• Candle Pattern: {ind_pri.get('candle_pattern', 'N/A')}

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

        # Build a balanced subset so one source does not dominate the prompt.
        def source_family(src: str) -> str:
            s = (src or "").lower()
            if s.startswith("blockchain api/"):
                return "blockchain"
            if s.startswith("reddit"):
                return "reddit"
            if s.startswith("google news"):
                return "google"
            if s.startswith("cryptopanic"):
                return "cryptopanic"
            return "rss"

        max_total = 30
        max_per_family = 8
        selected_articles = []
        family_counts = {}
        overflow = []

        for a in articles:
            src = a.get("source", "Unknown")
            fam = source_family(src)
            if family_counts.get(fam, 0) < max_per_family:
                selected_articles.append(a)
                family_counts[fam] = family_counts.get(fam, 0) + 1
            else:
                overflow.append(a)
            if len(selected_articles) >= max_total:
                break

        if len(selected_articles) < max_total:
            for a in overflow:
                selected_articles.append(a)
                if len(selected_articles) >= max_total:
                    break

        news_text = ""
        for i, a in enumerate(selected_articles, 1):
            title = a.get("title", "")
            src   = a.get("source", "")
            pv    = a.get("votes_positive", 0)
            nv    = a.get("votes_negative", 0)
            news_text += f"{i}. [{src}] {title} (👍{pv} 👎{nv})\n"

        gecko_desc = gecko.get("description", "")[:300]

        return f"""You are a sentiment analyst specializing in cryptocurrency markets.

Analyze the following data for {self.symbol} and evaluate market sentiment:

═══ LATEST NEWS (showing {len(selected_articles)} of {len(articles)} articles, source-balanced) ═══
{news_text if news_text else 'No news available'}

═══ CURRENT SENTIMENT ═══
• Fear & Greed Index: {fg.get('value', 50)}/100 — {fg.get('classification', 'Neutral')}
• Index Trend: {fg.get('trend', 'Stable')}
• CryptoPanic Community Score: {news.get('sentiment_score', 0):+.1f}

═══ COIN DESCRIPTION ═══
{gecko_desc}

═══ YOUR TASK ═══
1. Analyze news headlines ruthlessly — ignore fluff. Identify ONLY structural catalysts: partnerships, hacks, regulation, massive inflows, or bankruptcies.
2. Evaluate trader/community enthusiasm vs. market reality.
3. Weigh the Fear & Greed Index vs News Momentum: If the market is in "Extreme Greed" but news is bearish, this is a catastrophic reversal signal.
4. Provide a definitive sentiment rating on the STRICT scale below:
   [CATASTROPHIC, BEARISH, NEUTRAL, BULLISH, MOONSHOT]

Respond with STRICT JSON only:
{{
  "overall_sentiment": "CATASTROPHIC/BEARISH/NEUTRAL/BULLISH/MOONSHOT",
  "sentiment_score": "number 0 to 100",
  "decision": "BUY" or "SELL" or "HOLD",
  "confidence": "number 0-100",
  "positive_news": ["structural positive catalyst 1", "structural positive catalyst 2"],
  "negative_news": ["structural negative catalyst 1", "structural negative catalyst 2"],
  "key_events": ["event1", "event2", "event3"],
  "community_mood": "brutal reality of community mood",
  "fear_greed_interpretation": "divergence check against F&G",
  "summary": "Brutal, decisive 2-sentence summary of impending market movement based strictly on news.",
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
                             s5: dict, strategy_consensus: dict,
                             on_chunk: Callable[[str], None] = None) -> dict:
        """
        Stage 6: The Ultimate Blender
        Sends ALL previous stage results to DeepSeek V3.2 for the absolute final decision.
        """
        # Prepare the ultimate prompt
        fg_val = s5.get('fear_greed_value', 50)
        buy_press = s5.get('buy_pressure', 50)
        strat_dec = strategy_consensus.get('decision', 'HOLD')
        strat_conf = strategy_consensus.get('confidence', 50)
        
        prompt = f"""You are the ULTIMATE Crypto Trading Judge (The Blender).
You must analyze the findings from 5 distinct expert engines for {self.symbol} and make the ABSOLUTE FINAL trading decision.

═══ STAGE 1: PURE MATH (Technical) ═══
Decision: {s1.get('decision')} | Score: {s1.get('score', 50)}/100
Signals: {', '.join(s1.get('signals', [])[:5])}

═══ STAGE 2: MULTI-TIMEFRAME (Trend) ═══
Decision: {s2.get('decision')} | Confidence: {s2.get('confidence', 50)}%

═══ STAGE 3: AI TECHNICAL ENGINE ═══
Decision: {s3_raw.get('decision')} | Confidence: {s3_raw.get('confidence', 50)}%
Suggested Entry: {s3_raw.get('entry_price', 'N/A')} | SL: {s3_raw.get('stop_loss', 'N/A')}
Targets: {s3_raw.get('take_profit_1', 'N/A')}, {s3_raw.get('take_profit_2', 'N/A')}
Reasoning: {s3_raw.get('reasoning', 'N/A')}

═══ STAGE 4: AI SENTIMENT ENGINE (News & Crowd) ═══
Sentiment: {s4_raw.get('overall_sentiment')} | Score: {s4_raw.get('sentiment_score', 0)}
Decision: {s4_raw.get('decision')}
Summary: {s4_raw.get('summary', 'N/A')}

═══ STAGE 5: MARKET CONTEXT ═══
Fear & Greed: {fg_val}/100 | Buy Pressure: {buy_press}%
Strategies Consensus: {strat_dec} ({strat_conf}% confidence)

═══ YOUR TASK ═══
Blend all of this data. Weigh the Pure Math, the Sentiment, and the AI Technicals together.
Resolve any conflicts. If S1 is SELL but S3 and S4 are BUY, you must decide who is right.

Respond with STRICT JSON only (no text outside JSON). The JSON must exactly match this format:
{{
  "decision": "BUY" or "SELL" or "HOLD",
  "confidence": number 0-100,
  "entry_price": suggested optimal entry price number,
  "stop_loss": strictly proper stop loss number (if SHORT/SELL, SL should be > Entry),
  "take_profit_1": target 1 number,
  "take_profit_2": target 2 number,
  "risk_reward_ratio": "e.g. 2.5:1",
  "reasoning": "Detailed final summary explaining why this decision was reached after blending all stages (150-250 words)"
}}"""

        # Call DeepSeek as the Final Blender
        while True:
            raw = analyze_with_deepseek(prompt, on_chunk=on_chunk)
            if not raw.startswith("❌"):
                final_json = _parse_json(raw)
                if final_json and "decision" in final_json:
                    # If BUY/SELL, ensure it didn't output 0s
                    dec = final_json["decision"]
                    if dec in ["BUY", "SELL"]:
                        sl = final_json.get("stop_loss")
                        if sl in [None, 0, 0.0, "0", "N/A"]:
                            if on_chunk: on_chunk("\n⚠️ Network returned zeros in trade order. Forcing attempt to fix numbers...\n")
                            time.sleep(2)
                            continue
                    break
            
            if on_chunk: on_chunk("\n⚠️ Connection hung or incomplete reply. Retrying infinitely...\n")
            time.sleep(3)

        dec = final_json["decision"]
        price = self.full_data.get(f"indicators_{self.primary_tf}", {}).get("price", 0) or 0
        atr   = self.full_data.get(f"indicators_{self.primary_tf}", {}).get("atr", 0) or 0
        
        # Ensure SL/TP are provided if missing or if DeepSeek outputted 0
        if not final_json.get("entry_price") or float(final_json.get("entry_price")) == 0:
            final_json["entry_price"] = price

        if atr and price:
            sl = final_json.get("stop_loss")
            tp1 = final_json.get("take_profit_1")
            
            # If values are missing / zero, fallback
            if sl in [None, 0, 0.0, "0", "N/A"]:
                final_json["stop_loss"] = price - 2 * atr if dec in ["BUY", "HOLD"] else price + 2 * atr
            if tp1 in [None, 0, 0.0, "0", "N/A"]:
                final_json["take_profit_1"] = price + 3 * atr if dec in ["BUY", "HOLD"] else price - 3 * atr
            if final_json.get("take_profit_2") in [None, 0, 0.0, "0", "N/A"]:
                final_json["take_profit_2"] = price + 5 * atr if dec in ["BUY", "HOLD"] else price - 5 * atr
                
            # Logically Validate Direction (Auto-correct an AI hallucination)
            ep = float(final_json["entry_price"])
            sl = float(final_json["stop_loss"])
            if dec == "BUY" and sl >= ep:
                final_json["stop_loss"] = ep - 2 * atr
            elif dec == "SELL" and sl <= ep:
                final_json["stop_loss"] = ep + 2 * atr

        return {
            "decision":           dec,
            "confidence":         final_json.get("confidence", 50),
            "vote_breakdown": {
                "technical_pure":   s1["decision"],
                "multi_timeframe":  s2["decision"],
                "deepseek_tech":    s3_raw.get("decision", "?"),
                "llama_sentiment":  s4_raw.get("decision", "?"),
                "market_extras":    s5["decision"],
                "strategies":       strat_dec,
            },
            "entry_price":        final_json.get("entry_price", price),
            "stop_loss":          final_json.get("stop_loss"),
            "take_profit_1":      final_json.get("take_profit_1"),
            "take_profit_2":      final_json.get("take_profit_2"),
            "risk_reward_ratio":  final_json.get("risk_reward_ratio", "2:1"),
            "trend_strength":     s3_raw.get("trend_strength", "—"),
            "reasoning":          final_json.get("reasoning", ""),
            "sentiment_summary":  s4_raw.get("summary", ""),
            "positive_news":      s4_raw.get("positive_news", []),
            "negative_news":      s4_raw.get("negative_news", []),
            "key_events":         s4_raw.get("key_events", []),
            "warning":            s3_raw.get("warning") or s4_raw.get("warning"),
            "fear_greed":         fg_val,
            "buy_pressure":       buy_press,
            "s1_score":           s1.get("score", 50),
            "s5_score":           s5.get("score", 50),
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
            on_progress("stage3", "🤖 Stage 3: AI Technical (Math + DeepSeek)…")
            while True:
                ds_raw = analyze_with_deepseek(
                    self._build_deepseek_prompt(),
                    on_chunk=lambda c: on_progress("stage3_stream", c),
                )
                if not ds_raw.startswith("❌"):
                    s3 = _parse_json(ds_raw)
                    if s3 and "decision" in s3:
                        dec = s3["decision"]
                        if dec in ["BUY", "SELL"]:
                            sl = s3.get("stop_loss")
                            if sl in [None, 0, 0.0, "0", "N/A"]:
                                on_progress("stage3_stream", "\n⚠️ Stage 3 returned zeros by mistake. Retrying...\n")
                                time.sleep(2)
                                continue
                        break
                on_progress("stage3_stream", "\n⚠️ Stage 3 network error. Retrying infinitely...\n")
                time.sleep(3)
                
            self.results["stage3"] = s3
            on_progress("stage3", f"✅ Stage 3 DeepSeek: {s3.get('decision','?')}  ({s3.get('confidence','?')}% confidence)  |  R:R = {s3.get('risk_reward_ratio','?')}")

            # ── Stage 4: Llama ──
            on_progress("stage4", "📰 Stage 4: AI Sentiment (News + Llama)…")
            while True:
                llama_raw = analyze_with_llama(
                    self._build_llama_prompt(),
                    on_chunk=lambda c: on_progress("stage4_stream", c),
                )
                if not llama_raw.startswith("❌"):
                    s4 = _parse_json(llama_raw)
                    if s4 and "decision" in s4:
                        break
                on_progress("stage4_stream", "\n⚠️ Stage 4 network error. Retrying infinitely...\n")
                time.sleep(3)
                
            self.results["stage4"] = s4
            on_progress("stage4", f"✅ Stage 4 Llama: {s4.get('decision','?')}  |  Sentiment: {s4.get('overall_sentiment','?')}  ({s4.get('sentiment_score','?')})")

            # ── Stage 5 ──
            on_progress("stage5", "⚖️ Stage 5: Market Context (F&G + Order Book)…")
            s5 = self.run_stage5()
            self.results["stage5"] = s5
            on_progress("stage5", f"✅ Stage 5: {s5['decision']}  |  F&G: {s5['fear_greed_value']}/100  |  Buy pressure: {s5['buy_pressure']}%")

            # ── Stage 6 ──
            on_progress("stage6", "🔮 Stage 6: The Ultimate Blender (DeepSeek Verification)…")
            strat_consensus = self.full_data.get("strategy_consensus", {})
            final = self.make_final_decision(
                s1, s2, s3, s4, s5, strat_consensus,
                on_chunk=lambda c: on_progress("stage6_stream", c)
            )
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
