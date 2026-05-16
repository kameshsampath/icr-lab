"""CLI entry point for ICR Lab."""

import sys
from pathlib import Path


def main():
    """Launch the ICR Lab Streamlit application."""
    from streamlit.web.cli import main as st_main

    app_path = str(Path(__file__).parent / "main.py")
    sys.argv = ["streamlit", "run", app_path]
    st_main()
