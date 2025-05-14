# Streamlit Hyperliquid Trader Analysis App

This app analyzes trading activity for specified wallet addresses on Hyperliquid, showing:
- Trading volumes
- Long/Short ratios
- Entry prices
- Price changes

## Setup Instructions

1. Make sure your GitHub repository contains these files:
   - `app.py` - The main Streamlit application
   - `hyperliquid_analysis.py` - The analysis code
   - `requirements.txt` - The dependencies for the app

2. Update your `requirements.txt` to include:
   ```
   streamlit>=1.31.0
   pandas>=2.1.0
   numpy>=1.26.0
   requests>=2.31.0
   ```

3. Deploy the app to Streamlit Cloud by connecting your GitHub repository.

## Usage

1. When the app runs, select one of the following input methods:
   - **CSV in Directory**: Select an existing CSV file in the app directory
   - **Upload CSV**: Upload a CSV file with trader addresses
   - **Enter addresses manually**: Type wallet addresses directly
   - **Use sample addresses**: Use predefined sample addresses

2. The CSV file must have a column named `address` containing the wallet addresses to analyze.

3. Click "Run Analysis" to process the data and generate reports.

4. View the results in different formats:
   - Table View: Simple tabular format
   - Formatted View: Styled HTML table with colors
   - Raw Data: JSON representation of the data

5. Download the results in CSV, JSON, or HTML format.

## Troubleshooting

If you experience issues:

1. Check the debug information in the sidebar to see available files
2. Verify that your CSV file has an "address" column
3. Try with fewer addresses first (5-10) to test functionality
4. Check for errors in the console and fix accordingly

## Key Files

- `app.py`: The main Streamlit interface
- `hyperliquid_analysis.py`: The analysis logic
- `requirements.txt`: Dependencies
- `streamlit_adapter.py`: (Created at runtime) Compatibility layer for IPython functions
