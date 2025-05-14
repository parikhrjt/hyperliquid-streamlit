"""
Adapter to make the notebook code work in Streamlit
"""
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
