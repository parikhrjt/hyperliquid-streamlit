import streamlit as st
import pandas as pd
import os
import time
import sys

# Configure page
st.set_page_config(page_title="Hyperliquid Trader Analysis", layout="wide")
st.title("Hyperliquid Trader Analysis")

# Find CSV files
csv_files = [f for f in os.listdir() if f.endswith('.csv')]

if csv_files:
    selected_csv = st.sidebar.selectbox("Select trader addresses file", csv_files)
    try:
        df = pd.read_csv(selected_csv)
        st.sidebar.success(f"Found {len(df)} addresses in file")
        
        if 'address' in df.columns:
            addresses = df['address'].tolist()
            st.sidebar.success(f"Using {len(addresses)} addresses")
        else:
            st.sidebar.error("CSV doesn't have 'address' column")
            addresses = []
    except Exception as e:
        st.sidebar.error(f"Error loading CSV: {e}")
        addresses = []
else:
    st.sidebar.warning("No CSV files found")
    default_address = "0xac50a255e330c388f44b9d01259d6b153a9f0ed9"
    address_input = st.sidebar.text_area("Enter trader addresses (one per line)", default_address)
    addresses = [addr.strip() for addr in address_input.split("\n") if addr.strip()]

# Display addresses
st.write(f"Ready to analyze {len(addresses)} trader addresses")
if addresses:
    st.write("Sample addresses:")
    for i, addr in enumerate(addresses[:5]):
        st.write(f"{i+1}. {addr}")
    if len(addresses) > 5:
        st.write(f"... and {len(addresses)-5} more")

# Create global variable for hyperliquid_analysis.py
global tt
tt = {"address": addresses}

# Create data directory
os.makedirs("hyperliquid_data", exist_ok=True)

# Add imports for IPython display
sys.modules['IPython'] = type('', (), {})()
sys.modules['IPython.display'] = type('', (), {})()
sys.modules['IPython.display'].HTML = lambda x: x
sys.modules['IPython.display'].display = lambda x: None

# Import hyperliquid_analysis.py
try:
    # Import just to verify the file exists
    import hyperliquid_analysis
    
    # Replace IPython display with our adapter
    sys.modules['IPython.display'].HTML = lambda x: st.markdown(x, unsafe_allow_html=True)
    sys.modules['IPython.display'].display = lambda x: st.write(x)
    
    st.sidebar.success("Hyperliquid analysis code loaded successfully")
    analysis_available = True
except Exception as e:
    st.sidebar.error(f"Error loading analysis code: {e}")
    st.error(f"Cannot load analysis code: {e}")
    analysis_available = False

# Run button
if st.button("Run Analysis"):
    if not analysis_available:
        st.error("Analysis code could not be loaded")
    elif not addresses:
        st.error("No addresses available for analysis")
    else:
        start_time = time.time()
        progress_bar = st.progress(0)
        status = st.empty()
        
        status.write("Starting analysis...")
        
        try:
            # Just run the analysis directly
            result_df = hyperliquid_analysis.analyze_trader_activity()
            
            # Display the results
            if result_df is not None and not result_df.empty:
                display_df = hyperliquid_analysis.format_for_display(result_df)
                
                st.subheader("Analysis Results")
                st.write(f"Found {len(display_df)} assets with trading activity")
                st.write(f"Time to complete: {time.time() - start_time:.1f} seconds")
                
                # Show the data
                st.dataframe(display_df)
                
                # Add download button
                csv = display_df.to_csv(index=False).encode('utf-8')
                st.download_button("Download CSV", csv, "hyperliquid_analysis.csv", "text/csv")
                
                # Success message
                st.success("Analysis completed successfully!")
            else:
                st.error("Analysis completed but no data was returned")
        except Exception as e:
            st.error(f"An error occurred: {e}")
            st.exception(e)
