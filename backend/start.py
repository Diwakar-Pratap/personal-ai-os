"""
start.py - Launcher script.
Optionally starts ngrok for phone access, then starts the Uvicorn server.

Usage:
    python start.py

Set ENABLE_NGROK=true in .env and add your NGROK_AUTH_TOKEN to get a public URL.
Get a free token at: https://dashboard.ngrok.com/get-started/your-authtoken
"""
import os
import sys
from pathlib import Path

# Ensure backend/ is on the Python path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()


def start():
    enable_ngrok = os.getenv("ENABLE_NGROK", "false").lower() == "true"
    port = int(os.getenv("PORT", "8000"))

    if enable_ngrok:
        try:
            from pyngrok import ngrok

            auth_token = os.getenv("NGROK_AUTH_TOKEN", "")
            if auth_token:
                ngrok.set_auth_token(auth_token)
            else:
                print("[WARN] NGROK_AUTH_TOKEN not set - running without authentication.")

            # Kill any stale tunnels from previous sessions before opening a new one
            ngrok.kill()

            tunnel = ngrok.connect(port)
            public_url = tunnel.public_url

            print("\n" + "=" * 55)
            print(f"  [URL]   Public URL  : {public_url}")
            print(f"  [PHONE] Use on phone: {public_url}")
            print(f"  [DOCS]  API docs    : {public_url}/docs")
            print("=" * 55 + "\n")

        except ImportError:
            print("[ERROR] pyngrok not installed. Run: pip install pyngrok")
        except Exception as e:
            print(f"[WARN] ngrok failed ({e}). Running on localhost only.")

    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=port,
        reload=True,
        log_level="info",
    )


if __name__ == "__main__":
    start()
