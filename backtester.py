import os
import time
import json
import math
import logging
import numpy as np
import pandas as pd
import yfinance as yf
import wikipedia as wp
import backtrader as bt
import matplotlib.pyplot as plt
from datetime import datetime

from src.strategies import MomentumStrategy, Benchmark
from src.data import HistoricalData

# NASDAQ 100 
# RUSSEL 1000
        
""" logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', 
    handlers=[
        logging.FileHandler('logs/backtest_output.log'), 
    ]
)

logger = logging.getLogger(__name__)

class Benchmark(bt.Strategy):
    def __init__(self):
        self.data_feeds = self.datas
        self.spy = self.datas[0]  # Assuming SPY is the first data feed
        self.order = None
        self.portfolio_values = []
        self.dates = []

    def next(self):
        # Record portfolio value and date
        self.portfolio_values.append(self.broker.getvalue())
        self.dates.append(self.datas[0].datetime.date(0))

        if self.order:
            return

        if not self.position:
            cash = self.broker.getcash()
            shares = int(cash / self.spy.close[0])
            self.order = self.buy(data=self.spy, size=shares)

    def stop(self):
        self.portfolio_values.append(self.broker.getvalue())
        self.dates.append(self.datas[0].datetime.date(0))

class MomentumStrategy(bt.Strategy):
    params = (
        ("momentum_window", 0),
        ("total_window", 0),
        ("long_percentile", 0.0),
        ("num_stocks", 0),
    )
    
    def __init__(self):
        self.data_feeds = self.datas
        self.top_assets = []
        self.current_positions = []
        self.portfolio_values = []
        self.dates = []
        self.total_counter = 0
        
    def next(self):
        self.portfolio_values.append(self.broker.getvalue())
        self.dates.append(self.data.datetime.date(0))
        
        self.rebalance_portfolio()
        self.total_counter += 1

    def notify_order(self, order):
        if order.status in [order.Completed]:
            if order.isbuy():
                logger.info(f"BUY EXECUTED: {order.data._name}, Price: {order.executed.price}, Cost: {order.executed.value}, Size: {order.executed.size}")
            elif order.issell():
                logger.info(f"SELL EXECUTED: {order.data._name}, Price: {order.executed.price}, Cost: {order.executed.value}, Size: {order.executed.size}")
        elif order.status == order.Canceled:
            logger.warning(f"Order Failed: {order.data._name}. Order was canceled.")
        elif order.status == order.Margin: 
            logger.warning(f"Order Failed: {order.data._name}. Order was margin.")
        elif order.status == order.Rejected: 
            logger.warning(f"Order Failed: {order.data._name}. Order was rejected.")

        return order

    def notify_trade(self, trade):
        if trade.isclosed:
            logger.info(f"OPERATION PROFIT: {trade.data._name}, Gross: {trade.pnl}, Net: {trade.pnlcomm}")

        return trade

    def rebalance_portfolio(self):
        # Checks if current bar is one day BEFORE the rebalance window
        if ((self.total_counter % self.p.momentum_window == self.p.momentum_window - 1) and (self.total_counter >= self.p.total_window)):
            self.current_positions = []
            current_datetime = self.datetime.datetime(0)
            logger.info("-----")
            logger.info(f"{current_datetime} - Started rebalancing.")
            momentum = {}
            for data in self.data_feeds: 
                if len(data) >= self.p.momentum_window:
                    momentum_factor = self.compute_momentum(data, self.p.momentum_window, self.p.total_window)
                    if momentum_factor > 0: 
                        momentum[data._name] = momentum_factor

            sorted_assets = sorted(momentum.items(), key=lambda x: x[1], reverse=True)
            top_count = int(math.ceil(self.p.num_stocks * self.p.long_percentile))
            self.top_assets = [name for name, _ in sorted_assets[:top_count]]
            logger.info(f"top assets: {self.top_assets}")

            for data in self.data_feeds: 
                if data._name not in self.top_assets and self.getposition(data).size > 0: 
                    self.order_target_percent(data, 0)
                    logger.info(f"{current_datetime} - Target order placed to sell {data._name}. {data._name} no longer has high momentum.")

                if self.getposition(data).size > 0: 
                    self.current_positions.append(data)
            logger.info(f"{current_datetime} - All positions: {[(position._name, self.getposition(position).size * self.getposition(position).price, self.getposition(position).size, self.getposition(position).price) for position in self.current_positions]}")

        # Checks if the current bar is ON the rebalance window
        if ((self.total_counter % self.p.momentum_window == 0) and (self.total_counter >= self.p.total_window)): 
            current_datetime = self.datetime.datetime(0)
            sorted_data_feeds = sorted(
                self.data_feeds,
                key=lambda data: self.getposition(data).size * self.getposition(data).price,
                reverse=True
            )
            for data in sorted_data_feeds: 
                if data._name in self.top_assets: 
                    if self.getposition(data).size > 0: 
                        self.order_target_percent(data, 1.0 / len(self.top_assets))
                        logger.info(f"{current_datetime} - Rebalancing old stock {data._name}. Target order placed for {data._name} to allocate {1.0 / len(self.top_assets):.2%} of the portfolio.")
                    elif self.getposition(data).size == 0:
                        self.order_target_percent(data, 1.0 / len(self.top_assets))
                        logger.info(f"{current_datetime} - Buying new stock {data._name}. Target order placed for {data._name} to allocate {1.0 / len(self.top_assets):.2%} of the portfolio.")
                
            logger.info(f"{current_datetime} - Finished rebalancing. ")
            logger.info("-----")
        
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

        return momentum_factor """

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

        self.benchmark_cerebro = bt.Cerebro()
        self.benchmark_cerebro.broker.setcash(self.initial_cash)
        
    def add_stock_data(self, csv_filename):
        if self.num_stocks_added > self.num_stocks: 
            return
        
        if os.path.exists(csv_filename):
            print(f"{self.num_stocks_added}: Adding {csv_filename} to backtesting engine")
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

    def add_spy_data(self):
        print("Downloading SPY data")
        # Fetch SPY data from yfinance
        spy_data = yf.download("SPY", start=self.start_date, end=self.end_date)
        spy_data.index.name = 'Date'  # Rename index to match your CSV format
        spy_data.reset_index(inplace=True)  # Reset index to make 'Date' a column
        
        # Convert DataFrame to Backtrader data feed
        data = bt.feeds.PandasData(dataname=spy_data, fromdate=self.start_date, todate=self.end_date)
        
        self.benchmark_cerebro.adddata(data, name="SPY")

    def run_backtest(self):
        self.cerebro.addstrategy(
            MomentumStrategy,
            momentum_window=self.momentum_window,
            total_window=self.total_window,
            long_percentile=self.long_percentile,
            num_stocks=self.num_stocks
        )
        self.benchmark_cerebro.addstrategy(Benchmark)
        csv_filename = "data/stock_data/SPY.csv"
        df = pd.read_csv(csv_filename, index_col='Date', parse_dates=True)
        data = bt.feeds.PandasData(dataname=df, 
                                       fromdate=self.start_date,
                                       todate=self.end_date)
        stock_name = os.path.basename(csv_filename).split('.')[0]
        self.benchmark_cerebro.adddata(data, name=stock_name)



        print(f"Starting portfolio value: {self.cerebro.broker.getvalue():,.2f}")
        
        results = self.cerebro.run()
        benchmark_results = self.benchmark_cerebro.run()

        print(f"Final Momentum portfolio value: {self.cerebro.broker.getvalue():,.2f}")
        print(f"Final Benchmark portfolio value: {self.benchmark_cerebro.broker.getvalue():,.2f}")

        # Extract portfolio values and dates for plotting
        momentum_strategy = results[0]
        benchmark_strategy = benchmark_results[0]

        # Plot portfolio values
        plt.figure(figsize=(12, 6))
        plt.plot(momentum_strategy.dates, momentum_strategy.portfolio_values, label='Momentum Strategy')
        plt.plot(benchmark_strategy.dates, benchmark_strategy.portfolio_values, label='Benchmark (SPY)')
        plt.xlabel('Date')
        plt.ylabel('Value')
        plt.title('Portfolio Value Over Time: Momentum Strategy vs Benchmark')
        plt.legend()
        plt.grid()

        # Save the plot to a file
        plot_filename = f"src/data/output_plots/varying_universe_size/N={self.num_stocks}.png"
        plt.savefig(plot_filename)
        plt.close()

        return results, benchmark_results

if __name__ == "__main__": 
    
    start = datetime(2000, 1, 1)
    end = datetime(2024, 8, 23)
    resolution = '1d'
    
    data = HistoricalData(start_date=start, end_date=end, resolution=resolution)
    
    
    
    """ output_file_path = "data/tickers/s+p_500_tickers.json"
    
    tickers_snapshot_file_path = "data/s+p500_snapshots/tickers_snapshot.csv"
    df = pd.read_csv(tickers_snapshot_file_path, index_col='date', parse_dates=True)
    filtered_df = df.loc[start:end]
    unique_tickers = set()
    
    for tickers_string in filtered_df['tickers']: 
        tickers = [ticker.strip() for ticker in tickers_string.split(',')]
        unique_tickers.update(tickers)
        
    unique_tickers_list = sorted(unique_tickers)
    with open(output_file_path, 'w') as json_file: 
        json.dump(unique_tickers_list, json_file, indent=4) """
    
    """ tickers_file_path = "src/data/tickers.json"
    with open(tickers_file_path, 'r') as file:
        tickers_data = json.load(file)
    tickers = tickers_data['tickers'][:1]
    
    start = datetime(2000, 1, 1)
    end = datetime(2024, 8, 23)
    interval = '1d'
    stock_data_dir = "src/data/stock_data"
    
    for ticker in tickers:
        ticker = 'FB'
        data = yf.download(ticker, start=start, end=end, interval=interval)
        ticker_info = yf.Ticker(ticker).info
        market_cap = ticker_info.get('marketCap', None)
        data['Market Cap'] = market_cap
        
        ticker_filename = os.path.join(stock_data_dir, f"{ticker}.csv")
        data.to_csv(ticker_filename)
        print(f"Saved {ticker}.csv") """
        
    
    
    

    """ start = datetime(2001, 1, 2)
    end = datetime(2022, 12, 31)
    
    tickers_snapshot_file_path = "data/s+p500_snapshots/tickers_snapshot.csv"
    df = pd.read_csv(tickers_snapshot_file_path, index_col='date', parse_dates=True)

    # Assuming the column containing tickers is named 'tickers'
    tickers_string = df.asof(start)['tickers']    

    # Convert the tickers string into a list of tickers
    tickers = [ticker.strip() for ticker in tickers_string.split(',')]

    N = 20

    backtester = MomentumStrategyBacktester(
        start_date=start,
        end_date=end,
        num_stocks=N, 
        initial_cash=100000,
        momentum_window=21,
        total_window=252,
        long_percentile=0.1
    )

    csv_dir = "src/data/stock_data"
    for ticker in tickers[:N]:  # Limit the number of tickers based on current universe size
        stock_data_filename = os.path.join(csv_dir, f"{ticker}.csv")
        backtester.add_stock_data(stock_data_filename)
    
    backtester.run_backtest() """