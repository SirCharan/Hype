import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

def analyze_funding_rates():
    # Read the CSV file
    df = pd.read_csv('hype_funding_rates_15min.csv', index_col=0, parse_dates=True)
    
    if df.empty:
        print("No data found in the CSV file.")
        return

    # Calculate statistics
    stats = {
        'max': df['annualized_rate'].max(),
        'min': df['annualized_rate'].min(),
        'mean': df['annualized_rate'].mean(),
        'median': df['annualized_rate'].median(),
        'std_dev': df['annualized_rate'].std(),
        'above_10': (df['annualized_rate'] > 10).sum(),
        'below_10': (df['annualized_rate'] <= 10).sum(),
        'total': len(df)
    }

    # Print statistics
    print("\nHYPE Funding Rate Analysis (March 24 - June 14, 2025) [15-Minute Intervals]")
    print("=" * 80)
    print("\nAnnualized Rate Statistics (%):")
    print(f"Maximum Rate:     {stats['max']:.2f}%")
    print(f"Minimum Rate:     {stats['min']:.2f}%")
    print(f"Mean Rate:        {stats['mean']:.2f}%")
    print(f"Median Rate:      {stats['median']:.2f}%")
    print(f"Standard Dev:     {stats['std_dev']:.2f}%")
    print("\nTime Distribution:")
    print(f"Intervals above 10%:  {stats['above_10']} ({stats['above_10']/stats['total']*100:.1f}%)")
    print(f"Intervals below 10%:  {stats['below_10']} ({stats['below_10']/stats['total']*100:.1f}%)")
    print(f"Total Intervals:      {stats['total']}")

    # Create the plot with y-axis scale from 0 to 100%
    plt.figure(figsize=(14, 6))
    plt.plot(df.index, df['annualized_rate'], label='Annualized Rate (%)')
    
    # Add a horizontal line at 10%
    plt.axhline(y=10, color='r', linestyle='--', alpha=0.5, label='10% Threshold')
    
    # Add a horizontal line for Strategy returns excluding fees (20/23 of mean)
    strategy_return = stats['mean'] * 20 / 23
    plt.axhline(y=strategy_return, color='orange', linestyle='-.', alpha=0.7, 
                label=f'Strategy returns excluding fees ({strategy_return:.1f}%)')
    
    plt.xlabel('Time (UTC)')
    plt.ylabel('Annualized Rate (%)')
    plt.title('HYPE Funding Rate (March 24 - June 14, 2025) [15-Minute Intervals]')
    plt.legend()
    plt.grid(True, alpha=0.3)
    plt.ylim(0, 100)  # Set y-axis limit from 0 to 100%
    plt.tight_layout()
    
    # Save the plot
    plt.savefig('funding_rate_analysis_scaled.png')
    plt.close()

if __name__ == "__main__":
    analyze_funding_rates()