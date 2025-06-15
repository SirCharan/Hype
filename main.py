import time
from datetime import datetime, timedelta, UTC
from hyperliquid.info import Info
from hyperliquid.utils import constants
import matplotlib.pyplot as plt
import numpy as np

# Initialize Info with mainnet URL
info = Info(constants.MAINNET_API_URL, skip_ws=True)

# Set time range for past month (May 14 to June 14)
end_time = int(time.time() * 1000)  # Current time in milliseconds
start_time = end_time - (30 * 24 * 60 * 60 * 1000)  # 30 days ago

# Fetch funding history for HYPE
funding_data = info.funding_history("HYPE", start_time, end_time)

# Print only one entry per hour, formatted
last_hour = None
print("\nHYPE Funding Rate History (May 14 - June 14)")
print("=" * 80)
print("Timestamp (UTC)           Funding Rate        Premium           Annualized Rate (%)")
print("-" * 80)

# Prepare data for plotting
plot_times = []
plot_annualized = []

for entry in funding_data:
    # Convert ms timestamp to hour string using timezone-aware datetime
    dt = datetime.fromtimestamp(entry['time'] / 1000, UTC)
    hour_str = dt.strftime('%Y-%m-%d %H:00 UTC')
    if hour_str != last_hour:
        # Convert funding rate and premium to float before formatting
        funding_rate = float(entry['fundingRate'])
        premium = float(entry['premium'])
        # Calculate annualized rate
        annualized_rate = (1 + funding_rate) ** 8760 - 1
        print(f"{hour_str:<25} {funding_rate:<18.8f} {premium:<.8f} {annualized_rate * 100:>18.2f}")
        plot_times.append(dt)
        plot_annualized.append(annualized_rate * 100)
        last_hour = hour_str

# After collecting plot_annualized, calculate statistics
if plot_annualized:
    arr = np.array(plot_annualized)
    print("\nAnnualized Rate Statistics (%):")
    print(f"Max:     {arr.max():.2f}")
    print(f"Min:     {arr.min():.2f}")
    print(f"Mean:    {arr.mean():.2f}")
    print(f"Median:  {np.median(arr):.2f}")
    print(f"Std Dev: {arr.std():.2f}")

# Plotting
plt.figure(figsize=(14, 6))
plt.plot(plot_times, plot_annualized, label='Annualized Rate (%)')
plt.xlabel('Time (UTC)')
plt.ylabel('Annualized Rate (%)')
plt.title('HYPE Hourly Annualized Funding Rate (May 14 - June 14)')
plt.legend()
plt.tight_layout()
plt.show()