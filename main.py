import pandas as pd
import pandas_ta as ta
import ccxt
import time

# === CONFIG ===
SYMBOLS = [
    'XRP/USDT', 'BTC/USDT', 'ETH/USDT', 'SOL/USDT', 'ADA/USDT', 'DOGE/USDT',
    'AVAX/USDT', 'LINK/USDT', 'SHIB/USDT', 'TON/USDT', 'UNI/USDT', 'LTC/USDT',
    'BCH/USDT', 'APT/USDT', 'DOT/USDT', 'OP/USDT', 'MATIC/USDT', 'FET/USDT',
    'SUI/USDT', 'ARB/USDT', 'PEPE/USDT'
]

TIMEFRAME = '1h'
LIMIT = 100
SLEEP_SECONDS = 30

# === EXCHANGE ===
exchange = ccxt.bitrue({'enableRateLimit': True})

# === ORDER FUNCTION ===
def place_order(symbol, side, price):
    try:
        balance = exchange.fetch_balance()
        quote_currency = symbol.split('/')[1]
        quote_available = balance[quote_currency]['free']
        amount_to_trade = (quote_available * 0.05) / price

        exchange.create_market_order(symbol, side, round(amount_to_trade, 4))
        print(f"✅ {side.upper()} order placed for {symbol} — Amount: {round(amount_to_trade, 4)} at price {price}")
    except Exception as e:
        print(f"❌ Failed to place {side} order for {symbol}: {e}")

# === STRATEGY LOGIC ===
def analyze_pair(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, TIMEFRAME, limit=LIMIT)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

        df['rsi'] = ta.rsi(df['close'], length=14)
        macd = ta.macd(df['close'])
        bbands = ta.bbands(df['close'])

        df = pd.concat([df, macd, bbands], axis=1)

        if df.empty or len(df) < 50:
            return "ERROR"

        last = df.iloc[-1]
        price = last['close']

        if (
            last['rsi'] < 30 and
            last['MACD_12_26_9'] > last['MACDs_12_26_9'] and
            last['close'] < last['BBL_20_2.0']
        ):
            place_order(symbol, 'buy', price)
            return "BUY"
        elif (
            last['rsi'] > 70 and
            last['MACD_12_26_9'] < last['MACDs_12_26_9'] and
            last['close'] > last['BBU_20_2.0']
        ):
            place_order(symbol, 'sell', price)
            return "SELL"
        else:
            return "HOLD"

    except Exception as e:
        print(f"⚠️ Error analyzing {symbol}: {e}")
        return "ERROR"

# === MAIN LOOP ===
while True:
    for symbol in SYMBOLS:
        signal = analyze_pair(symbol)
        print(f"[{symbol}] Signal: {signal}")

    print("\n🔁 Cycle complete. Sleeping 30s...\n")
    time.sleep(SLEEP_SECONDS)
