"""ICR Lab — Intent Compression Ratio & Token Economics Explorer.

A Streamlit dashboard for visualizing how interaction architecture
affects token consumption in AI systems.
"""

import sys
from pathlib import Path

import streamlit as st

# Add project root to path for imports
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

# --- Navigation (hidden from sidebar — pages use inline nav links) ---
home_page = st.Page("pages/home.py", title="Home", icon="🏠", default=True)
help_page = st.Page("pages/help.py", title="Help & Glossary", icon="📖")

nav = st.navigation([home_page, help_page], position="hidden")

st.set_page_config(
    page_title="ICR and Token Economics",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

nav.run()
