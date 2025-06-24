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
WINDOW_HOURS = 24  # length of each sub-range to query

START_DT = datetime.datetime(2025, 1, 1, 0, 0, 0, tzinfo=datetime.timezone.utc)
END_DT = datetime.datetime(2025, 6, 19, 23, 59, 59, tzinfo=datetime.timezone.utc)

info = Info(constants.MAINNET_API_URL, skip_ws=True)

logging.info(
    "Scanning candle availability from %s to %s UTC in %d-hour windows",
    START_DT.isoformat(),
    END_DT.isoformat(),
    WINDOW_HOURS,
)

window_delta = datetime.timedelta(hours=WINDOW_HOURS)
current_start = START_DT

while current_start < END_DT:
    current_end = min(current_start + window_delta, END_DT)
    start_ms = int(current_start.timestamp() * 1000)
    end_ms = int(current_end.timestamp() * 1000)
    window_str = f"{current_start.isoformat()} → {current_end.isoformat()}"

    found_any = False
    for variant in NAME_VARIANTS:
        try:
            candles = info.candles_snapshot(variant, INTERVAL, start_ms, end_ms)
        except Exception as e:
            logging.error("Error querying %s for window %s: %s", variant, window_str, e)
            continue
        count = len(candles) if candles else 0
        if count > 0:
            first_ts = datetime.datetime.fromtimestamp(candles[0]["t"] / 1000, datetime.timezone.utc)
            last_ts = datetime.datetime.fromtimestamp(candles[-1]["T"] / 1000, datetime.timezone.utc)
            logging.info(
                "✅ %s — %d candles found for %s (first %s, last %s)",
                window_str,
                count,
                variant,
                first_ts.isoformat(),
                last_ts.isoformat(),
            )
            found_any = True
            # Break after first successful variant to avoid duplicate work
            break
    if not found_any:
        logging.info("❌ %s — no candles for any variant", window_str)

    current_start = current_end

logging.info("Scan complete.") 