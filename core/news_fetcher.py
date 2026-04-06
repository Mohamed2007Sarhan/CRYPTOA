"""
News Fetcher — Multi-source: CryptoPanic, RSS, Reddit, Google News
"""
import time
import threading
import requests
import feedparser
from typing import List, Dict, Optional, Callable
from config.settings import NEWS_RSS_FEEDS


# Extended RSS feed list
ALL_RSS_FEEDS = [
    # Crypto-specific
    "https://cointelegraph.com/rss",
    "https://decrypt.co/feed",
    "https://cryptonews.com/news/feed/",
    "https://bitcoinmagazine.com/.rss/full/",
    "https://www.coindesk.com/arc/outboundfeeds/rss/",
    "https://dailyhodl.com/feed/",
    "https://cryptopotato.com/feed/",
    "https://beincrypto.com/feed/",
    "https://cryptobriefing.com/feed/",
    "https://ambcrypto.com/feed/",
    # Financial
    "https://feeds.bloomberg.com/markets/news.rss",
    "https://seekingalpha.com/feed.xml",
]


class NewsFetcher:

    def __init__(self):
        self.session = requests.Session()
        self.session.headers["User-Agent"] = (
            "Mozilla/5.0 (CryptoAI Trading Bot; compatible; research)"
        )
        self._cache: Dict[str, dict] = {}
        self._cache_ttl = 240   # 4 minutes

    @staticmethod
    def _extract_base_asset(symbol: str) -> str:
        """Extract base asset from trading pair like BTCUSDT -> BTC."""
        if not symbol:
            return ""
        s = symbol.upper().strip()
        quote_suffixes = ("USDT", "USDC", "BUSD", "FDUSD", "BTC", "ETH", "BNB")
        for q in quote_suffixes:
            if s.endswith(q) and len(s) > len(q):
                return s[:-len(q)]
        return s

    @staticmethod
    def _symbol_to_keywords(symbol: str) -> List[str]:
        base = NewsFetcher._extract_base_asset(symbol)
        name_map = {
            "BTC": ["bitcoin", "btc"],
            "ETH": ["ethereum", "eth"],
            "SOL": ["solana", "sol"],
            "XRP": ["ripple", "xrp"],
            "ADA": ["cardano", "ada"],
            "DOGE": ["dogecoin", "doge"],
            "BNB": ["binance coin", "bnb"],
            "DOT": ["polkadot", "dot"],
            "AVAX": ["avalanche", "avax"],
            "LINK": ["chainlink", "link"],
            "MATIC": ["polygon", "matic", "pol"],
            "SHIB": ["shiba", "shib", "shiba inu"],
        }
        keywords = [base.lower()]
        keywords.extend(name_map.get(base, []))
        return list(dict.fromkeys(keywords))

    # ── CryptoPanic ──────────────────────────────────────────────────────────

    def fetch_cryptopanic(self, symbol: str, limit: int = 30) -> List[dict]:
        base = symbol.replace("USDT", "").replace("BTC", "")
        try:
            # public endpoint (no auth)
            r = self.session.get(
                "https://cryptopanic.com/api/v1/posts/",
                params={"auth_token": "public", "currencies": base,
                        "kind": "news", "limit": limit},
                timeout=12,
            )
            if r.status_code == 200:
                articles = []
                for post in r.json().get("results", []):
                    articles.append({
                        "title":   post.get("title", ""),
                        "url":     post.get("url", ""),
                        "source":  post.get("source", {}).get("title", "CryptoPanic"),
                        "time":    post.get("published_at", "")[:16],
                        "votes_positive": post.get("votes", {}).get("positive", 0),
                        "votes_negative": post.get("votes", {}).get("negative", 0),
                        "impact":  post.get("votes", {}).get("important",  0),
                    })
                return articles
        except Exception as e:
            print(f"[News] CryptoPanic error: {e}")
        return []

    # ── RSS Feeds ─────────────────────────────────────────────────────────────

    def fetch_rss_all(self, keyword: str, max_articles: int = 40) -> List[dict]:
        articles = []
        kw = keyword.replace("USDT", "").replace("BTC", "").upper()
        kw_lower = kw.lower()

        # Map common symbols to names
        name_map = {
            "BTC": "bitcoin", "ETH": "ethereum", "SOL": "solana", 
            "XRP": "ripple", "ADA": "cardano", "DOGE": "dogecoin",
            "BNB": "binance", "DOT": "polkadot", "AVAX": "avalanche",
            "LINK": "chainlink", "MATIC": "polygon", "SHIB": "shiba"
        }
        kw_name = name_map.get(kw, kw_lower)

        for feed_url in ALL_RSS_FEEDS:
            try:
                feed    = feedparser.parse(feed_url)
                feed_title = feed.feed.get("title", feed_url.split("/")[2])
                for entry in feed.entries[:30]:
                    title   = entry.get("title", "")
                    summary = entry.get("summary", "")
                    # Strict relevance: only the exact coin symbol or name
                    relevant = (
                        kw_lower in title.lower().split()
                        or kw_name in title.lower()
                        or kw_name in summary.lower()
                    )
                    if relevant:
                        articles.append({
                            "title":   title,
                            "url":     entry.get("link", ""),
                            "source":  feed_title,
                            "time":    entry.get("published", "")[:16],
                            "summary": summary[:400],
                            "votes_positive": 0,
                            "votes_negative": 0,
                        })
                        if len(articles) >= max_articles:
                            return articles
            except Exception as e:
                pass   # skip bad feed silently
        return articles

    # ── Reddit (via RSS) ──────────────────────────────────────────────────────

    def fetch_reddit(self, symbol: str) -> List[dict]:
        base = symbol.replace("USDT", "").replace("BTC", "").upper()
        name_map = {
            "BTC": "Bitcoin", "ETH": "ethereum", "SOL": "solana", "DOGE": "dogecoin", "ADA": "cardano"
        }
        sub_name = name_map.get(base, base.lower())
        subreddits = [sub_name, "CryptoCurrency"] # Focus strictly on the coin and general crypto
        articles = []
        for sub in subreddits:
            try:
                r = self.session.get(
                    f"https://www.reddit.com/r/{sub}/hot.json",
                    params={"limit": 10},
                    headers={"User-Agent": "CryptoAI/1.0"},
                    timeout=10,
                )
                if r.status_code == 200:
                    for post in r.json().get("data", {}).get("children", []):
                        d = post.get("data", {})
                        title = d.get("title", "")
                        score = d.get("score", 0)
                        if score > 10:
                            articles.append({
                                "title":   title,
                                "url":     f"https://reddit.com{d.get('permalink','')}",
                                "source":  f"Reddit r/{sub}",
                                "time":    "",
                                "summary": d.get("selftext", "")[:300],
                                "votes_positive": score,
                                "votes_negative": 0,
                            })
            except Exception:
                pass
        return articles

    # ── Google News ───────────────────────────────────────────────────────────

    def fetch_google_news(self, symbol: str) -> List[dict]:
        base = symbol.replace("USDT", "")
        try:
            feed = feedparser.parse(
                f"https://news.google.com/rss/search?q={base}+crypto+price&hl=en-US&gl=US&ceid=US:en"
            )
            articles = []
            for entry in feed.entries[:15]:
                articles.append({
                    "title":   entry.get("title", ""),
                    "url":     entry.get("link", ""),
                    "source":  "Google News",
                    "time":    entry.get("published", "")[:16],
                    "summary": "",
                    "votes_positive": 0,
                    "votes_negative": 0,
                })
            return articles
        except Exception as e:
            print(f"[News] Google News error: {e}")
        return []

    # ── Blockchain.com Explorer News ─────────────────────────────────────────

    def fetch_blockchain_explorer_news(self, symbol: str, max_articles: int = 35) -> List[dict]:
        base = self._extract_base_asset(symbol)
        if not base:
            return []
        try:
            r = self.session.get(
                "https://api.blockchain.info/news/articles",
                params={"limit": max_articles, "assets": base},
                timeout=12,
            )
            if r.status_code != 200:
                return []

            payload = r.json()
            raw_articles = payload.get("articles", []) if isinstance(payload, dict) else []

            articles = []
            for item in raw_articles[:max_articles]:
                upstream_source = item.get("source", "Unknown")
                assets = item.get("assets", [])
                assets_text = ", ".join(assets[:5]) if isinstance(assets, list) else ""
                articles.append({
                    "title": item.get("title", ""),
                    "url": item.get("link", ""),
                    "source": f"Blockchain API/{upstream_source}",
                    "time": item.get("date", "")[:16],
                    "summary": assets_text,
                    "votes_positive": 0,
                    "votes_negative": 0,
                })
            return articles
        except Exception as e:
            print(f"[News] Blockchain.com news error: {e}")
            return []

    # ── Unified Fetch ─────────────────────────────────────────────────────────

    def get_news_for_symbol(self, symbol: str) -> dict:
        now = time.time()
        if symbol in self._cache:
            cached = self._cache[symbol]
            if now - cached["time"] < self._cache_ttl:
                return cached["data"]

        all_articles = []

        # CryptoPanic (most targeted)
        cp = self.fetch_cryptopanic(symbol, limit=30)
        all_articles.extend(cp)

        # Blockchain.com direct API (asset-targeted)
        blockchain = self.fetch_blockchain_explorer_news(symbol, max_articles=35)
        all_articles.extend(blockchain)

        # RSS from crypto news sites
        rss = self.fetch_rss_all(symbol, max_articles=40)
        all_articles.extend(rss)

        # Reddit
        reddit = self.fetch_reddit(symbol)
        all_articles.extend(reddit)

        # Google News
        google = self.fetch_google_news(symbol)
        all_articles.extend(google)

        # Deduplicate by title
        seen = set()
        unique = []
        for a in all_articles:
            t = a["title"][:60]
            if t not in seen:
                seen.add(t)
                unique.append(a)

        # Sentiment from votes
        pos = sum(a.get("votes_positive", 0) for a in unique)
        neg = sum(a.get("votes_negative", 0) for a in unique)
        total_votes = pos + neg
        sentiment_score = ((pos - neg) / total_votes * 100) if total_votes > 0 else 0

        # Build full text for AI
        text_parts = []
        for a in unique[:35]:
            src   = a.get("source", "")
            title = a.get("title", "")
            summ  = a.get("summary", "")
            line  = f"[{src}] {title}"
            if summ:
                line += f" — {summ[:200]}"
            text_parts.append(line)

        full_text = "\n\n".join(text_parts) or "No news available."

        result = {
            "articles":        unique,
            "text":            full_text,
            "count":           len(unique),
            "sentiment_score": round(sentiment_score, 1),
            "sources": {
                "cryptopanic": len(cp),
                "rss":         len(rss),
                "reddit":      len(reddit),
                "google":      len(google),
                "blockchain":  len(blockchain),
            },
        }
        self._cache[symbol] = {"time": now, "data": result}
        return result

    def get_news_async(self, symbol: str, on_done: Callable[[dict], None]):
        def _w():
            on_done(self.get_news_for_symbol(symbol))
        threading.Thread(target=_w, daemon=True).start()
