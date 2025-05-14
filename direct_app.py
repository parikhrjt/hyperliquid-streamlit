import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import time
import os
from datetime import datetime, timedelta
from IPython.display import HTML, display
import random

st.title("Hyperliquid Trader Analysis")

# Find CSV files
csv_files = [f for f in os.listdir() if f.endswith('.csv')]
if csv_files:
    csv_file = st.selectbox("Select CSV file", csv_files)
    
    if st.button("Analyze"):
        # Create data directory
        os.makedirs("hyperliquid_data", exist_ok=True)
        
        # ===== YOUR EXACT CODE BELOW =====
        
        # Define the trader addresses
        try:
            # Read CSV file directly
            df = pd.read_csv(csv_file)
            if 'address' in df.columns:
                TRADER_ADDRESSES = df['address'].tolist()
                st.write(f"Successfully loaded {len(TRADER_ADDRESSES)} trader addresses from CSV")
            else:
                TRADER_ADDRESSES = ["0xac50a255e330c388f44b9d01259d6b153a9f0ed9"]
                st.write(f"CSV doesn't have 'address' column. Using test address: {TRADER_ADDRESSES[0]}")
        except Exception as e:
            TRADER_ADDRESSES = ["0xac50a255e330c388f44b9d01259d6b153a9f0ed9"]
            st.write(f"Error loading addresses from CSV: {e}")
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
                        st.write("Unexpected response structure from metaAndAssetCtxs")
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
                    st.write(f"Error fetching market data: Status code {response.status_code}")
                    return {}, {}
            except Exception as e:
                st.write(f"Exception when fetching market data: {e}")
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
                    st.write(f"Error fetching fills for {address}: Status code {response.status_code}")
                    return []
            except Exception as e:
                st.write(f"Exception when fetching fills for {address}: {e}")
                return []

        def save_fills_to_csv(fills, filename):
            """Save fills data to CSV"""
            if not fills:
                st.write("No fills data to save")
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
            # Add progress bar and status
            progress_bar = st.progress(0)
            status_text = st.empty()
            
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
            status_text.write("Fetching current prices...")
            progress_bar.progress(10)
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
            
            total_addresses = len(TRADER_ADDRESSES)
            for i, address in enumerate(TRADER_ADDRESSES):
                # Update progress
                progress_value = 10 + (i / total_addresses) * 50
                progress_bar.progress(int(progress_value))
                status_text.write(f"Processing address {i+1}/{total_addresses}: {address}")
                
                # Fetch all fills for this address
                fills = get_user_fills(address)
                
                # Add trader address to each fill
                for fill in fills:
                    fill['trader_address'] = address
                
                # Add to all fills
                all_fills.extend(fills)
            
            # Step 3: Filter only fills from the last 24 hours
            status_text.write("Processing fill data...")
            progress_bar.progress(70)
            
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
            status_text.write("Calculating metrics...")
            progress_bar.progress(80)
            
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
            status_text.write("Generating summary...")
            progress_bar.progress(90)
            
            summary_data = []
            
            # Process each coin with activity
            all_coins = set()
            for data in time_windows.values():
                all_coins.update(data['volumes'].keys())
            
            st.write(f"Found activity for {len(all_coins)} coins")
            
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
                    st.write(f"Warning: No price found for {coin}, using $1.00")
                
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
            
            # Sort by 24h volume (descending)
            if '24h Volume' in df.columns and not df.empty:
                df = df.sort_values('24h Volume', ascending=False)
            
            # Save the summary data to file
            save_to_file(summary_data, "trading_summary")
            
            # Complete the progress bar
            progress_bar.progress(100)
            status_text.write("Analysis complete!")
            
            return df

        # =========================
        # Run the analysis
        result = analyze_trader_activity()
        
        # Display the DataFrame
        if result is not None and not result.empty:
            st.write(f"Analysis found data for {len(result)} coins")
            st.dataframe(result)
            
            # Offer download
            csv = result.to_csv(index=False).encode('utf-8')
            st.download_button("Download CSV", csv, "hyperliquid_analysis.csv", "text/csv")
        else:
            st.error("No data was found")
else:
    st.error("No CSV files found in directory")
