import os
import logging
from datetime import datetime
from typing import Optional, Dict
from dotenv import load_dotenv
import ccxt
import numpy as np
import pandas as pd
from model import CryptoTradingModel

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
        
        # Initialize exchange
        self.exchange = self._init_exchange()
        
        # Initialize ML model
        model_path = os.getenv('MODEL_PATH', './models/trading_model.h5')
        lookback = int(os.getenv('LOOKBACK_WINDOW', 60))
        self.model = CryptoTradingModel(lookback_window=lookback, model_path=model_path)
        
        # Trading state
        self.position = None  # 'long', 'short', or None
        self.entry_price = None
        self.balance = float(os.getenv('INITIAL_BALANCE', 1000))
        self.trades_history = []
        
        logger.info(f"Trading bot initialized for {self.symbol} on {self.exchange_name}")
    
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
            
            # For backtesting, simulate the order
            self.position = 'long'
            self.entry_price = current_price
            self.balance -= position_size * current_price
            
            logger.info(f"BUY signal at {current_price} (confidence: {prediction:.2%}), position size: {position_size:.4f}")
            return True
            
        except Exception as e:
            logger.error(f"Error executing buy order: {e}")
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
            
            # For backtesting, simulate the order
            self.balance += (self.balance / self.entry_price) * current_price
            self.position = None
            self.entry_price = None
            
            trade = {
                'timestamp': datetime.now(),
                'profit_loss': profit_loss,
                'profit_loss_pct': profit_loss_pct
            }
            self.trades_history.append(trade)
            
            logger.info(f"SELL signal at {current_price} (confidence: {prediction:.2%}), P&L: {profit_loss_pct:.2f}%")
            return True
            
        except Exception as e:
            logger.error(f"Error executing sell order: {e}")
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
    Main entry point for the trading bot.
    """
    try:
        bot = CryptoTradingBot()
        logger.info("Starting trading bot...")
        
        # Run trading cycle (in production, this would run in a loop with timing)
        bot.run_trading_cycle()
        
        # Print statistics
        bot.print_stats()
        
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        raise


if __name__ == "__main__":
    main()
