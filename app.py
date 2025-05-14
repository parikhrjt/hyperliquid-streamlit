import streamlit as st

# Simple app
st.title("Hyperliquid Trader Analysis")
st.write("Initial setup successful!")

# Show environment details
st.sidebar.header("Configuration")
st.sidebar.info("App is running on Streamlit Cloud!")

# Add a simple button
if st.button("Click me to confirm the app is working"):
    st.success("Success! The app is working correctly.")
