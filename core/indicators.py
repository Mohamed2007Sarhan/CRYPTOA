"""
Technical Indicators — حساب المؤشرات الفنية
"""
import pandas as pd
import numpy as np
from typing import Dict, Any


def compute_rsi(series: pd.Series, period: int = 14) -> pd.Series:
    delta = series.diff()
    gain  = delta.clip(lower=0)
    loss  = -delta.clip(upper=0)
    avg_gain = gain.ewm(com=period - 1, min_periods=period).mean()
    avg_loss = loss.ewm(com=period - 1, min_periods=period).mean()
    rs  = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def compute_macd(series: pd.Series,
                 fast: int = 12, slow: int = 26, signal: int = 9):
    ema_fast   = series.ewm(span=fast, adjust=False).mean()
    ema_slow   = series.ewm(span=slow, adjust=False).mean()
    macd_line  = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram  = macd_line - signal_line
    return macd_line, signal_line, histogram


def compute_bollinger_bands(series: pd.Series, period: int = 20, std_dev: float = 2.0):
    sma    = series.rolling(period).mean()
    std    = series.rolling(period).std()
    upper  = sma + std_dev * std
    lower  = sma - std_dev * std
    return upper, sma, lower


def compute_ema(series: pd.Series, period: int) -> pd.Series:
    return series.ewm(span=period, adjust=False).mean()


def compute_stochastic(high: pd.Series, low: pd.Series, close: pd.Series,
                        k_period: int = 14, d_period: int = 3):
    lowest_low   = low.rolling(k_period).min()
    highest_high = high.rolling(k_period).max()
    k = 100 * (close - lowest_low) / (highest_high - lowest_low)
    d = k.rolling(d_period).mean()
    return k, d


def compute_atr(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14) -> pd.Series:
    tr = pd.concat([
        high - low,
        (high - close.shift()).abs(),
        (low  - close.shift()).abs(),
    ], axis=1).max(axis=1)
    return tr.ewm(com=period - 1, min_periods=period).mean()


def compute_vwap(df: pd.DataFrame) -> pd.Series:
    tp = (df["high"] + df["low"] + df["close"]) / 3
    return (tp * df["volume"]).cumsum() / df["volume"].cumsum()


def get_candle_pattern(df: pd.DataFrame) -> str:
    """تحديد نمط آخر شمعة"""
    if len(df) < 3:
        return "Insufficient"
    last  = df.iloc[-1]
    prev  = df.iloc[-2]
    body  = abs(last["close"] - last["open"])
    total = last["high"] - last["low"]
    if total == 0:
        return "Neutral"
    body_ratio = body / total

    # Doji
    if body_ratio < 0.1:
        return "Doji - Indecision"
    # Hammer
    lower_shadow = min(last["open"], last["close"]) - last["low"]
    upper_shadow = last["high"] - max(last["open"], last["close"])
    if lower_shadow > 2 * body and upper_shadow < body * 0.5:
        return "Hammer - Bullish"
    # Shooting Star
    if upper_shadow > 2 * body and lower_shadow < body * 0.5:
        return "Shooting Star - Bearish"
    # Bullish Engulfing
    if (last["close"] > last["open"] and prev["close"] < prev["open"]
            and last["open"] < prev["close"] and last["close"] > prev["open"]):
        return "Bullish Engulfing"
    # Bearish Engulfing
    if (last["close"] < last["open"] and prev["close"] > prev["open"]
            and last["open"] > prev["close"] and last["close"] < prev["open"]):
        return "Bearish Engulfing"
    if last["close"] > last["open"]:
        return "Bullish Candle"
    return "Bearish Candle"


def compute_all_indicators(df: pd.DataFrame) -> Dict[str, Any]:
    """
    يحسب جميع المؤشرات ويرجع dict جاهز للـ AI prompt
    """
    c = df["close"]
    h = df["high"]
    l = df["low"]
    v = df["volume"]

    rsi = compute_rsi(c)
    macd_line, macd_signal, macd_hist = compute_macd(c)
    bb_upper, bb_mid, bb_lower = compute_bollinger_bands(c)
    ema20 = compute_ema(c, 20)
    ema50 = compute_ema(c, 50)
    ema200 = compute_ema(c, 200)
    stoch_k, stoch_d = compute_stochastic(h, l, c)
    atr = compute_atr(h, l, c)
    
    df_rf = compute_range_filter(df, src_col='close')

    def last(s):
        val = s.iloc[-1] if len(s) > 0 else None
        if val is None or (isinstance(val, float) and np.isnan(val)):
            return None
        return round(float(val), 4)

    price = last(c)
    change_pct = round(((c.iloc[-1] - c.iloc[-2]) / c.iloc[-2]) * 100, 2) if len(c) > 1 else 0

    return {
        "price":         price,
        "change_24h":    change_pct,
        "volume_24h":    round(float(v.sum()), 2),
        "rsi":           last(rsi),
        "macd":          last(macd_line),
        "macd_signal":   last(macd_signal),
        "macd_hist":     last(macd_hist),
        "bb_upper":      last(bb_upper),
        "bb_mid":        last(bb_mid),
        "bb_lower":      last(bb_lower),
        "ema20":         last(ema20),
        "ema50":         last(ema50),
        "ema200":        last(ema200),
        "stoch_k":       last(stoch_k),
        "stoch_d":       last(stoch_d),
        "atr":           last(atr),
        "candle_pattern": get_candle_pattern(df),
        "rf_buy":        bool(df_rf['buy_signal'].iloc[-1]) if len(df_rf) > 0 else False,
        "rf_sell":       bool(df_rf['sell_signal'].iloc[-1]) if len(df_rf) > 0 else False,
    }


def compute_range_filter(df: pd.DataFrame, src_col: str = 'close', rng_per: int = 20, rng_qty: float = 3.5) -> pd.DataFrame:
    """Range Filter - B&S Signals (TradingView)"""
    if len(df) == 0:
        return df

    x = df[src_col]
    diff = x.diff().abs()
    
    # avrng = ema(abs(x - x[1]), n)
    avrng = diff.ewm(span=rng_per, adjust=False).mean()
    
    # wper = (n*2) - 1
    wper = (rng_per * 2) - 1
    
    # AC = ema(avrng, wper)*qty
    rng = avrng.ewm(span=wper, adjust=False).mean() * rng_qty
    
    rfilt = np.zeros(len(x))
    
    rfilt[0] = x.iloc[0]
    
    for i in range(1, len(x)):
        rfilt_1 = rfilt[i-1]
        rng_i = rng.iloc[i]
        x_i = x.iloc[i]

        val = rfilt_1
        if pd.isna(rng_i):
            pass
        elif x_i - rng_i > rfilt_1:
            val = x_i - rng_i
        elif x_i + rng_i < rfilt_1:
            val = x_i + rng_i
            
        rfilt[i] = val
        
    res = df.copy()
    res['filt'] = rfilt
    res['h_band'] = rfilt + rng
    res['l_band'] = rfilt - rng
    
    fdir = np.zeros(len(x))
    for i in range(1, len(x)):
        if rfilt[i] > rfilt[i-1]:
            fdir[i] = 1
        elif rfilt[i] < rfilt[i-1]:
            fdir[i] = -1
        else:
            fdir[i] = fdir[i-1]
            
    upward = (pd.Series(fdir, index=x.index) == 1).astype(int)
    downward = (pd.Series(fdir, index=x.index) == -1).astype(int)
    
    long_cond = ((x > res['filt']) & (x > x.shift(1)) & (upward > 0)) | \
                ((x > res['filt']) & (x < x.shift(1)) & (upward > 0))
                
    short_cond = ((x < res['filt']) & (x < x.shift(1)) & (downward > 0)) | \
                 ((x < res['filt']) & (x > x.shift(1)) & (downward > 0))
    
    cond_ini = np.zeros(len(x))
    for i in range(1, len(x)):
        if long_cond.iloc[i]:
            cond_ini[i] = 1
        elif short_cond.iloc[i]:
            cond_ini[i] = -1
        else:
            cond_ini[i] = cond_ini[i-1]
            
    cond_ini_series = pd.Series(cond_ini, index=x.index)
    res['buy_signal'] = long_cond & (cond_ini_series.shift(1) == -1)
    res['sell_signal'] = short_cond & (cond_ini_series.shift(1) == 1)
    
    return res
