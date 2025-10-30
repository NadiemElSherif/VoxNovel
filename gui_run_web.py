#!/usr/bin/env python3
"""
Web-based GUI for VoxNovel - replaces the desktop tkinter GUI with a web interface
"""

import os
import sys
import subprocess
import webbrowser
import time
import threading
from pathlib import Path

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import existing VoxNovel functionality
try:
    import download_missing_booknlp_models
    print("✓ BookNLP modules initialized")
except ImportError as e:
    print(f"⚠ Warning: Could not import BookNLP modules: {e}")

# Import the web server
try:
    from web_server import app
    WEB_SERVER_AVAILABLE = True
    print("✓ Web server module available")
except ImportError as e:
    print(f"⚠ Warning: Could not import web server: {e}")
    print("  Make sure web_server.py and Flask are installed")
    WEB_SERVER_AVAILABLE = False

def check_dependencies():
    """Check if all required dependencies are available"""
    print("Checking dependencies...")

    # Check for required Python packages
    required_packages = ['flask', 'werkzeug']
    missing_packages = []

    for package in required_packages:
        try:
            __import__(package)
            print(f"✓ {package} installed")
        except ImportError:
            missing_packages.append(package)
            print(f"✗ {package} missing")

    if missing_packages:
        print(f"\nInstalling missing packages: {', '.join(missing_packages)}")
        try:
            subprocess.check_call([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            print("✓ Dependencies installed successfully")
            return True
        except subprocess.CalledProcessError:
            print("✗ Failed to install dependencies")
            return False

    return True

def setup_directories():
    """Create necessary directories if they don't exist"""
    directories = [
        'uploads',
        'output_audiobooks',
        'Working_files',
        'Working_files/generated_audio_clips',
        'Working_files/temp_ebook',
        'Final_combined_output_audio',
        'tortoise',
        'web_interface/static',
        'web_interface/templates'
    ]

    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✓ Directory ready: {directory}")

def initialize_models():
    """Initialize BookNLP and TTS models"""
    print("Initializing AI models...")

    try:
        # This will download and initialize BookNLP models
        if 'download_missing_booknlp_models' in sys.modules:
            print("✓ BookNLP models checked")

        # Test basic TTS import
        try:
            from TTS.api import TTS
            print("✓ TTS library available")
        except ImportError:
            print("⚠ TTS library not available - will install later")

        return True
    except Exception as e:
        print(f"⚠ Model initialization warning: {e}")
        return True  # Continue even if models aren't fully ready

def get_local_ip():
    """Get the local IP address for the server"""
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except:
        return "127.0.0.1"

def open_browser_delayed(url):
    """Open browser after a short delay to ensure server is running"""
    time.sleep(2)
    try:
        webbrowser.open(url)
        print(f"✓ Browser opened to {url}")
    except:
        print(f"⚠ Could not open browser automatically")
        print(f"  Please manually navigate to: {url}")

def main():
    """Main function to run the web GUI"""
    print("🎭 VoxNovel Web Interface Starting...")
    print("=" * 50)

    # Check dependencies
    if not check_dependencies():
        print("❌ Failed to install dependencies")
        return 1

    # Setup directories
    setup_directories()

    # Initialize models
    if not initialize_models():
        print("❌ Failed to initialize models")
        return 1

    # Check if web server is available
    if not WEB_SERVER_AVAILABLE:
        print("❌ Web server not available")
        print("  Please ensure web_server.py exists and Flask is installed")
        return 1

    # Get local IP and port
    local_ip = get_local_ip()
    port = 8080

    print("\n" + "=" * 50)
    print("🚀 Starting VoxNovel Web Server...")
    print(f"📡 Local access: http://127.0.0.1:{port}")
    print(f"📡 Network access: http://{local_ip}:{port}")
    print("=" * 50)

    # Open browser in a separate thread after delay
    browser_thread = threading.Thread(
        target=open_browser_delayed,
        args=(f"http://127.0.0.1:{port}",),
        daemon=True
    )
    browser_thread.start()

    try:
        # Run the Flask web server
        app.run(
            host='0.0.0.0',  # Listen on all interfaces
            port=port,
            debug=False,     # Don't run in debug mode for production
            threaded=True    # Handle multiple requests
        )
    except KeyboardInterrupt:
        print("\n👋 VoxNovel Web Server stopped by user")
        return 0
    except Exception as e:
        print(f"\n❌ Error running web server: {e}")
        return 1

if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)