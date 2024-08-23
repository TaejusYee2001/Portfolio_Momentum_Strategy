import os
import json
import math
import numpy as np
import pandas as pd
import yfinance as yf
import backtrader as bt
import matplotlib.pyplot as plt
from datetime import datetime
        
class MomentumStrategy(bt.Strategy):
    params = (
        ("momentum_window", 20),
        ("total_window", 60),
        ("long_percentile", 0.8),
        ("num_stocks", 50),
    )
    
    def __init__(self):
        self.data_feeds = self.datas
        self.portfolio_values = []
        self.dates = []
        self.total_counter = 0
        
    def next(self):
        self.portfolio_values.append(self.broker.getvalue())
        self.dates.append(self.data.datetime.date(0))
        
        self.rebalance_portfolio()
        self.total_counter += 1

    def rebalance_portfolio(self):
        if self.total_counter % self.p.total_window == 0:
            print("---")
            momentum = {}
            for data in self.datas:
                if len(data) >= self.p.momentum_window:
                    momentum_factor = self.compute_momentum(data, self.p.momentum_window, self.p.total_window)
                    if momentum_factor > 0:
                        momentum[data._name] = momentum_factor
                        # Print(f"Ticker: {data._name}, momentum factor: {momentum[data._name]}")
            
            sorted_assets = sorted(momentum.items(), key=lambda x: x[1], reverse=True)
            # Debugging: Print the sorted assets
            print("Sorted assets:", sorted_assets)

            # Calculate top assets based on the percentile
            top_count = int(math.ceil(self.p.num_stocks * self.p.long_percentile))
            top_assets = [name for name, factor in sorted_assets[:top_count]]
            # Debugging: Print the top assets
            print("Top assets:", top_assets)
            
            for data in self.datas:
                if data._name in top_assets:
                    self.order_target_percent(data, 1.0 / len(top_assets))
                else:
                    self.order_target_percent(data, 0)
            print("---")
        
    def compute_momentum(self, data, momentum_window, total_window):
        # Convert Backtrader data feed to pandas DataFrame
        df = pd.DataFrame({
            'close': data.close.get(size=len(data)),
            'datetime': data.datetime.datetime()
        })
        df.set_index('datetime', inplace=True)
        df.sort_index(inplace=True)

        if len(df) < total_window:
            print(f"Length of data must be at least {total_window}")
            return 0

        # End of date range
        now = df.index[-1]

        total_window_start = df.index[-total_window]
        momentum_window_start = df.index[-momentum_window]

        # Get price change up to before the momentum window
        df_past_total_window = df[(df.index >= total_window_start) & (df.index < momentum_window_start)]
        if len(df_past_total_window) > 0: 
            price_change_total_window = (df_past_total_window['close'].iloc[-1] - df_past_total_window['close'].iloc[0]) / df_past_total_window['close'].iloc[0]
        else: 
            price_change_total_window = 0

        df_past_momentum_window = df[(df.index >= momentum_window_start) & (df.index <= now)]
        if len(df_past_momentum_window) > 0:
            price_change_momentum_window = (df_past_momentum_window['close'].iloc[-1] - df_past_momentum_window['close'].iloc[0]) / df_past_momentum_window['close'].iloc[0]
        else:
            price_change_momentum_window = 0
        
        # Calculate daily returns and standard deviation over the total window
        df_last_total_window = df[df.index >= total_window_start]
        df_last_total_window['Daily_Return'] = df_last_total_window['close'].pct_change()
        std_dev = df_last_total_window['Daily_Return'].std()

        # Compute momentum factor
        if std_dev != 0:
            momentum_factor = (price_change_total_window - price_change_momentum_window) / std_dev
        else: 
            momentum_factor = 0

        return momentum_factor

class MomentumStrategyBacktester:
    def __init__(self, start_date, end_date, num_stocks, initial_cash, momentum_window, total_window, long_percentile):
        self.start_date = start_date
        self.end_date = end_date
        self.num_stocks = num_stocks
        self.initial_cash = initial_cash   
        self.momentum_window = momentum_window
        self.total_window = total_window
        self.long_percentile = long_percentile
        
        self.cerebro = bt.Cerebro()
        self.cerebro.broker.setcash(self.initial_cash)
        
        self.num_stocks_added = 0
        
    def add_stock_data(self, csv_filename):
        if self.num_stocks_added > self.num_stocks: 
            return
        
        if os.path.exists(csv_filename):
            df = pd.read_csv(csv_filename, index_col='Date', parse_dates=True)
            start_date = df.index[0]
            data = bt.feeds.PandasData(dataname=df, 
                                       fromdate=self.start_date,
                                       todate=self.end_date)
            
            stock_name = os.path.basename(csv_filename).split('.')[0]
            
            if start_date <= self.start_date:
                self.cerebro.adddata(data, name=stock_name)
                self.num_stocks_added += 1
            else:
                pass
        else:
            print(f"File {csv_filename} does not exist")

    def run_backtest(self):
        self.cerebro.addstrategy(
            MomentumStrategy,
            momentum_window=self.momentum_window,
            total_window=self.total_window,
            long_percentile=self.long_percentile, 
            num_stocks = self.num_stocks
        )
        
        print(f"Starting portfolio value: {self.cerebro.broker.getvalue():,.2f}")
        results = self.cerebro.run()
        print(f"Final portfolio value: {self.cerebro.broker.getvalue():,.2f}")
        
        # Extract portfolio values and dates for plotting
        strategy = results[0]
        portfolio_values = strategy.portfolio_values
        dates = strategy.dates        

        # Plot portfolio value against SPY value
        plt.figure(figsize=(12, 6))
        plt.plot(dates, portfolio_values, label='Portfolio Value')
        plt.xlabel('Date')
        plt.ylabel('Value')
        plt.title('Portfolio Value vs. SPY Value Over Time')
        plt.legend()
        plt.grid()

        # Save the plot to a file
        plot_filename = f"src/data/output_plots/varying_universe_size/N={self.num_stocks}.png"
        plt.savefig(plot_filename)
        plt.close()
        

if __name__ == "__main__": 
    # Load tickers
    print("Loading tickers")
    tickers_file_path = "src/data/tickers.json"
    with open(tickers_file_path, 'r') as file:
        tickers_data = json.load(file)
    tickers = tickers_data['tickers'][:1000]
    
    spy_data = yf.download('SPY', start=datetime(2001, 1, 1), end=datetime(2022, 12, 31))
    plt.figure(figsize=(12, 6))
    plt.plot(spy_data.index, spy_data['Close'], label='SPY Value')
    plt.xlabel('Date')
    plt.ylabel('Value')
    plt.title('Portfolio Value vs. SPY Value Over Time')
    plt.legend()
    plt.grid()
    plt.show()
    
    # Save the plot to a file
    plot_filename = f"src/data/output_plots/varying_universe_size/SPY.png"
    plt.savefig(plot_filename)
    plt.close()
    
    universe_sizes = range(50, 501, 50)  # Universe sizes from 50 to 500 in increments of 50

    for size in universe_sizes:
        print(f"Running backtest with universe size: {size}")

        backtester = MomentumStrategyBacktester(
            start_date=datetime(2001, 1, 1),
            end_date=datetime(2022, 12, 31),
            num_stocks=size, 
            initial_cash=100000,
            momentum_window=21,
            total_window=252,
            long_percentile=0.1
        )

        csv_dir = "src/data/stock_data"
        for ticker in tickers[:size]:  # Limit the number of tickers based on current universe size
            stock_data_filename = os.path.join(csv_dir, f"{ticker}.csv")
            backtester.add_stock_data(stock_data_filename)
        
        backtester.run_backtest()