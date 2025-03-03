"""
Main entry point for the FastAPI application
"""
import os
import sys

# Add the backend directory to Python path
current_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.server import app 