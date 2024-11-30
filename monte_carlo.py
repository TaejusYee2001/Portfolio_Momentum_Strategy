import os
import numpy as np 
import pandas as pd 
import yfinance as yf 
import backtrader as bt
import matplotlib.pyplot as plt
from datetime import datetime

from src.strategies import MomentumStrategy
from src.data import ETFHistoricalData


def calculate_drawdown(series):
    """
    Calculates the drawdown of a given time series.
    """
    peak = series.cummax()
    dd = (series - peak) / peak
    return dd

if __name__ == "__main__":
    
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 18), sharex=True)

    start = datetime(2000, 1, 1)
    end = datetime(2024, 9, 3)
    resolution = 'd'
    
    tickers = [
        'XLY', 'XLP', 'XLE', 'XLF', 'XLV', 'XLI', 'XLB', 'XLRE', 'XLK', 'XLU', # Sector Etfs
        'SCHA', # Schwab small cap etf
        'VONG', # Vanguard Russel 1000 growth
        'IWD', # Russel 1000 value
        'IDEV', # IShares international developed
        'INDA', # IShares India
        'EWJ', # IShares Japan
    ]

    data = ETFHistoricalData(start, end, resolution, etf_tickers=tickers)
    tickers_list = data.etf_tickers
    csv_data_dir = data.output_dir  

    total_window = 252
    num_stocks = 16
    initial_cash = 1000000

    smallest_max_drawdown = -float('inf')

    # Calculate the benchmark strategy (buy and hold SPY)
    benchmark_data = yf.download('PTNQ', start=start, end=end, progress=False)
    initial_benchmark_price = benchmark_data['Adj Close'].iloc[0]
    benchmark_shares = initial_cash / initial_benchmark_price
    benchmark_values = benchmark_data['Adj Close'] * benchmark_shares
        
    benchmark_drawdown = calculate_drawdown(benchmark_values)

    for i in range(1, 17):
        long_percentile = i / 16

        for j in range(1, 21):
            momentum_window = j

            cerebro = bt.Cerebro()
            cerebro.broker.setcash(initial_cash)
            cerebro.broker.set_coc(True)  # Cheat on close (coc) allows trades to be placed on closing bars
            
            spy_filepath = "data/benchmark/SPY.csv"
            spy_df = yf.download("SPY", start=start, end=end, period=f"1{resolution}")
            spy_df.to_csv(spy_filepath)
            spy_feed = bt.feeds.YahooFinanceCSVData(dataname=spy_filepath)
            cerebro.adddata(spy_feed, name="SPY")

            for ticker in tickers_list: 
                ticker_filepath = os.path.join(csv_data_dir, f"{ticker}.csv")
                if os.path.exists(ticker_filepath):
                    print(f"adding: {ticker}")
                    data_feed = bt.feeds.YahooFinanceCSVData(dataname=ticker_filepath)
                    cerebro.adddata(data_feed, name=ticker)

            cerebro.addstrategy(
                MomentumStrategy, 
                momentum_window=momentum_window,
                total_window=total_window,
                long_percentile=long_percentile,
                num_stocks=num_stocks
            )

            # Run the backtest
            results = cerebro.run()
            momentum_strategy = results[0]
            portfolio_values = momentum_strategy.portfolio_values[:len(momentum_strategy.dates)]
            dates = momentum_strategy.dates

            # Calculate drawdown
            portfolio_series = pd.Series(portfolio_values, index=dates)
            drawdown_series = calculate_drawdown(portfolio_series)
            max_drawdown = drawdown_series.min()  # Get the max drawdown (most negative value)

            hursts = momentum_strategy.hursts
            pvalues = momentum_strategy.pvalues

            # Track the lowest drawdown
            if max_drawdown > smallest_max_drawdown:
                smallest_max_drawdown = max_drawdown
                best_percentile = long_percentile
                best_rebalance_window = momentum_window
                best_portfolio_value = portfolio_values
                best_drawdown_curve = drawdown_series
                best_dates = dates
                best_hursts = hursts
                best_pvalues = pvalues

            # Plot each iteration
            ax1.plot(dates, portfolio_values)
    


    # Plot the best performing portfolio (lowest max drawdown)
    ax1.plot(best_dates, best_portfolio_value, color='black', linewidth=2, label=f'Best Percentile: {best_percentile:.2f}, Best Rebalance Frequency: {best_rebalance_window:.2f}')
    ax1.set_ylabel('Portfolio Value')
    ax1.set_title(f'Varying Allocation: Best Percentile: {best_percentile:.2f}')
    ax1.legend(handles=[], labels= [])
    ax1.grid()

    ax2.plot(best_dates, best_hursts[:len(best_dates)], label="Hurst Exponent")
    ax2.plot(best_dates, best_pvalues[:len(best_dates)], label="P-Values")
    ax2.axhline(y=0.05, color='r', linestyle='--', label='P-value = 0.05')
    ax2.axhline(y=0.5, color='g', linestyle='--', label='Hurst = 0.5')
    ax2.set_title('Rolling Window Hurst Exponents and P-values for for SPY')
    ax2.legend()
    ax2.grid()

    # Plot the drawdown curve of the best performing portfolio
    ax3.fill_between(best_dates, best_drawdown_curve, 0, alpha=0.3, label='Momentum Drawdown')
    ax3.fill_between(best_dates, benchmark_drawdown[:len(best_dates)], 0, alpha=0.3, label='PTNQ Drawdown')
    ax3.set_ylabel('Drawdown')
    ax3.set_title(f'Drawdown Curve (Best Percentile: {best_percentile:.2f})')
    ax3.grid()

    plt.savefig('monte_carlo_results.png')
    plt.show()