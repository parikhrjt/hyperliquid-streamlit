import streamlit as st
import pandas as pd
import os
import sys
import time
import traceback

# Set page config
st.set_page_config(
    page_title="Hyperliquid Trader Analysis", 
    layout="wide",
    initial_sidebar_state="expanded"
)

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

# Sidebar
st.sidebar.header("Configuration")
st.sidebar.info("App is running on Streamlit Cloud!")

# Input methods
input_method = st.sidebar.radio(
    "Select input method",
    ["Upload CSV", "Use sample addresses", "Enter addresses manually"]
)

addresses = []

if input_method == "Upload CSV":
    uploaded_file = st.sidebar.file_uploader("Upload CSV with addresses", type=["csv"])
    
    if uploaded_file is not None:
        try:
            df = pd.read_csv(uploaded_file)
            
            if 'address' not in df.columns:
                st.sidebar.error("CSV file must have an 'address' column")
            else:
                addresses = df['address'].tolist()
                st.sidebar.success(f"Found {len(addresses)} addresses")
        except Exception as e:
            st.sidebar.error(f"Error reading CSV: {str(e)}")

elif input_method == "Use sample addresses":
    # Add some sample addresses (replace with actual sample addresses)
    addresses = [
        "0xac50a255e330c388f44b9d01259d6b153a9f0ed9",
        # Add more sample addresses if needed
    ]
    st.sidebar.success(f"Using {len(addresses)} sample addresses")

else:  # Manual entry
    manual_addresses = st.sidebar.text_area(
        "Enter addresses (one per line)",
        "0xac50a255e330c388f44b9d01259d6b153a9f0ed9"
    )
    if manual_addresses:
        addresses = [addr.strip() for addr in manual_addresses.split('\n') if addr.strip()]
        st.sidebar.success(f"Using {len(addresses)} manually entered addresses")

# Show sample of addresses
if addresses:
    with st.sidebar.expander(f"Showing {min(5, len(addresses))} of {len(addresses)} addresses"):
        for i, addr in enumerate(addresses[:5]):
            st.write(f"{i+1}. `{addr}`")
        if len(addresses) > 5:
            st.write(f"...and {len(addresses)-5} more")

    # Set global variable for hyperliquid_analysis.py
    global tt
    tt = {"address": addresses}

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
                
                # Import hyperliquid_analysis here to ensure tt is set
                import hyperliquid_analysis
                
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
    st.info("Please select addresses using one of the input methods in the sidebar.")

# Add some extra information at the bottom
st.sidebar.markdown("---")
st.sidebar.write("Made with ❤️ using Streamlit")
