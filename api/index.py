"""
Vercel serverless handler for Streamlit app.
This acts as an HTTP handler that starts the Streamlit process.
"""

import subprocess
import sys
import os

def handler(request):
    """Vercel handler function"""
    # This is a placeholder - Streamlit doesn't work well with Vercel's serverless model
    # Instead, you should use Streamlit Cloud or Docker on Vercel
    return {
        "statusCode": 200,
        "body": "Use Streamlit Cloud instead. See README for deployment instructions."
    }

# For Vercel to recognize this as a valid entrypoint
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 3000))
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        "app.py",
        f"--server.port={port}",
        "--server.headless=true"
    ])
