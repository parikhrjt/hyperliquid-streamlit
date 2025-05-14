import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import time
import os
from datetime import datetime

# Import the functions from your analysis file
from hyperliquid_analysis import get_price_data, get_user_fills, analyze_trader_activity, format_for_display, format_currency

# Set page title
st.set_page_config(page_title="Hyperliquid Trader Analysis", layout="wide")
st.title("Hyperliquid Trader Analysis")

# Sidebar for configuration
st.sidebar.header("Configuration")

# Input for trader addresses
default_trader = "0xac50a255e330c388f44b9d01259d6b153a9f0ed9"
trader_input = st.sidebar.text_area("Trader Addresses (one per line)", default_trader)
TRADER_ADDRESSES = [addr.strip() for addr in trader_input.split("\n") if addr.strip()]

# Create a global variable tt that your original code uses
tt = {"address": TRADER_ADDRESSES}

# Run analysis button
if st.sidebar.button("Run Analysis"):
    with st.spinner("Analyzing trader data..."):
        try:
            # Create data directory if it doesn't exist
            os.makedirs("hyperliquid_data", exist_ok=True)
            
            # Run the analysis
            st.info(f"Analyzing {len(TRADER_ADDRESSES)} trader addresses...")
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
else:
    st.info("Click 'Run Analysis' to fetch the latest trading data.")

# Add app explanation
with st.expander("About this app"):
    st.write("""
    This app analyzes top trader activity on Hyperliquid using the official API.
    Enter trader addresses in the sidebar and click 'Run Analysis' to start.
    """)
