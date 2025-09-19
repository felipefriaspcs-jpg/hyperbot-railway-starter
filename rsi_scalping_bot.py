import os, time
import ccxt
import pandas as pd
import pandas_ta as ta

# ====== CONFIG ======
SYMBOL = os.getenv("SYMBOL", "XRP/USDT")     # perp symbol; some ccxt setups use "XRP/USDT:USDT"
TIMEFRAME_FAST = "1m"
TIMEFRAME_SLOW = "1h"
DRY_RUN = os.getenv("DRY_RUN", "false").lower() == "true"  # set to "true" to simulate
MARGIN_USD = float(os.getenv("MARGIN_USD", 20))            # your test margin
LEVERAGE = int(os.getenv("LEVERAGE", 50))                  # 50x
TP_PCT = float(os.getenv("TP_PCT", 0.012))                 # +1.2%
SL_PCT = float(os.getenv("SL_PCT", 0.008))                 # -0.8%
CONFIRM_BARS = int(os.getenv("CONFIRM_BARS", 2))           # bars to hold above/below level

# ====== EXCHANGE INIT (Bitrue Perps) ======
EXCHANGE = ccxt.bitrue({
    'apiKey': os.getenv("BITRUE_API_KEY"),
    'secret': os.getenv("BITRUE_SECRET_KEY"),
    'enableRateLimit': True,
    'options': {
        'defaultType': 'swap',           # perpetual futures
        'exchangeType': 'perpetual',
        'enableUnifiedAccount': True,
    }
})

def fetch_df(symbol, timeframe, limit=200):
    ohlcv = EXCHANGE.fetch_ohlcv(symbol, timeframe=timeframe, limit=limit)
    df = pd.DataFrame(ohlcv, columns=["ts","open","high","low","close","volume"])
    df["ts"] = pd.to_datetime(df["ts"], unit="ms")
    return df

def get_breakout_signal(symbol):
    # 1) Get the 1h range (last closed candle)
    df_h = fetch_df(symbol, TIMEFRAME_SLOW, limit=50)
    h_last_closed = df_h.iloc[-2]              # last *closed* 1h
    range_high = h_last_closed["high"]
    range_low  = h_last_closed["low"]

    # 2) Get recent 1m closes to confirm breakout
    df_m = fetch_df(symbol, TIMEFRAME_FAST, limit=30)
    closes = df_m["close"].values

    above = all(c > range_high for c in closes[-CONFIRM_BARS:])
    below = all(c < range_low  for c in closes[-CONFIRM_BARS:])

    if above:
        return "LONG", float(closes[-1]), range_high, range_low
    if below:
        return "SHORT", float(closes[-1]), range_high, range_low
    return "HOLD", float(closes[-1]), range_high, range_low

def ensure_leverage_and_isolated(symbol):
    try:
        EXCHANGE.set_leverage(LEVERAGE, symbol)
    except Exception as e:
        print(f"⚠️ set_leverage failed ({symbol}): {e}")
    # Try to set isolated margin if supported
    try:
        EXCHANGE.set_margin_mode('isolated', symbol)
    except Exception as e:
        print(f"⚠️ set_margin_mode isolated failed ({symbol}): {e}")

def size_from_margin(symbol, entry_price):
    # $notional = margin * leverage
    notional = MARGIN_USD * LEVERAGE
    raw_amount = notional / entry_price
    # conform to exchange precision
    try:
        amount = float(EXCHANGE.amount_to_precision(symbol, raw_amount))
    except Exception:
        amount = raw_amount
    return max(amount, 0.0)

def place_orders(symbol, side, entry_price):
    """
    Market entry + separate reduce-only TP & SL.
    We use separate orders because OCO params differ by exchange.
    """
    ensure_leverage_and_isolated(symbol)
    amount = size_from_margin(symbol, entry_price)
    if amount <= 0:
        print("❌ Computed amount <= 0; aborting.")
        return

    # Compute targets
    if side == "buy":
        tp_price = entry_price * (1 + TP_PCT)
        sl_price = entry_price * (1 - SL_PCT)
    else:
        tp_price = entry_price * (1 - TP_PCT)
        sl_price = entry_price * (1 + SL_PCT)

    # Precision
    try:
        tp_price = float(EXCHANGE.price_to_precision(symbol, tp_price))
        sl_price = float(EXCHANGE.price_to_precision(symbol, sl_price))
    except Exception:
        pass

    print(f"→ {side.upper()} {symbol} @ mkt  | qty≈{amount} | TP {tp_price} | SL {sl_price}")
    if DRY_RUN:
        print("🧪 DRY_RUN enabled: skipping live orders.")
        return

    # 1) Market entry
    if side == "buy":
        EXCHANGE.create_market_buy_order(symbol, amount)
    else:
        EXCHANGE.create_market_sell_order(symbol, amount)

    # 2) Place reduce-only TP & SL (types vary; we try reasonable ccxt params)
    params_reduce = {'reduceOnly': True}

    # Try take profit (limit or market-if-touched)
    try:
        # Many swaps accept 'take_profit' via params; else fallback to limit reduce-only
        EXCHANGE.create_order(symbol, 'limit', 'sell' if side=='buy' else 'buy',
                              amount, tp_price, params=params_reduce)
        print("✅ TP placed.")
    except Exception as e:
        print(f"⚠️ TP placement failed: {e}")

    # Try stop loss (stop-market if available, else stop-limit as limit)
    try:
        # Some exchanges want 'stopLossPrice' in params; Bitrue may differ, so we fallback:
        EXCHANGE.create_order(symbol, 'stop', 'sell' if side=='buy' else 'buy',
                              amount, None, params={'stopPrice': sl_price, **params_reduce})
        print("✅ SL placed.")
    except Exception as e:
        # Fallback: place a limit order past SL as last resort (not ideal)
        try:
            EXCHANGE.create_order(symbol, 'limit', 'sell' if side=='buy' else 'buy',
                                  amount, sl_price, params=params_reduce)
            print("⚠️ Used limit SL fallback.")
        except Exception as e2:
            print(f"❌ SL placement failed: {e2}")

def run_once():
    signal, last_price, hi, lo = get_breakout_signal(SYMBOL)
    print(f"[{SYMBOL}] last={last_price:.6f} | 1hH={hi:.6f} 1hL={lo:.6f} → Signal: {signal}")

    if signal == "LONG":
        place_orders(SYMBOL, 'buy', last_price)
    elif signal == "SHORT":
        place_orders(SYMBOL, 'sell', last_price)
    else:
        print("…holding; no breakout confirmation yet.")

if __name__ == "__main__":
    # Run a single cycle. If you want continuous scanning, wrap in a loop with sleep.
    run_once()
