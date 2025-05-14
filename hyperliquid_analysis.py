import pandas as pd
import numpy as np
import requests
import json
import time
import os
from datetime import datetime, timedelta
import streamlit as st

# Define class for compatibility with IPython.display
class HTML:
    def __init__(self, content):
        self.content = content

# Define display function for compatibility with IPython.display
def display(content):
    if isinstance(content, HTML):
        st.markdown(content.content, unsafe_allow_html=True)
    else:
        st.write(content)

# Define the trader addresses
try:
    # Try to access tt["address"] 
    TRADER_ADDRESSES = tt["address"]
    st.write(f"Successfully loaded {len(TRADER_ADDRESSES)} trader addresses")
except:
    # If tt is not defined, use a placeholder address for testing
    TRADER_ADDRESSES = ["0xac50a255e330c388f44b9d01259d6b153a9f0ed9"]
    st.write(f"Using test address: {TRADER_ADDRESSES[0]}")

# Fallback prices if needed
DEFAULT_PRICES = {
    "BTC": 83100.00,
    "ETH": 4450.00,
    "SOL": 267.60,
    "AVAX": 114.85,
    "HYPE": 11.39,
    "XRP": 0.52,
    "HBAR": 0.09,
    "FARTCOIN": 1.20,
    "MELANIA": 0.39,
    "@107": 0.09
}

def save_to_file(data, filename):
    """Save data to a JSON file"""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{filename}_{timestamp}.json"
    
    with open(filename, 'w') as f:
        json.dump(data, f, indent=2)
    
    st.write(f"Data saved to {filename}")
    return filename

def get_price_data():
    """Fetch current prices from Hyperliquid API"""
    url = "https://api.hyperliquid.xyz/info"
    payload = {"type": "metaAndAssetCtxs"}
    
    try:
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            data = response.json()
            
            # Check if the response has the expected structure
            if not isinstance(data, list) or len(data) < 2:
                st.warning("Unexpected response structure from metaAndAssetCtxs")
                return {}, {}
            
            # Extract universe (metadata) and asset contexts (prices)
            meta = data[0]
            asset_ctxs = data[1]
            
            # Create price mappings
            current_prices = {}
            prev_day_prices = {}
            
            # Get list of coin names from universe
            coin_names = [coin['name'] for coin in meta['universe']]
            
            # Extract prices from asset contexts
            for i, ctx in enumerate(asset_ctxs):
                if i < len(coin_names):
                    coin_name = coin_names[i]
                    
                    # Get current price in priority order: midPx, markPx, oraclePx
                    current_price = None
                    if 'midPx' in ctx and ctx['midPx'] is not None:
                        try:
                            current_price = float(ctx['midPx'])
                        except (ValueError, TypeError):
                            pass
                    
                    if current_price is None and 'markPx' in ctx and ctx['markPx'] is not None:
                        try:
                            current_price = float(ctx['markPx'])
                        except (ValueError, TypeError):
                            pass
                    
                    if current_price is None and 'oraclePx' in ctx and ctx['oraclePx'] is not None:
                        try:
                            current_price = float(ctx['oraclePx'])
                        except (ValueError, TypeError):
                            pass
                    
                    # Store current price if valid
                    if current_price is not None:
                        current_prices[coin_name] = current_price
                    
                    # Get previous day price
                    prev_price = None
                    if 'prevDayPx' in ctx and ctx['prevDayPx'] is not None:
                        try:
                            prev_price = float(ctx['prevDayPx'])
                        except (ValueError, TypeError):
                            pass
                    
                    # Store previous day price if valid
                    if prev_price is not None:
                        prev_day_prices[coin_name] = prev_price
            
            st.write(f"Fetched current prices for {len(current_prices)} coins")
            return current_prices, prev_day_prices
        else:
            st.error(f"Error fetching market data: Status code {response.status_code}")
            return {}, {}
    except Exception as e:
        st.error(f"Exception when fetching market data: {e}")
        return {}, {}

def get_user_fills(address):
    """Fetch fills data for a specific address"""
    url = "https://api.hyperliquid.xyz/info"
    
    payload = {
        "type": "userFills",
        "user": address,
        "aggregateByTime": True
    }
    headers = {"Content-Type": "application/json"}
    
    try:
        response = requests.post(url, headers=headers, json=payload)
        if response.status_code == 200:
            data = response.json()
            st.write(f"Fetched {len(data)} fills for {address}")
            return data
        else:
            st.error(f"Error fetching fills for {address}: Status code {response.status_code}")
            return []
    except Exception as e:
        st.error(f"Exception when fetching fills for {address}: {e}")
        return []

def save_fills_to_csv(fills, filename):
    """Save fills data to CSV"""
    if not fills:
        st.warning("No fills data to save")
        return None
    
    # Convert to DataFrame
    df = pd.DataFrame(fills)
    
    # Add human-readable timestamp column
    if 'time' in df.columns:
        df['datetime'] = pd.to_datetime(df['time'], unit='ms')
    
    # Save to CSV
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"{filename}_{timestamp}.csv"
    df.to_csv(csv_filename, index=False)
    
    st.write(f"Saved {len(df)} fills to CSV: {csv_filename}")
    return csv_filename

def calculate_price_change(current, previous):
    """Calculate percentage change between current and previous values"""
    if current is None or previous is None or previous == 0:
        return None
    
    return ((current - previous) / previous) * 100

def analyze_trader_activity():
    """Main function to analyze trader activity based on fills data"""
    # Calculate cutoff time for 24h window
    now = datetime.now()
    cutoff_times = {
        '24h': now - timedelta(hours=24),
        '12h': now - timedelta(hours=12),
        '6h': now - timedelta(hours=6),
        '3h': now - timedelta(hours=3),
        '1h': now - timedelta(hours=1)
    }
    
    # Convert to timestamps (milliseconds)
    cutoff_timestamps = {
        window: int(dt.timestamp() * 1000) 
        for window, dt in cutoff_times.items()
    }
    
    st.write(f"Using cutoff timestamp for 24h: {cutoff_timestamps['24h']} ({cutoff_times['24h'].strftime('%Y-%m-%d %H:%M:%S')})")
    
    # Step 1: Fetch current prices
    st.write("Fetching current prices...")
    current_prices, prev_day_prices = get_price_data()
    
    # Calculate price changes
    price_changes = {}
    for coin in current_prices:
        if coin in prev_day_prices:
            change = calculate_price_change(current_prices[coin], prev_day_prices[coin])
            if change is not None:
                price_changes[coin] = change
    
    # Step 2: Fetch and process fills for each address
    all_fills = []
    
    progress_bar = st.progress(0)
    for i, address in enumerate(TRADER_ADDRESSES):
        # Update progress
        progress = (i + 1) / len(TRADER_ADDRESSES)
        progress_bar.progress(progress)
        
        # Fetch all fills for this address
        fills = get_user_fills(address)
        
        # Add trader address to each fill
        for fill in fills:
            fill['trader_address'] = address
        
        # Add to all fills
        all_fills.extend(fills)
    
    # Reset progress bar
    progress_bar.empty()
    
    # Step 3: Filter only fills from the last 24 hours
    last_24h_cutoff = cutoff_timestamps['24h']
    fills_24h = [f for f in all_fills if int(f.get('time', 0)) >= last_24h_cutoff]
    
    st.write(f"Total fills: {len(all_fills)}")
    st.write(f"Fills from last 24 hours: {len(fills_24h)}")
    
    # Save all 24h fills to CSV file for investigation
    fills_csv = save_fills_to_csv(fills_24h, "fills_last_24h")
    
    # Step 4: Initialize data structures for each time window
    time_windows = {}
    for window, cutoff in cutoff_timestamps.items():
        fills_window = [f for f in all_fills if int(f.get('time', 0)) >= cutoff]
        time_windows[window] = {
            'fills': fills_window,
            'open_positions': {},  # Coin -> {long, short}
            'volumes': {},         # Coin -> total volume
            'unique_traders': {},  # Coin -> set of traders
            'entry_prices': {}     # Coin -> {long_value, long_size, short_value, short_size}
        }
    
    # Step 5: Process fills for each time window
    for window, data in time_windows.items():
        fills = data['fills']
        
        # Initialize entry price tracking
        data['entry_prices'] = {}  # Coin -> {long_value, long_size, short_value, short_size}
        
        # Process each fill
        for fill in fills:
            # Get basic fill data
            coin = fill.get('coin')
            if not coin:
                continue
                
            # Get trader address
            trader = fill.get('trader_address')
            
            # Track unique traders for this coin
            if coin not in data['unique_traders']:
                data['unique_traders'][coin] = set()
            if trader:
                data['unique_traders'][coin].add(trader)
            
            # Get size, price and direction
            size = abs(float(fill.get('sz', 0.0)))
            price = float(fill.get('px', 0.0))
            direction = fill.get('dir', '')
            
            # Track trading volume for this coin
            if coin not in data['volumes']:
                data['volumes'][coin] = 0.0
            data['volumes'][coin] += size
            
            # Track open positions and weighted entry prices
            if 'Open' in direction:
                # Initialize entry price tracking for this coin
                if coin not in data['entry_prices']:
                    data['entry_prices'][coin] = {
                        'long_value': 0.0,
                        'long_size': 0.0,
                        'short_value': 0.0,
                        'short_size': 0.0
                    }
                
                # Initialize open positions for this coin
                if coin not in data['open_positions']:
                    data['open_positions'][coin] = {'long': 0.0, 'short': 0.0}
                
                if 'Long' in direction:
                    data['open_positions'][coin]['long'] += size
                    # Add to weighted entry price calculation
                    data['entry_prices'][coin]['long_value'] += size * price
                    data['entry_prices'][coin]['long_size'] += size
                elif 'Short' in direction:
                    data['open_positions'][coin]['short'] += size
                    # Add to weighted entry price calculation
                    data['entry_prices'][coin]['short_value'] += size * price
                    data['entry_prices'][coin]['short_size'] += size
    
    # Step 6: Calculate metrics for the summary table
    summary_data = []
    
    # Process each coin with activity
    all_coins = set()
    for data in time_windows.values():
        all_coins.update(data['volumes'].keys())
    
    for coin in all_coins:
        # Skip coins with no data
        if coin not in time_windows['24h']['volumes']:
            continue
        
        # Get current price for this coin
        if coin in current_prices:
            current_price = current_prices[coin]
        elif coin in DEFAULT_PRICES:
            current_price = DEFAULT_PRICES[coin]
        else:
            # Use $1 as fallback price
            current_price = 1.0
            st.warning(f"No price found for {coin}, using $1.00")
        
        # Calculate total volume in USD
        volume_usd = {}
        for window, data in time_windows.items():
            if coin in data['volumes']:
                volume_usd[window] = data['volumes'][coin] * current_price
            else:
                volume_usd[window] = 0.0
        
        # Calculate long/short ratios
        ls_ratios = {}
        for window, data in time_windows.items():
            if coin in data['open_positions']:
                pos = data['open_positions'][coin]
                total = pos['long'] + pos['short']
                if total > 0:
                    ls_ratios[window] = {
                        'long': (pos['long'] / total) * 100,
                        'short': (pos['short'] / total) * 100
                    }
                else:
                    ls_ratios[window] = {'long': 0, 'short': 0}
            else:
                ls_ratios[window] = {'long': 0, 'short': 0}
        
        # Count unique traders
        trader_counts = {}
        for window, data in time_windows.items():
            if coin in data['unique_traders']:
                trader_counts[window] = len(data['unique_traders'][coin])
            else:
                trader_counts[window] = 0
        
        # Get price change
        price_change = price_changes.get(coin, 0)
        
        # Calculate weighted average entry prices (24h window only)
        entry_prices = {}
        if coin in time_windows['24h']['entry_prices']:
            entry_data = time_windows['24h']['entry_prices'][coin]
            
            # Calculate long entry price
            if entry_data['long_size'] > 0:
                long_entry = entry_data['long_value'] / entry_data['long_size']
            else:
                long_entry = None
                
            # Calculate short entry price
            if entry_data['short_size'] > 0:
                short_entry = entry_data['short_value'] / entry_data['short_size']
            else:
                short_entry = None
                
            # Calculate total entry price
            total_size = entry_data['long_size'] + entry_data['short_size']
            if total_size > 0:
                total_entry = (entry_data['long_value'] + entry_data['short_value']) / total_size
            else:
                total_entry = None
                
            entry_prices = {
                'total': total_entry,
                'long': long_entry,
                'short': short_entry
            }
            
            # Debug print entry prices for this coin
            st.write(f"Entry prices for {coin}: Total=${entry_prices['total']}, Long=${entry_prices['long']}, Short=${entry_prices['short']}")
        else:
            entry_prices = {'total': None, 'long': None, 'short': None}
        
        # Add to summary data
        summary_data.append({
            'Asset': coin,
            'Current Price': current_price,
            'Price Change': price_change,
            'Total Notional Value': volume_usd['24h'],  # Use 24h volume
            
            # Open position percentages (24h)
            'Open Pct Long': ls_ratios['24h']['long'],
            'Open Pct Short': ls_ratios['24h']['short'],
            
            # Entry prices
            'Open Total Avg Entry': entry_prices['total'],
            'Open Long Avg Entry': entry_prices['long'],
            'Open Short Avg Entry': entry_prices['short'],
            
            # Time window data
            '24h Volume': volume_usd['24h'],
            '24h Pct Long': ls_ratios['24h']['long'],
            '24h Pct Short': ls_ratios['24h']['short'],
            '24h Traders': trader_counts['24h'],
            
            '12h Volume': volume_usd['12h'],
            '12h Pct Long': ls_ratios['12h']['long'],
            '12h Pct Short': ls_ratios['12h']['short'],
            '12h Traders': trader_counts['12h'],
            
            '6h Volume': volume_usd['6h'],
            '6h Pct Long': ls_ratios['6h']['long'],
            '6h Pct Short': ls_ratios['6h']['short'],
            '6h Traders': trader_counts['6h'],
            
            '3h Volume': volume_usd['3h'],
            '3h Pct Long': ls_ratios['3h']['long'],
            '3h Pct Short': ls_ratios['3h']['short'],
            '3h Traders': trader_counts['3h'],
            
            '1h Volume': volume_usd['1h'],
            '1h Pct Long': ls_ratios['1h']['long'],
            '1h Pct Short': ls_ratios['1h']['short'],
            '1h Traders': trader_counts['1h'],
        })
    
    # Create DataFrame
    df = pd.DataFrame(summary_data)
    
    # Debug column names
    st.write("Summary data columns:", df.columns.tolist())
    
    # Sort by 24h volume (descending)
    if '24h Volume' in df.columns and not df.empty:
        df = df.sort_values('24h Volume', ascending=False)
    
    # Save the summary data to file
    save_to_file(summary_data, "trading_summary")
    
    return df

def format_currency(value):
    """Format numeric value as currency"""
    if value is None or pd.isna(value):
        return "N/A"
    
    if value >= 1000000:
        return f"${value/1000000:.2f}M"
    elif value >= 1000:
        return f"${value/1000:.2f}K"
    else:
        return f"${value:.2f}"

def format_percent(value):
    """Format numeric value as percentage with + or - sign"""
    if value is None or pd.isna(value):
        return ""
    
    return f"+{value:.0f}%" if value >= 0 else f"{value:.0f}%"

def format_ls_ratio(long_pct, short_pct):
    """Format long/short ratio properly ensuring sum is 100%"""
    # Round to nearest integer
    long_rounded = round(long_pct)
    short_rounded = 100 - long_rounded  # Ensure they sum to 100%
    
    return f"{long_rounded}% L / {short_rounded}% S"

def format_volume_with_traders(volume, traders):
    """Format volume with trader count"""
    vol_str = format_currency(volume)
    return f"{vol_str}\n({traders} traders)"

def format_for_display(df):
    """Format DataFrame for display"""
    if df is None or df.empty:
        return None
    
    # Make a copy
    formatted_df = df.copy()
    
    # Format current price
    formatted_df['Current Price'] = formatted_df.apply(
        lambda row: f"{format_currency(row['Current Price'])}\n{format_percent(row['Price Change'])}", 
        axis=1
    )
    
    # Format volume
    formatted_df['Volume'] = formatted_df.apply(
        lambda row: f"{format_currency(row['Total Notional Value'])}", 
        axis=1
    )
    
    # Format open positions
    formatted_df['Open Positions'] = formatted_df.apply(
        lambda row: format_ls_ratio(row['Open Pct Long'], row['Open Pct Short']), 
        axis=1
    )
    
    # Only attempt to format entry prices if the columns exist
    if all(col in df.columns for col in ['Open Total Avg Entry', 'Open Long Avg Entry', 'Open Short Avg Entry']):
        st.write("Entry price columns found, formatting...")
        
        # Safe getter function to handle missing values
        def safe_get(row, key):
            val = row.get(key)
            if val is None or pd.isna(val):
                return "N/A"
            return format_currency(val)
        
        # Format entry prices
        formatted_df['Open Trades Entry'] = formatted_df.apply(
            lambda row: f"Total: {safe_get(row, 'Open Total Avg Entry')}\nLong: {safe_get(row, 'Open Long Avg Entry')}\nShort: {safe_get(row, 'Open Short Avg Entry')}",
            axis=1
        )
    else:
        st.write("Entry price columns not found, using placeholder")
        formatted_df['Open Trades Entry'] = "N/A"
    
    # Format time windows
    for window in ['24h', '12h', '6h', '3h', '1h']:
        # Format L/S ratio
        formatted_df[f'{window} L/S'] = formatted_df.apply(
            lambda row: format_ls_ratio(row[f'{window} Pct Long'], row[f'{window} Pct Short']), 
            axis=1
        )
        
        # Format volume with traders
        formatted_df[f'{window} Volume'] = formatted_df.apply(
            lambda row: format_volume_with_traders(row[f'{window} Volume'], row[f'{window} Traders']),
            axis=1
        )
    
    # Add action column
    formatted_df['Action'] = "LongShort"
    
    # Prepare column list
    columns = [
        'Asset', 'Current Price', 'Volume', 'Open Positions', 
        '24h L/S', '24h Volume',
        '12h L/S', '12h Volume',
        '6h L/S', '6h Volume',
        '3h L/S', '3h Volume',
        '1h L/S', '1h Volume',
        'Open Trades Entry', 'Action'
    ]
    
    # Return the formatted DataFrame
    return formatted_df[columns]

def generate_styled_table(df):
    """Generate styled HTML table"""
    styles = """
    <style>
        table {
            width: 100%;
            border-collapse: collapse;
            font-family: Arial, sans-serif;
            font-size: 14px;
        }
        th {
            background-color: #f2f2f2;
            color: #333;
            font-weight: bold;
            text-align: left;
            padding: 10px;
            border-bottom: 2px solid #ddd;
        }
        td {
            padding: 10px;
            border-bottom: 1px solid #ddd;
            white-space: pre-line;  /* Allows line breaks */
        }
        tr:hover {
            background-color: #f5f5f5;
        }
        .positive {
            color: green;
        }
        .negative {
            color: red;
        }
        .action-button {
            background-color: #4CAF50;
            border: none;
            color: white;
            padding: 5px 10px;
            text-align: center;
            text-decoration: none;
            display: inline-block;
            font-size: 14px;
            margin: 2px;
            cursor: pointer;
            border-radius: 4px;
        }
    </style>
    """
    
    html_table = df.to_html(classes='table', index=False, escape=False)
    
    # Add color to positive and negative percentages
    html_table = html_table.replace('>+', ' class="positive">+')
    html_table = html_table.replace('>-', ' class="negative">-')
    
    # Replace "LongShort" text with styled buttons
    html_table = html_table.replace('>LongShort<', '><button class="action-button">Long</button><button class="action-button">Short</button><')
    
    return styles + html_table

def save_formatted_table(df, filename="hyperliquid_analysis"):
    """Save the formatted table as HTML"""
    if df is None or df.empty:
        st.warning("No data to save")
        return None
    
    # Generate HTML table
    styled_table = generate_styled_table(df)
    
    # Add HTML wrapper
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>Hyperliquid Analysis</title>
        <meta charset="UTF-8">
    </head>
    <body>
        <h1>Hyperliquid Top Traders Analysis</h1>
        <p>Generated on: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}</p>
        {styled_table}
    </body>
    </html>
    """
    
    # Save to file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    html_filename = f"{filename}_{timestamp}.html"
    
    with open(html_filename, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    st.write(f"HTML table saved to {html_filename}")
    return html_filename

def run_analysis():
    """Main function to run the analysis"""
    st.write("Analyzing Hyperliquid trader activity...")
    
    try:
        # Try to create data directory, but continue if it fails
        data_dir = "hyperliquid_data"
        os.makedirs(data_dir, exist_ok=True)
        os.chdir(data_dir)
        st.write(f"Saving data to {os.path.abspath(data_dir)}")
    except:
        st.write("Working in current directory")
    
    # Analyze trader activity
    result_df = analyze_trader_activity()
    
    if result_df is not None and not result_df.empty:
        # Format for display
        display_df = format_for_display(result_df)
        
        st.write("\nHyperliquid Top Traders Analysis")
        st.write("===============================")
        
        # Generate and display styled table
        styled_table = generate_styled_table(display_df)
        display(HTML(styled_table))
        
        # Save formatted table to HTML file
        save_formatted_table(display_df)
        
        return display_df
    else:
        st.warning("No data available to display")
        return None

# Execute the analysis
if __name__ == "__main__":
    run_analysis()
