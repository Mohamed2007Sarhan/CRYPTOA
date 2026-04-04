"""
AI Crypto Trading Platform - Settings
"""
import os
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
DATA_DIR = BASE_DIR / "data"
STRATEGIES_DIR = BASE_DIR / "config" / "strategies"

# NVIDIA API
NVIDIA_API_KEY = "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"
NVIDIA_BASE_URL = "https://integrate.api.nvidia.com/v1"

# Models
DEEPSEEK_MODEL = "deepseek-ai/deepseek-v3.2"
LLAMA_MODEL    = "nvidia/llama-3.3-nemotron-super-49b-v1.5"

# Binance
BINANCE_BASE_URL       = "https://api.binance.com"
BINANCE_TESTNET_URL    = "https://testnet.binance.vision"

# News
CRYPTOPANIC_BASE = "https://cryptopanic.com/api/v1/posts/"
NEWS_RSS_FEEDS = [
    "https://cointelegraph.com/rss",
    "https://coindesk.com/arc/outboundfeeds/rss/",
    "https://decrypt.co/feed",
]

# Top crypto pairs
TOP_CRYPTO_PAIRS = [
    "BTCUSDT", "ETHUSDT", "BNBUSDT", "SOLUSDT",
    "XRPUSDT", "ADAUSDT", "DOTUSDT", "DOGEUSDT",
    "AVAXUSDT", "MATICUSDT", "LINKUSDT", "UNIUSDT",
    "LTCUSDT", "ATOMUSDT", "NEARUSDT", "FTMUSDT",
]

# Strategy URLs (GitHub raw files)
STRATEGY_SOURCES = {
    "RSI_Strategy":     "https://raw.githubusercontent.com/freqtrade/freqtrade-strategies/main/user_data/strategies/berlinguyinca/README.md",
    "MACD_Strategy":    None,
    "BB_Strategy":      None,
    "EMA_Cross":        None,
    "ICT_Strategy":     None,
    "Scalping":         None,
}

# Risk defaults
DEFAULT_RISK_PERCENT   = 1.0   # % of balance per trade
DEFAULT_STOP_LOSS_PCT  = 2.0
DEFAULT_TAKE_PROFIT_PCT = 4.0

# Colors (Dark Theme)
COLORS = {
    "bg_dark":    "#0D1117",
    "bg_card":    "#161B22",
    "bg_input":   "#21262D",
    "accent1":    "#00FFB2",
    "accent2":    "#6366F1",
    "accent3":    "#F59E0B",
    "buy_green":  "#22C55E",
    "sell_red":   "#EF4444",
    "wait_yellow":"#F59E0B",
    "text_prim":  "#F0F6FC",
    "text_sec":   "#8B949E",
    "border":     "#30363D",
}

def load_user_config() -> dict:
    cfg_path = DATA_DIR / "user_config.json"
    if cfg_path.exists():
        with open(cfg_path, "r") as f:
            return json.load(f)
    return {}

def save_user_config(data: dict):
    DATA_DIR.mkdir(exist_ok=True)
    cfg_path = DATA_DIR / "user_config.json"
    with open(cfg_path, "w") as f:
        json.dump(data, f, indent=2)
