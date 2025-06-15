from datetime import datetime, timedelta, UTC
from hyperliquid.info import Info
from hyperliquid.utils import constants
import time

def find_funding_data_range(symbol="HYPE", days_per_batch=7, max_months=12):
    info = Info(constants.MAINNET_API_URL, skip_ws=True)
    now = datetime.now(UTC)
    earliest = None
    latest = None
    found_any = False

    # Search backwards in time, batch by batch
    for month_offset in range(max_months):
        batch_end = now - timedelta(days=month_offset * days_per_batch)
        batch_start = batch_end - timedelta(days=days_per_batch)
        start_time = int(batch_start.timestamp() * 1000)
        end_time = int(batch_end.timestamp() * 1000)
        print(f"Checking {batch_start.strftime('%Y-%m-%d')} to {batch_end.strftime('%Y-%m-%d')}...")
        data = info.funding_history(symbol, start_time, end_time)
        if data:
            found_any = True
            # Find earliest and latest timestamps in this batch
            times = [entry['time'] for entry in data]
            batch_earliest = min(times)
            batch_latest = max(times)
            if earliest is None or batch_earliest < earliest:
                earliest = batch_earliest
            if latest is None or batch_latest > latest:
                latest = batch_latest
    if found_any:
        print("\nFunding data available for:")
        print(f"Earliest: {datetime.fromtimestamp(earliest/1000, UTC)}")
        print(f"Latest:   {datetime.fromtimestamp(latest/1000, UTC)}")
    else:
        print("No funding data found for the given symbol and search range.")

if __name__ == "__main__":
    find_funding_data_range() 