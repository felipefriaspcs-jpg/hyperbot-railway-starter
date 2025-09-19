# Breakout Bot for Bitrue Perpetuals

💹 A crypto trading bot built for Bitrue’s Unified Perpetual Futures.  
It watches for 1-hour breakout levels, confirms on 1-minute candles, and executes a high-leverage trade with automatic stop-loss and take-profit.

## 🚀 Deployment Instructions

1. Clone this repo  
2. Create a `.env` file with your API keys:
    ```
    BITRUE_API_KEY=xxx
    BITRUE_SECRET_KEY=yyy
    ```
3. Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```
4. Run the bot:
    ```bash
    python main.py
    ```

## ⚙️ How It Works
- **Exchange:** Bitrue Unified Perpetual Futures (via `ccxt`)
- **Symbol:** Default is `XRP/USDT:USDT` (can be changed in code)
- **Breakout Logic:**
  - Finds the last closed 1-hour candle’s high/low.
  - Waits for confirmation on 1–2 consecutive 1-minute candles above/below.
  - Triggers **LONG** above high, **SHORT** below low.
- **Risk Management:**
  - Margin: `$20` test capital
  - Leverage: `50×` isolated
  - Stop-loss: ~0.8% past entry
  - Take-profit: ~1.2% past entry
  - Orders placed with `reduceOnly` flags to avoid accidental flips
- **Loop:** `main.py` runs continuous cycles (default sleep 20s)

## 🛠 Configurable via ENV
- `SYMBOL` → e.g., `BTC/USDT:USDT`
- `MARGIN_USD` → test capital (default 20)
- `LEVERAGE` → leverage (default 50)
- `TP_PCT` / `SL_PCT` → profit/stop ratios
- `DRY_RUN` → set to `true` to simulate trades without sending to exchange

## ⚠️ Disclaimer
Trading with leverage is extremely risky. This code is for **educational purposes only**. Use at your own risk.
