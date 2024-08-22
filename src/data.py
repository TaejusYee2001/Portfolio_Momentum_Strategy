import os
import json
import time
import pandas as pd
from pprint import pprint
from ib_api.client import IBClient
from datetime import datetime, timedelta, timezone

tickers_info_file_path = '../src/data/tickers_info.json'
ticker_conid_map_file_path = "../src/data/ticker_conid_map.json"

class MarketData: 
    def __init__(self, tickers, period, resolution, exchange=["NYSE", "NASDAQ"]):
        self.tickers = tickers
        self.period = period
        self.resolution = resolution
        self.exchange = exchange
        self.securities_dir_path = f"../src/data/securities_{period}_{resolution}/"

    def initialize_ib_client(self, username, account_number): 
        """Assumes client is authorized through client portal"""
        self.ib_client = IBClient(username, account_number)
        self.ib_client.create_session()

    
    def extract_conid(self, response_data, ticker):
        for ticker_data in response_data:
            for item in ticker_data:
                if isinstance(item, dict) and 'symbol' in item and 'description' in item:
                    if item['symbol'] == ticker and item['description'] in self.exchange:
                        return item['conid']
        return None
    
    def _securities_dir_exists(self): 
        if os.path.exists(self.securities_dir): 
            return True
        else: 
            return False

    def fetch_historical_data(self, update_tickers=False, update_ticker_conid_map=False):
        if update_tickers:
            self._update_ticker_info()
        
        if update_ticker_conid_map: 
            self._update_ticker_conid_map()

        with open(ticker_conid_map_file_path, 'r') as file: 
            ticker_conid_map = json.load(file)

        for ticker in self.tickers:
            print(f"Fetching data for ticker: {ticker}")
            conid = ticker_conid_map.get(ticker)
            if conid is not None:
                
                start_time = datetime.now(timezone.utc)
                end_time = start_time - self._parse_period(self.period)

                print("Start time: ", self._format_datetime(start_time))
                print("End time: ", self._format_datetime(end_time))

                all_data = pd.DataFrame()

                while start_time > end_time:
                    formatted_start_time = self._format_datetime(start_time)
                    
                    print(f"Fetching data starting from {formatted_start_time}")
                    response = self.ib_client.market_data_history(
                        conid=conid,
                        period=self.period,
                        bar=self.resolution,
                        start_time=formatted_start_time,
                    )

                    data = response['data']
                    if not data:
                        break
                    
                    df = pd.DataFrame(data)
                    print("Data length: ", len(df))
                    df['t'] = df['t'].apply(lambda x: datetime.fromtimestamp(x / 1000, tz=timezone.utc))
                    df = df.rename(columns={
                        'o': 'Open',
                        'c': 'Close',
                        'h': 'High',
                        'l': 'Low',
                        'v': 'Volume',
                        't': 'Datetime'
                    })
                    df = df[['Datetime', 'Open', 'High', 'Low', 'Close', 'Volume']]
                    
                    all_data = pd.concat([all_data, df], ignore_index=True)

                    df = df.sort_values(by='Datetime').reset_index(drop=True)
                    
                    earliest_datetime = df['Datetime'].iloc[0]  # Get the last datetime from the fetched data
                    start_time = earliest_datetime

                
                all_data = all_data.sort_values(by='Datetime').reset_index(drop=True)
                all_data = all_data[all_data['Datetime'] >= end_time]

                if not os.path.exists(self.securities_dir_path): 
                    os.makedirs(self.securities_dir_path)

                csv_file_name = f"{ticker}.csv"
                csv_file_path = os.path.join(self.securities_dir_path, csv_file_name)

                if os.path.exists(csv_file_path):
                    os.remove(csv_file_path)

                all_data.to_csv(csv_file_path, index=False)

                print(f"Data for {ticker} saved to {csv_file_path}")

        print(f"Data for all securities saved to {self.securities_dir_path}")

    def _update_ticker_info(self): 
        tickers_info = []

        for ticker in self.tickers:
            response = self.ib_client.symbol_search(symbol=ticker)
            
            print(f"Fetching info for ticker: {ticker}")
            tickers_info.append(response)

        with open(tickers_info_file_path, 'w') as file:
            json.dump(tickers_info, file, indent=4, sort_keys=True)
        print(f"Tickers info saved to {tickers_info_file_path}")

    def _update_ticker_conid_map(self): 
        with open(tickers_info_file_path, 'r') as file: 
            tickers_info = json.load(file)

        ticker_conid_map = {}
        
        for ticker in self.tickers: 
            conid = self.extract_conid(tickers_info, ticker)
            ticker_conid_map[ticker] = conid

        ticker_conid_map_json = json.dumps(ticker_conid_map, indent=4)

        with open(ticker_conid_map_file_path, 'w') as file: 
            file.write(ticker_conid_map_json)

        print(f"Ticker-conid map saved to {ticker_conid_map_file_path}")


    def _parse_period(self, period_str):
        """Convert period string to a timedelta object."""
        period_type = period_str[-1]
        period_value = int(period_str[:-1])

        if period_type == 'd':
            return timedelta(days=period_value)
        elif period_type == 'w':
            return timedelta(weeks=period_value)
        elif period_type == 'h':
            return timedelta(hours=period_value)
        elif period_type == 'm':
            # Approximate a month as 30 days
            return timedelta(days=period_value * 30)
        elif period_type == 'y':
            # Approximate a year as 365 days
            return timedelta(days=period_value * 365)
        else:
            raise ValueError(f"Unsupported period type: {period_type}")

    def _format_datetime(self, dt):
        """Format datetime as YYYYMMDD-HH:MM:SS."""
        return dt.strftime('%Y%m%d-%H:%M:%S')