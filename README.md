# RSI Scalping Bot for Bitrue Perpetuals

💹 A crypto trading bot built for Bitrue's Unified Perpetual Futures. It uses:
- RSI (14)
- MACD
- Bollinger Bands
- SL/TP with risk management
- Triple timeframe scanning (1m, 15m, 30m)

## 🚀 Deployment Instructions

1. Clone the repo
2. Create `.env` file with your API keys:
    ```
    BITRUE_API_KEY=xxx
    BITRUE_API_SECRET=yyy
    ```
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Run the bot:
    ```bash
    python rsi_scalping_bot.py
    ```

## 🧠 Strategy
- Entry: RSI under 30/over 70 + MACD + Bollinger confirmation
- SL: 1.5%, TP: 3%
- Uses 5% of USDT balance per trade
- Automatically sets 5x leverage
