import os
import math
import logging
import numpy as np
import pandas as pd
import pandas_ta as ta
import backtrader as bt
import scipy.stats as sps
import statsmodels.api as sm

logging.basicConfig(
    level=logging.INFO, 
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/backtest_output.log'),
    ]
)

logger = logging.getLogger(__name__)

class MomentumStrategy(bt.Strategy):
    params = (
        ("momentum_window", 0),
        ("total_window", 0),
        ("long_percentile", 0.0),
        ("num_stocks", 0),
        ("plot_only", False)
    )
    
    def __init__(self):
        self.data_feeds = self.datas
        self.top_assets = []
        self.current_positions = []
        self.portfolio_values = []
        self.dates = []
        self.hursts = []
        self.pvalues = []
        self.total_counter = 0
        self.prev_hurst = 0.5
        self.prev_pvalue = 0

        # clear logs
        if os.path.exists('logs/backtest_output.log'):
            with open('logs/backtest_output.log', 'w'):
                pass
        
    def next(self):
        power = 8
        num_values = 2**power + 1
        
        # Check if there are enough data points
        if self.total_counter > num_values:
            self.portfolio_values.append(self.broker.getvalue())
            self.dates.append(self.data.datetime.date(0))  
            # Use Backtrader's methods to get the most recent num_values
            data_list = [self.data.close[i] for i in range(-num_values, 0)]  # Replace .close with the appropriate line if needed
            
            # Ensure compute_hurst_exponent handles the data_list correctly
            hursts, tstats, pvalues = self.compute_hurst_exponent(data_list, power)

            if ((self.total_counter % self.p.momentum_window == 0) and (self.total_counter >= self.p.total_window)):
                if hursts[0] > 0.5 and pvalues[0] < 0.05:
                    logger.info("-----")
                    logger.info("Rebalancing -- market is momentum driven.")
                    self.rebalance_portfolio()
                else:
                    logger.info("-----")
                    logger.info("Staying in cash -- market is not momentum driven.")
                    for data in self.data_feeds:
                        if self.getposition(data).size > 0:
                            self.order_target_percent(data, 0)

                self.hursts.append(hursts[0])
                self.pvalues.append(pvalues[0])
                self.prev_hurst = hursts[0]
                self.prev_pvalue = pvalues[0]
            else: 
                self.hursts.append(self.prev_hurst)
                self.pvalues.append(self.prev_pvalue)

            """ if hursts[0] > 0.5 and pvalues[0] < 0.05:
                if ((self.total_counter % self.p.momentum_window == 0) and (self.total_counter >= self.p.total_window)):
                    logger.info("-----")
                    logger.info("Rebalancing -- market is momentum driven.")
                    self.rebalance_portfolio()

                    self.hursts.append(hursts[0])
                    self.pvalues.append(pvalues[0])
                    self.prev_hurst = hursts[0]
                    self.prev_pvalue = pvalues[0]
                else: 
                    self.hursts.append(self.prev_hurst)
                    self.pvalues.append(self.prev_pvalue)
            else:
                logger.info("-----")
                logger.info("Staying in cash -- market is not momentum driven.")
                for data in self.data_feeds:
                    if self.getposition(data).size > 0:
                        self.order_target_percent(data, 0) """
                        
        self.total_counter += 1

    def rebalance_portfolio(self):
        # Checks if the current bar is on the rebalance window
        if ((self.total_counter % self.p.momentum_window == 0) and (self.total_counter >= self.p.total_window)):
            current_datetime = self.datetime.datetime(0)
            
            # Filter data feeds to remove stocks with volume == -1 
            # for any date in the past total_window days. 
            # This indicates that the stock was not tradeable
            filtered_data_feeds = [data for data in self.data_feeds if all((data.volume[0 - i] > 0 and data.close[0 - i] > 0 )for i in range(self.p.total_window))]            
            
            # Sort data by dollar volume
            dollar_volumes = {
                data: sum(data.volume[0 - i] * data.close[0 - i] for i in range(self.p.total_window))
                for data in filtered_data_feeds
            }
            sorted_by_dollar_volume = sorted(filtered_data_feeds, key=lambda data: dollar_volumes[data], reverse=True)
            
            # Construct the universe by selecting the top N stocks by dollar volume
            data_universe = sorted_by_dollar_volume[:self.p.num_stocks]
            print(len(data_universe))

            # Compute momentum for each stock in the universe
            momentum_factors = {}
            for data in data_universe:
                momentum_factor = self.compute_rsi(data, self.p.momentum_window, self.p.total_window)
                #momentum_factor = self.compute_macd(data)
                momentum_factors[data] = momentum_factor
                #print(f"Date: {current_datetime}, Stock: {data._name}, Dollar Volume: {dollar_volumes[data]:,.2f}, Volume: {data.volume[0]:,.2f}, Momentum Factor: {momentum_factors[data]:,.2f}")
            
            # Create list of top stocks ranked by momentum
            sorted_by_momentum = sorted(data_universe, key=lambda data: momentum_factors[data], reverse=True)
            
            # Generate a list of stocks to long by selecting
            # the top percentile of stocks sorted by momentum,
            # excluding stocks with negative momentum factors
            num_stocks_to_long = int(math.ceil(self.p.num_stocks * self.p.long_percentile))
            stocks_to_long = sorted_by_momentum[:num_stocks_to_long]
            stocks_to_long = [data for data in stocks_to_long if momentum_factors[data] > 0]
            print(len(stocks_to_long))

            total_momentum = sum(momentum_factors[data] for data in stocks_to_long)
            target_percentages = {}
            for data in stocks_to_long:
                if total_momentum > 0:
                    target_percentages[data] = (momentum_factors[data] / total_momentum) * 0.9
                else:
                    target_percentages[data] = 0
                    #target_percentages[data] = 0.16

            # Fetch current positions
            current_holdings = [data for data in self.data_feeds if self.getposition(data).size > 0]
            logger.info("Current holdings:")
            for data in current_holdings:
                logger.info(f"{data._name}")
            
            # Sell any stocks which are currently being held
            # but are not in the stocks_to_long list
            for data in current_holdings:
                if data not in stocks_to_long:
                    self.order_target_percent(data, 0)
                    logger.info(f"Selling {data._name}: {data._name} is no longer high momentum.")
            
            if len(stocks_to_long) > 0:
                # Rebalance all stocks in the stocks_to_long list
                for data in stocks_to_long:
                    if data.volume[0] > 0:
                        target_percent = target_percentages[data]
                        if data in current_holdings:
                            self.order_target_percent(data, target_percent)
                            logger.info(f"Rebalancing {data._name}: {data._name} is still high momentum. New target: {target_percent:.2%}")
                
                for data in stocks_to_long: 
                    if data.volume[0] > 0: 
                        target_percent = target_percentages[data]
                        if data not in current_holdings: 
                            self.order_target_percent(data, target_percent)
                            logger.info(f"Buying {data._name}: {data._name} became high momentum. Target: {target_percent:.2%}")
            
            logger.info(f"{current_datetime} - Finished rebalancing. ")
            logger.info("-----")

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
    
    def compute_hurst_exponent(self, data, power):
        n = 2**power
        # Compute returns
        prices = np.array(data)[1:]
        returns = prices / np.array(data)[:-1] - 1
        # Initialize empty arrays
        hursts = np.array([])
        tstats = np.array([])
        pvalues = np.array([])
        # Start sliding the rolling window from n to the end of array
        # (need to wait for n values to compute the first hurst exponent value)
        for t in np.arange(n, len(returns) + 1):
            # Rolling window sample
            data = returns[t-n:t]
            # Generate list of powers of two
            X = np.arange(2, power + 1)
            # Initialize empty array for mean adjusted series
            Y = np.array([])
            # Iterate through list of powers of two
            for p in X:
                # Indexing for window subdivisions
                m = 2**p
                s = 2**(power - p)
                rs_array = np.array([])
                for i in np.arange(0, s):
                    # Subsample window (depends on m which depends on the power p)
                    subsample = data[i*m:(i+1)*m]
                    # Compute mean
                    mean = np.average(subsample)
                    deviate = np.cumsum(subsample - mean)
                    difference = max(deviate) - min(deviate)
                    stdev = np.std(subsample)
                    rescaled_range = difference / stdev
                    rs_array = np.append(rs_array, rescaled_range)
                Y = np.append(Y, np.log2(np.average(rs_array)))
            reg = sm.OLS(Y, sm.add_constant(X))
            res = reg.fit()
            hurst = res.params[1]
            tstat = (res.params[1] - 0.5) / res.bse[1]
            pvalue = 2 * (1 - sps.t.cdf(abs(tstat), res.df_resid))
            hursts = np.append(hursts, hurst)
            tstats = np.append(tstats, tstat)
            pvalues = np.append(pvalues, pvalue)
        
        return hursts, tstats, pvalues
            
        
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
    
    def compute_rsi(self, data, rsi_window, total_window):
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
        rsi_window_start = df.index[-rsi_window]

        # Calculate RSI
        df_last_total_window = df[df.index >= total_window_start]
        df_last_total_window['RSI'] = ta.rsi(df_last_total_window['close'], length=rsi_window)

        # Ensure RSI values are computed
        if df_last_total_window['RSI'].isnull().all():
            print(f"Not enough data to compute RSI")
            return 0

        # Compute RSI value for the most recent date
        latest_rsi = df_last_total_window['RSI'].iloc[-1]
        
        # Return 100 - RSI
        return 100 - latest_rsi
    
    def compute_macd(self, data, fast=12, slow=26, signal=9, total_window=None):
        # Convert Backtrader data feed to pandas DataFrame
        df = pd.DataFrame({
            'close': data.close.get(size=len(data)),
            'datetime': data.datetime.datetime()
        })
        df.set_index('datetime', inplace=True)
        df.sort_index(inplace=True)

        if total_window is not None and len(df) < total_window:
            print(f"Length of data must be at least {total_window}")
            return 0

        # Calculate MACD
        macd = ta.macd(df['close'], fast=fast, slow=slow, signal=signal)
        
        # Ensure MACD values are computed
        if macd['MACD_12_26_9'].isnull().all() or macd['MACDs_12_26_9'].isnull().all():
            print(f"Not enough data to compute MACD")
            return 0

        # Compute MACD histogram (MACD line - Signal line)
        macd['MACD_hist'] = macd['MACD_12_26_9'] - macd['MACDs_12_26_9']

        # If total_window is specified, only consider the last total_window periods
        if total_window is not None:
            macd = macd.iloc[-total_window:]

        # Compute momentum factor based on MACD histogram
        momentum_factor = macd['MACD_hist'].iloc[-1]

        return momentum_factor