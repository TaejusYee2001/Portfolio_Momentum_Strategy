import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

def plot_momentum_portfolio_strategy(strategy_results, initial_cash):
    momentum_strategy = strategy_results[0]

    # Calculate the benchmark strategy (buy and hold SPY)
    spy_data = yf.download('PTNQ', start=momentum_strategy.dates[0], end=momentum_strategy.dates[-1], progress=False)
    initial_spy_price = spy_data['Adj Close'].iloc[0]
    spy_shares = initial_cash / initial_spy_price
    spy_values = spy_data['Adj Close'] * spy_shares
    print(f"Final Benchmark value: {spy_values.iloc[-1]:,.2f}")

    # Reindex spy_values to match momentum strategy dates
    spy_values = spy_values.reindex(momentum_strategy.dates, method='ffill')
    momentum_dates = momentum_strategy.dates
        
    momentum_drawdown = calculate_drawdown(pd.Series(momentum_strategy.portfolio_values))
    spy_drawdown = calculate_drawdown(spy_values)

    hursts = momentum_strategy.hursts
    pvalues = momentum_strategy.pvalues

    # Plot portfolio values
    fig, (ax1, ax2, ax3) = plt.subplots(3, 1, figsize=(12, 18), sharex=True)

    ax1.plot(momentum_dates, momentum_strategy.portfolio_values[:len(momentum_dates)], label='Momentum Strategy')
    ax1.plot(momentum_dates, spy_values[:len(momentum_dates)], label='PTNQ Benchmark')
    ax1.set_ylabel('Value')
    ax1.set_title('Portfolio Value Over Time: Momentum Strategy vs PTNQ Benchmark')
    ax1.legend()
    ax1.grid()

    # Plot rolling Sharpe ratio
    ax2.plot(momentum_dates[len(momentum_dates) - len(hursts):], hursts, label='Hurst exponent')
    ax2.plot(momentum_dates[len(momentum_dates) - len(pvalues):], pvalues, label='P-values')
    ax2.axhline(y=0.05, color='r', linestyle='--', label='P-value = 0.05')
    ax2.axhline(y=0.5, color='g', linestyle='--', label='Hurst = 0.5')
    ax2.set_ylabel('Sharpe Ratio')
    ax2.set_title('Rolling Window Hurst Exponents and P-values for SPY')
    ax2.legend()
    ax2.grid()

    # Plot drawdown
    ax3.fill_between(momentum_dates, momentum_drawdown[:len(momentum_dates)], 0, alpha=0.3, label='Momentum Drawdown')
    ax3.fill_between(momentum_dates, spy_drawdown[:len(momentum_dates)], 0, alpha=0.3, label='SPY Drawdown')
    ax3.set_ylabel('Drawdown')
    ax3.set_title('Drawdown Over Time: Momentum Strategy vs PTNQ Benchmark')
    ax3.legend()
    ax3.grid()

    plt.xlabel('Date')
    plt.savefig('backtrader_strategy_plot.png')
    plt.close()

def calculate_drawdown(series):
    """
    Calculates the drawdown of a given time series.
    """
    peak = series.cummax()
    dd = (series - peak) / peak
    return dd