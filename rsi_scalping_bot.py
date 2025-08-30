import pandas as pd
import pandas_ta as ta
import ccxt
import os

# Load env vars or hardcode if testing
EXCHANGE = ccxt.bitrue({
    'apiKey': os.getenv("BITRUE_API_KEY"),
    'secret': os.getenv("BITRUE_SECRET_KEY"),
    'enableRateLimit': True,
})

SYMBOLS = [
    "XRP/USDT", "BTC/USDT", "ETH/USDT", "ADA/USDT",
    "SOL/USDT", "MATIC/USDT", "DOGE/USDT"
]

TIMEFRAME = "1m"  # You can also run additional timeframes in parallel

def fetch_ohlcv(symbol):
    try:
        ohlcv = EXCHANGE.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=100)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df
    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return None

def add_indicators(df):
    df["rsi"] = ta.rsi(df["close"], length=14)
    macd = ta.macd(df["close"])
    df["macd"] = macd["MACD_12_26_9"]
    df["signal"] = macd["MACDs_12_26_9"]
    bb = ta.bbands(df["close"], length=14, std=1.5)
    df["bb_lower"] = bb["BBL_14_1.5"]
    df["bb_upper"] = bb["BBU_14_1.5"]
    return df

def generate_signal(df):
    last = df.iloc[-1]

    if (
        last["rsi"] < 30 and
        last["macd"] > last["signal"] and
        last["close"] < last["bb_lower"]
    ):
        return "LONG"

    elif (
        last["rsi"] > 70 and
        last["macd"] < last["signal"] and
        last["close"] > last["bb_upper"]
    ):
        return "SHORT"

    return "HOLD"

def run_bot():
    for symbol in SYMBOLS:
        df = fetch_ohlcv(symbol)
        if df is None or df.empty:
            print(f"[{symbol}] Signal: ERROR")
            continue

        df = add_indicators(df)
        signal = generate_signal(df)
        print(f"[{symbol}] Signal: {signal}")
