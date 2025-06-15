# HYOE - Funding Rate Analysis Tool

A Python-based tool for analyzing and visualizing cryptocurrency funding rates across different timeframes.

## Overview

This project provides tools to fetch, process, and analyze funding rate data from cryptocurrency exchanges. It includes functionality for:
- Fetching funding rate data
- Resampling data to different timeframes
- Generating visualizations
- Analyzing funding rate patterns

## Setup

1. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

The project consists of several Python scripts:

- `fetch_funding_data.py`: Fetches funding rate data
- `resample_funding_data.py`: Resamples data to different timeframes
- `funding_analysis.py`: Performs analysis on the funding rate data
- `main.py`: Main entry point for the application

To run the analysis:
```bash
python main.py
```

## Data Files

The project generates several CSV files containing funding rate data at different timeframes:
- `hype_funding_rates_1min.csv`
- `hype_funding_rates_15min.csv`
- `hype_funding_rates_6h.csv`
- `hype_funding_rates_24h.csv`

## Visualizations

The tool generates various visualization files:
- `funding_rate_analysis.png`
- `funding_rate_analysis_6h.png`
- `funding_rate_analysis_24h.png`
- `funding_rate_analysis_24h_with_strategy.png`
- `funding_rate_analysis_scaled.png`

## License

MIT License 