import os
import time
import logging
from datetime import datetime
from typing import Optional, Dict
from dotenv import load_dotenv
import ccxt
import numpy as np
import pandas as pd
import requests
from model import CryptoTradingModel

TIMEFRAME_SECONDS = {
    '1m': 60, '3m': 180, '5m': 300, '15m': 900, '30m': 1800,
    '1h': 3600, '2h': 7200, '4h': 14400, '6h': 21600, '8h': 28800,
    '12h': 43200, '1d': 86400, '3d': 259200, '1w': 604800,
}

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.getenv('LOG_FILE', 'trading_bot.log')),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CryptoTradingBot:
    """
    Automated cryptocurrency trading bot with AI predictions.
    """
    
    def __init__(self):
        """
        Initialize the trading bot with exchange connection and model.
        """
        # Load configuration from environment
        self.exchange_name = os.getenv('EXCHANGE', 'binance')
        self.symbol = os.getenv('SYMBOL', 'BTC/USDT')
        self.timeframe = os.getenv('TIMEFRAME', '1h')
        self.risk_per_trade = float(os.getenv('RISK_PER_TRADE', 0.02))
        self.prediction_threshold = float(os.getenv('PREDICTION_THRESHOLD', 0.55))

        # Safety gate: real orders only fire when BOTH of these are set.
        # This defaults to paper trading (simulated fills, no exchange calls)
        # so the bot is safe to run before you trust the model's predictions.
        self.live_trading = os.getenv('LIVE_TRADING', 'false').lower() == 'true'
        confirmed = os.getenv('CONFIRM_LIVE_TRADING', '') == 'YES_I_UNDERSTAND_THE_RISK'
        if self.live_trading and not confirmed:
            raise RuntimeError(
                "LIVE_TRADING=true but CONFIRM_LIVE_TRADING is not set to "
                "'YES_I_UNDERSTAND_THE_RISK'. Refusing to start with real "
                "orders enabled. Set CONFIRM_LIVE_TRADING explicitly in your "
                ".env once you've reviewed the risk, or leave LIVE_TRADING=false "
                "to keep running in paper-trading mode."
            )

        # Initialize exchange
        self.exchange = self._init_exchange()

        # Initialize ML model
        model_path = os.getenv('MODEL_PATH', './models/trading_model.keras')
        lookback = int(os.getenv('LOOKBACK_WINDOW', 60))
        self.model = CryptoTradingModel(lookback_window=lookback, model_path=model_path)
        if not os.path.exists(model_path):
            logger.warning(
                f"No trained model found at {model_path}. Running with a freshly "
                "initialized, untrained network -- predictions will be close to "
                "random. Run `python train.py` first to fetch history and train."
            )

        # Trading state
        self.position = None  # 'long', 'short', or None
        self.entry_price = None
        self.position_size = None
        self.balance = float(os.getenv('INITIAL_BALANCE', 1000))
        self.trades_history = []

        # Telegram alerting (optional): set both TELEGRAM_BOT_TOKEN and
        # TELEGRAM_CHAT_ID to receive alerts; leave either unset to disable.
        self.telegram_token = os.getenv('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

        mode = "LIVE (real orders)" if self.live_trading else "PAPER (simulated)"
        logger.info(f"Trading bot initialized for {self.symbol} on {self.exchange_name} [{mode}]")

    def notify(self, message: str) -> None:
        """
        Send an alert to the configured Telegram chat/channel. No-ops
        silently if Telegram isn't configured.

        Args:
            message: Plain-text message to send
        """
        if not self.telegram_token or not self.telegram_chat_id:
            return
        try:
            response = requests.post(
                f"https://api.telegram.org/bot{self.telegram_token}/sendMessage",
                json={'chat_id': self.telegram_chat_id, 'text': message},
                timeout=10,
            )
            response.raise_for_status()
        except Exception as e:
            logger.warning(f"Failed to send Telegram alert: {e}")

    def _init_exchange(self) -> ccxt.Exchange:
        """
        Initialize CCXT exchange connection.
        
        Returns:
            Exchange instance
        """
        try:
            exchange_class = getattr(ccxt, self.exchange_name)
            exchange = exchange_class({
                'apiKey': os.getenv('API_KEY'),
                'secret': os.getenv('API_SECRET'),
                'enableRateLimit': True,
                'options': {'defaultType': 'future'}  # Use futures trading
            })
            
            # Test connection
            exchange.load_markets()
            logger.info(f"Connected to {self.exchange_name}")
            return exchange
            
        except Exception as e:
            logger.error(f"Failed to connect to exchange: {e}")
            raise
    
    def fetch_ohlcv(self, limit: int = 100) -> Optional[np.ndarray]:
        """
        Fetch OHLCV data from exchange.
        
        Args:
            limit: Number of candles to fetch
            
        Returns:
            Array of closing prices
        """
        try:
            ohlcv = self.exchange.fetch_ohlcv(self.symbol, self.timeframe, limit=limit)
            prices = np.array([candle[4] for candle in ohlcv])  # Extract closing prices
            logger.debug(f"Fetched {len(prices)} candles")
            return prices
            
        except Exception as e:
            logger.error(f"Error fetching OHLCV data: {e}")
            return None
    
    def calculate_position_size(self, current_price: float) -> float:
        """
        Calculate trading position size based on risk management.
        
        Args:
            current_price: Current asset price
            
        Returns:
            Position size in base currency
        """
        risk_amount = self.balance * self.risk_per_trade
        position_size = risk_amount / current_price
        return position_size
    
    def should_buy(self, prediction: float) -> bool:
        """
        Determine if we should open a long position.
        
        Args:
            prediction: Model prediction probability (0-1)
            
        Returns:
            True if prediction is bullish
        """
        return prediction > self.prediction_threshold and self.position is None
    
    def should_sell(self, prediction: float, current_price: float) -> bool:
        """
        Determine if we should close a long position.
        
        Args:
            prediction: Model prediction probability (0-1)
            current_price: Current asset price
            
        Returns:
            True if we should exit the position
        """
        if self.position != 'long' or self.entry_price is None:
            return False
        
        # Exit if prediction turns bearish
        if prediction < (1 - self.prediction_threshold):
            return True
        
        # Exit if we hit a stop loss (5% loss)
        stop_loss = self.entry_price * 0.95
        if current_price < stop_loss:
            return True
        
        # Exit if we hit a take profit (10% gain)
        take_profit = self.entry_price * 1.10
        if current_price > take_profit:
            return True
        
        return False
    
    def execute_buy(self, current_price: float, prediction: float) -> bool:
        """
        Execute a buy order.
        
        Args:
            current_price: Current asset price
            prediction: Model prediction
            
        Returns:
            True if order was successful
        """
        try:
            position_size = self.calculate_position_size(current_price)

            if self.live_trading:
                order = self.exchange.create_market_buy_order(self.symbol, position_size)
                logger.info(f"LIVE BUY order placed: {order.get('id', order)}")
            else:
                logger.info(
                    f"BUY signal at {current_price} (confidence: {prediction:.2%}), "
                    f"position size: {position_size:.4f} [paper trade]"
                )

            self.position = 'long'
            self.entry_price = current_price
            self.position_size = position_size
            self.balance -= position_size * current_price

            mode_tag = "LIVE" if self.live_trading else "PAPER"
            self.notify(
                f"[{mode_tag}] BUY {self.symbol} at ${current_price:.2f} "
                f"(confidence {prediction:.2%}), size {position_size:.4f}"
            )
            return True

        except Exception as e:
            logger.error(f"Error executing buy order: {e}")
            self.notify(f"[ERROR] Buy order failed for {self.symbol}: {e}")
            return False
    
    def execute_sell(self, current_price: float, prediction: float) -> bool:
        """
        Execute a sell order.
        
        Args:
            current_price: Current asset price
            prediction: Model prediction
            
        Returns:
            True if order was successful
        """
        try:
            if self.position != 'long' or self.entry_price is None:
                return False

            # Calculate P&L
            profit_loss = (current_price - self.entry_price) * (self.balance / self.entry_price)
            profit_loss_pct = (current_price - self.entry_price) / self.entry_price * 100

            if self.live_trading:
                order = self.exchange.create_market_sell_order(self.symbol, self.position_size)
                logger.info(f"LIVE SELL order placed: {order.get('id', order)}")

            self.balance += (self.balance / self.entry_price) * current_price
            self.position = None
            self.entry_price = None
            self.position_size = None

            trade = {
                'timestamp': datetime.now(),
                'profit_loss': profit_loss,
                'profit_loss_pct': profit_loss_pct
            }
            self.trades_history.append(trade)

            logger.info(f"SELL signal at {current_price} (confidence: {prediction:.2%}), P&L: {profit_loss_pct:.2f}%")
            mode_tag = "LIVE" if self.live_trading else "PAPER"
            self.notify(
                f"[{mode_tag}] SELL {self.symbol} at ${current_price:.2f}, "
                f"P&L: {profit_loss_pct:+.2f}% (${profit_loss:+.2f})"
            )
            return True

        except Exception as e:
            logger.error(f"Error executing sell order: {e}")
            self.notify(f"[ERROR] Sell order failed for {self.symbol}: {e}")
            return False
    
    def run_trading_cycle(self) -> None:
        """
        Execute one complete trading cycle:
        1. Fetch market data
        2. Generate prediction
        3. Execute trades
        """
        try:
            # Fetch recent price data
            prices = self.fetch_ohlcv(limit=100)
            if prices is None or len(prices) < self.model.lookback_window:
                logger.warning("Insufficient data for prediction")
                return
            
            current_price = prices[-1]
            
            # Generate prediction
            prediction = self.model.predict(prices)
            logger.info(f"Price: ${current_price:.2f}, Prediction: {prediction:.2%} (bullish)")
            
            # Decision logic
            if self.should_buy(prediction):
                self.execute_buy(current_price, prediction)
            elif self.should_sell(prediction, current_price):
                self.execute_sell(current_price, prediction)
            else:
                logger.info("No trading signal")
            
        except Exception as e:
            logger.error(f"Error in trading cycle: {e}")
    
    def print_stats(self) -> None:
        """
        Print trading statistics.
        """
        if not self.trades_history:
            logger.info("No trades executed yet")
            return
        
        total_trades = len(self.trades_history)
        winning_trades = sum(1 for t in self.trades_history if t['profit_loss'] > 0)
        losing_trades = total_trades - winning_trades
        total_pnl = sum(t['profit_loss'] for t in self.trades_history)
        
        logger.info(f"\n===== Trading Statistics =====")
        logger.info(f"Total Trades: {total_trades}")
        logger.info(f"Winning Trades: {winning_trades} ({winning_trades/total_trades*100:.1f}%)")
        logger.info(f"Losing Trades: {losing_trades}")
        logger.info(f"Total P&L: ${total_pnl:.2f}")
        logger.info(f"Current Balance: ${self.balance:.2f}")
        logger.info(f"ROI: {(self.balance / float(os.getenv('INITIAL_BALANCE', 1000)) - 1) * 100:.2f}%")


def main():
    """
    Main entry point for the trading bot. Runs continuously, one trading
    cycle per candle interval, until interrupted with Ctrl+C.
    """
    bot = None
    try:
        bot = CryptoTradingBot()
        interval = int(os.getenv(
            'POLL_INTERVAL_SECONDS',
            TIMEFRAME_SECONDS.get(bot.timeframe, 3600)
        ))
        logger.info(f"Starting trading bot (cycle every {interval}s). Press Ctrl+C to stop.")
        bot.notify(f"Trading bot started for {bot.symbol} on {bot.exchange_name}.")

        while True:
            bot.run_trading_cycle()
            time.sleep(interval)

    except KeyboardInterrupt:
        logger.info("Stopping trading bot (Ctrl+C received)...")
        bot.print_stats()
        bot.notify("Trading bot stopped (Ctrl+C).")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        if bot is not None:
            bot.notify(f"[ERROR] Trading bot crashed: {e}")
        raise


if __name__ == "__main__":
    main()
