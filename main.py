import os
import sys
import subprocess

if __name__ == "__main__":
    port = os.environ.get("PORT", "10000")
    print(f"[*] Démarrage optimisé de Streamlit sur le port {port}...", flush=True)
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port", str(port),
        "--server.address", "0.0.0.0",
        "--server.headless", "true",
        "--server.enableCORS", "false",
        "--server.enableXsrfProtection", "false",
        "--server.enableWebsocketCompression", "false",
        "--server.fileWatcherType", "none",
        "--browser.gatherUsageStats", "false"
    ]
    sys.exit(subprocess.call(cmd))
