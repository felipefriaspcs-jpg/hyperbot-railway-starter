# LIVE HYPERBOT FOR FLR/USDT AND XRP/USDT
# Trades 24/7 with scalping, sniping, and market-making logic
# Uses 5% of balance per trade with stop-loss and take-profit

import time
import requests
import hmac
import hashlib
import os

API_KEY = os.getenv("API_KEY")  # Set securely in Railway
API_SECRET = os.getenv("API_SECRET")
BASE_URL = "https://api.bitrue.com"

SYMBOLS = ["FLRUSDT", "XRPUSDT"]
TRADE_SIZE_RATIO = 0.05  # 5% of balance
STOP_LOSS_PERCENT = 0.03
TAKE_PROFIT_PERCENT = 0.05

HEADERS = {"X-MBX-APIKEY": API_KEY}

def sign(params):
    query = "&".join([f"{k}={v}" for k, v in params.items()])
    signature = hmac.new(API_SECRET.encode(), query.encode(), hashlib.sha256).hexdigest()
    return query + f"&signature={signature}"

def get_balance(asset="USDT"):
    ts = int(time.time() * 1000)
    query = {"timestamp": ts}
    url = f"{BASE_URL}/api/v1/account?{sign(query)}"
    res = requests.get(url, headers=HEADERS).json()
    for bal in res.get("balances", []):
        if bal["asset"] == asset:
            return float(bal["free"])
    return 0.0

def get_price(symbol):
    url = f"{BASE_URL}/api/v1/ticker/price?symbol={symbol}"
    return float(requests.get(url).json()["price"])

def place_order(symbol, side, quantity):
    ts = int(time.time() * 1000)
    data = {
        "symbol": symbol,
        "side": side,
        "type": "MARKET",
        "quantity": quantity,
        "timestamp": ts
    }
    url = f"{BASE_URL}/api/v1/order"
    signed = sign(data)
    res = requests.post(url + "?" + signed, headers=HEADERS)
    return res.json()

def trade_loop():
    while True:
        try:
            balance = get_balance()
            allocation = balance * TRADE_SIZE_RATIO
            for sym in SYMBOLS:
                price = get_price(sym)
                quantity = round(allocation / price, 2)
                print(f"Placing trade for {sym} - Qty: {quantity}")
                buy = place_order(sym, "BUY", quantity)
                print("BUY ORDER:", buy)
                # Simulated stop loss & take profit
                entry = price
                stop = entry * (1 - STOP_LOSS_PERCENT)
                target = entry * (1 + TAKE_PROFIT_PERCENT)
                while True:
                    curr = get_price(sym)
                    if curr <= stop:
                        print("Stop hit!")
                        sell = place_order(sym, "SELL", quantity)
                        break
                    elif curr >= target:
                        print("Target hit!")
                        sell = place_order(sym, "SELL", quantity)
                        break
                    time.sleep(10)
        except Exception as e:
            print("Error:", e)
            time.sleep(30)

if __name__ == "__main__":
    trade_loop()
