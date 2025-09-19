import os, csv
from datetime import datetime
import ccxt
import pandas as pd
from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands

# === Config ===
SYMBOL        = os.getenv("SYMBOL", "XRP/USDT:USDT")
TIMEFRAME     = "1m"
MARGIN_USD    = float(os.getenv("MARGIN_USD", 20))   # margin to risk per trade
LEVERAGE      = int(os.getenv("LEVERAGE", 50))       # ⚠️ high risk
TP_PCT        = float(os.getenv("TP_PCT", 0.012))    # +1.2%
SL_PCT        = float(os.getenv("SL_PCT", 0.008))    # -0.8%
LOG_CSV       = os.getenv("LOG_CSV", "trade_log.csv")

EXCHANGE = ccxt.bitrue({
    'apiKey': os.getenv("BITRUE_API_KEY"),
    'secret': os.getenv("BITRUE_SECRET_KEY"),
    'enableRateLimit': True,
    'options': {
        'defaultType': 'swap',
        'exchangeType': 'perpetual',
        'enableUnifiedAccount': True,
    }
})

# === Data ===
def fetch_ohlcv(symbol):
    ohlcv = EXCHANGE.fetch_ohlcv(symbol, timeframe=TIMEFRAME, limit=100)
    df = pd.DataFrame(ohlcv, columns=["ts","open","high","low","close","volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms")
    df[["open","high","low","close","volume"]] = df[["open","high","low","close","volume"]].astype(float)
    return df

# === Indicators & Signal ===
def add_indicators(df):
    rsi = RSIIndicator(close=df["close"], window=14)
    macd = MACD(close=df["close"], window_slow=26, window_fast=12, window_sign=9)
    bb = BollingerBands(close=df["close"], window=14, window_dev=1.5)

    df["rsi"] = rsi.rsi()
    df["macd"] = macd.macd()
    df["signal"] = macd.macd_signal()
    df["bb_lower"] = bb.bollinger_lband()
    df["bb_upper"] = bb.bollinger_hband()
    return df

def generate_signal(df):
    last = df.iloc[-1]
    if last["rsi"] < 30 and last["macd"] > last["signal"] and last["close"] < last["bb_lower"]:
        return "LONG"
    elif last["rsi"] > 70 and last["macd"] < last["signal"] and last["close"] > last["bb_upper"]:
        return "SHORT"
    return "HOLD"

# === Helpers ===
def log_trade(row):
    header = ["ts","symbol","side","entry","tp","sl","qty","note"]
    exists = os.path.exists(LOG_CSV)
    with open(LOG_CSV, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=header)
        if not exists: w.writeheader()
        w.writerow(row)

def ensure_leverage(symbol):
    try: EXCHANGE.set_leverage(LEVERAGE, symbol)
    except Exception as e: print(f"⚠️ set_leverage failed: {e}")
    try: EXCHANGE.set_margin_mode('isolated', symbol)
    except Exception as e: print(f"⚠️ set_margin_mode(isolated) failed: {e}")

def size_from_margin(symbol, entry_price):
    notional = MARGIN_USD * LEVERAGE
    raw = notional / entry_price
    try: return float(EXCHANGE.amount_to_precision(symbol, raw))
    except Exception: return raw

# === Order flow ===
def place_trade(symbol, signal, entry_price):
    ensure_leverage(symbol)

    if signal == "LONG":
        side, exit_side = "buy", "sell"
        tp_price = entry_price * (1 + TP_PCT)
        sl_price = entry_price * (1 - SL_PCT)
    else:
        side, exit_side = "sell", "buy"
        tp_price = entry_price * (1 - TP_PCT)
        sl_price = entry_price * (1 + SL_PCT)

    qty = size_from_margin(symbol, entry_price)
    try:
        tp_price = float(EXCHANGE.price_to_precision(symbol, tp_price))
        sl_price = float(EXCHANGE.price_to_precision(symbol, sl_price))
        qty      = float(EXCHANGE.amount_to_precision(symbol, qty))
    except Exception:
        pass

    print(f"→ LIVE {side.upper()} {symbol} | qty≈{qty} | TP {tp_price} | SL {sl_price}")

    # 1) Market entry
    if side == "buy":
        EXCHANGE.create_market_buy_order(symbol, qty)
    else:
        EXCHANGE.create_market_sell_order(symbol, qty)

    # 2) TP order
    try:
        EXCHANGE.create_order(symbol, 'limit', exit_side, qty, tp_price, params={'reduceOnly': True})
        print("✅ TP placed.")
    except Exception as e:
        print(f"⚠️ TP failed: {e}")

    # 3) SL order
    try:
        EXCHANGE.create_order(symbol, 'stop', exit_side, qty, None,
                              params={'stopPrice': sl_price, 'reduceOnly': True})
        print("✅ SL placed.")
    except Exception as e:
        print(f"⚠️ SL failed: {e}")

    log_trade({"ts": datetime.utcnow().isoformat(), "symbol": symbol,
               "side": side.upper(), "entry": entry_price,
               "tp": tp_price, "sl": sl_price, "qty": qty,
               "note": "submitted"})

# === Entry point ===
def run_once():
    df = fetch_ohlcv(SYMBOL)
    df = add_indicators(df)
    sig = generate_signal(df)
    last = float(df.iloc[-1]["close"])
    print(f"[{SYMBOL}] Signal: {sig}")
    if sig in ("LONG","SHORT"):
        place_trade(SYMBOL, sig, last)
    return sig
