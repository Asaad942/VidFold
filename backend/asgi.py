import os
import sys

# Get the absolute path of the current file's directory
current_dir = os.path.dirname(os.path.abspath(__file__))

# Add the backend directory to Python path
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

from app.main import app 