"""
Runtime hook for PyQt6 on macOS
Fixes Qt plugin loading issues
"""
import os
import sys

# Set Qt plugin path
if sys.platform == 'darwin':
    # Get the directory where the executable is located
    if getattr(sys, 'frozen', False):
        bundle_dir = sys._MEIPASS
        
        # Set Qt plugin paths
        os.environ['QT_PLUGIN_PATH'] = os.path.join(bundle_dir, 'PyQt6', 'Qt6', 'plugins')
        os.environ['QT_QPA_PLATFORM_PLUGIN_PATH'] = os.path.join(bundle_dir, 'PyQt6', 'Qt6', 'plugins', 'platforms')
        
        # Disable Qt's internal plugin search
        os.environ['QT_DEBUG_PLUGINS'] = '0'
