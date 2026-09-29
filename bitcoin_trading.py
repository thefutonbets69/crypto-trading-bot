import numpy as np
import pandas as pd

def simulate_bitcoin_price(days=60, initial_price=50000.0):
    """Return daily Bitcoin prices simulated using geometric Brownian motion.

    Args:
        days: Number of daily prices to generate, including the initial price.
        initial_price: Starting Bitcoin price in USD.

    Returns:
        A list of simulated prices beginning with the initial price.
    """
    mu = 0.5 # expected return
    sigma = 0.6 # volatility
    dt = 1.0 / 365.0

    prices = [initial_price]
    for i in range(1, days):
        Z = np.random.normal(0, 1)
        price = prices[-1] * np.exp((mu - 0.5 * sigma**2) * dt + sigma * np.sqrt(dt) * Z)
        prices.append(price)

    return prices

def main():
    """Run a seeded 60-day moving-average strategy and print trades and results."""
    np.random.seed(42)

    days = 60
    prices = simulate_bitcoin_price(days=days)

    df = pd.DataFrame({
        'Day': range(1, days + 1),
        'Price': prices
    })

    df['MA7'] = df['Price'].rolling(window=7).mean()
    df['MA30'] = df['Price'].rolling(window=30).mean()

    initial_balance = 10000.0
    balance_usd = initial_balance
    balance_btc = 0.0

    print("--- Daily Ledger of Trades ---")

    for i in range(1, len(df)):
        if pd.isna(df['MA30'].iloc[i]) or pd.isna(df['MA30'].iloc[i-1]):
            continue

        prev_ma7 = df['MA7'].iloc[i-1]
        prev_ma30 = df['MA30'].iloc[i-1]

        curr_ma7 = df['MA7'].iloc[i]
        curr_ma30 = df['MA30'].iloc[i]

        curr_price = df['Price'].iloc[i]
        day = df['Day'].iloc[i]

        # Golden Cross: MA7 crosses above MA30 -> Buy
        if prev_ma7 <= prev_ma30 and curr_ma7 > curr_ma30:
            if balance_usd > 0:
                btc_bought = balance_usd / curr_price
                balance_btc += btc_bought
                print(f"Day {day:02d}: BUY  {btc_bought:.6f} BTC @ ${curr_price:,.2f}. Spent ${balance_usd:,.2f}")
                balance_usd = 0.0

        # Death Cross: MA7 crosses below MA30 -> Sell
        elif prev_ma7 >= prev_ma30 and curr_ma7 < curr_ma30:
            if balance_btc > 0:
                usd_gained = balance_btc * curr_price
                balance_usd += usd_gained
                print(f"Day {day:02d}: SELL {balance_btc:.6f} BTC @ ${curr_price:,.2f}. Received ${usd_gained:,.2f}")
                balance_btc = 0.0

    final_price = df['Price'].iloc[-1]
    final_portfolio_value = balance_usd + balance_btc * final_price

    print("\n--- Final Portfolio Performance ---")
    print(f"Initial Portfolio Value: ${initial_balance:,.2f}")
    print(f"Final USD Balance:       ${balance_usd:,.2f}")
    print(f"Final BTC Balance:       {balance_btc:.6f} BTC")
    print(f"Current BTC Price:       ${final_price:,.2f}")
    print(f"Final Portfolio Value:   ${final_portfolio_value:,.2f}")
    roi = (final_portfolio_value - initial_balance) / initial_balance * 100
    print(f"Return on Investment:    {roi:.2f}%")

if __name__ == "__main__":
    main()
