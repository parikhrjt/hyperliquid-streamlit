import streamlit as st
import pandas as pd
import os
import sys
import time

# Set page config
st.set_page_config(page_title="Hyperliquid Trader Analysis", layout="wide")
st.title("Hyperliquid Trader Analysis")

# Create adapter file first before anything else
adapter_content = """
import streamlit as st

class HTML:
    def __init__(self, content):
        self.content = content

def display(content):
    if hasattr(content, 'content'):
        st.markdown(content.content, unsafe_allow_html=True)
    else:
        st.write(content)
"""

# Write the adapter file
with open("streamlit_adapter.py", "w") as f:
    f.write(adapter_content)

# Now we can import it
from streamlit_adapter import HTML, display

# Also inject IPython module for compatibility
sys.modules['IPython'] = type('', (), {})()
sys.modules['IPython.display'] = type('', (), {})()
sys.modules['IPython.display'].HTML = HTML
sys.modules['IPython.display'].display = display

# Make sure hyperliquid_data directory exists
os.makedirs("hyperliquid_data", exist_ok=True)

# Find CSV files
csv_files = [f for f in os.listdir() if f.endswith('.csv')]

if not csv_files:
    st.error("No CSV files found. Please add a CSV file with trader addresses.")
    st.stop()

# Ask user to select a CSV file
selected_csv = st.selectbox("Select trader addresses file", csv_files)

# Try to load the selected CSV
try:
    df = pd.read_csv(selected_csv)
    
    if 'address' not in df.columns:
        st.error("The CSV file does not have an 'address' column.")
        st.stop()
        
    addresses = df['address'].tolist()
    st.success(f"Found {len(addresses)} addresses in {selected_csv}")
    
    # Show sample addresses
    with st.expander("Sample addresses"):
        for i, addr in enumerate(addresses[:5]):
            st.write(f"{i+1}. {addr}")
        if len(addresses) > 5:
            st.write(f"...and {len(addresses)-5} more")
            
    # Set global variable for hyperliquid_analysis.py
    # This needs to be in the global namespace
    global tt
    tt = {"address": addresses}
    
    # Run analysis button
    if st.button("Run Analysis"):
        start_time = time.time()
        
        with st.spinner("Analyzing Hyperliquid data... This may take a while"):
            try:
                # Import hyperliquid_analysis here to ensure tt is set
                import hyperliquid_analysis
                
                # Show message
                progress_text = st.empty()
                progress_text.write("Fetching price data...")
                
                # Run analysis
                result_df = hyperliquid_analysis.analyze_trader_activity()
                
                # Check results
                if result_df is not None and not result_df.empty:
                    # Show results
                    st.success(f"Analysis complete! Found data for {len(result_df)} assets.")
                    st.metric("Time to complete", f"{time.time() - start_time:.1f} seconds")
                    
                    # Show dataframe
                    st.dataframe(result_df)
                    
                    # Download option
                    csv = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button("Download CSV", csv, "hyperliquid_analysis.csv", "text/csv")
                else:
                    st.warning("Analysis completed but no data was returned.")
            except Exception as e:
                st.error(f"Error during analysis: {e}")
                st.exception(e)
except Exception as e:
    st.error(f"Error loading CSV file: {e}")
