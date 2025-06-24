import json
import csv
import time
from hyperliquid.info import Info
from hyperliquid.utils import constants
import datetime
import logging
from typing import List

# Configure logging for detailed debug output
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Initialize the Info object with the mainnet API URL
info = Info(constants.MAINNET_API_URL, skip_ws=True)

# Parameters (edit these for different queries)
name_variants: List[str] = [
    "HYPE/USDC",  # UI-friendly pair name
    "@107",       # Spot index for HYPE according to docs
]
interval = "1m"  # Granularity (1 minute)

# ---- Set target time window (June 10th 2025, 19:13–20:13 UTC) ----
end_dt = datetime.datetime(2025, 6, 10, 20, 13, 0, tzinfo=datetime.timezone.utc)
start_dt = end_dt - datetime.timedelta(hours=1)
endTime = int(end_dt.timestamp() * 1000)
startTime = int(start_dt.timestamp() * 1000)
# -----------------------------------------------------------------

logging.info("Target window: %s to %s UTC", start_dt.isoformat(), end_dt.isoformat())
logging.info("Epoch ms: start=%d, end=%d", startTime, endTime)
logging.info("Interval: %s", interval)

all_candles = []
used_name = None
for variant in name_variants:
    logging.info("Attempting to fetch candles with symbol '%s'", variant)
    try:
        candles_data = info.candles_snapshot(variant, interval, startTime, endTime)
        logging.info("Returned %d candles", len(candles_data) if candles_data else 0)
        if candles_data:
            all_candles = candles_data
            used_name = variant
            break
    except Exception as e:
        logging.error("Error fetching with symbol '%s': %s", variant, e)

if not all_candles:
    logging.warning("No candle data found for any symbol variant in the specified window.")
    logging.warning(
        "Possible reasons: symbol listing after this date, incorrect symbol, or no trades during this window."
    )
    logging.warning(
        "Refer to Hyperliquid docs for candle snapshot: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/info-endpoint#candle-snapshot"
    )
    # Exit early to avoid writing empty files
    exit()

logging.info("Using symbol variant '%s' with %d candles", used_name, len(all_candles))
# Show first and last candle timestamps for verification
first_ts = datetime.datetime.fromtimestamp(all_candles[0]['t'] / 1000, datetime.UTC)
last_ts = datetime.datetime.fromtimestamp(all_candles[-1]['T'] / 1000, datetime.UTC)
logging.info("First candle opens at %s UTC", first_ts)
logging.info("Last candle closes at %s UTC", last_ts)

# ----- Save data -----
json_file = "candles.json"
csv_file = "candles.csv"

with open(json_file, "w") as f:
    json.dump(all_candles, f, indent=4)
    logging.info("Saved candles to %s", json_file)

with open(csv_file, "w", newline="") as f:
    fieldnames = list(all_candles[0].keys())
    writer = csv.DictWriter(f, fieldnames=fieldnames)
    writer.writeheader()
    for candle in all_candles:
        writer.writerow(candle)
    logging.info("Saved candles to %s", csv_file)

logging.info("Finished. Fetched %d candles for %s.", len(all_candles), used_name) 