import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def resample_and_analyze():
    # Read the original 15-minute interval data
    df = pd.read_csv('hype_funding_rates_15min.csv', index_col=0, parse_dates=True)
    
    if df.empty:
        print("No data found in the CSV file.")
        return

    # Resample to 24-hour intervals using mean
    df_24h = df.resample('D').agg({
        'annualized_rate': 'mean',
        'funding_rate': 'mean',
        'premium': 'mean'
    }).dropna()

    # Calculate statistics
    mean_rate = df_24h['annualized_rate'].mean()
    median_rate = df_24h['annualized_rate'].median()
    std_dev = df_24h['annualized_rate'].std()
    max_rate = df_24h['annualized_rate'].max()
    min_rate = df_24h['annualized_rate'].min()

    # Save resampled data to new CSV
    df_24h.to_csv('hype_funding_rates_24h.csv')

    # Calculate distribution statistics
    stats = {
        'max': max_rate,
        'min': min_rate,
        'mean': mean_rate,
        'median': median_rate,
        'std_dev': std_dev,
        'total': len(df_24h)
    }

    # Print statistics
    print("\nHYPE Funding Rate Analysis (March 24 - June 14, 2025) [24-Hour Intervals]")
    print("=" * 80)
    print("\nAnnualized Rate Statistics (%):")
    print(f"Maximum Rate:     {stats['max']:.2f}%")
    print(f"Minimum Rate:     {stats['min']:.2f}%")
    print(f"Mean Rate:        {stats['mean']:.2f}%")
    print(f"Median Rate:      {stats['median']:.2f}%")
    print(f"Standard Dev:     {stats['std_dev']:.2f}%")
    print(f"Total Intervals:  {stats['total']}")

    # Create the plot with y-axis scale from 0 to 100%
    plt.figure(figsize=(14, 6))
    
    # Plot daily rates
    plt.plot(df_24h.index, df_24h['annualized_rate'], 
             label='Daily Rate (%)', 
             alpha=0.6, 
             linewidth=1)
    
    # Add statistical reference lines
    plt.axhline(y=mean_rate, color='green', linestyle='--', alpha=0.7, 
                label=f'Mean ({mean_rate:.1f}%)')
    plt.axhline(y=median_rate, color='purple', linestyle='--', alpha=0.7, 
                label=f'Median ({median_rate:.1f}%)')
    plt.axhline(y=10, color='gray', linestyle='--', alpha=0.5, 
                label='10% Threshold')
    
    # Add a horizontal line for Strategy returns excluding fees (20/23 of mean)
    strategy_return = mean_rate * 20 / 23
    plt.axhline(y=strategy_return, color='orange', linestyle='-.', alpha=0.7, 
                label=f'Strategy returns excluding fees ({strategy_return:.1f}%)')
    
    plt.xlabel('Time (UTC)')
    plt.ylabel('Annualized Rate (%)')
    plt.title('HYPE Funding Rate (March 24 - June 14, 2025) [24-Hour Intervals]')
    plt.legend(bbox_to_anchor=(1.05, 1), loc='upper left')
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 100)  # Set y-axis limit from 0 to 100%
    plt.tight_layout()
    
    # Save the plot with extra space for legend
    plt.savefig('funding_rate_analysis_24h.png', bbox_inches='tight', dpi=300)
    plt.close()

if __name__ == "__main__":
    resample_and_analyze() 