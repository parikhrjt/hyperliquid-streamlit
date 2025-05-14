"""
Adapter file to make hyperliquid_analysis.py compatible with Streamlit
"""

# Create a mock display function
class MockDisplay:
    @staticmethod
    def display(content):
        # This is a no-op since Streamlit has its own display mechanism
        pass

# Create a bridge between notebook and Streamlit
try:
    from IPython.display import HTML, display
except ImportError:
    # Create mock versions if not in notebook environment
    HTML = lambda content: content
    display = MockDisplay.display
