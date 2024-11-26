import math
import logging
import numpy as np
import pandas as pd
import yfinance as yf
import wikipedia as wp
import backtrader as bt
import matplotlib.pyplot as plt
from datetime import datetime

# NASDAQ 100 
# RUSSEL 1000
        
logging.basicConfig(
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

        return momentum_factor