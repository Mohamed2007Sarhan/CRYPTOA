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

> *"Don't trade on gut feelings — trade on data, confirmed by 25 strategies, verified by 6 AI stages."*

</div>

---

## 🌟 What is CryptoAI?

**CryptoAI** is a fully autonomous, AI-powered cryptocurrency trading platform with a rich desktop GUI. It combines **real-time market data** from multiple sources, **25+ trading strategies**, and a **6-stage AI verification engine** powered by DeepSeek V3.2 and Llama 3.3 Nemotron to deliver high-confidence trading decisions — automatically.

No guesswork. No emotions. Pure data-driven intelligence.

---

## ✨ Key Features

```
┌─────────────────────────────────────────────────────────────────┐
│                    FEATURE OVERVIEW                              │
├────────────────────────┬────────────────────────────────────────┤
│  🤖 6-Stage AI Engine  │  DeepSeek + Llama multi-layer verify   │
│  📊 25+ Strategies     │  Built-in + AI-generated, weighted vote │
│  📰 Quad-Source News   │  CryptoPanic + RSS + Reddit + Google    │
│  ⚡ Auto Trading       │  Binance API live/testnet execution      │
│  🧪 Backtest Mode      │  Historical strategy performance test   │
│  🌐 Web Discovery      │  AI finds optimal strategies online     │
│  📈 Multi-Timeframe    │  1h + 4h + 1d simultaneous analysis     │
│  😱 Fear & Greed       │  Alternative.me index integration       │
│  📦 Order Book         │  Real-time buy/sell pressure analysis   │
│  🌍 Global Market      │  BTC dominance & market cap tracking    │
└────────────────────────┴────────────────────────────────────────┘
```

---

## 🧠 The 6-Stage AI Verification Engine

> The heart of CryptoAI — every trade decision passes through **6 independent verification layers** before a signal is issued.

```
 ╔══════════════════════════════════════════════════════════════╗
 ║                   AI DECISION PIPELINE                       ║
 ╠══════════════════════════════════════════════════════════════╣
 ║                                                              ║
 ║  1️⃣  STAGE 1 — Technical Indicators (1h)          [w: 1.0]  ║
 ║       RSI · MACD · Bollinger · EMA · Stochastic · ATR       ║
 ║                           │                                  ║
 ║  2️⃣  STAGE 2 — Multi-Timeframe Analysis            [w: 1.8]  ║
 ║       Cross-validates 4h and 1d charts for trend direction   ║
 ║                           │                                  ║
 ║  3️⃣  STAGE 3 — DeepSeek V3.2 Deep Analysis        [w: 2.5]  ║
 ║       Full technical analysis with ALL market data in prompt ║
 ║       → Provides Entry, Stop Loss, TP1, TP2, Risk:Reward    ║
 ║                           │                                  ║
 ║  4️⃣  STAGE 4 — Llama 3.3 Sentiment Analysis       [w: 1.5]  ║
 ║       Analyzes 35+ news articles across 4 sources            ║
 ║       → Detects positive/negative events, community mood     ║
 ║                           │                                  ║
 ║  5️⃣  STAGE 5 — Market Extras                      [w: 1.2]  ║
 ║       Fear & Greed · Order Book Pressure · Recent Trades     ║
 ║       · Global Market Cap Trend · BTC Dominance              ║
 ║                           │                                  ║
 ║  6️⃣  STAGE 6 — Weighted Final Decision            [∑ all]   ║
 ║       Confidence-adjusted vote → BUY / SELL / HOLD          ║
 ║       + Gap bonus for high-conviction signals                 ║
 ║                                                              ║
 ╚══════════════════════════════════════════════════════════════╝
```

---

## 📐 Architecture

```
trade/
├── 🚀 main.py                     # Entry point
│
├── core/
│   ├── 🧠 ai_engine.py            # 6-Stage MultiStageAnalyzer
│   ├── 📊 strategy_manager.py     # 25 strategies + AI discovery
│   ├── 📈 market_data.py          # Binance + CoinGecko + F&G
│   ├── 📰 news_fetcher.py         # CryptoPanic + RSS + Reddit + Google
│   ├── 🔢 indicators.py           # RSI, MACD, BB, EMA, Stoch, ATR
│   └── 🧪 backtester.py           # Historical strategy testing
│
├── gui/
│   ├── 🖥️  app.py                  # Main window + navigation
│   ├── 🏠 welcome_screen.py       # Pair selection screen
│   ├── 📊 dashboard.py            # Live analysis dashboard
│   ├── ⚡ auto_trade.py           # Binance auto-trading screen
│   ├── 🧪 test_mode.py            # Backtest screen
│   └── 🎨 styles.py               # Dark theme CSS
│
└── config/
    ├── ⚙️  settings.py             # API keys + configuration
    └── 📁 strategies/             # Saved custom strategies (JSON)
```

---

## 📊 Strategy Engine

CryptoAI runs **25+ strategies simultaneously** and uses a **weighted consensus vote** to determine the final signal:

| Category | Strategies | Max Weight |
|----------|-----------|-----------|
| 🔴 Reversal | RSI Extreme, RSI Standard, BB Bounce, Stochastic Extreme | 1.5 |
| 📈 Trend | Golden/Death Cross, Full Trend Following, Smart Trend | 2.0 |
| 🚀 Momentum | MACD Strong, MACD Zero Cross, Momentum Surge | 1.6 |
| 🎯 Combined | Triple Confirmation, Dip Buy, BB+RSI Combo | 2.2 |
| 📉 Breakout | BB Breakout, BB Squeeze | 1.5 |
| 🤖 AI-Generated | 5 custom strategies per coin per session | Dynamic |

```python
# Every strategy fires independently → weighted vote
BUY_weight  = Σ(strategy_weight × confidence) for all BUY signals
SELL_weight = Σ(strategy_weight × confidence) for all SELL signals
winner = argmax(BUY_weight, SELL_weight, HOLD_weight)
```

---

## 📰 News & Sentiment

```
Sources (per analysis cycle):
┌──────────────────┬──────────────────────────────────────────────┐
│  CryptoPanic     │  30 targeted crypto news with community votes │
│  12 RSS Feeds    │  CoinTelegraph, Decrypt, CoinDesk, BeInCrypto │
│                  │  BitcoinMagazine, Cryptonews, DailyHodl +more │
│  Reddit          │  r/CryptoCurrency, r/{coin}, r/Bitcoin        │
│  Google News     │  Real-time search for coin-specific headlines  │
└──────────────────┴──────────────────────────────────────────────┘

→ Up to 75 articles deduplicated → 35 sent to Llama 3.3
→ Llama identifies: key events, partnerships, hacks, regulation
→ Outputs: BULLISH / BEARISH / NEUTRAL + key_events + warning
```

---

## ⚡ Auto Trading Mode

```
┌─────────────────────────────────────────────────┐
│  Input:  Binance API Key + Secret               │
│  Mode:   Testnet ✅ / Live ⚠️                   │
│  Risk:   % of balance per trade (configurable)  │
│  SL:     Auto stop-loss (ATR-based or % based)  │
│  TP:     Dual targets (TP1 + TP2)              │
└─────────────────────────────────────────────────┘
         ↓ AI makes decision every cycle
    BUY → Binance buy order placed
    SELL → Binance sell order placed
    HOLD → Wait for next cycle
```

---

## 🧪 Backtest Mode

Test all 25+ strategies against **up to 365 days** of historical data:

```
📥 Fetch 1h/4h/1d OHLCV data from Binance
📊 Run every strategy with sliding window
📈 Calculate: Win Rate · Total Return · Max Drawdown · Sharpe Ratio
🏆 Rank strategies by performance
```

---

## 🚀 Quick Start

### 1. Prerequisites

```bash
git clone <your-repo>
cd trade
python -m venv venv
source venv/bin/activate   # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Configure API Keys

Edit `config/settings.py`:

```python
NVIDIA_API_KEY = "nvapi-your-key-here"   # DeepSeek + Llama via NVIDIA API
# Binance keys are entered in the GUI (Auto Trade screen)
```

> Get your NVIDIA API key free at → [build.nvidia.com](https://build.nvidia.com)

### 3. Run

```bash
python main.py
```

---

## 📦 Requirements

```
PyQt6>=6.4.0         # Desktop GUI
python-binance        # Binance market data + trading
ccxt                  # Extended exchange support
openai                # NVIDIA API (DeepSeek + Llama)
pandas / numpy        # Data processing
ta                    # Technical indicators
requests              # HTTP calls
feedparser            # RSS news feeds
```

---

## 🖥️ Screenshots

```
┌──────────────────────────────────────────┐
│  🏠 Welcome Screen                        │
│  → Select from 50+ crypto pairs          │
│  → Search or type any symbol             │
│                                          │
│  📊 Analysis Dashboard                   │
│  → Live price + 7 metric cards           │
│  → 6-stage progress indicators           │
│  → Real-time AI log stream               │
│  → Strategy signals table                │
│  → News feed with sentiment              │
│  → Indicators tab (18 indicators)        │
│                                          │
│  ⚡ Auto Trade                            │
│  → Live P&L tracking                    │
│  → Trade log with color coding          │
│                                          │
│  🧪 Backtest                             │
│  → Strategy ranking table               │
│  → Sortable by win rate / return        │
└──────────────────────────────────────────┘
```

---

## ⚠️ Disclaimer

> **CryptoAI is for educational and research purposes only.**
> Cryptocurrency trading involves significant risk of loss.
> Past performance of any strategy does not guarantee future results.
> Never invest money you cannot afford to lose.
> The AI analysis is a tool — not financial advice.

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
