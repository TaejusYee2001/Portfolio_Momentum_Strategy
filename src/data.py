import os
import json
import pandas as pd
import yfinance as yf

class HistoricalData: 
    def __init__(self, start_date, end_date, resolution): 
        self.start_date = start_date
        self.end_date = end_date
        self.resolution = resolution
        self.valid_dates = set()
        
        # Directories and filenames
        self.output_dir = "data/stock_data/"
        self.S_and_P_500_snapshot_file = "data/s+p500_snapshots/tickers_snapshot.csv"
        self.tickers_file = "data/tickers/s+p_500_tickers.json"
        
        # Get tickers and download raw data for time period
        self._generate_tickers_json()
        self._download_stock_data()
        self._format_stock_data()
        
    def _generate_tickers_json(self): 
        df = pd.read_csv(self.S_and_P_500_snapshot_file, index_col='date', parse_dates=True)
        filtered_df = df.loc[self.start_date:self.end_date]
        unique_tickers = set()
        
        for tickers_string in filtered_df['tickers']: 
            tickers = [ticker.strip() for ticker in tickers_string.split(',')]
            unique_tickers.update(tickers)
            
        unique_tickers_list = sorted(unique_tickers)
        with open(self.tickers_file, 'w') as json_file: 
            json.dump(unique_tickers_list, json_file, indent=4)
            
    def _download_stock_data(self): 
        with open(self.tickers_file, 'r') as file: 
            self.tickers_list = json.load(file)
        
        for ticker in self.tickers_list:
            if not os.path.exists(os.path.join(self.output_dir, f"{ticker}.csv")):
                data = yf.download(ticker, start=self.start_date, end=self.end_date, interval=self.resolution, progress=False)
                
                if not data.empty:
                    self.valid_dates.update(data.index.strftime('%Y-%m-%d'))
                    ticker_filename = os.path.join(self.output_dir, f"{ticker}.csv")
                    data.to_csv(ticker_filename)
                    #print(f"Saved {ticker}.csv to {self.output_dir}")
                
        self.valid_dates = sorted(self.valid_dates)
        
    def _format_stock_data(self):
        for ticker in self.tickers_list:
            ticker_filename = os.path.join(self.output_dir, f"{ticker}.csv")
            if os.path.exists(ticker_filename):
                df = pd.read_csv(ticker_filename, index_col='Date', parse_dates=True)

                df = df.reindex(pd.to_datetime(self.valid_dates))
                
                df.fillna(-1, inplace=True)
                
                df.to_csv(ticker_filename)
                print(f"Formatted {ticker}.csv to include all valid dates")
