import time
import random

def fetch_mock_price(symbol):
    return round(random.uniform(0.02, 0.06), 5)

def calculate_mock_rsi():
    return round(random.uniform(20, 80), 2)

def analyze_rsi(symbol):
    price = fetch_mock_price(symbol)
    rsi = calculate_mock_rsi()

    print(f"{symbol} price: {price}")
    print(f"{symbol} RSI: {rsi}")

    if rsi < 30:
        print(f"{symbol}: Oversold — Consider buying ✅")
    elif rsi > 70:
        print(f"{symbol}: Overbought — Consider selling 🚨")
    else:
        print(f"{symbol}: RSI normal — Hold 🟡")

def main():
    import os
    trading_pairs = os.getenv("TRADING_PAIRS", "FLR/USDT,FLR/XRP").split(",")

    while True:
        for pair in trading_pairs:
            analyze_rsi(pair.strip())
        print("Sleeping for 10 seconds...\n")
        time.sleep(10)
