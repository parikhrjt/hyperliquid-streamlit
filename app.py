import streamlit as st
import pandas as pd
import os
import sys
import time
import traceback
import glob

# Set page config
st.set_page_config(
    page_title="Hyperliquid Trader Analysis", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# Define the tt variable correctly at the global scope
tt = {"address": []}

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

# Write the adapter file if it doesn't exist
if not os.path.exists("streamlit_adapter.py"):
    with open("streamlit_adapter.py", "w") as f:
        f.write(adapter_content)
    st.sidebar.success("Created streamlit_adapter.py")

# Now we can import it
from streamlit_adapter import HTML, display

# Also inject IPython module for compatibility
sys.modules['IPython'] = type('', (), {})()
sys.modules['IPython.display'] = type('', (), {})()
sys.modules['IPython.display'].HTML = HTML
sys.modules['IPython.display'].display = display

# Main app
st.title("Hyperliquid Trader Analysis")
st.markdown("""
This app analyzes trading activity for specified wallet addresses on Hyperliquid, showing:
- Trading volumes
- Long/Short ratios
- Entry prices
- Price changes
""")

# Debug information
st.sidebar.header("Configuration")
st.sidebar.info("App is running on Streamlit Cloud!")

# Show current directory files
with st.sidebar.expander("Debug: Show Files in Directory"):
    files = glob.glob("*.*")
    st.write("Files in current directory:")
    for file in files:
        st.write(f"- {file}")

# Input methods
input_method = st.radio(
    "Select input method",
    ["CSV in Directory", "Upload CSV", "Enter addresses manually", "Use sample addresses"]
)

addresses = []

if input_method == "CSV in Directory":
    # Find existing CSV files
    csv_files = glob.glob("*.csv")
    
    if not csv_files:
        st.error("No CSV files found in the current directory.")
    else:
        selected_file = st.selectbox("Select a CSV file", csv_files)
        
        try:
            # Display content of file for debugging
            with open(selected_file, 'r') as f:
                sample_content = f.read(1000)  # Read first 1000 chars
            
            st.expander("Preview file content").code(sample_content)
            
            # Read the file
            df = pd.read_csv(selected_file)
            
            # Show column names
            st.write(f"Columns in file: {', '.join(df.columns.tolist())}")
            
            # Check for address column
            if 'address' not in df.columns:
                st.error(f"The CSV file '{selected_file}' does not have an 'address' column.")
                possible_columns = [col for col in df.columns if 'addr' in col.lower()]
                
                if possible_columns:
                    st.warning(f"Found similar columns: {', '.join(possible_columns)}")
                    selected_column = st.selectbox("Select column to use as address", possible_columns)
                    if st.button("Use selected column"):
                        addresses = df[selected_column].tolist()
                        st.success(f"Loaded {len(addresses)} addresses from column '{selected_column}'")
            else:
                addresses = df['address'].tolist()
                st.success(f"Loaded {len(addresses)} addresses from file '{selected_file}'")
                
        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")
            st.code(traceback.format_exc())

elif input_method == "Upload CSV":
    uploaded_file = st.file_uploader("Upload CSV with addresses", type=["csv"])
    
    if uploaded_file is not None:
        try:
            # Display preview of uploaded content
            content = uploaded_file.getvalue().decode('utf-8')
            st.expander("Preview file content").code(content[:1000])  # Show first 1000 chars
            
            # Reset file position
            uploaded_file.seek(0)
            
            # Read the file
            df = pd.read_csv(uploaded_file)
            
            # Show column names
            st.write(f"Columns in file: {', '.join(df.columns.tolist())}")
            
            # Check for address column
            if 'address' not in df.columns:
                st.error("The CSV file does not have an 'address' column.")
                possible_columns = [col for col in df.columns if 'addr' in col.lower()]
                
                if possible_columns:
                    st.warning(f"Found similar columns: {', '.join(possible_columns)}")
                    selected_column = st.selectbox("Select column to use as address", possible_columns)
                    if st.button("Use selected column"):
                        addresses = df[selected_column].tolist()
                        st.success(f"Loaded {len(addresses)} addresses from column '{selected_column}'")
            else:
                addresses = df['address'].tolist()
                st.success(f"Loaded {len(addresses)} addresses from uploaded file")
                
        except Exception as e:
            st.error(f"Error reading CSV: {str(e)}")
            st.code(traceback.format_exc())

elif input_method == "Enter addresses manually":
    manual_addresses = st.text_area(
        "Enter addresses (one per line)",
        "0xac50a255e330c388f44b9d01259d6b153a9f0ed9"
    )
    if manual_addresses:
        addresses = [addr.strip() for addr in manual_addresses.split('\n') if addr.strip()]
        st.success(f"Using {len(addresses)} manually entered addresses")

else:  # Use sample addresses
    # Add some sample addresses
    addresses = [
        "0xac50a255e330c388f44b9d01259d6b153a9f0ed9",
        "0x7ad5ebad9f38eb0859a61b030fe0e462944a50f3",
        "0x38de9e2a992a12bdc566fca8162aeaca749b49d5"
    ]
    st.success(f"Using {len(addresses)} sample addresses")

# Show sample of addresses
if addresses:
    with st.expander(f"Showing addresses ({len(addresses)} total)"):
        for i, addr in enumerate(addresses[:10]):  # Show first 10
            st.write(f"{i+1}. `{addr}`")
        if len(addresses) > 10:
            st.write(f"...and {len(addresses)-10} more")

    # Update the global tt variable with the addresses
    tt["address"] = addresses
    
    # Also create a file with addresses to make sure it's accessible
    with open("addresses.txt", "w") as f:
        for addr in addresses:
            f.write(addr + "\n")
    
    # Show what was set
    st.write(f"Analysis will run on {len(tt['address'])} addresses")
    
    # Debug - Show content of tt
    st.sidebar.write(f"Debug: Global tt has {len(tt['address'])} addresses")

    # Run analysis button
    if st.button("🚀 Run Analysis", type="primary", use_container_width=True):
        start_time = time.time()
        
        # Make sure hyperliquid_data directory exists
        os.makedirs("hyperliquid_data", exist_ok=True)
        
        with st.spinner("📊 Analyzing Hyperliquid data..."):
            try:
                # Progress indicators
                progress_container = st.empty()
                progress_container.info("Importing analysis module...")
                
                # Create a context file to pass addresses to the analysis module
                with open("trader_addresses.txt", "w") as f:
                    for addr in addresses:
                        f.write(addr + "\n")
                
                progress_container.info(f"Set up {len(addresses)} addresses for analysis...")
                
                # Import hyperliquid_analysis here 
                import hyperliquid_analysis
                
                # Explicitly set addresses in the module
                hyperliquid_analysis.TRADER_ADDRESSES = addresses
                
                progress_container.info("Fetching price data...")
                
                # Run analysis with progress updates
                result_df = hyperliquid_analysis.analyze_trader_activity()
                
                # Check results
                if result_df is not None and not result_df.empty:
                    # Show results
                    progress_container.empty()
                    
                    duration = time.time() - start_time
                    
                    # Results section
                    st.success(f"✅ Analysis complete! Found data for {len(result_df)} assets. Time to complete {duration:.1f} seconds")
                    
                    # Create tabs for different views
                    tab1, tab2, tab3 = st.tabs(["Table View", "Formatted View", "Raw Data"])
                    
                    with tab1:
                        # Show dataframe
                        st.dataframe(result_df, use_container_width=True)
                    
                    with tab2:
                        # Format for display
                        try:
                            display_df = hyperliquid_analysis.format_for_display(result_df)
                            styled_table = hyperliquid_analysis.generate_styled_table(display_df)
                            st.markdown(styled_table, unsafe_allow_html=True)
                        except Exception as format_error:
                            st.error(f"Error formatting display: {str(format_error)}")
                            st.dataframe(result_df, use_container_width=True)
                    
                    with tab3:
                        # Raw JSON view
                        st.json(result_df.to_dict(orient="records"))
                    
                    # Download options
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        csv = result_df.to_csv(index=False).encode('utf-8')
                        st.download_button(
                            "📥 Download CSV", 
                            csv, 
                            "hyperliquid_analysis.csv", 
                            "text/csv",
                            use_container_width=True
                        )
                    
                    with col2:
                        # JSON download
                        json_str = result_df.to_json(orient="records", indent=2)
                        st.download_button(
                            "📥 Download JSON",
                            json_str,
                            "hyperliquid_analysis.json",
                            "application/json",
                            use_container_width=True
                        )
                    
                    with col3:
                        # HTML download
                        try:
                            display_df = hyperliquid_analysis.format_for_display(result_df)
                            html = hyperliquid_analysis.generate_styled_table(display_df)
                            html_full = f"""
                            <!DOCTYPE html>
                            <html>
                            <head>
                                <title>Hyperliquid Analysis</title>
                                <meta charset="UTF-8">
                            </head>
                            <body>
                                <h1>Hyperliquid Top Traders Analysis</h1>
                                {html}
                            </body>
                            </html>
                            """
                            st.download_button(
                                "📥 Download HTML",
                                html_full,
                                "hyperliquid_analysis.html",
                                "text/html",
                                use_container_width=True
                            )
                        except Exception as html_error:
                            st.error(f"Error generating HTML: {str(html_error)}")
                else:
                    st.warning("⚠️ Analysis completed but no data was returned.")
            except Exception as e:
                st.error(f"❌ Error during analysis: {str(e)}")
                st.code(traceback.format_exc())
else:
    st.info("Please select addresses using one of the input methods above.")

# Add extra information at the bottom
st.sidebar.markdown("---")
st.sidebar.write("Made with ❤️ using Streamlit")
