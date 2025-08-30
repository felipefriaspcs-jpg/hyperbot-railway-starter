import pandas as pd
import pandas_ta as ta
import ccxt
import os

# === INIT EXCHANGE (with unified account + leverage support) ===
EXCHANGE = ccxt.bitrue({
    'apiKey': os.getenv("BITRUE_API_KEY"),
    'secret': os.getenv("BITRUE_SECRET_KEY"),
    'enableRateLimit': True,
    'options': {
        'defaultType': 'swap',  # enable perpetual futures
        'exchangeType': 'perpetual',
        'enableUnifiedAccount': True,
    }
})

# === SETTINGS ===
SYMBOLS = [
    "XRP/USDT", "BTC/USDT", "ETH/USDT", "ADA/USDT",
    "SOL/USDT", "MATIC/USDT", "DOGE/USDT"
]

TIMEFRAME = "1m"

# === FETCH OHLCV ===
def fetch_ohlcv(symbol):
    try:
        ohlcv = EXCHANGE.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=100)
        df = pd.DataFrame(ohlcv, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df["timestamp"] = pd.to_datetime(df["timestamp"], unit="ms")
        return df
    except Exception as e:
        print(f"❌ Error fetching {symbol}: {e}")
        return None

# === INDICATORS ===
def add_indicators(df):
    df["rsi"] = ta.rsi(df["close"], length=14)
    macd = ta.macd(df["close"])
    df["macd"] = macd["MACD_12_26_9"]
    df["signal"] = macd["MACDs_12_26_9"]
    bb = ta.bbands(df["close"], length=14, std=1.5)
    df["bb_lower"] = bb["BBL_14_1.5"]
    df["bb_upper"] = bb["BBU_14_1.5"]
    return df

# === SIGNAL STRATEGY ===
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

# === EXECUTE TRADE (real orders with leverage) ===
def execute_trade(symbol, signal):
    try:
        price = EXCHANGE.fetch_ticker(symbol)['last']
        balance = EXCHANGE.fetch_balance()
        usdt = balance['total']['USDT']
        amount = (usdt * 0.05) / price  # Use 5% of balance
        amount = EXCHANGE.amount_to_precision(symbol, amount)

        EXCHANGE.set_leverage(10, symbol)

        if signal == "LONG":
            EXCHANGE.create_market_buy_order(symbol, amount)
            print(f"✅ LONG order placed on {symbol} — {amount} at {price}")
        elif signal == "SHORT":
            EXCHANGE.create_market_sell_order(symbol, amount)
            print(f"✅ SHORT order placed on {symbol} — {amount} at {price}")
    except Exception as e:
        print(f"❌ Trade error on {symbol}: {e}")

# === MAIN BOT FUNCTION ===
def run_bot():
    for symbol in SYMBOLS:
        df = fetch_ohlcv(symbol)
        if df is None or df.empty:
            print(f"[{symbol}] Signal: ERROR")
            continue

        df = add_indicators(df)
        signal = generate_signal(df)
        print(f"[{symbol}] Signal: {signal}")

        if signal in ["LONG", "SHORT"]:
            execute_trade(symbol, signal)
