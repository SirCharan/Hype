import time
from datetime import datetime, timedelta, UTC
from hyperliquid.info import Info
from hyperliquid.utils import constants
import pandas as pd
import numpy as np
from typing import Dict, Optional
import os

def fetch_current_prices(info: Info, symbol: str) -> Optional[Dict]:
    """
    Fetch current perpetual and spot prices from Hyperliquid
    
    Args:
        info: Hyperliquid Info instance
        symbol: Trading pair symbol (e.g., 'HYPE')
        
    Returns:
        Dictionary containing perp_price and spot_price, or None if error
    """
    try:
        meta = info.meta()
        for coin in meta['universe']:
            if coin['name'] == symbol:
                print(f"DEBUG: coin dict for {symbol}: {coin}")  # Debug print
                # Temporarily return None to avoid further errors
                return None
        return None
    except Exception as e:
        print(f"Error fetching prices: {str(e)}")
        return None

def save_price_data(df: pd.DataFrame, output_file: str):
    """
    Save price data to CSV file, handling incremental updates
    
    Args:
        df: DataFrame containing price data
        output_file: Path to output CSV file
    """
    if os.path.exists(output_file):
        # Read existing data
        existing_df = pd.read_csv(output_file, index_col=0, parse_dates=True)
        # Combine with new data
        combined_df = pd.concat([existing_df, df])
        # Remove duplicates
        combined_df = combined_df[~combined_df.index.duplicated(keep='last')]
        # Sort by timestamp
        combined_df = combined_df.sort_index()
    else:
        combined_df = df
    
    # Save to CSV
    combined_df.to_csv(output_file)
    print(f"Saved {len(df)} new data points to {output_file}")

def fetch_price_data(symbol: str, interval_minutes: int = 1, duration_hours: int = 24) -> pd.DataFrame:
    """
    Fetch price data at regular intervals for a specified duration
    
    Args:
        symbol: Trading pair symbol (e.g., 'HYPE')
        interval_minutes: Time interval between price fetches in minutes
        duration_hours: Total duration to fetch data for in hours
        
    Returns:
        DataFrame containing price data
    """
    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    output_file = f'hype_prices_{interval_minutes}min.csv'
    
    end_time = datetime.now(UTC)
    start_time = end_time - timedelta(hours=duration_hours)
    
    print(f"Fetching price data for {symbol} from {start_time} to {end_time}")
    print(f"Interval: {interval_minutes} minutes")
    
    data_points = []
    current_time = start_time
    
    while current_time <= end_time:
        prices = fetch_current_prices(info, symbol)
        if prices:
            data_points.append(prices)
            print(f"Fetched prices at {current_time}: Perp=${prices['perp_price']:.2f}, Spot=${prices['spot_price']:.2f}")
        
        # Wait for the next interval
        time.sleep(interval_minutes * 60)
        current_time = datetime.now(UTC)
    
    if data_points:
        # Convert to DataFrame
        df = pd.DataFrame(data_points)
        df.set_index('timestamp', inplace=True)
        
        # Calculate additional metrics
        df['price_difference'] = df['perp_price'] - df['spot_price']
        df['price_difference_pct'] = (df['price_difference'] / df['spot_price']) * 100
        
        # Save data
        save_price_data(df, output_file)
        
        return df
    
    return pd.DataFrame()

def main():
    # Fetch price data for HYPE
    df = fetch_price_data("HYPE", interval_minutes=1, duration_hours=24)
    
    if df.empty:
        print("No data collected")
        return
    
    # Print summary statistics
    print("\nPrice Data Summary:")
    print(f"Total data points: {len(df)}")
    print(f"Date range: {df.index.min()} to {df.index.max()}")
    
    print("\nPerpetual Price Statistics ($):")
    print(f"Maximum:     ${df['perp_price'].max():.2f}")
    print(f"Minimum:     ${df['perp_price'].min():.2f}")
    print(f"Mean:        ${df['perp_price'].mean():.2f}")
    print(f"Median:      ${df['perp_price'].median():.2f}")
    print(f"Standard Dev: ${df['perp_price'].std():.2f}")
    
    print("\nSpot Price Statistics ($):")
    print(f"Maximum:     ${df['spot_price'].max():.2f}")
    print(f"Minimum:     ${df['spot_price'].min():.2f}")
    print(f"Mean:        ${df['spot_price'].mean():.2f}")
    print(f"Median:      ${df['spot_price'].median():.2f}")
    print(f"Standard Dev: ${df['spot_price'].std():.2f}")
    
    print("\nPrice Difference Statistics:")
    print(f"Maximum Difference:     ${df['price_difference'].max():.2f}")
    print(f"Minimum Difference:     ${df['price_difference'].min():.2f}")
    print(f"Mean Difference:        ${df['price_difference'].mean():.2f}")
    print(f"Median Difference:      ${df['price_difference'].median():.2f}")
    print(f"Standard Dev:           ${df['price_difference'].std():.2f}")

if __name__ == "__main__":
    main() 