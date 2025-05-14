import streamlit as st
import pandas as pd
import os
import sys

# Create streamlit_adapter.py if it doesn't exist
if not os.path.exists("streamlit_adapter.py"):
    with open("streamlit_adapter.py", "w") as f:
        f.write("""
import streamlit as st

class HTML:
    def __init__(self, content):
        self.content = content

def display(content):
    if hasattr(content, 'content'):
        st.markdown(content.content, unsafe_allow_html=True)
    else:
        st.write(content)
""")

# Configure page
st.set_page_config(page_title="Hyperliquid Trader Analysis", layout="wide")
st.title("Hyperliquid Trader Analysis")

# Find CSV files
csv_files = [f for f in os.listdir() if f.endswith('.csv')]

if csv_files:
    selected_csv = st.selectbox("Select trader addresses file", csv_files)
    try:
        df = pd.read_csv(selected_csv)
        st.success(f"Found {len(df)} addresses in file")
        
        if 'address' in df.columns:
            addresses = df['address'].tolist()
            st.success(f"Using {len(addresses)} addresses")
            
            # Set global variable for hyperliquid_analysis.py
            global tt
            tt = {"address": addresses}
            
            # Create data directory
            os.makedirs("hyperliquid_data", exist_ok=True)
            
            # Create a button to run the analysis
            if st.button("Run Analysis"):
                st.write("Running analysis... This may take several minutes")
                
                try:
                    # Import hyperliquid_analysis.py
                    import hyperliquid_analysis
                    
                    # Run the analysis
                    result_df = hyperliquid_analysis.analyze_trader_activity()
                    
                    # Check if we got results
                    if result_df is not None and not result_df.empty:
                        st.success(f"Analysis found {len(result_df)} coins with trading activity")
                        
                        # Display the dataframe
                        st.dataframe(result_df)
                        
                        # Download button
                        csv = result_df.to_csv(index=False).encode('utf-8')
                        st.download_button("Download CSV", csv, "hyperliquid_analysis.csv", "text/csv")
                    else:
                        st.error("No data was found in the analysis results")
                except Exception as e:
                    st.error(f"An error occurred during analysis: {e}")
                    st.exception(e)  # Show detailed error
        else:
            st.error("CSV file doesn't have an 'address' column. Please use a different file.")
    except Exception as e:
        st.error(f"Error loading CSV: {e}")
else:
    st.error("No CSV files found in the repository. Please add a CSV file with trader addresses.")
