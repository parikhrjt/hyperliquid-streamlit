import streamlit as st
import pandas as pd
import os

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

# Add analysis button (without functionality yet)
if st.button("Run Analysis"):
    st.info("Analysis feature will be added in the next step")
    
    # Show spinner to simulate work being done
    with st.spinner("Simulating analysis..."):
        import time
        time.sleep(2)
    
    st.success("Basic UI is working correctly!")
