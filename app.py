import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import os
from datetime import datetime

# Page configuration
st.set_page_config(page_title="Hyperliquid Trader Analysis", layout="wide")
st.title("Hyperliquid Trader Analysis")

# Sidebar configuration
st.sidebar.header("Configuration")

# Find CSV files in the directory
csv_files = [f for f in os.listdir() if f.endswith('.csv')]

if csv_files:
    st.sidebar.success(f"Found {len(csv_files)} CSV files")
    selected_csv = st.sidebar.selectbox("Select trader addresses file", csv_files)
    
    # Try to load and display the CSV
    try:
        df = pd.read_csv(selected_csv)
        st.sidebar.write(f"Found {len(df)} addresses in file")
        
        # Display sample addresses
        with st.expander("Preview of addresses"):
            st.dataframe(df.head())
            
        # Set up addresses for analysis - use all addresses
        if 'address' in df.columns:
            addresses = df['address'].tolist()
            st.sidebar.success(f"Using all {len(addresses)} addresses")
        else:
            st.sidebar.error("CSV does not have an 'address' column")
            addresses = []
    except Exception as e:
        st.sidebar.error(f"Error loading CSV: {e}")
        addresses = []
else:
    st.sidebar.warning("No CSV files found")
    
    # Fallback to manual address input
    default_address = "0xac50a255e330c388f44b9d01259d6b153a9f0ed9"
    address_input = st.sidebar.text_area("Enter trader addresses (one per line)", default_address)
    addresses = [addr.strip() for addr in address_input.split("\n") if addr.strip()]

# Display the selected addresses
st.write(f"Ready to analyze {len(addresses)} trader addresses")
if addresses:
    st.write("Sample of addresses to analyze:")
    for i, addr in enumerate(addresses[:5]):
        st.write(f"{i+1}. {addr}")
    if len(addresses) > 5:
        st.write(f"... and {len(addresses)-5} more")

# Create global variable that will be used by hyperliquid_analysis.py
# This is a bridge between the two files
global tt
tt = {"address": addresses}

# Import analysis functions
try:
    from hyperliquid_analysis import get_price_data, analyze_trader_activity, format_for_display
    st.sidebar.success("Analysis functions loaded successfully")
    analysis_available = True
except Exception as e:
    st.sidebar.error(f"Error loading analysis functions: {e}")
    analysis_available = False

# Create data directory
os.makedirs("hyperliquid_data", exist_ok=True)

# Add analysis button with actual functionality
if st.button("Run Analysis"):
    if not analysis_available:
        st.error("Analysis functions could not be loaded")
    elif not addresses:
        st.error("No addresses available for analysis")
    else:
        with st.spinner("Running Hyperliquid trader analysis..."):
            try:
                # Run the analysis
                st.info(f"Analyzing trading activity for {len(addresses)} addresses...")
                result_df = analyze_trader_activity()
                
                if result_df is not None and not result_df.empty:
                    # Format for display
                    display_df = format_for_display(result_df)
                    
                    # Show summary stats
                    st.subheader("Analysis Results")
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Total Assets Analyzed", len(display_df))
                    with col2:
                        total_volume = result_df['24h Volume'].sum() if '24h Volume' in result_df.columns else 0
                        st.metric("Total 24h Volume", f"${total_volume/1000000:.2f}M")
                    
                    # Display the full table
                    st.subheader("Trader Activity Analysis")
                    st.dataframe(display_df)
                    
                    # Add download option
                    csv = display_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        "Download CSV",
                        csv,
                        "hyperliquid_analysis.csv",
                        "text/csv",
                        key='download-csv'
                    )
                    
                    st.success("Analysis completed successfully!")
                else:
                    st.warning("Analysis completed but no data was returned")
            except Exception as e:
                st.error(f"An error occurred during analysis: {e}")
                st.exception(e)  # This will show the full error traceback
