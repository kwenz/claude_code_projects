"""Startup script for the AI Research Paper Feed web application."""

import subprocess
import sys
import os
from pathlib import Path

# Add project root to path to import config
sys.path.insert(0, str(Path(__file__).parent.parent))
import config

def main():
    """Run the Streamlit application."""
    
    # Ensure we're in the right directory (project root, not scripts)
    script_dir = Path(__file__).parent.parent
    os.chdir(script_dir)
    
    print("🚀 Starting AI Research Paper Feed Web Application...")
    print("📍 Navigate to the URL shown below in your browser")
    print("🔄 Use the 'Refresh' button to fetch and analyze new papers")
    print("🛑 Press Ctrl+C to stop the server")
    print("-" * 60)
    
    # Run Streamlit
    try:
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app/app.py",
            "--server.headless", "true",
            "--server.port", str(config.SERVER_PORT),
            "--server.address", config.SERVER_HOST
        ])
    except KeyboardInterrupt:
        print("\n👋 Shutting down the application...")
    except Exception as e:
        print(f"❌ Error starting the application: {e}")
        print("💡 Make sure you have installed the requirements: pip install -r requirements.txt")

if __name__ == "__main__":
    main()
