import os
import time
import random
import requests

# === CONFIG ===
DEFAULT_PAIRS = "FLR/USDT,FLR/XRP"
DEFAULT_SLEEP = 10
DEFAULT_RETRY = 5

USE_TELEGRAM = os.getenv("USE_TELEGRAM", "false").lower() == "true"
TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "")

# === MOCK FUNCTIONS (for test mode) ===
def fetch_mock_price(symbol):
    return round(random.uniform(0.02, 0.06), 5)

def calculate_mock_rsi():
    return round(random.uniform(20, 80), 2)

# === TELEGRAM ALERT (optional) ===
def send_telegram(message):
    if USE_TELEGRAM and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
        try:
            requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message})
        except Exception as e:
            print(f"⚠️ Failed to send Telegram alert: {e}")

# === MAIN SCALPING LOGIC ===
def analyze_rsi(symbol):
    price = fetch_mock_price(symbol)
    rsi = calculate_mock_rsi()

    print(f'{symbol} price: {price}')
    print(f'{symbol} RSI: {rsi}')

    if rsi < 25:
        print(f'{symbol}: Oversold — Consider buying')
        send_telegram(f'📈 {symbol} is Oversold! RSI: {rsi} — Consider Buying')
    elif rsi > 75:
        print(f'{symbol}: Overbought — Consider selling')
        send_telegram(f'📉 {symbol} is Overbought! RSI: {rsi} — Consider Selling')
    else:
        print(f'{symbol}: RSI normal — Hold')

# === MAIN LOOP (Self-Healing) ===
def main():
    trading_pairs = os.getenv("TRADING_PAIRS", DEFAULT_PAIRS).split(",")
    sleep_duration = int(os.getenv("SLEEP_DURATION", DEFAULT_SLEEP))
    retry_delay = int(os.getenv("RETRY_DELAY", DEFAULT_RETRY))

    while True:
        try:
            for pair in trading_pairs:
                analyze_rsi(pair.strip())
                time.sleep(sleep_duration)
        except Exception as e:
            print(f"❌ Error: {e}")
            print(f"Retrying in {retry_delay} seconds...")
            time.sleep(retry_delay)

if __name__ == "__main__":
    main()
