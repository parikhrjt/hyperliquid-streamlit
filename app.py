import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import time
import os
from datetime import datetime

# Set page title
st.set_page_config(page_title="Hyperliquid Trader Analysis", layout="wide")
st.title("Hyperliquid Trader Analysis")

# Sidebar for configuration
st.sidebar.header("Configuration")

# Check if CSV file exists and load it
csv_file_path = "top traders hyperdash hyperliquid sample big.csv"
use_csv = False

if os.path.exists(csv_file_path):
    st.sidebar.success(f"Found traders CSV file: {csv_file_path}")
    use_csv = st.sidebar.checkbox("Use traders from CSV file", value=True)
else:
    st.sidebar.warning(f"CSV file not found: {csv_file_path}")
    use_csv = False

# Only show manual input if not using CSV
if not use_csv:
    # Input for trader addresses
    default_trader = "0xac50a255e330c388f44b9d01259d6b153a9f0ed9"
    trader_input = st.sidebar.text_area("Trader Addresses (one per line)", default_trader)
    TRADER_ADDRESSES = [addr.strip() for addr in trader_input.split("\n") if addr.strip()]
else:
    try:
        # Just to show the user
        addresses_df = pd.read_csv(csv_file_path)
        num_addresses = len(addresses_df)
        limit = st.sidebar.slider("Limit number of addresses to analyze", 
                                  min_value=1, 
                                  max_value=min(num_addresses, 100), 
                                  value=min(50, num_addresses))
        st.sidebar.info(f"Using {limit} addresses from CSV file (out of {num_addresses} total)")
        
        # Display sample of addresses
        with st.sidebar.expander("View sample addresses"):
            st.dataframe(addresses_df.head(5))
    except Exception as e:
        st.sidebar.error(f"Error reading CSV: {e}")

# Import the functions from your analysis file (do this after setting global variables)
from hyperliquid_analysis import analyze_trader_activity, format_for_display, format_currency

# Run analysis button
if st.sidebar.button("Run Analysis"):
    with st.spinner("Analyzing trader data..."):
        try:
            # Create data directory if it doesn't exist
            os.makedirs("hyperliquid_data", exist_ok=True)
            
            # Run the analysis (no need to pass TRADER_ADDRESSES, it will use the CSV)
            st.info("Fetching and analyzing trader data...")
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
            st.error("Check the logs for more details")
else:
    st.info("Click 'Run Analysis' to fetch the latest trading data.")

# Add app explanation
with st.expander("About this app"):
    st.write("""
    This app analyzes top trader activity on Hyperliquid using the official API.
    It reads trader addresses from the CSV file or you can enter them manually.
    Click 'Run Analysis' to start the process.
    """)
