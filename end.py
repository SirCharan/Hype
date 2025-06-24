import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

def simulate_delta_neutral(
    spot_prices: pd.Series,
    perp_prices: pd.Series,
    funding_rates: pd.Series,
    capital: float = 23_000,
    a: float = 89/100,
    sl_mult: float = 1.1,
    fee_spot_entry: float = 0.0007,
    fee_perp_entry: float = 0.00045,
    fee_spot_exit: float = 0.0004,
    fee_perp_exit: float = 0.00015,
    fund_thresh: float = 0.00001,
    spot_price_exit_multiplier: float = 1.0,
) -> tuple[pd.DataFrame, dict, pd.DataFrame, float]:
    """
    Simulates a delta-neutral trading strategy using spot prices, perpetual futures prices, and funding rates.

    The strategy enters a trade when the perpetual price is higher than the spot price and the funding rate is above a threshold.
    It exits when the perpetual price rises by a certain multiple (stop-loss), when the perpetual price falls below the spot price,
    or when the funding rate falls below the threshold.

    Parameters:
    - spot_prices (pd.Series): Time series of spot prices.
    - perp_prices (pd.Series): Time series of perpetual futures prices.
    - funding_rates (pd.Series): Time series of funding rates (positive means position earns funding).
    - capital (float): Total trading capital. Default is 23,000.
    - a (float): Fraction of capital allocated to the trade. Default is 89/100.
    - sl_mult (float): Stop-loss multiplier for perpetual price. Default is 1.1.
    - fee_spot_entry (float): Spot trading fee for entry. Default is 0.0007 (0.07%).
    - fee_perp_entry (float): Perpetual trading fee for entry. Default is 0.00045 (0.045%).
    - fee_spot_exit (float): Spot trading fee for exit. Default is 0.0004 (0.040%).
    - fee_perp_exit (float): Perpetual trading fee for exit. Default is 0.00015 (0.015%).
    - fund_thresh (float): Funding rate threshold for entry and exit. Default is 0.00001.
    - spot_price_exit_multiplier (float): Multiplier for the spot price in the exit condition. Default is 1.0.

    Returns:
    - df (pd.DataFrame): DataFrame with columns for spot, perp, fund_rate, entry, exit, exit_clause, yield_before_fees, yield_after_fees.
    - stats (dict): Dictionary with counts of each exit clause (1: stop-loss, 2: perp < spot, 3: fund_rate < thresh).
    - trade_df (pd.DataFrame): DataFrame with detailed information for each trade.
    - time_utilization_percentage (float): Percentage of time the strategy is in play.
    """

    # Step 1: Create a DataFrame with the input time series and remove any rows with missing values
    df = pd.DataFrame({
        'spot': spot_prices,
        'perp': perp_prices,
        'fund_rate': funding_rates,
    }).dropna()

    # Step 2: Initialize trade tracking variables
    in_trade = False
    entry_price_perp = 0.0
    entry_price_spot = 0.0
    entry_time = None
    cum_before = 0.0  # Cumulative yield before fees
    cum_after = 0.0   # Cumulative yield after fees
    stats = {1: 0, 2: 0, 3: 0}  # Exit clauses: 1 - stop-loss, 2 - perp < spot, 3 - fund_rate < thresh
    all_trades = []  # List to store trade details
    allocated_capital = 0.0  # To store the dynamically calculated capital for each trade
    entry_fee_cost = 0.0  # To store the entry fee for the current trade
    
    # Time tracking variables
    total_time_periods = 0
    active_trading_periods = 0

    # Step 4: Add columns for trade events and yields
    df['entry'] = False
    df['exit'] = False
    df['exit_clause'] = 0
    df['yield_before_fees'] = 0.0
    df['yield_after_fees'] = 0.0

    # Step 5: Iterate through each time step to simulate trades
    for t, row in df.iterrows():
        total_time_periods += 1
        
        if not in_trade:
            # Check entry conditions: perpetual price > spot price and funding rate > threshold
            if (row['perp'] > row['spot']) and (row['fund_rate'] > fund_thresh):
                in_trade = True
                entry_price_perp = row['perp']
                entry_price_spot = row['spot']
                entry_time = t
                df.at[t, 'entry'] = True
                # Dynamically calculate the capital for this trade based on running capital
                running_capital = capital + cum_after
                allocated_capital = a * running_capital

                # Calculate and store entry fee
                entry_fee_cost = allocated_capital * (fee_spot_entry + fee_perp_entry)

                # Record entry event
                entry_details = {
                    'time': entry_time,
                    'type': 'entry',
                    'spot_price': entry_price_spot,
                    'perp_price': entry_price_perp,
                    'funding_rate': row['fund_rate'],
                    'allocated_capital': allocated_capital,
                    'current_capital': running_capital,
                    'reason': "Entry: Perp > Spot & Funding Rate > Threshold",
                    'fees': entry_fee_cost,
                    'trade_pnl_before_fees': 0,
                    'trade_pnl_after_fees': 0,
                    'cumulative_pnl_after_fees': cum_after
                }
                all_trades.append(entry_details)
        else:
            active_trading_periods += 1
            # Check exit conditions
            if row['perp'] >= sl_mult * entry_price_perp:
                clause = 1  # Exit due to stop-loss (perp price increased by sl_mult)
            elif row['perp'] < spot_price_exit_multiplier * row['spot']:
                clause = 2  # Exit due to premium disappearance (perp price < spot price)
            elif row['fund_rate'] < fund_thresh:
                clause = 3  # Exit due to funding rate dropping below threshold
            else:
                clause = 0

            if clause:
                in_trade = False
                df.at[t, 'exit'] = True
                df.at[t, 'exit_clause'] = clause
                stats[clause] += 1
                exit_time = t

                # Calculate funding earned during the trade (from entry_time to just before t)
                trade_df = df[(df.index >= entry_time) & (df.index < t)]
                fund_earned = (trade_df['fund_rate'] * allocated_capital).sum()

                # Calculate exit and total fees
                exit_fee_cost = allocated_capital * (fee_spot_exit + fee_perp_exit)
                total_fee_cost = entry_fee_cost + exit_fee_cost

                # Compute yields before and after fees
                before = fund_earned
                after = fund_earned - total_fee_cost

                # Update cumulative yields
                cum_before += before
                cum_after += after

                exit_reason_map = {
                    1: "Stop-loss",
                    2: "Perp price < Spot price",
                    3: "Funding rate < Threshold"
                }

                # Record exit event
                exit_details = {
                    'time': exit_time,
                    'type': 'exit',
                    'spot_price': row['spot'],
                    'perp_price': row['perp'],
                    'funding_rate': row['fund_rate'],
                    'allocated_capital': allocated_capital,
                    'current_capital': capital + cum_after,
                    'reason': exit_reason_map.get(clause, "Unknown"),
                    'fees': exit_fee_cost,
                    'trade_pnl_before_fees': before,
                    'trade_pnl_after_fees': after,
                    'cumulative_pnl_after_fees': cum_after
                }
                all_trades.append(exit_details)

        # Update cumulative yields in the DataFrame for this time step
        df.at[t, 'yield_before_fees'] = cum_before
        df.at[t, 'yield_after_fees'] = cum_after

    trades_df = pd.DataFrame(all_trades)
    
    # Calculate time utilization percentage
    time_utilization_percentage = (active_trading_periods / total_time_periods) * 100 if total_time_periods > 0 else 0
    
    return df, stats, trades_df, time_utilization_percentage

if __name__ == "__main__":
    df = pd.read_csv("data (1).csv")
    spot_series = df['spot_open']
    perp_series = df['perp_open']
    fund_rate_series = df['funding_fundingRate']

    results_df, stats, trades_df, time_utilization_percentage = simulate_delta_neutral(
        spot_series,
        perp_series,
        fund_rate_series,
        capital=100_000,
        spot_price_exit_multiplier=0.99,
        fund_thresh=0
    )

    if not trades_df.empty:
        trades_df.to_csv('trades.csv', index=False)
        print("Trade data saved to trades.csv")

        # Create the running trade capital graph
        exit_trades_df = trades_df[trades_df['type'] == 'exit']
        plt.figure(figsize=(12, 6))
        plt.plot(exit_trades_df['time'], exit_trades_df['current_capital'], linewidth=2, color='blue')
        plt.title('Running Trade Capital Over Time', fontsize=14, fontweight='bold')
        plt.xlabel('Time (Trade Exit Index)', fontsize=12)
        plt.ylabel('Running Trade Capital ($)', fontsize=12)
        plt.grid(True, alpha=0.3)

        # Add horizontal line for initial capital
        plt.axhline(y=100000, color='red', linestyle='--', alpha=0.7, label='Initial Capital ($100,000)')
        plt.legend()

        # Format y-axis to show currency
        plt.gca().yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))

        plt.tight_layout()
        plt.savefig('running_trade_capital.png', dpi=300, bbox_inches='tight')
        # plt.show()
        print("Graph saved as 'running_trade_capital.png'")

        print("\n--- Simulation Summary ---")
        optimal_thresh = 0
        print(f"Optimal fund_thresh: {optimal_thresh:.6f}")
        print(f"Total trades: {len(exit_trades_df)}")
        total_yield = exit_trades_df['cumulative_pnl_after_fees'].iloc[-1]
        print(f"Total Yield (after fees): {total_yield:.2f}")

        # --- APY Calculation ---
        # Assumption: Each data point in the CSV represents 1 hour.
        initial_capital = 100_000
        num_periods = len(df)
        total_days = num_periods / 24  # As per the assumption of hourly data

        if total_days > 0:
            total_return = total_yield / initial_capital
            # Annualize the return
            apy = ((1 + total_return) ** (365 / total_days)) - 1
            print(f"Final APY (assuming hourly data): {apy:.2%}")
        # --- End APY Calculation ---

        print("\nExit reasons breakdown:")
        exit_counts = exit_trades_df['reason'].value_counts(normalize=True) * 100
        for reason, percentage in exit_counts.items():
            count = stats[
                next(key for key, value in
                     {1: "Stop-loss", 2: "Perp price < Spot price", 3: "Funding rate < Threshold"}.items() if
                     value == reason)]
            print(f"- {reason}: {count} trades ({percentage:.2f}%)")

        print(f"\nTime Utilization: {time_utilization_percentage:.2f}% of total time period")
        active_periods = (time_utilization_percentage / 100) * num_periods
        print(f"Active Trading Periods: {int(active_periods):,} out of {num_periods:,} total periods")
    else:
        print("No trades were made during the simulation.")