import os
import warnings
import pandas as pd
from eodhd import APIClient
from dotenv import load_dotenv

# Suppress FutureWarnings
warnings.simplefilter(action='ignore', category=FutureWarning)

load_dotenv()

class SPYHistoricalData: 
    def __init__(self, start_date, end_date, resolution, tickers=None, redownload=True): 
        self.start_date = start_date
        self.end_date = end_date
        self.resolution = resolution

        # Directories and filenames
        self.output_dir = f"data/stock_data/stock_data_{start_date.strftime('%m-%d-%Y')}-{end_date.strftime('%m-%d-%Y')}/"
        if not os.path.exists(self.output_dir): 
            os.makedirs(self.output_dir)

        self.SP_500_snapshot_file = "data/ticker_snapshots/s+p_500_tickers_snapshot.csv"
        self.tickers_file = "data/tickers/SP_500_tickers.json"

        
        # Generate list of tickers included in S&P500 from start date to end date
        df = pd.read_csv(self.SP_500_snapshot_file, index_col = 'date', parse_dates=True)
        filtered_df = df.loc[self.start_date:self.end_date]
        unique_tickers = set()
        ticker_addition_dates = {}

        if tickers is None:
            for date, tickers_string in filtered_df['tickers'].items(): 
                tickers = [ticker.strip() for ticker in tickers_string.split(",")]
                for ticker in tickers:
                    if ticker not in unique_tickers:
                        unique_tickers.add(ticker)
                        ticker_addition_dates[ticker] = date

            self.unique_tickers_list = sorted(unique_tickers)
        else:
            self.unique_tickers_list = tickers
        
        if redownload:
            # Download tickers data to the appropriate directory: 
            eod_api_key = os.getenv('EOD_API_KEY')
            client = APIClient(eod_api_key)
            for ticker in self.unique_tickers_list: 
                ticker_filename = f"{ticker}.csv"
                if not os.path.exists(os.path.join(self.output_dir, ticker_filename)): 
                    stock_data_json = client.get_eod_historical_stock_market_data(
                        symbol=ticker, 
                        from_date=self.start_date.strftime('%Y-%m-%d'),
                        to_date=self.end_date.strftime('%Y-%m-%d'),
                        period=self.resolution
                    )
                    data = pd.DataFrame(stock_data_json)
                    if not data.empty: 
                        # Rename columns to match Backtrader's expected format
                        data = data.rename(columns={
                            'date': 'Date',
                            'open': 'Open',
                            'high': 'High',
                            'low': 'Low',
                            'close': 'Close',
                            'adjusted_close': 'Adj Close',
                            'volume': 'Volume'
                        })
                        data['Date'] = pd.to_datetime(data['Date'])
                        data.set_index('Date', inplace=True)
                        data.index.name = 'Date'
                        
                        # Check for zero or negative values and replace them
                        columns_to_check = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
                        should_save = True
                        for column in columns_to_check:
                            if (data[column] <= 0).any():
                                zero_or_negative_values = data[data[column] <= 0][column]
                                print(f"{ticker} has zero or negative values in column '{column}':")
                                print(zero_or_negative_values)

                                # Check for more than 14 consecutive zero values
                                zero_series = (data[column] == 0).astype(int)
                                consecutive_zeroes = (zero_series != zero_series.shift()).cumsum()
                                max_consecutive_zeroes = zero_series.groupby(consecutive_zeroes).transform('sum').max()
                                
                                if max_consecutive_zeroes > 14:
                                    print(f"{ticker} has more than 14 consecutive zero values in column '{column}', skipping file.")
                                    should_save = False
                                
                                # Replace zero or negative values with previous row's value
                                data[column] = data[column].astype(float).replace(0, pd.NA).ffill().infer_objects()
                        
                        if should_save:
                            # Save the data to a CSV file
                            ticker_filepath = os.path.join(self.output_dir, ticker_filename)
                            data.to_csv(ticker_filepath)

            valid_dates = set()
            for ticker in self.unique_tickers_list: 
                ticker_filename = f"{ticker}.csv"
                ticker_filepath = os.path.join(self.output_dir, ticker_filename)
                if os.path.exists(ticker_filepath):
                    data = pd.read_csv(ticker_filepath, parse_dates=['Date'], index_col='Date')
                    
                    # add all dates present in the csv file to the valid_dates set
                    valid_dates.update(data.index.strftime('%Y-%m-%d'))
                    
                    # Set values to -1 for dates before the ticker was added to the S&P 500
                    addition_date = ticker_addition_dates[ticker]
                    data.loc[data.index < addition_date, ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']] = -1
                    data.index.name = 'Date'
                    data.to_csv(ticker_filepath)
                    
            # Ensure all tickers have data for all valid dates
            for ticker in self.unique_tickers_list:
                ticker_filename = f"{ticker}.csv"
                ticker_filepath = os.path.join(self.output_dir, ticker_filename)
                if os.path.exists(ticker_filepath):
                    data = pd.read_csv(ticker_filepath, parse_dates=['Date'], index_col='Date')
                    
                    # Find missing dates
                    missing_dates = sorted(set(valid_dates) - set(data.index.strftime('%Y-%m-%d')))
                    
                    # Create a DataFrame with missing dates filled with -2
                    missing_data = pd.DataFrame(
                        index=pd.to_datetime(missing_dates),
                        columns=['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume'],
                        data=-2
                    )
                    
                    # Concatenate the existing data with the missing data
                    data = pd.concat([data, missing_data]).sort_index()
                    data.index.name = 'Date'
                    
                    data.to_csv(ticker_filepath)


class ETFHistoricalData:
    def __init__(self, start_date, end_date, resolution, etf_tickers=None):
        self.etf_tickers = etf_tickers
        self.start_date = start_date
        self.end_date = end_date
        self.resolution = resolution

        # Directories and filenames
        self.output_dir = f"data/stock_data/stock_data_{start_date.strftime('%m-%d-%Y')}-{end_date.strftime('%m-%d-%Y')}/"
        if not os.path.exists(self.output_dir): 
            os.makedirs(self.output_dir)

        # Download tickers data to the appropriate directory: 
        eod_api_key = os.getenv('EOD_API_KEY')
        client = APIClient(eod_api_key)
        for ticker in etf_tickers: 
            ticker_filename = f"{ticker}.csv"
            if not os.path.exists(os.path.join(self.output_dir, ticker_filename)): 
                stock_data_json = client.get_eod_historical_stock_market_data(
                    symbol=ticker, 
                    from_date=self.start_date.strftime('%Y-%m-%d'),
                    to_date=self.end_date.strftime('%Y-%m-%d'),
                    period=self.resolution
                )
                data = pd.DataFrame(stock_data_json)
                if not data.empty: 
                    # Rename columns to match Backtrader's expected format
                    data = data.rename(columns={
                        'date': 'Date',
                        'open': 'Open',
                        'high': 'High',
                        'low': 'Low',
                        'close': 'Close',
                        'adjusted_close': 'Adj Close',
                        'volume': 'Volume'
                    })
                    data['Date'] = pd.to_datetime(data['Date'])
                    data.set_index('Date', inplace=True)
                    data.index.name = 'Date'
                    
                    # Check for zero or negative values and replace them
                    columns_to_check = ['Open', 'High', 'Low', 'Close', 'Adj Close', 'Volume']
                    should_save = True
                    for column in columns_to_check:
                        if (data[column] <= 0).any():
                            zero_or_negative_values = data[data[column] <= 0][column]
                            #print(f"{ticker} has zero or negative values in column '{column}':")
                            #print(zero_or_negative_values)

                            # Check for more than 14 consecutive zero values
                            zero_series = (data[column] == 0).astype(int)
                            consecutive_zeroes = (zero_series != zero_series.shift()).cumsum()
                            max_consecutive_zeroes = zero_series.groupby(consecutive_zeroes).transform('sum').max()
                            
                            if max_consecutive_zeroes > 21:
                                print(f"{ticker} has more than 14 consecutive zero values in column '{column}', skipping file.")
                                #should_save = False
                            
                            # Replace zero or negative values with previous row's value
                            data[column] = data[column].astype(float).replace(0, pd.NA).ffill().infer_objects()
                    
                    if should_save:
                        # Save the data to a CSV file
                        ticker_filepath = os.path.join(self.output_dir, ticker_filename)
                        data.to_csv(ticker_filepath)