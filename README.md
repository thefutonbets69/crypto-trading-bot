# Crypto Trading Bot 🤖

An AI-powered cryptocurrency trading bot using LSTM neural networks for predictive price analysis and automated trading on multiple exchanges.

## Features

- **Machine Learning Model**: LSTM-based neural network for price prediction
- **Multi-Exchange Support**: Compatible with CCXT exchanges (Binance, Kraken, etc.)
- **Risk Management**: Configurable position sizing and stop-loss/take-profit levels
- **Real-time Trading**: Automated trading based on model predictions
- **Backtesting Ready**: Historical data analysis and performance tracking
- **Logging & Monitoring**: Comprehensive logging and trading statistics

## Tech Stack

- **Python 3.8+**
- **TensorFlow/Keras**: Deep learning model
- **Pandas/NumPy**: Data processing
- **CCXT**: Cryptocurrency exchange connectivity
- **scikit-learn**: Data normalization and preprocessing

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/<your-username>/crypto-trading-bot.git
cd crypto-trading-bot
```

### 2. Create Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Exchange API
EXCHANGE=binance
API_KEY=your_api_key
API_SECRET=your_api_secret

# Trading Parameters
SYMBOL=BTC/USDT
TIMEFRAME=1h
RISK_PER_TRADE=0.02  # 2% risk per trade
PREDICTION_THRESHOLD=0.55  # Confidence threshold

# Model
MODEL_PATH=./models/trading_model.keras
LOOKBACK_WINDOW=60  # Number of candles for input
```

## Quick Start

### 1. Train the Model (do this first)

Without this step the bot runs with an untrained, randomly-initialized
network and its predictions are close to a coin flip. `train.py` fetches
real historical candles for your configured `SYMBOL`/`TIMEFRAME` from the
exchange's public API (no API key needed for this step) and trains + saves
the model to `MODEL_PATH`:

```bash
python train.py --epochs 50 --candles 2000
```

### 2. Run the Bot

```bash
python bot.py
```

This runs continuously — one trading cycle per candle (e.g. every hour for
`TIMEFRAME=1h`), or every `POLL_INTERVAL_SECONDS` if you set that instead.
Press `Ctrl+C` to stop; it prints a final stats summary on exit.

By default the bot runs in **paper trading** mode: it simulates fills
against live prices and never sends orders to the exchange, and it doesn't
require API keys. To place real orders, see [Going Live](#going-live) below.

## How It Works

### Architecture

```
Price Data (60 candles) → LSTM Layer → Dropout → LSTM Layer → Dropout → Dense → Prediction (0-1)
```

### Trading Logic

1. **Fetch Market Data**: Gets last 100 candles from exchange
2. **Normalize Data**: Scales prices to 0-1 range
3. **Generate Prediction**: LSTM model predicts probability of price increase
4. **Execute Trades**:
   - **BUY**: If prediction > threshold (default 55%)
   - **SELL**: If prediction < threshold OR stop-loss/take-profit hit
5. **Log Results**: Tracks P&L and trading statistics

### Risk Management

- **Position Sizing**: Risk amount = Account balance × Risk per trade
- **Stop Loss**: -5% from entry price
- **Take Profit**: +10% from entry price
- **Max Position**: Limited by account balance and risk parameters

## Going Live

Real order execution is off by default. It requires **both** of these set
in `.env`:

```env
LIVE_TRADING=true
CONFIRM_LIVE_TRADING=YES_I_UNDERSTAND_THE_RISK
```

If `LIVE_TRADING=true` without the exact confirmation string, the bot
refuses to start rather than silently falling back to paper trading. Only
enable this with API keys that have trading (not withdrawal) permissions,
after you've watched the bot run in paper mode and reviewed its decisions.

## Configuration

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `EXCHANGE` | binance | CCXT exchange name |
| `SYMBOL` | BTC/USDT | Trading pair |
| `TIMEFRAME` | 1h | Candle timeframe |
| `POLL_INTERVAL_SECONDS` | (matches TIMEFRAME) | Seconds between trading cycles |
| `LIVE_TRADING` | false | Set true to place real orders (see Going Live) |
| `CONFIRM_LIVE_TRADING` | (unset) | Must equal `YES_I_UNDERSTAND_THE_RISK` when LIVE_TRADING=true |
| `RISK_PER_TRADE` | 0.02 | Risk percentage per trade |
| `PREDICTION_THRESHOLD` | 0.55 | Model confidence threshold |
| `LOOKBACK_WINDOW` | 60 | Historical candles for prediction |
| `MODEL_PATH` | ./models/trading_model.keras | Trained model location |

## API Keys Setup

### Binance (Recommended)

1. Log in to [Binance](https://www.binance.com)
2. Go to **Account → API Management**
3. Create new API key
4. Enable trading permissions
5. Copy API Key and Secret to `.env`

## Performance Metrics

The bot tracks:

- Total trades executed
- Win rate (%)
- Total profit/loss
- Return on Investment (ROI)
- Individual trade P&L

## Backtesting

```python
from bot import CryptoTradingBot

bot = CryptoTradingBot()
for _ in range(100):  # Run 100 cycles
    bot.run_trading_cycle()

bot.print_stats()
```

## Disclaimer

⚠️ **RISK WARNING**: Cryptocurrency trading carries significant risk. This bot is for educational purposes. Always:

- Start with paper trading
- Use small amounts of capital
- Validate predictions before deployment
- Monitor the bot regularly
- Never trade with money you can't afford to lose

## Contributing

Contributions welcome! Areas for improvement:

- [ ] Sentiment analysis integration
- [ ] Multi-symbol trading
- [ ] Advanced risk management
- [ ] Portfolio optimization
- [ ] Real-time alerts (Discord/Telegram)

## License

MIT License - See LICENSE file

## Support

For issues or questions:

1. Check existing GitHub issues
2. Review logs in `trading_bot.log`
3. Verify API keys and exchange connection
4. Test with paper trading first

## Roadmap

- [ ] Reinforcement learning model
- [ ] Multi-timeframe analysis
- [ ] Advanced charting
- [ ] Web dashboard
- [ ] Docker containerization

---

**Built with ❤️ for cryptocurrency traders**
