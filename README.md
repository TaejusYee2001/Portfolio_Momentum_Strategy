# Momentum Based Long Only ETF Portfolio Strategy

## Project Overview
This project implements a momentum-based long-only portfolio strategy using Exchange-Traded-Funds (ETFs). The strategy chooses ETFs from a predefined universe to identify and invest in based on which securities show the strongest positive momentum. This Python-based project allows you to backtest the strategy using historical data, optimize parameters, and evaluate portfolio performance through various metrics. 

## Installation Instructions
### Prerequisites
- Python 3.8+
- Pandas
- NumPy
- Backtrader
- EodHD or yFinance
- Pandas-ta
### Install Dependencies
Start by cloning the repository: 
```bash
git clone https://github.com/Ruminate-Capital/trading.git
```
To install the required packages, run the following command:

```bash
pip install -r requirements.txt
```
## Usage Instructions (Backtest)
To run the backtest with the predefined list of stocks we chose, simply run the backtest.py file. 

Note: this repository also supports execution on historical S&P 500 stocks, fetched using delisted data from EodHD. To test this functionality, see ```src/data.py```, and use the SPYHistoricalData class. This code will check the list of historical S&P 500 constituents and trade them in backtests, simulating historical portfolio management without introducing survivorship bias. 

## Usage Instructions (Live)
Launch trader workstation and log in. Then, open notebooks/etf_momentum_hurst_live_trading.ipynb and run all cells. 

## Strategy Description
This strategy follows a momentum-based approach to select and invest in ETFs.
- Universe Selection: The strategy starts with a predefined universe of ETFs covering various asset classes and 
sectors.
- Momentum Calculation: For each ETF in the universe, the strategy calculates momentum the Relative Strength Index (RSI).
- Ranking: ETFs are ranked based on their momentum scores.
- Portfolio Construction: A top percentile of the ETFs with the highest momentum scores are selected for the portfolio.
- Rebalancing: The portfolio is rebalanced periodically (e.g., weekly or monthly) to maintain exposure to the ETFs with the strongest momentum. Percentage allocation of capital to individual ETFs is proportional to the strength of the momentum factor.
- Risk Management: The strategy implements a Hurst Exponent market regime filter to manage risk and exit trading in market environments which are not conducive to momentum-based trading.

## Results
- Hurst exponent for different time series: Plotted below are four time series expressing different levels of mean-reverting and trending behaviour. We can see from the labeled values that hurst exponents above 0.5 indicate trending behaviour whereas hurst exponents below 0.5 indicate mean-reverting behaviour. For more information on the mathematics behind the hurst exponent, see docs/hurst_exponent_derivation.pdf.
![image](https://github.com/TaejusYee2001/Portfolio_Momentum_Strategy/blob/main/results/hurst_exponent_for_different_time_series.png)
- Hurst exponent visualization for SPY: Plotted below are the hurst exponent and p-value curves. We can notice that generally, the hurst exponent of SPY is above 0.5, indicating trending market behaviour. Additionally, in severe market downturns, the hurst drops significantly, and its p-value increases significantly, making this indicator good for determining market regimes.
![image](https://github.com/TaejusYee2001/Portfolio_Momentum_Strategy/blob/main/results/hurst_exponent_visualization.png)
- Backtest results: The strategy exhibits comparable returns with far lower risk in comparison to a buy-and-hold baseline strategy executed on the Pacer Trendpilot 100 (PTNQ) ETF. Plotted below are the portfolio return, hurst exponent and p-value, and drawdown curves.
![image](https://github.com/TaejusYee2001/Portfolio_Momentum_Strategy/blob/main/results/etf_portfolio_momentum_backtest.png)
- Monte Carlo optimization: Plotted below are the Monte Carlo simulation results. Optimizing the strategy drawdown over the percentage allocation and rebalancing frequency parameters, we arrived at 0.38 as the optimal percentage of the ticker universe to trade at a given time, and 14 days as the best rebalancing frequency.
![image](https://github.com/TaejusYee2001/Portfolio_Momentum_Strategy/blob/main/results/monte_carlo_results.png)

## Areas for Further Research
- Exploring alternative momentum calculation methods.
- Incorporating other strategies when the regime filter prevents execution of the momentum strategy.
- Testing on different bar sizes (Hourly, Daily). 
