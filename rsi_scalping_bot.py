import pandas as pd
import pandas_ta as ta
import ccxt

# === CONFIG ===
symbol = 'XRP/USDT'
timeframe = '1h'
limit = 100

# === Initialize Bitrue ===
exchange = ccxt.bitrue({'enableRateLimit': True})

try:
    # === Fetch OHLCV data ===
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

    # === Add Indicators ===
    df['rsi'] = ta.rsi(df['close'], length=14)
    macd = ta.macd(df['close'])
    bbands = ta.bbands(df['close'])

    # === Merge all indicators ===
    df = pd.concat([df, macd, bbands], axis=1)

    # === Signal Logic ===
    def generate_signal(df):
        if df is None or df.empty or len(df) < 50:
            return "ERROR"

        last = df.iloc[-1]
        if (
            last['rsi'] < 30 and
            last['MACD_12_26_9'] > last['MACDs_12_26_9'] and
            last['close'] < last['BBL_20_2.0']
        ):
            return "BUY"
        elif (
            last['rsi'] > 70 and
            last['MACD_12_26_9'] < last['MACDs_12_26_9'] and
            last['close'] > last['BBU_20_2.0']
        ):
            return "SELL"
        else:
            return "HOLD"

    # === Run Signal Check ===
    signal = generate_signal(df)
    print(f"🔍 Trade Signal for {symbol}: {signal}")

except Exception as e:
    print(f"❌ Error fetching or analyzing data: {e}")
