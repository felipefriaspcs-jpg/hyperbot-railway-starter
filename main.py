import pandas as pd
import pandas_ta as ta
import ccxt
import time

# Trading configuration
SYMBOLS = [
    'XRP/USDT', 'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT', 'DOGE/USDT',
    'AVAX/USDT', 'LINK/USDT', 'SHIB/USDT', 'TON/USDT', 'UNI/USDT', 'LTC/USDT',
    'BCH/USDT', 'APT/USDT', 'DOT/USDT', 'OP/USDT', 'MATIC/USDT', 'FET/USDT',
    'SUI/USDT', 'ARB/USDT', 'PEPE/USDT'
]

TIMEFRAME = '1h'
LIMIT = 100
SLEEP_SECONDS = 30

# Initialize Bitrue exchange
exchange = ccxt.bitrue({'enableRateLimit': True})

def analyze_pair(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=LIMIT)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        df['rsi'] = ta.rsi(df['close'], length=14)
        macd = ta.macd(df['close'])
        bbands = ta.bbands(df['close'])

        df = pd.concat([df, macd, bbands], axis=1)
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
    except Exception as e:
        print(f"⚠️ Error analyzing {symbol}: {e}")
        return "ERROR"

# Main loop
while True:
    for symbol in SYMBOLS:
        signal = analyze_pair(symbol)
        print(f"[{symbol}] Signal: {signal}")

    print("\n🔁 Cycle complete. Sleeping 30s...\n")
    time.sleep(SLEEP_SECONDS)
def generate_signal(df):
    # Skip processing if we have too few candles or dataframe is empty
    if df is None or df.empty or len(df) < 50:
        return "ERROR"

    last = df.iloc[-1]
    try:
        if (
            last['rsi'] < 30
            and last['MACD_12_26_9'] > last['MACDs_12_26_9']
            and last['close'] < last['BBL_20_2.0']
        ):
            return "BUY"
        elif (
            last['rsi'] > 70
            and last['MACD_12_26_9'] < last['MACDs_12_26_9']
            and last['close'] > last['BBU_20_2.0']
        ):
            return "SELL"
        else:
            return "HOLD"
    except Exception:
        return "ERROR"
