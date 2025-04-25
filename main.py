import streamlit as st
from ui.streamlit_app import StreamlitUI
# from utils.logger import logger
import torch

# torch.classes.__path__ = []

def main():
    """Main entry point of the application."""
    try:
        app = StreamlitUI()
        app.render()
    except Exception as e:
        st.error(f"The application encountered an error: {str(e)}")
        # logger.error(f"Application error: {e}")

if __name__ == "__main__":
    main()
