"""
Fetches historical OHLCV data from the configured exchange and trains the
LSTM model on it, saving the result to MODEL_PATH so bot.py can load a model
that has actually seen data (instead of a freshly initialized, random one).

Usage:
    python train.py [--epochs 50] [--candles 2000]
"""
import os
import argparse
import logging

import ccxt
import numpy as np
from dotenv import load_dotenv

from model import CryptoTradingModel

load_dotenv()

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def fetch_history(exchange_name: str, symbol: str, timeframe: str, candles: int) -> np.ndarray:
    """
    Fetch up to `candles` closing prices, paging backwards since most
    exchanges cap a single fetch_ohlcv call at ~500-1000 candles.
    """
    exchange_class = getattr(ccxt, exchange_name)
    exchange = exchange_class({'enableRateLimit': True})
    exchange.load_markets()

    all_candles = []
    since = None
    per_call_limit = 1000

    while len(all_candles) < candles:
        batch = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=per_call_limit)
        if not batch:
            break
        all_candles = batch + all_candles if since else all_candles + batch
        if since is None:
            # Walk backwards from the oldest candle we just received.
            since = batch[0][0] - per_call_limit * exchange.parse_timeframe(timeframe) * 1000
        else:
            since = since - per_call_limit * exchange.parse_timeframe(timeframe) * 1000
        if len(batch) < per_call_limit:
            break

    closes = np.array([c[4] for c in all_candles[-candles:]])
    logger.info(f"Fetched {len(closes)} candles for {symbol} ({timeframe}) from {exchange_name}")
    return closes


def main():
    parser = argparse.ArgumentParser(description="Train the crypto trading model on real market history.")
    parser.add_argument('--epochs', type=int, default=50)
    parser.add_argument('--candles', type=int, default=2000, help="Number of historical candles to train on")
    args = parser.parse_args()

    exchange_name = os.getenv('EXCHANGE', 'binance')
    symbol = os.getenv('SYMBOL', 'BTC/USDT')
    timeframe = os.getenv('TIMEFRAME', '1h')
    model_path = os.getenv('MODEL_PATH', './models/trading_model.keras')
    lookback = int(os.getenv('LOOKBACK_WINDOW', 60))

    if args.candles <= lookback:
        raise ValueError(f"--candles ({args.candles}) must be greater than LOOKBACK_WINDOW ({lookback})")

    prices = fetch_history(exchange_name, symbol, timeframe, args.candles)
    if len(prices) <= lookback:
        raise RuntimeError(
            f"Only fetched {len(prices)} candles, need more than {lookback}. "
            "Try a smaller --candles value or check exchange/symbol/timeframe."
        )

    trading_model = CryptoTradingModel(lookback_window=lookback)
    trading_model.train(prices, epochs=args.epochs)
    trading_model.save_model(model_path)
    logger.info(f"Done. Trained model saved to {model_path} -- run `python bot.py` to use it.")


if __name__ == "__main__":
    main()
