from hyperliquid.info import Info
from hyperliquid.utils import constants
import time

# Initialize the Hyperliquid API client
# Use MAINNET_API_URL for production; TESTNET_API_URL for testing
info = Info(constants.MAINNET_API_URL, skip_ws=True)

def fetch_candles_in_batches(info_client, name, interval, start_time, end_time, chunk_size=5000):
    # Define interval durations in milliseconds
    interval_ms = {
        "1m": 60000,
        "5m": 300000,
        "15m": 900000,
        "1h": 3600000,
    }
    
    # Get the interval duration
    interval_duration = interval_ms.get(interval, 60000)  # Default to 1m if not found
    
    all_candles = []
    current_start = start_time
    
    while current_start <= end_time:
        # Calculate the end time for this chunk
        chunk_end = min(current_start + (chunk_size * interval_duration) - 1, end_time)
        
        # Fetch candles for this chunk
        candles = info_client.candles_snapshot(name, interval, current_start, chunk_end)
        
        # If no candles are returned, break the loop
        if not candles:
            break
        
        # Add fetched candles to the total list
        all_candles.extend(candles)
        
        # Get the timestamp of the last candle
        last_time = candles[-1].get('time', None)
        
        # If no 'time' field is present, break (safety check)
        if last_time is None:
            break
        
        # Set the next start time to the end of the last candle
        current_start = last_time + interval_duration
    
    return all_candles

# Example usage
if __name__ == "__main__":
    # Set parameters
    name_spot = "HYPE"  # For HYPE spot (verify with SDK)
    name_perp = "HYPEUSD"  # For HYPEUSD perp (verify with SDK)
    interval = "1m"  # 1-minute candles
    start_time = 1680000000000  # April 1, 2023 (Unix timestamp in ms)
    end_time = 1714534400000  # April 1, 2024 (Unix timestamp in ms)
    
    # Fetch candles for HYPE spot
    spot_candles = fetch_candles_in_batches(info, name_spot, interval, start_time, end_time)
    
    # Fetch candles for HYPEUSD perp
    perp_candles = fetch_candles_in_batches(info, name_perp, interval, start_time, end_time)
    
    # Print the total number of candles fetched
    print(f"Total HYPE spot candles fetched: {len(spot_candles)}")
    print(f"Total HYPEUSD perp candles fetched: {len(perp_candles)}")