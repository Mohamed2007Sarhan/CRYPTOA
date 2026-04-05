"""
Market Data — بيانات شاملة: Binance + Fear/Greed + CoinGecko + OrderBook
"""
import time
import requests
import pandas as pd
from typing import Optional, Dict, List
from config.settings import BINANCE_BASE_URL


class MarketData:
    BASE = BINANCE_BASE_URL

    def __init__(self, api_key: str = "", api_secret: str = "", testnet: bool = False):
        self.api_key    = api_key
        self.api_secret = api_secret
        self.testnet    = testnet
        if testnet:
            self.BASE = "https://testnet.binance.vision"
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (CryptoAI Trading Bot)",
        })
        if api_key:
            self.session.headers["X-MBX-APIKEY"] = api_key

    # ── Binance Public ─────────────────────────────────────────────────────────

    def get_ticker(self, symbol: str) -> dict:
        r = self.session.get(f"{self.BASE}/api/v3/ticker/24hr",
                             params={"symbol": symbol}, timeout=10)
        r.raise_for_status()
        return r.json()

    def get_price(self, symbol: str) -> float:
        r = self.session.get(f"{self.BASE}/api/v3/ticker/price",
                             params={"symbol": symbol}, timeout=10)
        r.raise_for_status()
        return float(r.json()["price"])

    def get_klines(self, symbol: str, interval: str = "1h", limit: int = 300) -> pd.DataFrame:
        r = self.session.get(
            f"{self.BASE}/api/v3/klines",
            params={"symbol": symbol, "interval": interval, "limit": limit},
            timeout=15,
        )
        r.raise_for_status()
        raw = r.json()
        df = pd.DataFrame(raw, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades",
            "taker_buy_base", "taker_buy_quote", "ignore",
        ])
        for col in ["open", "high", "low", "close", "volume", "quote_volume"]:
            df[col] = df[col].astype(float)
        df["open_time"] = pd.to_datetime(df["open_time"], unit="ms")
        df.set_index("open_time", inplace=True)
        return df

    def get_multi_timeframe(self, symbol: str) -> Dict[str, pd.DataFrame]:
        """جلب البيانات على أطر زمنية متعددة لتشمل الأساسي والمتقدم"""
        frames = {}
        for interval in ["15m", "1h", "4h", "1d"]:
            try:
                frames[interval] = self.get_klines(symbol, interval, limit=1000)
            except Exception as e:
                print(f"⚠️ Failed to load {interval}: {e}")
        return frames

    def get_order_book(self, symbol: str, limit: int = 20) -> dict:
        r = self.session.get(
            f"{self.BASE}/api/v3/depth",
            params={"symbol": symbol, "limit": limit},
            timeout=10,
        )
        r.raise_for_status()
        data = r.json()
        bids = [[float(p), float(q)] for p, q in data.get("bids", [])]
        asks = [[float(p), float(q)] for p, q in data.get("asks", [])]
        bid_vol = sum(q for _, q in bids)
        ask_vol = sum(q for _, q in asks)
        pressure = round((bid_vol / (bid_vol + ask_vol)) * 100, 1) if (bid_vol + ask_vol) > 0 else 50
        return {
            "bids": bids[:5],
            "asks": asks[:5],
            "bid_volume": round(bid_vol, 2),
            "ask_volume": round(ask_vol, 2),
            "buy_pressure": pressure,
            "sell_pressure": round(100 - pressure, 1),
        }

    def get_recent_trades(self, symbol: str, limit: int = 50) -> dict:
        """تحليل الصفقات الأخيرة لمعرفة الاتجاه"""
        r = self.session.get(
            f"{self.BASE}/api/v3/trades",
            params={"symbol": symbol, "limit": limit},
            timeout=10,
        )
        r.raise_for_status()
        trades = r.json()
        buy_vol  = sum(float(t["qty"]) for t in trades if not t["isBuyerMaker"])
        sell_vol = sum(float(t["qty"]) for t in trades if t["isBuyerMaker"])
        total    = buy_vol + sell_vol
        return {
            "buy_volume":  round(buy_vol, 4),
            "sell_volume": round(sell_vol, 4),
            "buy_ratio":   round((buy_vol / total) * 100, 1) if total > 0 else 50,
        }

    def get_top_movers(self, limit: int = 10) -> List[dict]:
        r = self.session.get(f"{self.BASE}/api/v3/ticker/24hr", timeout=15)
        r.raise_for_status()
        usdt = [t for t in r.json() if t["symbol"].endswith("USDT")]
        usdt.sort(key=lambda x: abs(float(x["priceChangePercent"])), reverse=True)
        return usdt[:limit]

    def get_all_usdt_pairs(self) -> List[str]:
        r = self.session.get(f"{self.BASE}/api/v3/exchangeInfo", timeout=15)
        r.raise_for_status()
        return [
            s["symbol"] for s in r.json()["symbols"]
            if s["symbol"].endswith("USDT") and s["status"] == "TRADING"
        ]

    # ── Fear & Greed Index ─────────────────────────────────────────────────────

    def get_fear_greed(self) -> dict:
        """مؤشر الخوف والطمع من Alternative.me"""
        try:
            r = requests.get(
                "https://api.alternative.me/fng/?limit=2",
                timeout=10,
            )
            if r.status_code == 200:
                data = r.json()
                results = data.get("data", [{}])
                current = results[0]
                prev    = results[1] if len(results) > 1 else {}
                val  = int(current.get("value", 50))
                prev_val = int(prev.get("value", 50))
                classification = current.get("value_classification", "Neutral")
                arabic_map = {
                    "Extreme Fear":  "Extreme Fear 😱",
                    "Fear":          "Fear 😨",
                    "Neutral":       "Neutral ⚖️",
                    "Greed":         "Greed 😏",
                    "Extreme Greed": "Extreme Greed 🤑",
                }
                return {
                    "value":          val,
                    "prev_value":     prev_val,
                    "classification": arabic_map.get(classification, classification),
                    "trend":          "Rising" if val > prev_val else ("Falling" if val < prev_val else "Flat"),
                    "signal":         "BUY" if val < 25 else ("SELL" if val > 75 else "HOLD"),
                }
        except Exception as e:
            print(f"⚠️ Fear & Greed error: {e}")
        return {"value": 50, "classification": "Neutral ⚖️", "signal": "HOLD", "prev_value": 50, "trend": "Flat"}

    # ── CoinGecko Data ─────────────────────────────────────────────────────────

    def get_coingecko_data(self, symbol: str) -> dict:
        """بيانات إضافية من CoinGecko: market cap، rank، supply"""
        try:
            # تحويل الرمز
            coin_id_map = {
                "BTC": "bitcoin", "ETH": "ethereum", "BNB": "binancecoin",
                "SOL": "solana",  "XRP": "ripple",   "ADA": "cardano",
                "DOT": "polkadot","DOGE": "dogecoin", "AVAX": "avalanche-2",
                "LINK": "chainlink", "MATIC": "matic-network", "UNI": "uniswap",
                "LTC": "litecoin", "ATOM": "cosmos",  "NEAR": "near",
            }
            base = symbol.replace("USDT", "").replace("BTC", "")
            coin_id = coin_id_map.get(base, base.lower())

            r = requests.get(
                f"https://api.coingecko.com/api/v3/coins/{coin_id}",
                params={"localization": "false", "tickers": "false",
                        "market_data": "true", "community_data": "false"},
                timeout=12,
            )
            if r.status_code == 200:
                d = r.json()
                md = d.get("market_data", {})
                return {
                    "market_cap_usd":   md.get("market_cap", {}).get("usd", 0),
                    "market_cap_rank":  d.get("market_cap_rank", 0),
                    "total_volume_usd": md.get("total_volume", {}).get("usd", 0),
                    "price_change_7d":  round(md.get("price_change_percentage_7d", 0), 2),
                    "price_change_14d": round(md.get("price_change_percentage_14d", 0), 2),
                    "price_change_30d": round(md.get("price_change_percentage_30d", 0), 2),
                    "ath":             md.get("ath", {}).get("usd", 0),
                    "ath_change_pct":  round(md.get("ath_change_percentage", {}).get("usd", 0), 2),
                    "circulating_supply": md.get("circulating_supply", 0),
                    "description":     d.get("description", {}).get("en", "")[:500],
                }
        except Exception as e:
            print(f"⚠️ CoinGecko error: {e}")
        return {}

    def get_global_market(self) -> dict:
        """بيانات السوق العالمي: Bitcoin Dominance، Total Market Cap"""
        try:
            r = requests.get("https://api.coingecko.com/api/v3/global", timeout=10)
            if r.status_code == 200:
                d = r.json().get("data", {})
                return {
                    "btc_dominance":       round(d.get("market_cap_percentage", {}).get("btc", 0), 1),
                    "eth_dominance":       round(d.get("market_cap_percentage", {}).get("eth", 0), 1),
                    "total_market_cap":    d.get("total_market_cap", {}).get("usd", 0),
                    "total_volume_24h":    d.get("total_volume", {}).get("usd", 0),
                    "market_cap_change_24h": round(d.get("market_cap_change_percentage_24h_usd", 0), 2),
                    "active_cryptos":      d.get("active_cryptocurrencies", 0),
                }
        except Exception as e:
            print(f"⚠️ Global market error: {e}")
        return {}

    # ── Binance Account (needs keys) ──────────────────────────────────────────

    def get_account(self) -> dict:
        import hmac, hashlib
        ts     = int(time.time() * 1000)
        params = f"timestamp={ts}"
        sig    = hmac.new(self.api_secret.encode(), params.encode(), hashlib.sha256).hexdigest()
        r = self.session.get(
            f"{self.BASE}/api/v3/account",
            params={"timestamp": ts, "signature": sig}, timeout=10,
        )
        r.raise_for_status()
        return r.json()

    def place_order(self, symbol: str, side: str, quantity: float,
                    order_type: str = "MARKET") -> dict:
        import hmac, hashlib
        ts     = int(time.time() * 1000)
        params = {
            "symbol": symbol, "side": side, "type": order_type,
            "quantity": f"{quantity:.6f}", "timestamp": ts,
        }
        query = "&".join(f"{k}={v}" for k, v in params.items())
        sig   = hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        params["signature"] = sig
        r = self.session.post(f"{self.BASE}/api/v3/order", params=params, timeout=10)
        r.raise_for_status()
        return r.json()

    def get_open_orders(self, symbol: str = "") -> list:
        import hmac, hashlib
        ts = int(time.time() * 1000)
        p  = {"timestamp": ts}
        if symbol:
            p["symbol"] = symbol
        query = "&".join(f"{k}={v}" for k, v in p.items())
        sig   = hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        p["signature"] = sig
        r = self.session.get(f"{self.BASE}/api/v3/openOrders", params=p, timeout=10)
        r.raise_for_status()
        return r.json()

    def cancel_order(self, symbol: str, order_id: int) -> dict:
        import hmac, hashlib
        ts = int(time.time() * 1000)
        p  = {"symbol": symbol, "orderId": order_id, "timestamp": ts}
        query = "&".join(f"{k}={v}" for k, v in p.items())
        sig   = hmac.new(self.api_secret.encode(), query.encode(), hashlib.sha256).hexdigest()
        p["signature"] = sig
        r = self.session.delete(f"{self.BASE}/api/v3/order", params=p, timeout=10)
        r.raise_for_status()
        return r.json()
