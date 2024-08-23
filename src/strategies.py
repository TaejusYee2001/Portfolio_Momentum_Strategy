import sys
import time
import math
import numpy as np
import pandas as pd
import backtrader as bt
from datetime import datetime, timedelta

class MomentumStrategy(bt.Strategy):
    params = (
        ("momentum_window", 21), 
        ("total_window", 252), 
        ("long_percentile", 0.1),
        ("stock_data", None)
    )
    def __init__(self):
        print("Initializing MomentumStrategy...")
        self.data_feeds = self.datas
        self.last_rebalance_bar = None
        self.portfolio_value = []
        self.start_date = None
        self.momentum_window_counter = 0
        self.total_counter = 0
        
        self.pending_stock_data = dict(self.params.stock_data)
        print(self.params.momentum_window)

    def next(self):
        self.portfolio_value.append(self.broker.getvalue())
                
        #print("Current bar: ", current_bar)
        #print("Total_window: ", self.params.total_window)
        #print("Last rebalance bar: ", self.last_rebalance_bar)
        #time.sleep(0.2)
        
        self.rebalance_portfolio()
        self.total_counter += 1
        self.momentum_window_counter += 1

    def rebalance_portfolio(self):
        momentum_factors = []
        data_to_momentum = {}  # Dictionary to map data feed to its momentum factor

        # Ensure that both conditions are met:
        # 1. `momentum_window` bars have passed since last rebalance
        # 2. At least `total_window` bars have passed since the start
        if (self.total_counter > self.params.total_window and self.momentum_window_counter > self.params.momentum_window):
            print("---")

            print("Rebalancing portfolio")
            self.momentum_window_counter = 0

            # Calculate momentum for each data feed
            for data in self.data_feeds:
                momentum_factor = self.compute_momentum(data, self.params.momentum_window, self.params.total_window)
                momentum_factors.append((momentum_factor, data))
                data_to_momentum[data] = momentum_factor  # Store the momentum factor in the dictionary
        else: 
            return

        # Filter out stocks with non-positive momentum factors
        #print("Momentum factors array: ", [(item[0], item[1]._name, item[1].datetime.datetime()) for item in momentum_factors])
        positive_momentum_factors = [item for item in momentum_factors if item[0] > 0]
        #print("Length of positive momentum factors: ", len(positive_momentum_factors))

        # Sort by momentum factor in descending order
        positive_momentum_factors.sort(key=lambda x: x[0], reverse=True)

        # Determine the top decile stocks from positive momentum factors
        top_decile_count = int(math.ceil(len(positive_momentum_factors) * self.params.long_percentile))
        top_stocks = [data for _, data in positive_momentum_factors[:top_decile_count]]
        
        #print("length of top stocks array: ", len(top_stocks))
        #print("Top Decile Stocks and Their Momentum Factors:")
        #for factor, data in momentum_factors[:top_decile_count]:
        #    print(f"Ticker: {data._name}, Momentum Factor: {factor:.4f}")

        # Close all existing positions
        if len(top_stocks) > 0:
            for data in self.data_feeds:
                if self.getposition(data).size > 0:
                    self.close(data)
        else:
            pass
            #print("No positive momentum values, not adding new stocks to portfolio")

        # Calculate the amount to invest in each top stock
        total_cash = self.broker.getcash()
        if len(top_stocks) > 0:
            #print("Num top stocks: ", len(top_stocks))
            investment_per_stock = total_cash / len(top_stocks)

        # Buy stocks in the top decile, allocating equal cash to each
        for data in top_stocks:
            stock_price = data.close[0]
            size = int(investment_per_stock / stock_price)
            momentum_factor = data_to_momentum[data]  # Retrieve the momentum factor for the current stock
            print(f"Buying {data._name} at price {stock_price} with momentum factor {momentum_factor:.4f} on date {data.datetime.datetime()}")
            self.buy(data=data, size=size)
        
        print("Portfolio rebalanced")
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

""" import numpy as np
import pandas as pd
import backtrader as bt
from datetime import datetime, timedelta

class MomentumStrategy(bt.Strategy):
    params = (
        ('momentum_window', 21), 
        ('total_window', 252), 
        ('long_percentile', 0.1), 
        ('start_date', datetime(2000, 1, 1)),  # Default start date
        ('end_date', datetime(2023, 1, 1)),    # Default end date
        ('resolution', '1d')  # Default resolution
    )
    
    def __init__(self): 
        self.data_feeds = self.datas
        self.last_rebalance_bar = None
        self.portfolio_value = []

        # Convert start_date and end_date to pandas datetime for comparison
        self.start_date = pd.to_datetime(self.params.start_date)
        self.end_date = pd.to_datetime(self.params.end_date)


    def next(self):
        self.portfolio_value.append(self.broker.getvalue())

        # Check if it's time to rebalance based on the momentum window
        current_bar = len(self.data0)
        if self.last_rebalance_bar is None or current_bar - self.last_rebalance_bar >= self.params.momentum_window:
            self.last_rebalance_bar = current_bar
            self.rebalance_portfolio()

    def rebalance_portfolio(self):
        momentum_factors = []
        dollar_volumes = []

        # Calculate momentum for each data feed
        for data in self.data_feeds:
            if len(data) >= self.params.total_window:
                if self.is_data_available(data):
                    df = self.to_dataframe(data)
                    
                    # Calculate dollar volume over the past total_window bars
                    end_date = df.index[-1]
                    start_date = end_date - timedelta(days=self.params.total_window)
                    df_past_total_window = df[(df.index > start_date) & (df.index <= end_date)]
                    
                    # Compute dollar volume for the period
                    dollar_volume = (df_past_total_window['close'] * df_past_total_window['volume']).sum()
                    dollar_volumes.append((dollar_volume, data))

        dollar_volumes.sort(key=lambda x: x[0], reverse=True)
        top_stocks_by_dollar_volume = [data for _, data in dollar_volumes[:150]]

        for data in top_stocks_by_dollar_volume:
            momentum_factor = self.compute_momentum(data, self.params.momentum_window, self.params.total_window)
            momentum_factors.append((momentum_factor, data))

        # Sort by momentum factor in descending order
        momentum_factors.sort(key=lambda x: x[0], reverse=True)

        # Determine the top decile stocks
        top_decile_count = max(int(len(momentum_factors) * self.params.long_percentile), 1)
        top_stocks = [data for _, data in momentum_factors[:top_decile_count]]
        
        # Print the top decile stocks and their momentum factors
        print("Top Decile Stocks and Their Momentum Factors:")
        for factor, data in momentum_factors[:top_decile_count]:
            print(f"Ticker: {data._name}, Momentum Factor: {factor:.4f}")

        # Close all existing positions
        for data in self.data_feeds:
            if self.getposition(data).size > 0:
                self.close(data)

        # Calculate the amount to invest in each top stock
        total_cash = self.broker.getcash()
        investment_per_stock = total_cash / len(top_stocks)

        # Buy stocks in the top decile, allocating equal cash to each
        for data in top_stocks:
            stock_price = data.close[0]
            if stock_price > 0:
                size = int(investment_per_stock / stock_price)
                if size > 0:
                    self.buy(data=data, size=size)

    def is_data_available(self, data):
        df = pd.DataFrame({
            'datetime': [dt.datetime.fromtimestamp(dt) for dt in data.datetime.datetime()]
        })
        df.set_index('datetime', inplace=True)
        
        if len(df) < self.params.total_window:
            return False

        date_total_window_ago = df.index[-self.params.total_window]

        return date_total_window_ago in df.index

    def compute_momentum(self, data, momentum_window, total_window):
        # Convert Backtrader data feed to pandas DataFrame
        df = pd.DataFrame({
            'close': data.close.get(size=len(data)),
            'datetime': data.datetime.datetime()
        })
        df.set_index('datetime', inplace=True)
        df.sort_index(inplace=True)

        if len(df) < total_window:
            print(f"Length of data must be more than {total_window}")
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

""" import numpy as np
import pandas as pd
import backtrader as bt
from datetime import datetime, timedelta

class MomentumStrategy(bt.Strategy):
    params = (
        ('momentum_window', 21), 
        ('total_window', 252), 
        ('long_percentile', 0.1), 
    )
    def __init__(self): 
        self.data_feeds = self.datas
        self.rebalance_bar = None
        self.portfolio_value = []

    def next(self):
        self.portfolio_value.append(self.broker.getvalue())

        # Check if it's time to rebalance based on the momentum window
        current_bar = len(self.data)
        if self.last_rebalance_bar is None or current_bar - self.last_rebalance_bar >= self.params.momentum_window:
            self.last_rebalance_bar = current_bar
            self.rebalance_portfolio()

    def rebalance_portfolio(self):
        momentum_factors = []

        # Calculate momentum for each data feed
        for data in self.data_feeds:
            momentum_factor = self.compute_momentum(data, self.params.momentum_window, self.params.total_window)
            momentum_factors.append((momentum_factor, data))

        # Sort by momentum factor in descending order
        momentum_factors.sort(key=lambda x: x[0], reverse=True)

        # Determine the top decile stocks
        top_decile_count = int(len(momentum_factors) * self.params.long_percentile)
        top_stocks = [data for _, data in momentum_factors[:top_decile_count]]
        
        # Print the top decile stocks and their momentum factors
        print("Top Decile Stocks and Their Momentum Factors:")
        for factor, data in momentum_factors[:top_decile_count]:
            print(f"Ticker: {data._name}, Momentum Factor: {factor:.4f}")

        # Close positions that are no longer in the top decile
        for data in self.positions:
            if data not in top_stocks:
                self.close(data)

        # Buy stocks that are in the top decile and not already held
        for data in top_stocks:
            if data not in self.positions:
                self.buy(data=data, size=1)

    def compute_momentum(self, data, momentum_window, total_window):
        # Convert Backtrader data feed to pandas DataFrame
        df = pd.DataFrame({
            'close': data.close.get(size=len(data)),
            'datetime': data.datetime.datetime()
        })
        df.set_index('datetime', inplace=True)
        df.sort_index(inplace=True)

        if len(df) < total_window:
            print(f"Length of data must be more than {total_window}")
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