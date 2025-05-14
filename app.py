import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import time
import os
import sys
from datetime import datetime

# Set environment variable to avoid permission issues
os.environ["STREAMLIT_HOME"] = os.path.join(os.getcwd(), ".streamlit")

# Configure page
st.set_page_config(page_title="Hyperliquid Trader Analysis", layout="wide")
st.title("Hyperliquid Trader Analysis")

# Debug information
st.sidebar.write("Current working directory:", os.getcwd())
st.sidebar.write("Files in directory:", os.listdir())

# Get available CSV files
csv_files = [f for f in os.listdir() if f.endswith('.csv')]
st.sidebar.write("Available CSV files:", csv_files)

# Sidebar for configuration
st.sidebar.header("Configuration")

# Default trader address
default_trader = "0xac50a255e330c388f44b9d01259d6b153a9f0ed9"

# Check for CSV files
if csv_files:
    selected_csv = st.sidebar.selectbox("Select CSV file", csv_files)
    use_csv = st.sidebar.checkbox("Use traders from CSV file", value=True)
    
    if use_csv and selected_csv:
        try:
            addresses_df = pd.read_csv(selected_csv)
            num_addresses = len(addresses_df)
            st.sidebar.write(f"Found {num_addresses} addresses in {selected_csv}")
            
            # Select how many addresses to use
            limit = st.sidebar.slider("Limit number of addresses to analyze", 
                                     min_value=1, 
                                     max_value=min(num_addresses, 100), 
                                     value=min(20, num_addresses))
            
            # Create global variable for addresses that will be used by hyperliquid_analysis.py
            if 'address' in addresses_df.columns:
                # Take only the first 'limit' addresses
                TRADER_ADDRESSES = addresses_df['address'].head(limit).tolist()
                # Set global tt variable that the original code uses
                global tt
                tt = {"address": TRADER_ADDRESSES}
                
                st.sidebar.success(f"Using {len(TRADER_ADDRESSES)} addresses from CSV")
                
                # Show sample addresses
                with st.sidebar.expander("Sample addresses"):
                    for i, addr in enumerate(TRADER_ADDRESSES[:5]):
                        st.write(f"{i+1}. {addr}")
            else:
                st.sidebar.error(f"CSV file doesn't have 'address' column. Columns found: {addresses_df.columns.tolist()}")
                use_csv = False
        except Exception as e:
            st.sidebar.error(f"Error reading CSV: {e}")
            use_csv = False
else:
    use_csv = False
    st.sidebar.warning("No CSV files found. Enter addresses manually.")

# If not using CSV, get manual input
if not use_csv:
    trader_input = st.sidebar.text_area("Trader Addresses (one per line)", default_trader)
    TRADER_ADDRESSES = [addr.strip() for addr in trader_input.split("\n") if addr.strip()]
    # Set global tt variable that the original code uses
    global tt
    tt = {"address": TRADER_ADDRESSES}

# Import the analysis functions
try:
    from hyperliquid_analysis import analyze_trader_activity, format_for_display, format_currency
    st.sidebar.success("Successfully imported analysis functions")
except Exception as e:
    st.error(f"Error importing analysis functions: {e}")
    st.stop()

# Create directories with error handling
try:
    os.makedirs("hyperliquid_data", exist_ok=True)
    st.sidebar.success("Created data directory")
except Exception as e:
    st.sidebar.warning(f"Could not create data directory: {e}")

# Run analysis button
if st.sidebar.button("Run Analysis"):
    with st.spinner("Analyzing trader data..."):
        try:
            st.info(f"Analyzing {len(TRADER_ADDRESSES)} trader addresses...")
            
            # Run the analysis
            result_df = analyze_trader_activity()
            
            if result_df is not None and not result_df.empty:
                # Format for display
                display_df = format_for_display(result_df)
                
                # Display summary metrics
                st.subheader("Summary")
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Total Assets", len(display_df))
                with col2:
                    if '24h Volume' in result_df.columns:
                        total_volume = result_df['24h Volume'].sum()
                        st.metric("Total 24h Volume", format_currency(total_volume))
                
                # Display the analysis table
                st.subheader("Trader Activity Analysis")
                st.dataframe(display_df)
                
                # Add download button
                csv = display_df.to_csv(index=False).encode('utf-8')
                st.download_button(
                    "Download CSV",
                    csv,
                    "hyperliquid_analysis.csv",
                    "text/csv",
                    key='download-csv'
                )
            else:
                st.error("No data available to display")
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.exception(e)  # This will show the full traceback
else:
    st.info("Click 'Run Analysis' to fetch the latest trading data.")

# Add app explanation
with st.expander("About this app"):
    st.write("""
    This app analyzes top trader activity on Hyperliquid using the official API.
    It reads trader addresses from a CSV file or you can enter them manually.
    Click 'Run Analysis' to start the process.
    """)
