import os
import sys
import subprocess

if __name__ == "__main__":
    port = os.environ.get("PORT", "10000")
    print(f"[*] Démarrage automatique de Streamlit sur le port Render {port}...", flush=True)
    cmd = [
        sys.executable,
        "-m",
        "streamlit",
        "run",
        "app.py",
        "--server.port",
        str(port),
        "--server.address",
        "0.0.0.0",
        "--server.headless",
        "true",
        "--server.enableCORS",
        "false",
        "--server.enableXsrfProtection",
        "false"
    ]
    sys.exit(subprocess.call(cmd))
