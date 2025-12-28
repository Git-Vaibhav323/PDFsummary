"""
Quick start script for Streamlit dashboard.
Run this file to start the Streamlit app.
"""
import subprocess
import sys
import os

# Add app directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    # Run Streamlit app
    # Use localhost instead of 0.0.0.0 for browser access
    subprocess.run([
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app/streamlit_app.py",
        "--server.port=8501",
        "--server.address=localhost"
    ])

