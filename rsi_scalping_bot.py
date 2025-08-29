import ccxt
import time
import logging

# Logging setup
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s')

# Your API keys (use Railway secrets or environment vars in production)
api_key = 'YOUR_API_KEY'
secret = 'YOUR_API_SECRET'

# Initialize exchange
exchange = ccxt.bitrue({
    'apiKey': api_key,
    'secret': secret,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot',  # Use 'future' if trading perpetuals
    }
})

# Config
PAIR_LIST = ['FLR/USDT', 'XRP/USDT']
TRADE_SIZE_PCT = 0.05
TAKE_PROFIT_PCT = 0.02   # 2%
STOP_LOSS_PCT = 0.01     # 1%
INTERVAL = 30  # seconds between cycles

def fetch_rsi(symbol, timeframe='1m', period=14):
    ohlcv = exchange.fetch_ohlcv(symbol, timeframe)
    closes = [x[4] for x in ohlcv]
    if len(closes) < period:
        return None

    gains, losses = [], []
    for i in range(1, period + 1):
        delta = closes[-i] - closes[-i - 1]
        if delta > 0:
            gains.append(delta)
        else:
            losses.append(abs(delta))

    avg_gain = sum(gains) / period if gains else 0.0001
    avg_loss = sum(losses) / period if losses else 0.0001

    rs = avg_gain / avg_loss
    rsi = 100 - (100 / (1 + rs))
    return round(rsi, 2)

def get_balance(asset):
    balance = exchange.fetch_balance()
    return balance[asset]['free']

def place_order(symbol, side, price, amount):
    try:
        logging.info(f"{symbol} Signal: {side.upper()}")
        logging.info(f"Placing {side.upper()} order for {amount:.2f} at {price}")
        if side == 'buy':
            order = exchange.create_limit_buy_order(symbol, amount, price)
        else:
            order = exchange.create_limit_sell_order(symbol, amount, price)
        logging.info(f"Order placed: {order['id']}")
        return order
    except Exception as e:
        logging.error(f"Order error: {e}")
        return None

def run_trading_cycle(symbol):
    try:
        rsi = fetch_rsi(symbol)
        logging.info(f"[{symbol}] RSI: {rsi}")

        if rsi is None:
            return

        ticker = exchange.fetch_ticker(symbol)
        price = ticker['last']
        base = symbol.split('/')[0]
        quote = symbol.split('/')[1]

        balance = get_balance(quote)
        trade_amount = (balance * TRADE_SIZE_PCT) / price

        if rsi < 30:
            # BUY Signal
            buy_order = place_order(symbol, 'buy', price, trade_amount)
            if buy_order:
                sl = price * (1 - STOP_LOSS_PCT)
                tp = price * (1 + TAKE_PROFIT_PCT)
                logging.info(f"[{symbol}] SL: {sl:.4f}, TP: {tp:.4f}")

        elif rsi > 70:
            # SELL Signal
            base_balance = get_balance(base)
            if base_balance > 0:
                sell_order = place_order(symbol, 'sell', price, base_balance)
                if sell_order:
                    sl = price * (1 + STOP_LOSS_PCT)
                    tp = price * (1 - TAKE_PROFIT_PCT)
                    logging.info(f"[{symbol}] SL: {sl:.4f}, TP: {tp:.4f}")
    except Exception as e:
        logging.error(f"[{symbol}] Trading error: {e}")

def main():
    while True:
        for pair in PAIR_LIST:
            run_trading_cycle(pair)
        logging.info("Cycle complete. Sleeping...\n")
        time.sleep(INTERVAL)
