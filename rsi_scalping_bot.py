import os
import ccxt
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands

# === Exchange init ===
EXCHANGE = ccxt.bitrue({
    'apiKey': os.getenv("BITRUE_API_KEY"),
    'secret': os.getenv("BITRUE_SECRET_KEY"),
    'enableRateLimit': True,
    'options': {
        'defaultType': 'swap',
        'exchangeType': 'perpetual',
        'enableUnifiedAccount': True,
    }
})

SYMBOL = os.getenv("SYMBOL", "XRP/USDT:USDT")
TIMEFRAME = "1m"

def fetch_ohlcv(symbol):
    """Get recent candles from Bitrue."""
    ohlcv = EXCHANGE.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=100)
    df = pd.DataFrame(ohlcv, columns=["ts","open","high","low","close","volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms")
    return df

def add_indicators(df):
    """Add RSI, MACD, Bollinger Bands to dataframe."""
    rsi = RSIIndicator(close=df["close"], window=14)
    macd = MACD(close=df["close"], window_slow=26, window_fast=12, window_sign=9)
    bb = BollingerBands(close=df["close"], window=14, window_dev=1.5)

    df["rsi"] = rsi.rsi()
    df["macd"] = macd.macd()
    df["signal"] = macd.macd_signal()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_upper"] = bb.bollinger_hband()
    return df

def generate_signal(df):
    """Return LONG, SHORT, or HOLD."""
    last = df.iloc[-1]
    if last["rsi"] < 30 and last["macd"] > last["signal"] and last["close"] < last["bb_lower"]:
        return "LONG"
    elif last["rsi"] > 70 and last["macd"] < last["signal"] and last["close"] > last["bb_upper"]:
        return "SHORT"
    return "HOLD"

def run_once():
    """One cycle: fetch data, compute indicators, print signal."""
    try:
        df = fetch_ohlcv(SYMBOL)
        df = add_indicators(df)
        signal = generate_signal(df)
        print(f"[{SYMBOL}] Signal: {signal}")
        return signal
    except Exception as e:
        print(f"❌ Error in run_once: {e}")
        return "ERROR"
