"""
Vercel serverless function entry point for the FastAPI backend.
"""
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.main import app

# Vercel requires a handler function
handler = app

