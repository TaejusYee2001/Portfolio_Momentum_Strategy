import os
import json
import numpy as np
import pandas as pd
import yfinance as yf
import backtrader as bt
import matplotlib.pyplot as plt
from datetime import datetime

from src.strategies import MomentumStrategy
from src.data import SPYHistoricalData, ETFHistoricalData
from src.plotting import plot_momentum_portfolio_strategy

if __name__ == "__main__": 
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

    """ data = SPYHistoricalData(start, end, resolution, redownload=False)
    tickers_list = data.unique_tickers_list
    csv_data_dir = data.output_dir  
    """
 
    momentum_window = 14
    total_window = 252
    long_percentile = 0.38
    num_stocks = 16
    
    initial_cash = 1000000
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

    # Print results
    print(f"Starting portfolio value: {cerebro.broker.getvalue():,.2f}")
    results = cerebro.run()
    momentum_strategy = results[0]
    print(f"Final Momentum portfolio value: {cerebro.broker.getvalue():,.2f}")

    plot_momentum_portfolio_strategy(results, initial_cash)
