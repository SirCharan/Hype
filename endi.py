# -*- coding: utf-8 -*-
"""
Created on Tue Jun 17 16:25:42 2025

@author: Rik

This script performs a backtest of a delta-neutral trading strategy
leveraging funding rates between spot and perpetual cryptocurrency markets.
It loads historical data, simulates trades based on predefined entry and
exit conditions, calculates yields, and generates performance reports
and visualizations.
"""

# Standard libs
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# --- 1. Data Loading and Preparation ---

# Read dataset, parse the timestamp column and set a DateTime index
# Assumes a CSV file named 'data (1).csv' is in the same directory.
df_raw = pd.read_csv(
    "data (1).csv",
    parse_dates=["date_time"],
)
df_raw.set_index("date_time", inplace=True)

# Select the series needed for the strategy
spot_series = df_raw["spot_open"]
perp_series = df_raw["perp_open"]
fund_rate_series = df_raw["funding_fundingRate"]

#capital = amt_USDC/price_HYPE

# --- 2. Simulation Function ---

def simulate_delta_neutral(
    spot_prices: pd.Series,
    perp_prices: pd.Series,
    funding_rates: pd.Series,
    capital: float = 23_000,
    a: float = 20/23,
    sl_mult: float = 1.1,
    fee_spot: float = 0.0007,
    fee_perp: float = 0.00045,
    fund_thresh: float = 0.00001,
) -> (pd.DataFrame, dict, list):
    """
    Simulates a delta-neutral funding rate arbitrage strategy.

    The strategy involves buying spot and shorting perpetuals when the funding
    rate is positive and the perpetual price is higher than spot.

    Args:
        spot_prices (pd.Series): Series of spot prices.
        perp_prices (pd.Series): Series of perpetual prices.
        funding_rates (pd.Series): Series of funding rates.
        capital (float): Initial capital in USDC.
        a (float): Proportion of capital to allocate to the spot leg.
        sl_mult (float): Stop-loss multiplier for the perpetual price.
        fee_spot (float): Trading fee for the spot market.
        fee_perp (float): Trading fee for the perpetual market.
        fund_thresh (float): Minimum funding rate to enter a trade.

    Returns:
        pd.DataFrame: DataFrame with simulation results for each timestamp.
        dict: A dictionary containing statistics on exit causes.
        list: A list of tuples, where each tuple represents a completed trade.
    """
    # Prepare the main DataFrame for the simulation
    df = pd.DataFrame({
        'spot': spot_prices,
        'perp': perp_prices,
        'fund_rate': funding_rates,
    }).dropna()

    # --- Initialize simulation state variables ---
    cap_spot = a * capital
    cap_perp = (1 - a) * capital
    df['r'] = cap_spot / df['spot']

    # Columns to track trade entry/exit points and reasons
    df['entry'] = False
    df['exit'] = False
    df['exit_clause'] = 0
    # Columns to track cumulative yield over time
    df['yield_before_fees'] = 0.0
    df['yield_after_fees'] = 0.0

    in_trade = False  # Flag to check if a position is currently open
    entry_price = 0.0 # Store the entry price of the perpetual contract
    entry_time = None # Store the entry timestamp
    cum_before = 0.0  # Cumulative yield before deducting fees
    cum_after = 0.0   # Cumulative yield after deducting fees
    stats = {1: 0, 2: 0, 3: 0} # Dictionary to count exit clauses
    trade_periods = [] # List to store details of each trade

    # --- Main simulation loop ---
    for t, row in df.iterrows():
        if not in_trade:
            # Entry condition: perp price > spot price AND funding rate is positive
            if (row['perp'] > row['spot']) and (row['fund_rate'] > fund_thresh):
                in_trade = True
                entry_price = row['perp']
                entry_time = t
                df.at[t, 'entry'] = True
        else:
            # --- Exit conditions ---
            # Clause 1: Stop-loss triggered if perp price rises too high
            if row['perp'] >= sl_mult * entry_price:
                clause = 1
            # Clause 2: Basis collapses (perp price drops below spot)
            elif row['perp'] < 0.99 * row['spot']:
                clause = 2
            # Clause 3: Funding rate drops below the threshold
            elif row['fund_rate'] < fund_thresh:
                clause = 3
            else:
                clause = 0 # No exit condition met

            # If an exit condition is met, close the trade
            if clause:
                in_trade = False
                df.at[t, 'exit'] = True
                df.at[t, 'exit_clause'] = clause
                stats[clause] += 1

                # Select the data for the duration of the completed trade
                trade_df = df.loc[entry_time:df.index[df.index.get_loc(t)-1] if df.index.get_loc(t) > 0 else t]

                # --- Calculate yield and fees for the trade ---
                fund_earned = (trade_df['fund_rate'] * cap_spot).sum()

                # Accurate fee calculation based on actual notionals at entry and exit
                entry_spot_price = df.loc[entry_time, 'spot']
                entry_perp_price = df.loc[entry_time, 'perp']
                exit_spot_price = row['spot']
                exit_perp_price = row['perp']

                num_tokens = cap_spot / entry_spot_price

                spot_notional_entry = num_tokens * entry_spot_price
                perp_notional_entry = num_tokens * entry_perp_price
                spot_notional_exit = num_tokens * exit_spot_price
                perp_notional_exit = num_tokens * exit_perp_price

                fee_entry = (spot_notional_entry * fee_spot) + (perp_notional_entry * fee_perp)
                fee_exit = (spot_notional_exit * fee_spot) + (perp_notional_exit * fee_perp)
                fee_cost = fee_entry + fee_exit
                
                # Calculate final yield for this trade
                before = fund_earned 
                after = (fund_earned - fee_cost) 

                # Update cumulative yields
                cum_before += before
                cum_after += after

                # Record the completed trade
                trade_periods.append((entry_time, t, before, after))

        # Update the main DataFrame with the latest cumulative yields
        df.at[t, 'yield_before_fees'] = cum_before
        df.at[t, 'yield_after_fees'] = cum_after

    return df, stats, trade_periods

# -----------------------------------------------------------------------------
# --- 3. Run Simulation ---
# -----------------------------------------------------------------------------

results_df, stats, trades = simulate_delta_neutral(
    spot_series, perp_series, fund_rate_series
)

# -----------------------------------------------------------------------------
# --- 4. Build Trade Ledger ---
# -----------------------------------------------------------------------------

# This section processes the list of trades from the simulation into a
# clean pandas DataFrame for easier analysis and visualization.
trade_records = []
for entry, exit, y_before, y_after in trades:
    # Fetch exit clause from results_df (0-based positional lookup safe via .loc)
    exit_clause = results_df.loc[exit, "exit_clause"] if exit in results_df.index else np.nan
    duration = exit - entry
    # Convert duration to hours for easier numeric work
    duration_hrs = duration / np.timedelta64(1, "h") if isinstance(duration, pd.Timedelta) else duration
    trade_records.append(
        {
            "entry_time": entry,
            "exit_time": exit,
            "duration_hours": duration_hrs,
            "exit_clause": exit_clause,
            "yield_before_fees": y_before,
            "yield_after_fees": y_after,
        }
    )

trades_df = pd.DataFrame(trade_records)
# Calculate the total fees paid for each trade
trades_df["fees"] = trades_df["yield_before_fees"] - trades_df["yield_after_fees"]

# -----------------------------------------------------------------------------
# --- 5. Print Summary Statistics ---
# -----------------------------------------------------------------------------

print("\n=== Strategy Summary ===")
print(f"Total trades: {len(trades_df)}")
print(f"Total yield (before fees): {trades_df['yield_before_fees'].sum():.2f}")
print(f"Total yield (after fees):  {trades_df['yield_after_fees'].sum():.2f}")
print("Exit cause counts:")
for k, v in stats.items():
    print(f"  Clause {k}: {v}")

# -----------------------------------------------------------------------------
# --- 6. Visualizations ---
# -----------------------------------------------------------------------------

# Calculate cumulative yields for plotting
trades_df["cum_yield_before_fees"] = trades_df["yield_before_fees"].cumsum()
trades_df["cum_yield_after_fees"] = trades_df["yield_after_fees"].cumsum()

sns.set(style="darkgrid")

# 1. Cumulative yield as a percentage of initial capital
capital = 23_000  # As defined in the function defaults
plt.figure(figsize=(10, 6))
plt.plot(
    trades_df["exit_time"],
    (trades_df["cum_yield_before_fees"] / capital) * 100,
    label="Cumulative Yield Before Fees (%)",
)
plt.plot(
    trades_df["exit_time"],
    (trades_df["cum_yield_after_fees"] / capital) * 100,
    label="Cumulative Yield After Fees (%)",
)
plt.xlabel("Exit Time")
plt.ylabel("Cumulative Yield (% of Initial Capital)")
plt.title("Cumulative Strategy Yield as % of Capital")
plt.legend()
plt.tight_layout()
plt.savefig("cumulative_yield_percent.png")
plt.close()

# 2. Duration vs. yield (after fees)
plt.figure(figsize=(8, 6))
sns.scatterplot(
    data=trades_df,
    x="duration_hours",
    y="yield_after_fees",
    hue="exit_clause",
    palette="viridis",
)
plt.xlabel("Trade Duration (hours)")
plt.ylabel("Yield After Fees (USDC)")
plt.title("Trade Duration vs. Yield After Fees")
plt.tight_layout()
plt.savefig("duration_vs_yield.png")
plt.close()

# 3. Histogram of yields after fees
plt.figure(figsize=(8, 6))
sns.histplot(trades_df["yield_after_fees"], bins=50, kde=True)
plt.xlabel("Yield After Fees (USDC)")
plt.title("Distribution of Trade Yields (After Fees)")
plt.tight_layout()
plt.savefig("yield_histogram.png")
plt.close()

# 4. Cumulative Yield and Annualized Returns (APR)
# Calculate days elapsed since the first trade
trades_df["days_elapsed"] = (
    trades_df["exit_time"] - trades_df["entry_time"].iloc[0]
).dt.total_seconds() / (24 * 3600)

# Avoid division by zero for the first few data points if they are on day 0
trades_df["days_elapsed"] = trades_df["days_elapsed"].replace(0, 1)

# Calculate APR (Annualized Percentage Rate)
trades_df["apr_before_fees"] = (
    (trades_df["cum_yield_before_fees"] / capital) * (365 / trades_df["days_elapsed"])
) * 100
trades_df["apr_after_fees"] = (
    (trades_df["cum_yield_after_fees"] / capital) * (365 / trades_df["days_elapsed"])
) * 100

# Create the plot with dual y-axes for yield and APR
fig, ax1 = plt.subplots(figsize=(12, 7))

# Plot cumulative yield % on the primary y-axis (ax1)
ax1.plot(
    trades_df["exit_time"],
    (trades_df["cum_yield_before_fees"] / capital) * 100,
    "g-",
    label="Cumulative Yield Before Fees (%)",
)
ax1.plot(
    trades_df["exit_time"],
    (trades_df["cum_yield_after_fees"] / capital) * 100,
    "b-",
    label="Cumulative Yield After Fees (%)",
)
ax1.set_xlabel("Time")
ax1.set_ylabel("Cumulative Yield (%)", color="b")
ax1.tick_params("y", colors="b")

# Create a secondary y-axis (ax2) for the APR
ax2 = ax1.twinx()
ax2.plot(
    trades_df["exit_time"],
    trades_df["apr_after_fees"],
    "r--",
    label="APR After Fees (%)",
)
ax2.set_ylabel("Annual Percentage Rate (APR %)", color="r")
ax2.tick_params("y", colors="r")

# Add a title and legend
plt.title("Cumulative Yield and APR Over Time")
fig.tight_layout()
fig.legend(loc="upper left", bbox_to_anchor=(0.1, 0.9))
plt.savefig("yield_and_apr.png")
plt.close()

# -----------------------------------------------------------------------------
# --- 7. Optional: Data Inspection ---
# -----------------------------------------------------------------------------

print("\nFirst five trades:\n", trades_df.head())