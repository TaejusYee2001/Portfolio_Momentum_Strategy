import os
import json
import numpy as np
import pandas as pd
import yfinance as yf
import backtrader as bt
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from src.strategies import MomentumStrategy

# Load tickers
print("Loading tickers data")
tickers_file_path = "src/data/tickers.json"
with open(tickers_file_path, 'r') as file:
    tickers_data = json.load(file)
tickers = tickers_data['tickers'][:30]


start_date = datetime(2019, 1, 1)
end_date = datetime(2023, 1, 1)

cerebro = bt.Cerebro()
cerebro.broker.setcash(100000)

# Download data and add to Cerebro
csv_dir = "src/data/stock_data"
for ticker in tickers:
    csv_file_path = os.path.join(csv_dir, f"{ticker}.csv")
    if os.path.exists(csv_file_path):
        df = pd.read_csv(csv_file_path, index_col='Date', parse_dates=True)
        data_feed = bt.feeds.PandasData(dataname=df, name=ticker)
        cerebro.adddata(data_feed)
    else:
        print(f"Data file for {ticker} does not exist. Skipping.")

cerebro.addstrategy(MomentumStrategy)

print("Starting Portfolio Value: %.2f" % cerebro.broker.getvalue())
strategies = cerebro.run()
print("Ending Portfolio Value: %.2f" % cerebro.broker.getvalue())

portfolio_values = strategies[0].portfolio_value

plt.figure(figsize=(10, 6))
plt.plot(portfolio_values)
plt.title('Portfolio Value Over Time')
plt.xlabel('Time (Bars)')
plt.ylabel('Portfolio Value')
plt.grid(True)
plt.show()

""" # Load tickers
print("Loading tickers data")
tickers_file_path = "src/data/tickers.json"
with open(tickers_file_path, 'r') as file:
    tickers_data = json.load(file)
tickers = tickers_data['tickers']

# Set date range
start_date = datetime(2000, 1, 1)
end_date = datetime(2023, 1, 1)

# Directory to save CSV files
csv_dir = "src/data/stock_data"
os.makedirs(csv_dir, exist_ok=True)

# Function to download and save data
def download_and_save_data(ticker, start_date, end_date, csv_dir):
    csv_file_path = os.path.join(csv_dir, f"{ticker}.csv")
    if not os.path.exists(csv_file_path):
        print(f"Downloading and saving data for {ticker}")
        df = yf.download(ticker, start=start_date, end=end_date)
        if len(df) > 0:  # Only save data if valid
            df.to_csv(csv_file_path)
    else:
        print(f"Data for {ticker} already exists, loading from CSV")

# Download and save data for each ticker
for ticker in tickers:
    download_and_save_data(ticker, start_date, end_date, csv_dir) """


""" import json
import numpy as np
import pandas as pd
import yfinance as yf
import backtrader as bt
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
from src.strategies import MomentumStrategy

print("Downloading tickers data")
tickers_file_path = "src/data/tickers.json"
with open(tickers_file_path, 'r') as file:
    tickers_data = json.load(file)
tickers = tickers_data['tickers'][:150]

cerebro = bt.Cerebro()

for ticker in tickers:
    df = yf.download(ticker, start='2000-01-01', end='2023-01-01')
    if len(df) > 0:  # Only add data feeds with valid data
        data_feed = bt.feeds.PandasData(dataname=df, name=ticker)
        cerebro.adddata(data_feed)

cerebro.addstrategy(MomentumStrategy)
cerebro.broker.setcash(100000)

print("Starting Portfolio Value: %.2f" % cerebro.broker.getvalue())
strategies = cerebro.run()
print("Ending Portfolio Value: %.2f" % cerebro.broker.getvalue())

# Extract portfolio values from the strategy
portfolio_values = strategies[0].portfolio_value

# Plot the portfolio value over time
plt.figure(figsize=(10, 6))
plt.plot(portfolio_values)
plt.title('Portfolio Value Over Time')
plt.xlabel('Time (Bars)')
plt.ylabel('Portfolio Value')
plt.grid(True)
plt.show() """

""" def get_market_caps(tickers, date):
    market_caps = {}
    for ticker in tickers:
        try:
            stock = yf.Ticker(ticker)
            history = stock.history(start=date, end=date + timedelta(days=1))
            if not history.empty:
                market_cap = history['Close'].iloc[0] * stock.info['sharesOutstanding']
                market_caps[ticker] = market_cap
        except Exception as e:
            print(f"Error fetching data for {ticker}: {e}")
    return market_caps """

