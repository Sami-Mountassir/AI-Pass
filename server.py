#!/usr/bin/env python
"""
Streamlit entrypoint for Vercel deployment.
This file serves as the recognized Python entrypoint for Vercel's Python builder.
"""

import subprocess
import sys
import os

if __name__ == "__main__":
    # Run Streamlit app with Vercel-compatible settings
    port = os.environ.get("PORT", "3000")
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "app.py",
        f"--server.port={port}",
        "--server.headless=true",
        "--server.enableCORS=false"
    ])
