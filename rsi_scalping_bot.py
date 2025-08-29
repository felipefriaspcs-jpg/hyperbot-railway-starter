import pandas as pd
import pandas_ta as ta
import ccxt

# Initialize Bitrue exchange
exchange = ccxt.bitrue({
    'enableRateLimit': True,
})

# Load candlestick data
symbol = 'XRP/USDT'
timeframe = '1h'
limit = 100
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)

# Convert to DataFrame
df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

# Calculate indicators
df['rsi'] = ta.rsi(df['close'], length=14)
macd = ta.macd(df['close'])
bbands = ta.bbands(df['close'])

# Merge indicators
df = pd.concat([df, macd, bbands], axis=1)

# Define signal logic
def generate_signal(df):
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

signal = generate_signal(df)
print(f"Trade Signal: {signal}")
