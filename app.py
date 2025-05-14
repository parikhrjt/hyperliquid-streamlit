import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import time
import os
import sys
from datetime import datetime

# Configure page
st.set_page_config(page_title="Hyperliquid Trader Analysis", layout="wide")
st.title("Hyperliquid Trader Analysis")

# Create streamlit_adapter.py if it doesn't exist
ADAPTER_CODE = """
import streamlit as st

# Create mock versions of IPython display functions
class HTML:
    def __init__(self, content):
        self.content = content

def display(content):
    if hasattr(content, 'content'):
        st.markdown(content.content, unsafe_allow_html=True)
    else:
        st.write(content)
"""

if not os.path.exists("streamlit_adapter.py"):
    with open("streamlit_adapter.py", "w") as f:
        f.write(ADAPTER_CODE)

# Make IPython.display work in Streamlit
try:
    import IPython.display
except ImportError:
    sys.modules['IPython.display'] = type('', (), {})()
    sys.modules['IPython.display'].HTML = lambda x: x
    sys.modules['IPython.display'].display = lambda x: None

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
            
        # Set up addresses for analysis
        if 'address' in df.columns:
            addresses = df['address'].tolist()
            st.sidebar.success(f"Ready to analyze {len(addresses)} addresses")
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
global tt
tt = {"address": addresses}

# Create data directory
os.makedirs("hyperliquid_data", exist_ok=True)

# Import analysis functions
try:
    from hyperliquid_analysis import analyze_trader_activity, format_for_display, format_currency
    st.sidebar.success("Analysis functions loaded successfully")
    analysis_available = True
except Exception as e:
    st.sidebar.error(f"Error loading analysis functions: {e}")
    st.error(f"Cannot load analysis functions: {e}")
    analysis_available = False

# Add analysis button
if st.button("Run Analysis"):
    if not analysis_available:
        st.error("Analysis functions could not be loaded")
    elif not addresses:
        st.error("No addresses available for analysis")
    else:
        start_time = time.time()
        
        # Progress indicators
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        status_text.write("Starting analysis...")
        progress_bar.progress(10)
        
        # Run in try-except block to catch any errors
        try:
            # Run the analysis
            result_df = analyze_trader_activity()
            
            if result_df is not None and not result_df.empty:
                # Format for display
                display_df = format_for_display(result_df)
                
                # Show summary stats
                st.subheader("Analysis Results")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Assets Analyzed", len(display_df))
                with col2:
                    total_volume = result_df['24h Volume'].sum() if '24h Volume' in result_df.columns else 0
                    st.metric("Total 24h Volume", format_currency(total_volume))
                with col3:
                    st.metric("Time to Complete", f"{time.time() - start_time:.1f} seconds")
                
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
                
                # Update progress
                progress_bar.progress(100)
                status_text.write("Analysis completed successfully!")
            else:
                st.error("Analysis completed but no data was returned")
        except Exception as e:
            st.error(f"An error occurred during analysis: {e}")
            st.exception(e)  # This will show the full error traceback

# Add an explanation at the bottom
with st.expander("About this app"):
    st.write("""
    This app analyzes top trader activity on Hyperliquid using the official API.
    
    It reads trader addresses from a CSV file and fetches their recent trading history.
    The analysis shows trading volumes, long/short ratios, and other metrics across multiple time frames.
    
    Created using Streamlit and the Hyperliquid API.
    """)
