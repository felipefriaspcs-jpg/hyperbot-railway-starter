from ta.momentum import RSIIndicator
from ta.trend import MACD
from ta.volatility import BollingerBands

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
