import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
from tensorflow.keras.models import Sequential, load_model
from tensorflow.keras.layers import LSTM, Dense, Dropout
from tensorflow.keras.optimizers import Adam
import os
from typing import Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class CryptoTradingModel:
    """
    LSTM-based neural network model for cryptocurrency price prediction.
    """
    
    def __init__(self, lookback_window: int = 60, model_path: Optional[str] = None):
        """
        Initialize the trading model.
        
        Args:
            lookback_window: Number of previous timesteps to use as input
            model_path: Path to load a pre-trained model
        """
        self.lookback_window = lookback_window
        self.scaler = MinMaxScaler(feature_range=(0, 1))
        self.model_path = model_path
        self.model = None
        
        if model_path and os.path.exists(model_path):
            self.load_model(model_path)
        else:
            self.build_model()
    
    def build_model(self) -> None:
        """
        Build LSTM neural network architecture.
        """
        self.model = Sequential([
            LSTM(128, return_sequences=True, input_shape=(self.lookback_window, 1)),
            Dropout(0.2),
            LSTM(64, return_sequences=True),
            Dropout(0.2),
            LSTM(32, return_sequences=False),
            Dropout(0.2),
            Dense(16, activation='relu'),
            Dense(1, activation='sigmoid')  # Output between 0-1 for probability
        ])
        
        self.model.compile(
            optimizer=Adam(learning_rate=0.001),
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        logger.info("LSTM model built successfully")
    
    def prepare_data(self, prices: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare price data for training/prediction.
        
        Args:
            prices: Array of historical prices
            
        Returns:
            Normalized features and labels
        """
        # Normalize prices
        scaled_prices = self.scaler.fit_transform(prices.reshape(-1, 1))
        
        X, y = [], []
        for i in range(len(scaled_prices) - self.lookback_window):
            X.append(scaled_prices[i:i + self.lookback_window])
            # Label: 1 if price goes up, 0 if goes down
            y.append(1 if scaled_prices[i + self.lookback_window] > scaled_prices[i + self.lookback_window - 1] else 0)
        
        return np.array(X), np.array(y)
    
    def train(self, prices: np.ndarray, epochs: int = 50, batch_size: int = 32) -> dict:
        """
        Train the model on historical price data.
        
        Args:
            prices: Array of historical prices
            epochs: Number of training epochs
            batch_size: Batch size for training
            
        Returns:
            Training history
        """
        X, y = self.prepare_data(prices)
        
        if len(X) == 0:
            logger.error("Insufficient data for training")
            return {}
        
        # Split into train/test
        split_idx = int(len(X) * 0.8)
        X_train, X_test = X[:split_idx], X[split_idx:]
        y_train, y_test = y[:split_idx], y[split_idx:]
        
        history = self.model.fit(
            X_train, y_train,
            epochs=epochs,
            batch_size=batch_size,
            validation_data=(X_test, y_test),
            verbose=1
        )
        
        logger.info(f"Model training completed. Test accuracy: {history.history['val_accuracy'][-1]:.4f}")
        return history.history
    
    def predict(self, recent_prices: np.ndarray) -> float:
        """
        Predict the next price movement.
        
        Args:
            recent_prices: Last N prices (N = lookback_window)
            
        Returns:
            Probability of price going up (0-1)
        """
        if len(recent_prices) < self.lookback_window:
            logger.warning(f"Insufficient data. Expected {self.lookback_window}, got {len(recent_prices)}")
            return 0.5
        
        # Normalize using historical data
        recent_prices = recent_prices[-self.lookback_window:]
        scaled = self.scaler.transform(recent_prices.reshape(-1, 1))
        
        # Reshape for LSTM [samples, timesteps, features]
        X = scaled.reshape(1, self.lookback_window, 1)
        
        prediction = self.model.predict(X, verbose=0)[0][0]
        return float(prediction)
    
    def save_model(self, path: str) -> None:
        """
        Save the trained model to disk.
        
        Args:
            path: Path to save the model
        """
        os.makedirs(os.path.dirname(path), exist_ok=True)
        self.model.save(path)
        logger.info(f"Model saved to {path}")
    
    def load_model(self, path: str) -> None:
        """
        Load a pre-trained model from disk.
        
        Args:
            path: Path to load the model
        """
        self.model = load_model(path)
        logger.info(f"Model loaded from {path}")
