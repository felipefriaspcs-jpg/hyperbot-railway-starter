# multi_pair_trading_bot.py

import time
import os
import logging
from decimal import Decimal
from exchange_api import ExchangeClient  # Custom wrapper for Bitrue or similar
from strategy import RSIStrategy

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment variables
TRADING_PAIRS = os.getenv("TRADING_PAIRS", "BTC/USDT,ETH/USDT").split(',')
TRADE_AMOUNT_PERCENTAGE = Decimal(os.getenv("TRADE_AMOUNT_PERCENTAGE", "5"))
STOP_LOSS_PERCENT = Decimal(os.getenv("STOP_LOSS_PERCENT", "2"))
TAKE_PROFIT_PERCENT = Decimal(os.getenv("TAKE_PROFIT_PERCENT", "3"))
POLL_INTERVAL = int(os.getenv("POLL_INTERVAL", 30))

# Initialize Exchange API
exchange = ExchangeClient(
    api_key=os.getenv("API_KEY"),
    api_secret=os.getenv("API_SECRET")
)

# Strategy
strategy = RSIStrategy()

# Main loop
while True:
    for pair in TRADING_PAIRS:
        try:
            balance = exchange.get_balance(pair.split("/")[1])
            trade_amount = balance * TRADE_AMOUNT_PERCENTAGE / Decimal(100)
            price_data = exchange.get_ohlcv(pair)

            signal = strategy.evaluate(price_data)
            if signal == "buy":
                logger.info(f"Buy signal for {pair}")
                exchange.buy(pair, trade_amount, STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT)

            elif signal == "sell":
                logger.info(f"Sell signal for {pair}")
                exchange.sell(pair, trade_amount, STOP_LOSS_PERCENT, TAKE_PROFIT_PERCENT)

        except Exception as e:
            logger.error(f"Error processing {pair}: {str(e)}")

    time.sleep(POLL_INTERVAL)
