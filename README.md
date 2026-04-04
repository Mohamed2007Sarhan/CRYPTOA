<div align="center">

```
╔═══════════════════════════════════════════════════════════════════╗
║                                                                   ║
║    ██████╗██████╗ ██╗   ██╗██████╗ ████████╗ ██████╗  █████╗    ║
║   ██╔════╝██╔══██╗╚██╗ ██╔╝██╔══██╗╚══██╔══╝██╔═══██╗██╔══██╗  ║
║   ██║     ██████╔╝ ╚████╔╝ ██████╔╝   ██║   ██║   ██║███████║  ║
║   ██║     ██╔══██╗  ╚██╔╝  ██╔═══╝    ██║   ██║   ██║██╔══██║  ║
║   ╚██████╗██║  ██║   ██║   ██║        ██║   ╚██████╔╝██║  ██║  ║
║    ╚═════╝╚═╝  ╚═╝   ╚═╝   ╚═╝        ╚═╝    ╚═════╝ ╚═╝  ╚═╝  ║
║                                                                   ║
║           🤖  AI-Powered Cryptocurrency Trading Platform          ║
║                                                                   ║
╚═══════════════════════════════════════════════════════════════════╝
```

<br/>

[![Python](https://img.shields.io/badge/Python-3.10%2B-00FFB2?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![PyQt6](https://img.shields.io/badge/PyQt6-GUI-00D4FF?style=for-the-badge&logo=qt&logoColor=white)](https://pypi.org/project/PyQt6/)
[![DeepSeek](https://img.shields.io/badge/DeepSeek-V3.2-8B5CF6?style=for-the-badge&logo=openai&logoColor=white)](https://nvidia.com)
[![Llama](https://img.shields.io/badge/Llama-3.3%20Nemotron-F59E0B?style=for-the-badge&logo=meta&logoColor=white)](https://nvidia.com)
[![Binance](https://img.shields.io/badge/Binance-API-F0B90B?style=for-the-badge&logo=binance&logoColor=black)](https://binance.com)
[![License](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

<br/>

> *"Don't trade on gut feelings — trade on data, confirmed by 25 strategies, verified by 6 AI stages, protected by a real-time anomaly guard."*

</div>

---

## 🌟 What is CryptoAI?

**CryptoAI** is a fully autonomous, AI-powered cryptocurrency trading platform with a rich dark-themed desktop GUI. It combines **real-time market data** from multiple sources, **25+ trading strategies**, a **6-stage AI verification engine** powered by DeepSeek V3.2 and Llama 3.3 Nemotron, and a **candle-synchronized smart trading loop** with built-in anomaly protection — all in one application.

No guesswork. No emotions. Pure data-driven intelligence.

---

## ✨ Feature Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                        FEATURE OVERVIEW                              │
├──────────────────────────┬──────────────────────────────────────────┤
│  🤖 6-Stage AI Engine    │  DeepSeek + Llama multi-layer verify      │
│  📊 25+ Strategies       │  Built-in + AI-generated, weighted vote   │
│  🔁 Smart Loop           │  Candle-aligned HUNT → GUARD state machine│
│  🛡️ Anomaly Guard        │  Real-time crash detection + emergency exit│
│  📰 Quad-Source News     │  CryptoPanic + RSS + Reddit + Google      │
│  ⚡ Auto Trading         │  Binance API live / testnet execution      │
│  🧪 Backtest Mode        │  Historical strategy performance test      │
│  🌐 Web Discovery        │  AI finds optimal strategies online        │
│  📈 Multi-Timeframe      │  1h + 4h + 1d simultaneous analysis       │
│  😱 Fear & Greed         │  Alternative.me index integration          │
│  📦 Order Book           │  Real-time buy/sell pressure analysis      │
│  🌍 Global Market        │  BTC dominance & market cap tracking       │
└──────────────────────────┴──────────────────────────────────────────┘
```

---

## 🔁 Smart Auto-Trading Loop (State Machine)

> The core of the automation engine — a **two-state machine** that never stops until you tell it to.

```
 ╔══════════════════════════════════════════════════════════════════╗
 ║                    AUTO TRADING STATE MACHINE                     ║
 ╠══════════════════════════════════════════════════════════════════╣
 ║                                                                  ║
 ║   🔍 HUNTING STATE (no open trade)                               ║
 ║   ─────────────────────────────────                              ║
 ║   Scans every X minutes looking for a BUY entry:                 ║
 ║                                                                  ║
 ║     Fetch live candle data                                       ║
 ║          ↓                                                       ║
 ║     Run Pre-Close Predictor (7 signals)                          ║
 ║          ↓                                                       ║
 ║     Check 25+ Strategy Consensus                                 ║
 ║          ↓                                                       ║
 ║     6-Stage AI Confirmation (DeepSeek + Llama)                   ║
 ║          ↓                                                       ║
 ║     ┌─ All say BUY? ──── YES ──→ 🛒 Open trade → GUARDING       ║
 ║     └─ No clear signal? ─ NO ──→ ⏳ Wait X min → scan again ↺   ║
 ║                                                                  ║
 ║   ⚔️ GUARDING STATE (trade open)                                 ║
 ║   ─────────────────────────────────                              ║
 ║   Sleeps precisely until 5 min before each candle close:         ║
 ║                                                                  ║
 ║     Sleep (candle_duration − 5 min)                              ║
 ║          ↓                                                       ║
 ║     Wake up, fetch fresh data                                    ║
 ║          ↓                                                       ║
 ║     ┌─ Stop Loss hit?    → 🔴 Sell → HUNTING                    ║
 ║     ├─ Take Profit hit?  → 🟢 Sell → HUNTING                    ║
 ║     ├─ DOWN predicted?   → 📉 Sell → HUNTING                    ║
 ║     └─ UP predicted?     → ✅ Hold → wait next candle ↺         ║
 ║                                                                  ║
 ╚══════════════════════════════════════════════════════════════════╝
```

### ⏱️ Scan Interval Table

The bot adapts its scan speed to the chosen candle interval:

| Candle | HUNTING scans every | GUARDING sleeps |
|--------|--------------------:|----------------:|
| `1m`   | 15 seconds          | Immediate       |
| `5m`   | 1m 15s              | Immediate       |
| `15m`  | 3m 45s              | 10 minutes      |
| `30m`  | 5 minutes           | 25 minutes      |
| `1h`   | 5 minutes           | 55 minutes      |
| `2h`   | 5 minutes           | 1h 55m          |
| `4h`   | 5 minutes           | 3h 55m          |
| `1d`   | 5 minutes           | 23h 55m         |

> **Key principle:** HUNTING scans continuously at frequent intervals so it never misses an opportunity. GUARDING rests precisely until 5 minutes before the candle closes, then wakes to check the prediction.

---

## 🛡️ Anomaly Guard

> A dedicated background thread watching the market every **20 seconds** — independent of the main trading loop.

```
 ╔══════════════════════════════════════════════════════════════════╗
 ║                       ANOMALY GUARD                               ║
 ╠══════════════════════════════════════════════════════════════════╣
 ║                                                                  ║
 ║   Runs every 20 seconds in parallel. Checks 5 danger types:      ║
 ║                                                                  ║
 ║   💥 Flash Crash                                                  ║
 ║      Price drops > 2.5% within the last 3 readings (60 sec)     ║
 ║                                                                  ║
 ║   📊 Volume Spike + Price Drop                                    ║
 ║      Volume > 4× rolling average AND price down > 1%             ║
 ║      (confirms panic sell-off, not just noise)                   ║
 ║                                                                  ║
 ║   📖 Order Book Collapse                                          ║
 ║      Buy pressure < 25% (sellers completely dominate)            ║
 ║      OR spread > 1.5% (illiquidity / market manipulation)        ║
 ║                                                                  ║
 ║   📉 RSI Cliff                                                    ║
 ║      RSI drops ≥ 15 points in 4 checks AND RSI < 40              ║
 ║      (panic capitulation detected)                               ║
 ║                                                                  ║
 ║   ☠️  EMA200 Break                                                ║
 ║      Price falls > 1.5% below EMA200 (death zone entry)         ║
 ║                                                                  ║
 ║   → Any trigger → 🆘 EMERGENCY EXIT: sell everything instantly  ║
 ║   → Switches back to HUNTING to look for safe re-entry          ║
 ║   → 3-minute cooldown prevents duplicate alerts                  ║
 ║                                                                  ║
 ╚══════════════════════════════════════════════════════════════════╝
```

---

## 🔮 Pre-Candle Predictor

> 5 minutes before every candle close, this module calculates a **weighted direction score** using 7 independent signals:

| # | Signal | Max Score |
|---|--------|----------:|
| 1 | Candle body momentum (last 3 candles) | ±15 |
| 2 | Volume surge + direction confirmation  | ±20 |
| 3 | RSI level & momentum                  | ±10 |
| 4 | MACD histogram direction              | ±10 |
| 5 | Price vs EMA20 (short-term trend)     | ±10 |
| 6 | Bollinger Band position               | ±15 |
| 7 | Short-term rate of change (ROC)       | ±10 |

```
Total Score > +10  →  UP   →  BUY    (enter or hold)
Total Score < −10  →  DOWN →  SELL   (exit before candle close)
Otherwise          →  NEUTRAL → HOLD
```

---

## 🧠 The 6-Stage AI Verification Engine

> Every trade decision passes through **6 independent verification layers** before a BUY signal is confirmed.

```
 ╔══════════════════════════════════════════════════════════════════╗
 ║                    AI DECISION PIPELINE                           ║
 ╠══════════════════════════════════════════════════════════════════╣
 ║                                                                  ║
 ║  1️⃣  STAGE 1 — Technical Indicators (1h)              [w: 1.0]  ║
 ║       RSI · MACD · Bollinger · EMA · Stochastic · ATR            ║
 ║                            │                                     ║
 ║  2️⃣  STAGE 2 — Multi-Timeframe Analysis               [w: 1.8]  ║
 ║       Cross-validates 4h and 1d charts for trend alignment       ║
 ║                            │                                     ║
 ║  3️⃣  STAGE 3 — DeepSeek V3.2 Deep Analysis           [w: 2.5]  ║
 ║       Full technical analysis with ALL market data in prompt     ║
 ║       → Provides Entry, Stop Loss, TP1, TP2, Risk:Reward        ║
 ║                            │                                     ║
 ║  4️⃣  STAGE 4 — Llama 3.3 Sentiment Analysis          [w: 1.5]  ║
 ║       Analyzes 35+ news articles across 4 sources                ║
 ║       → Detects events: partnerships, hacks, regulation, FUD    ║
 ║                            │                                     ║
 ║  5️⃣  STAGE 5 — Market Extras                         [w: 1.2]  ║
 ║       Fear & Greed · Order Book Pressure · Recent Trades         ║
 ║       · Global Market Cap Trend · BTC Dominance                  ║
 ║                            │                                     ║
 ║  6️⃣  STAGE 6 — Weighted Final Decision               [∑ all]   ║
 ║       Confidence-adjusted vote → BUY / SELL / HOLD              ║
 ║       + Gap bonus for high-conviction signals                    ║
 ║                                                                  ║
 ╚══════════════════════════════════════════════════════════════════╝
```

---

## 📊 Strategy Engine

CryptoAI runs **25+ strategies simultaneously** using a **weighted consensus vote**:

| Category | Strategies | Weight |
|----------|-----------|-------:|
| 🔴 Reversal | RSI Extreme, RSI Standard, BB Bounce, Stochastic Extreme | 1.5× |
| 📈 Trend | Golden/Death Cross, Full Trend Following, Smart Trend | 2.0× |
| 🚀 Momentum | MACD Strong, MACD Zero Cross, Momentum Surge | 1.6× |
| 🎯 Combined | Triple Confirmation, Dip Buy, BB+RSI Combo | 2.2× |
| 📉 Breakout | BB Breakout, BB Squeeze | 1.5× |
| 🤖 AI-Generated | 5 custom strategies discovered online per session | Dynamic |

```python
# Consensus formula
BUY_score  = Σ(strategy_weight × confidence)  for all BUY signals
SELL_score = Σ(strategy_weight × confidence)  for all SELL signals
decision   = argmax(BUY_score, SELL_score, HOLD_score)
```

---

## 📰 News & Sentiment Analysis

```
Sources fetched each analysis cycle:
┌────────────────────┬────────────────────────────────────────────────┐
│  CryptoPanic       │  30 targeted crypto news with community votes  │
│  12 RSS Feeds      │  CoinTelegraph · Decrypt · CoinDesk · BeInCrypto│
│                    │  BitcoinMagazine · Cryptonews · DailyHodl +more │
│  Reddit            │  r/CryptoCurrency · r/{coin} · r/Bitcoin        │
│  Google News       │  Real-time search for coin-specific headlines   │
└────────────────────┴────────────────────────────────────────────────┘

→ Up to 75 articles → deduplicated → top 35 sent to Llama 3.3
→ Llama identifies: key events, partnerships, hacks, regulation, FUD
→ Outputs: BULLISH / BEARISH / NEUTRAL + key_events list + warnings
```

---

## 📐 Project Architecture

```
trade/
├── 🚀 main.py                      # Application entry point
│
├── core/
│   ├── 🧠 ai_engine.py             # 6-Stage MultiStageAnalyzer
│   ├── 📊 strategy_manager.py      # 25 strategies + AI discovery
│   ├── 📈 market_data.py           # Binance + CoinGecko + Fear&Greed
│   ├── 📰 news_fetcher.py          # CryptoPanic + RSS + Reddit + Google
│   ├── 🔢 indicators.py            # RSI, MACD, BB, EMA, Stoch, ATR
│   ├── 🔮 pre_candle_predictor.py  # 5-min before-close direction model
│   ├── 🛡️  anomaly_guard.py         # Real-time crash detector (thread)
│   ├── 🔁 trading_engine.py        # HUNTING ↔ GUARDING state machine
│   └── 🧪 backtester.py            # Historical strategy testing
│
├── gui/
│   ├── 🖥️  app.py                   # Main window + navigation
│   ├── 🏠 welcome_screen.py        # Pair selection screen
│   ├── 📊 dashboard.py             # Live analysis dashboard
│   ├── ⚡ auto_trade.py            # Auto trading screen + state display
│   ├── 🧪 test_mode.py             # Backtest screen
│   └── 🎨 styles.py                # Dark theme stylesheet
│
└── config/
    ├── ⚙️  settings.py              # API keys + risk defaults
    └── 📁 strategies/              # Saved AI-generated strategies (JSON)
```

---

## ⚡ Auto Trading Screen — Live Log Examples

When running in auto-trade mode, the live log looks like this:

```
🚀 Smart AutoTrader started | BTCUSDT | Interval: 1h
🔍 HUNTING: scans every 5m | ⚔️ GUARDING: sleeps 55m then checks 5m before close
🛡️ AnomalyGuard active — monitoring every 20 seconds

🔍 [HUNTING] Scanning... BTCUSDT @ 14:05:32
  📈 Prediction: UP | Confidence: 72% | Last 3 candles: 2 bullish | High volume bullish
  📊 Consensus: BUY (65%) | Buy:8 Sell:3
🟢 Strong BUY signal! Running AI confirmation...
🤖 AI verdict: BUY | Confidence: 79%
✅ Trade opened | Qty: 0.001234 | USDT: 104.50 | SL: 83,000 | TP: 89,500
⚔️ Switched to GUARDING — monitoring until exit or target

⚔️ [GUARDING] In trade @ 85420.00 | Current PnL: +0.80% | Next check in 52m 14s
🔔 [GUARDING] Pre-close check | BTCUSDT @ 14:55:00
  📉 Prediction: DOWN | Confidence: 58% | MACD histogram negative
💰 PnL: +1.24% | Total P&L: +1.24% | Win rate: 100% (1/1)
🔍 Switched to HUNTING — looking for next buy opportunity...

🔍 [HUNTING] Scanning... BTCUSDT @ 14:55:03   ← immediately continues!
  ➡️ Prediction: NEUTRAL | Confidence: 31%
  📊 Consensus: HOLD (44%)
  ⏳ No entry signal (NEUTRAL/HOLD) — retrying in 5m 0s
```

---

## 🧪 Backtest Mode

Test all 25+ strategies against **up to 365 days** of historical data:

```
📥 Fetch 1h / 4h / 1d OHLCV from Binance
📊 Run each strategy with a sliding window across all candles
📈 Metrics: Win Rate · Total Return · Max Drawdown · Sharpe Ratio
🏆 Strategies ranked by performance for the selected coin & period
```

---

## 🚀 Quick Start

### 1. Clone & Install

```bash
git clone [https://github.com/Mohamed2007Sarhan/CRYPTOA](https://github.com/Mohamed2007Sarhan/CRYPTOA)
cd trade
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `config/settings.py`:

```python
NVIDIA_API_KEY = "nvapi-your-key-here"   # DeepSeek + Llama via NVIDIA API
# Binance keys are entered directly in the Auto Trade screen GUI
```

> Get your **free** NVIDIA API key at → [build.nvidia.com](https://build.nvidia.com)

### 3. Launch

```bash
python main.py
```

---

## 📦 Requirements

```
PyQt6 >= 6.4.0       # Desktop GUI framework
python-binance        # Binance market data + order execution
ccxt                  # Extended exchange support
openai                # NVIDIA API gateway (DeepSeek + Llama)
pandas / numpy        # Data processing & indicator math
ta                    # Technical analysis indicators library
requests              # HTTP API calls
feedparser            # RSS news feed parsing
```

---

## 🖥️ Screens

```
┌──────────────────────────────────────────────────────┐
│  🏠 Welcome Screen                                    │
│  → Choose from 50+ crypto pairs                      │
│  → Search or type any symbol                         │
│                                                      │
│  📊 Analysis Dashboard                               │
│  → Live price + 7 metric stat cards                  │
│  → 6-stage AI progress indicators                    │
│  → Real-time AI log stream                           │
│  → Strategy signals table (25+ rows)                 │
│  → News feed with sentiment badges                   │
│  → Indicators tab (18 live indicators)               │
│                                                      │
│  ⚡ Auto Trade Screen                                 │
│  → Interval selector (1m → 1d)                       │
│  → Mode badge: 🔍 HUNT or ⚔️ GUARD (live update)    │
│  → Win rate, Total P&L, Trade count cards            │
│  → Colour-coded live log (green=buy, red=sell)       │
│  → AnomalyGuard alerts in amber                      │
│                                                      │
│  🧪 Backtest Screen                                  │
│  → Strategy leaderboard table                        │
│  → Sortable by win rate / return / drawdown          │
└──────────────────────────────────────────────────────┘
```

---

## ⚠️ Disclaimer

> **CryptoAI is for educational and research purposes only.**
> Cryptocurrency trading involves significant risk of loss.
> Past performance of any strategy does not guarantee future results.
> Never invest money you cannot afford to lose.
> Always test on **Testnet** before going live.
> The AI analysis is a decision-support tool — **not financial advice.**

---

## 📄 License

MIT License — free to use, modify, and distribute.

---

<div align="center">

```
  ╔═══════════════════════════════════════╗
  ║   Built with ❤️  by Mohamed           ║
  ║   Powered by DeepSeek + Llama + You  ║
  ╚═══════════════════════════════════════╝
```

**⭐ Star this repo if it helped you trade smarter!**

</div>
