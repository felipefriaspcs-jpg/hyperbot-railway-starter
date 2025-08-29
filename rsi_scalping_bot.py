import os
import time
from exchange_api import BitrueAPI
from strategy import Strategy

# Load environment variables
API_KEY = os.getenv("API_KEY")
API_SECRET = os.getenv("API_SECRET")
TRADING_PAIRS = os.getenv("TRADING_PAIRS", "XRP/USDT").split(",")
TRADE_AMOUNT_PERCENTAGE = float(os.getenv("TRADE_AMOUNT_PERCENTAGE", 5))  # % of balance
STOP_LOSS_PERCENT = float(os.getenv("STOP_LOSS_PERCENT", 2))
TAKE_PROFIT_PERCENT = float(os.getenv("TAKE_PROFIT_PERCENT", 3))

# Initialize exchange and strategy
api = BitrueAPI(API_KEY, API_SECRET)
strategy = Strategy()

print("🔁 Starting XRP accumulation strategy...")

while True:
    for pair in TRADING_PAIRS:
        try:
            print(f"\n📊 Checking market for {pair}...")
            base, quote = pair.split("/")
            price = api.get_price(pair)
            rsi = strategy.calculate_rsi(pair)

            print(f"RSI: {rsi:.2f} | Price: {price}")

            if strategy.should_buy(rsi):
                balance = api.get_balance(quote)
                amount_to_trade = (balance * TRADE_AMOUNT_PERCENTAGE) / 100 / price
                print(f"✅ Buy signal detected. Placing buy order for {amount_to_trade:.4f} {base}")
                api.place_order(pair, side="BUY", amount=amount_to_trade)

            elif strategy.should_sell(rsi):
                balance = api.get_balance(base)
                print(f"🚨 Sell signal detected. Placing sell order for {balance:.4f} {base}")
                api.place_order(pair, side="SELL", amount=balance)

        except Exception as e:
            print(f"❌ Error with pair {pair}: {e}")

    time.sleep(15)  # Wait before checking again
