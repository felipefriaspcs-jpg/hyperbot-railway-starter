import ccxt
import time
import os
from datetime import datetime

# ENV Variables
API_KEY = os.getenv("BITRUE_API_KEY")
API_SECRET = os.getenv("BITRUE_API_SECRET")
TRADE_SIZE_PERCENT = float(os.getenv("TRADE_SIZE_PERCENT", 5))
TRADING_PAIRS = os.getenv("TRADING_PAIRS", "XRP/USDT,BTC/USDT,ETH/USDT").split(",")
RSI_PERIOD = 14
RSI_OVERBOUGHT = 70
RSI_OVERSOLD = 30
SLEEP_INTERVAL = 20  # in seconds

# Initialize Bitrue exchange
exchange = ccxt.bitrue({
    'apiKey': API_KEY,
    'secret': API_SECRET,
    'enableRateLimit': True
})

# Fetch RSI
def calculate_rsi(symbol, timeframe='1m'):
    try:
        ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=RSI_PERIOD + 1)
        if len(ohlcv) < RSI_PERIOD:
            return None
        closes = [x[4] for x in ohlcv]  # Closing prices
        gains = [max(closes[i] - closes[i - 1], 0) for i in range(1, len(closes))]
        losses = [max(closes[i - 1] - closes[i], 0) for i in range(1, len(closes))]
        avg_gain = sum(gains) / RSI_PERIOD
        avg_loss = sum(losses) / RSI_PERIOD
        if avg_loss == 0:
            return 100
        rs = avg_gain / avg_loss
        return 100 - (100 / (1 + rs))
    except Exception as e:
        print(f"Error calculating RSI for {symbol}: {e}")
        return None

# Place order to accumulate XRP
def place_order(symbol, signal):
    try:
        market = exchange.market(symbol)
        quote = market['quote']
        base = market['base']
        balance = exchange.fetch_balance()[quote]['free']
        price = exchange.fetch_ticker(symbol)['last']
        
        if price is None or balance is None:
            print(f"Skipping {symbol} due to missing price or balance.")
            return

        amount = (balance * (TRADE_SIZE_PERCENT / 100)) / price
        amount = float(exchange.amount_to_precision(symbol, amount))

        if signal == 'BUY':
            print(f"Buying {amount} of {symbol} to convert into XRP")
            exchange.create_market_buy_order(symbol, amount)

            # If not XRP pair, convert proceeds to XRP
            if quote != 'XRP':
                time.sleep(5)
                new_balance = exchange.fetch_balance()[base]['free']
                pair_to_xrp = f"{base}/XRP"
                if pair_to_xrp in exchange.load_markets():
                    amount_x = float(exchange.amount_to_precision(pair_to_xrp, new_balance))
                    print(f"Swapping {amount_x} {base} to XRP via {pair_to_xrp}")
                    exchange.create_market_sell_order(pair_to_xrp, amount_x)
    except Exception as e:
        print(f"Order failed for {symbol}: {e}")

# Bot loop
def run_bot():
    while True:
        for symbol in TRADING_PAIRS:
            rsi = calculate_rsi(symbol)
            if rsi:
                print(f"[{symbol}] RSI: {round(rsi, 2)}")
                if rsi <= RSI_OVERSOLD:
                    place_order(symbol, 'BUY')
        print("🔁 Cycle complete. Sleeping 20s...")
        time.sleep(SLEEP_INTERVAL)

if __name__ == '__main__':
    run_bot()
