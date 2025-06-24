import datetime
import logging
from typing import List

from hyperliquid.info import Info
from hyperliquid.utils import constants

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
)

# Parameters
NAME_VARIANTS: List[str] = ["HYPE/USDC", "@107"]
INTERVAL = "1m"
STEP_HOURS = 24  # size of the sliding window
MAX_DAYS = 365  # search up to one year back

info = Info(constants.MAINNET_API_URL, skip_ws=True)

now_dt = datetime.datetime.now(datetime.timezone.utc)
end_ms = int(now_dt.timestamp() * 1000)
step_ms = STEP_HOURS * 60 * 60 * 1000

logging.info("Starting backward search from %s UTC", now_dt.isoformat())
found = False
iteration = 0

while iteration < MAX_DAYS:
    iteration += 1
    start_ms = end_ms - step_ms
    start_dt = datetime.datetime.fromtimestamp(start_ms / 1000, datetime.timezone.utc)
    end_dt = datetime.datetime.fromtimestamp(end_ms / 1000, datetime.timezone.utc)
    logging.info("Window %d: %s → %s", iteration, start_dt.isoformat(), end_dt.isoformat())

    for variant in NAME_VARIANTS:
        try:
            candles = info.candles_snapshot(variant, INTERVAL, start_ms, end_ms)
        except Exception as e:
            logging.error("Error querying %s: %s", variant, e)
            continue
        if candles:
            logging.info("Found %d candles for %s in this window.", len(candles), variant)
            # Record earliest timestamp within this set
            earliest_ts = min(candle["t"] for candle in candles)
            earliest_dt = datetime.datetime.fromtimestamp(earliest_ts / 1000, datetime.timezone.utc)
            logging.info("Earliest candle open time inside window: %s UTC", earliest_dt.isoformat())
            found = True
            break
    if found:
        break

    # Shift window back one step
    end_ms = start_ms

if not found:
    logging.warning("No candles found in the last %d days.", MAX_DAYS)
else:
    logging.info("Earliest candle discovered at %s UTC", earliest_dt.isoformat()) 