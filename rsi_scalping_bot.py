import os
import ccxt
import pandas as pd
import pandas_ta as ta
from dotenv import load_dotenv

# === Load env vars ===
load_dotenv()
API_KEY = os.getenv("BITRUE_API_KEY")
API_SECRET = os.getenv("BITRUE_API_SECRET")

# === Trading Config ===
symbol = 'XRP/USDT:USDT'  # Unified Perpetual Futures pair
timeframes = ['1m', '15m', '30m']
limit = 100
leverage = 50
risk_pct = 0.05  # Use 5% of available capital
take_profit_pct = 0.03  # 3%
stop_loss_pct = 0.015   # 1.5%

# === Init Exchange ===
exchange = ccxt.bitrue({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True
})
exchange.options['defaultType'] = 'future'

# === Fetch + Merge Indicator Data ===
def fetch_data(timeframe):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
        df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df['rsi'] = ta.rsi(df['close'], length=14)
        macd = ta.macd(df['close'])
        bbands = ta.bbands(df['close'])
        df = pd.concat([df, macd, bbands], axis=1)
        return df
    except Exception as e:
        print(f"❌ Error fetching {timeframe} data: {e}")
        return None

# === Entry Signal Logic ===
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

# === Place Trade with SL/TP ===
def place_trade(signal, price):
    try:
        # Fetch balance & calculate trade size
        balance = exchange.fetch_balance({'type': 'future'})
        usdt = balance['total']['USDT']
        position_size = round(usdt * risk_pct, 2)
        exchange.set_leverage(leverage, symbol)

        # Calculate TP & SL
        if signal == "BUY":
            tp = round(price * (1 + take_profit_pct), 5)
            sl = round(price * (1 - stop_loss_pct), 5)
            exchange.create_market_buy_order(symbol, position_size)
            exchange.create_order(symbol, 'take_profit_market', 'sell', position_size, None, {
                'stopPrice': tp, 'reduceOnly': True
            })
            exchange.create_order(symbol, 'stop_market', 'sell', position_size, None, {
                'stopPrice': sl, 'reduceOnly': True
            })
            print(f"✅ LONG: Entry at {price}, TP at {tp}, SL at {sl}")

        elif signal == "SELL":
            tp = round(price * (1 - take_profit_pct), 5)
            sl = round(price * (1 + stop_loss_pct), 5)
            exchange.create_market_sell_order(symbol, position_size)
            exchange.create_order(symbol, 'take_profit_market', 'buy', position_size, None, {
                'stopPrice': tp, 'reduceOnly': True
            })
            exchange.create_order(symbol, 'stop_market', 'buy', position_size, None, {
                'stopPrice': sl, 'reduceOnly': True
            })
            print(f"✅ SHORT: Entry at {price}, TP at {tp}, SL at {sl}")
        else:
            print("⏸️ No trade — holding.")
    except Exception as e:
        print(f"🚨 Trade error: {e}")

# === Run Bot Per Timeframe ===
for tf in timeframes:
    print(f"\n⏱️ Checking {tf} timeframe...")
    df = fetch_data(tf)
    signal = generate_signal(df)

    if signal in ["BUY", "SELL"]:
        price = df.iloc[-1]['close']
        print(f"📊 Signal for {tf} = {signal} @ {price}")
        place_trade(signal, price)
    else:
        print(f"📉 Signal for {tf}: HOLD")
