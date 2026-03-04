import sys
import os

def get_asset_path(filename):
    """
    Get absolute path to resource, works for dev and for PyInstaller
    """
    if hasattr(sys, '_MEIPASS'):
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
        return os.path.join(base_path, "assets", filename)
    else:
        # Normal execution
        return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "assets", filename))
