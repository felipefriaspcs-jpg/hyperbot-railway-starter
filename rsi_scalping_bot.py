import ccxt
import time
import requests
import os
from datetime import datetime

# Configuration (use environment variables if deploying on Railway)
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TRADE_AMOUNT_PERCENTAGE = float(os.getenv("TRADE_AMOUNT_PERCENTAGE", 0.05))
STOP_LOSS_PERCENT = float(os.getenv("STOP_LOSS_PERCENT", 0.03))
TAKE_PROFIT_PERCENT = float(os.getenv("TAKE_PROFIT_PERCENT", 0.06))
MIN_VOLUME_USDT = float(os.getenv("MIN_VOLUME_USDT", 10000))

# Initialize Exchange (Bitrue uses ccxt bybit/okx interface)
exchange = ccxt.bitrue({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True
})

# -------------------
# Dynamic Pair Fetching
# -------------------
def get_liquid_usdt_pairs(min_volume_usdt=10000):
    url = "https://www.bitrue.com/api/v1/ticker/24hr"
    response = requests.get(url)
    pairs = []

    if response.status_code == 200:
        data = response.json()
        for item in data:
            if item['symbol'].endswith('USDT'):
                try:
                    volume = float(item['quoteVolume'])
                    if volume >= min_volume_usdt:
                        pairs.append(item['symbol'])
                except:
                    continue
    return pairs

# -------------------
# RSI Calculation
# -------------------
def calculate_rsi(prices, period=14):
    deltas = [prices[i + 1] - prices[i] for i in range(len(prices) - 1)]
    seed = deltas[:period]
    avg_gain = sum([delta for delta in seed if delta > 0]) / period
    avg_loss = -sum([delta for delta in seed if delta < 0]) / period
    
    rs = avg_gain / avg_loss if avg_loss != 0 else 0
    rsi = 100 - (100 / (1 + rs))
    return rsi

# -------------------
# Trading Logic
# -------------------
def run_bot():
    trading_pairs = get_liquid_usdt_pairs(MIN_VOLUME_USDT)

    for symbol in trading_pairs:
        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe='5m', limit=100)
            closes = [x[4] for x in ohlcv]
            rsi = calculate_rsi(closes)
            print(f"{symbol} RSI: {rsi:.2f}")

            balance = exchange.fetch_balance()
            usdt_balance = balance['total']['USDT']
            trade_size = usdt_balance * TRADE_AMOUNT_PERCENTAGE

            price = closes[-1]

            if rsi < 30:
                # Buy
                amount = trade_size / price
                order = exchange.create_market_buy_order(symbol, amount)
                print(f"BUY {symbol} at {price} => {order}")

            elif rsi > 70:
                # Sell
                coin = symbol.replace('USDT', '')
                if coin in balance['free'] and balance['free'][coin] > 0:
                    amount = balance['free'][coin]
                    order = exchange.create_market_sell_order(symbol, amount)
                    print(f"SELL {symbol} at {price} => {order}")

        except Exception as e:
            print(f"Error trading {symbol}: {e}")
            continue

# -------------------
# Main Loop
# -------------------
if __name__ == "__main__":
    while True:
        print(f"Running scalping bot - {datetime.utcnow()} UTC")
        run_bot()
        time.sleep(300)  # 5 minutes
