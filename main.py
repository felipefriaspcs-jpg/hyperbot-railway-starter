import os
import ccxt
import time

API_KEY = os.getenv("BITRUE_API_KEY")
API_SECRET = os.getenv("BITRUE_API_SECRET")
TRADING_PAIRS = os.getenv("TRADING_PAIRS", "FLR/USDT,XRP/USDT").split(",")
TRADE_SIZE_PERCENT = float(os.getenv("TRADE_SIZE_PERCENT", 5))

exchange = ccxt.bitrue({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True,
})

def get_balance(symbol):
    balance = exchange.fetch_balance()
    return balance['total'].get(symbol, 0)

def analyze_rsi(symbol):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=100)
        closes = [candle[4] for candle in ohlcv]
        delta = [closes[i] - closes[i-1] for i in range(1, len(closes))]
        gain = sum(d for d in delta if d > 0) / 14
        loss = -sum(d for d in delta if d < 0) / 14
        rs = gain / loss if loss != 0 else 0
        rsi = 100 - (100 / (1 + rs))
        print(f"[{symbol}] RSI: {rsi:.2f}")

        if rsi < 30:
            print(f"[{symbol}] Signal: BUY")
            return "buy"
        elif rsi > 70:
            print(f"[{symbol}] Signal: SELL")
            return "sell"
        return None
    except Exception as e:
        print(f"[{symbol}] Error calculating RSI: {e}")
        return None

def place_order(symbol, side):
    base, quote = symbol.split("/")
    balance = get_balance(quote if side == "buy" else base)
    price = exchange.fetch_ticker(symbol)["last"]
    amount = (balance * (TRADE_SIZE_PERCENT / 100)) / price
    amount = float(exchange.amount_to_precision(symbol, amount))

    if amount == 0:
        print(f"[{symbol}] Skipped: Insufficient balance for {side} order.")
        return

    print(f"[{symbol}] Placing {side.upper()} order for {amount} at {price}")
    try:
        order = exchange.create_market_order(symbol, side, amount)
        print(f"[{symbol}] Order placed: {order['id']}")
    except Exception as e:
        print(f"[{symbol}] Error placing order: {e}")

def run_bot():
    while True:
        for symbol in TRADING_PAIRS:
            symbol = symbol.strip()
            signal = analyze_rsi(symbol)
            if signal:
                place_order(symbol, signal)
            time.sleep(3)
        print("🔁 Cycle complete. Sleeping 20s...\n")
        time.sleep(20)

if __name__ == "__main__":
    run_bot()
