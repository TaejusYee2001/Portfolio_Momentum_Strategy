import os
import json
import pandas as pd
import matplotlib.pyplot as plt
from pprint import pprint
from dotenv import load_dotenv

from src.data import MarketData
from client_portal.bin.utils import start_client_portal, stop_client_portal, login_client_portal


if __name__ == "__main__":

    load_dotenv()

    paper_username = os.getenv("PAPER_USERNAME")
    paper_password = os.getenv("PAPER_PASSWORD")
    paper_account_number = os.getenv("PAPER_ACCOUNT_NUMBER")
    
    start_client_portal()
    login_client_portal(paper_username, paper_password)

    #tickers_file_path = "../src/data/tickers.json"
    #with open(tickers_file_path, 'r') as file:
    #    tickers_data = json.load(file)
    #tickers = tickers_data['tickers'][:100]
    
    #data = MarketData(tickers, "23y", "1d")
    #data = MarketData(['GOOGL'], "23y", "1d")
    #data.initialize_ib_client(paper_username, paper_account_number)
    #data.fetch_historical_data()

    """ def load_stock_data(file_path): 
        df = pd.read_csv(file_path, parse_dates=['Datetime'])
        df.set_index('Datetime', inplace=True)
        df.sort_index(inplace=True)
        return df
    
    def compute_momentum(df):
        # Ensure data is sorted by datetime
        df.sort_index(inplace=True)

        if len(df) < 60:  # Require at least 60 days of data
            return 0

        # Define date ranges
        now = df.index[-1]
        two_months_ago = now - pd.DateOffset(months=2)
        one_week_ago = now - pd.DateOffset(weeks=1)

        # Get the price change up to before the previous week
        df_past_2_months = df[(df.index >= two_months_ago) & (df.index <= one_week_ago)]
        if len(df_past_2_months) > 0:
            price_change_2_months = (df_past_2_months['Close'].iloc[-1] - df_past_2_months['Close'].iloc[0]) / df_past_2_months['Close'].iloc[0] * 100
        else:
            price_change_2_months = 0

        # Get the price change over the last week
        df_past_week = df[(df.index > one_week_ago) & (df.index <= now)]
        if len(df_past_week) > 0:
            price_change_week = (df_past_week['Close'].iloc[-1] - df_past_week['Close'].iloc[0]) / df_past_week['Close'].iloc[0] * 100
        else:
            price_change_week = 0

        # Calculate daily returns and standard deviation over the last two months
        df_last_2_months = df[df.index >= two_months_ago]
        df_last_2_months['Daily_Return'] = df_last_2_months['Close'].pct_change()
        std_dev = df_last_2_months['Daily_Return'].std()

        # Compute momentum factor
        if std_dev != 0:  # To avoid division by zero
            momentum_factor = (price_change_2_months - price_change_week) / std_dev
        else:
            momentum_factor = 0
        return momentum_factor
    
    def compute_and_plot_momentum(df):
        # Lists to store the computed momentum factors and corresponding dates
        momentum_factors = []
        dates = []

        # Lists to store the stock prices for the corresponding dates
        close_prices = []

        marker_dates = []
        marker_prices = []
        marker_colors = []

        for i in range(60, len(df)):
            df_window = df.iloc[i-60:i]
            momentum = compute_momentum(df_window)
            dates.append(df.index[i])
            momentum_factors.append(momentum)
            close_prices.append(df['Close'].iloc[i])

            # Check if momentum factor crosses above or below 0
            if momentum > 0:
                marker_dates.append(df.index[i])
                marker_prices.append(df['Close'].iloc[i])
                marker_colors.append('green')
            elif momentum < 0:
                marker_dates.append(df.index[i])
                marker_prices.append(df['Close'].iloc[i])
                marker_colors.append('red')

        # Create the plot
        fig, ax1 = plt.subplots(figsize=(14, 7))

        # Plot the stock price (close) on the primary y-axis
        ax1.set_xlabel('Date')
        ax1.set_ylabel('Close Price', color='tab:blue')
        ax1.plot(dates, close_prices, color='tab:blue', label='Close Price')
        ax1.tick_params(axis='y', labelcolor='tab:blue')
        ax1.set_title('Momentum Factor and Close Price Over Time')

        # Plot green and red markers on the price chart
        for date, price, color in zip(marker_dates, marker_prices, marker_colors):
            ax1.scatter(date, price, color=color, s=5, zorder=5)


        # Create a secondary y-axis for the momentum factor
        ax2 = ax1.twinx()
        ax2.set_ylabel('Momentum Factor', color='tab:red')
        ax2.plot(dates, momentum_factors, color='tab:red', label='Momentum Factor', linestyle='--')
        ax2.tick_params(axis='y', labelcolor='tab:red')

        ax2.axhline(y=0, color='gray', linestyle='--', linewidth=0.7)

        # Add a legend and grid
        ax1.legend(loc='upper left')
        ax2.legend(loc='upper right')
        ax1.grid(True)

        # Show the plot
        plt.show()

    file_path = data.securities_dir_path+"AMZN.csv"
    df_stock = load_stock_data(file_path)
    compute_and_plot_momentum(df_stock) 
    """

    """ib_client = IBClient(paper_username, paper_account_number)
    ib_client.create_session() 
    """

    """ account_data = ib_client.portfolio_accounts()
    pprint('Portfolio Accounts')
    pprint(account_data)
    """

    input("Press Enter to stop the client portal...")
    stop_client_portal()