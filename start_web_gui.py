#!/usr/bin/env python3
"""
Simple launcher for VoxNovel Web GUI
Use this script to directly start the web interface
"""

import os
import sys

# Add current directory to path
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

# Set environment variable to force web mode
os.environ['VOXNOVEL_WEB_MODE'] = '1'

# Import and run the web GUI
try:
    from gui_run_web import main
    print("🎭 VoxNovel Web GUI Launcher")
    print("=" * 40)
    exit_code = main()
    sys.exit(exit_code)
except ImportError as e:
    print(f"❌ Could not import web GUI: {e}")
    print("Make sure all dependencies are installed:")
    print("  pip install flask werkzeug")
    sys.exit(1)
except Exception as e:
    print(f"❌ Error starting web GUI: {e}")
    sys.exit(1)