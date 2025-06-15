import time
from datetime import datetime, timedelta, UTC
from hyperliquid.info import Info
from hyperliquid.utils import constants
import pandas as pd
import numpy as np
from typing import List, Dict
import json
import requests

def fetch_spot_price(symbol: str) -> float:
    """
    Fetch spot price from CoinGecko API
    """
    try:
        # Convert HYPE to lowercase for CoinGecko API
        symbol_lower = symbol.lower()
        url = f"https://api.coingecko.com/api/v3/simple/price?ids={symbol_lower}&vs_currencies=usd"
        response = requests.get(url)
        data = response.json()
        return data[symbol_lower]['usd']
    except Exception as e:
        print(f"Error fetching spot price: {str(e)}")
        return None

def fetch_funding_chunk(info: Info, symbol: str, start_time: int, end_time: int, max_retries: int = 3) -> List[Dict]:
    """
    Fetch funding data for a specific time chunk with retry logic
    """
    for attempt in range(max_retries):
        try:
            data = info.funding_history(symbol, start_time, end_time)
            if data:
                return data
            print(f"No data received for chunk {datetime.fromtimestamp(start_time/1000, UTC)} to {datetime.fromtimestamp(end_time/1000, UTC)}")
            return []
        except Exception as e:
            if attempt < max_retries - 1:
                wait_time = (attempt + 1) * 5  # Exponential backoff
                print(f"Rate limited, waiting {wait_time} seconds before retry...")
                time.sleep(wait_time)
            else:
                print(f"Failed to fetch data after {max_retries} attempts: {str(e)}")
                return []
    return []

def fetch_funding_data(symbol: str, start_date: datetime, end_date: datetime, chunk_hours: int = 4) -> pd.DataFrame:
    """
    Fetch funding data in chunks and combine into a single DataFrame
    Using 4-hour chunks to stay within 500 events limit
    """
    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    all_data = []
    
    # Convert dates to timestamps
    start_ts = int(start_date.timestamp() * 1000)
    end_ts = int(end_date.timestamp() * 1000)
    
    # Calculate number of chunks (4-hour intervals)
    total_hours = (end_date - start_date).total_seconds() / 3600
    num_chunks = int(np.ceil(total_hours / chunk_hours))
    
    print(f"Fetching data in {num_chunks} chunks of {chunk_hours} hours each...")
    
    current_start = start_ts
    for i in range(num_chunks):
        chunk_end = min(current_start + (chunk_hours * 60 * 60 * 1000), end_ts)
        print(f"\nFetching chunk {i+1}/{num_chunks}:")
        print(f"From: {datetime.fromtimestamp(current_start/1000, UTC)}")
        print(f"To:   {datetime.fromtimestamp(chunk_end/1000, UTC)}")
        
        chunk_data = fetch_funding_chunk(info, symbol, current_start, chunk_end)
        if chunk_data:
            all_data.extend(chunk_data)
            print(f"Received {len(chunk_data)} data points")
        
        current_start = chunk_end
        time.sleep(1)  # Small delay between chunks to avoid rate limiting
    
    if not all_data:
        print("No data received for any chunk")
        return pd.DataFrame()
    
    # Convert to DataFrame
    df = pd.DataFrame(all_data)
    df['timestamp'] = pd.to_datetime(df['time'], unit='ms', utc=True)
    df['funding_rate'] = df['fundingRate'].astype(float)
    df['premium'] = df['premium'].astype(float)
    df['perp_price'] = df['markPrice'].astype(float)  # Add perpetual price
    
    # Calculate annualized rate
    df['annualized_rate'] = ((1 + df['funding_rate']) ** 8760 - 1) * 100
    
    # Sort by timestamp
    df = df.sort_values('timestamp')
    
    # Fetch spot price
    spot_price = fetch_spot_price(symbol)
    if spot_price is not None:
        df['spot_price'] = spot_price
        df['price_difference'] = df['perp_price'] - df['spot_price']
        df['price_difference_pct'] = (df['price_difference'] / df['spot_price']) * 100
    
    # Resample to 1-minute intervals
    df_resampled = df.set_index('timestamp').resample('1T').agg({
        'funding_rate': 'last',
        'premium': 'last',
        'annualized_rate': 'last',
        'perp_price': 'last',
        'spot_price': 'last',
        'price_difference': 'last',
        'price_difference_pct': 'last'
    }).fillna(method='ffill')
    
    return df_resampled

def main():
    # Set date range
    start_date = datetime(2025, 3, 24, 0, 0, 0, tzinfo=UTC)
    end_date = datetime(2025, 6, 14, 23, 59, 59, tzinfo=UTC)
    
    # Fetch data
    df = fetch_funding_data("HYPE", start_date, end_date)
    
    if df.empty:
        print("No data to save")
        return
    
    # Save to CSV
    output_file = 'hype_funding_rates_1min.csv'
    df.to_csv(output_file)
    print(f"\nData saved to {output_file}")
    
    # Print summary statistics
    print("\nSummary Statistics:")
    print(f"Total 1-minute intervals: {len(df)}")
    print(f"Date range: {df.index.min()} to {df.index.max()}")
    print("\nAnnualized Rate Statistics (%):")
    print(f"Maximum Rate:     {df['annualized_rate'].max():.2f}%")
    print(f"Minimum Rate:     {df['annualized_rate'].min():.2f}%")
    print(f"Mean Rate:        {df['annualized_rate'].mean():.2f}%")
    print(f"Median Rate:      {df['annualized_rate'].median():.2f}%")
    print(f"Standard Dev:     {df['annualized_rate'].std():.2f}%")
    
    # Print price difference statistics
    print("\nPrice Difference Statistics:")
    print(f"Maximum Difference:     ${df['price_difference'].max():.2f}")
    print(f"Minimum Difference:     ${df['price_difference'].min():.2f}")
    print(f"Mean Difference:        ${df['price_difference'].mean():.2f}")
    print(f"Median Difference:      ${df['price_difference'].median():.2f}")
    print(f"Standard Dev:           ${df['price_difference'].std():.2f}")
    
    # Count intervals above/below 10%
    above_10 = (df['annualized_rate'] > 10).sum()
    below_10 = (df['annualized_rate'] <= 10).sum()
    total = len(df)
    
    print("\nTime Distribution:")
    print(f"Intervals above 10%:  {above_10} ({above_10/total*100:.1f}%)")
    print(f"Intervals below 10%:  {below_10} ({below_10/total*100:.1f}%)")
    print(f"Total Intervals:      {total}")

if __name__ == "__main__":
    main() 