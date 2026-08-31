import os
import sys
import socket
import subprocess

# Force IPv4 socket resolution globally for Render cloud container
_orig_getaddrinfo = socket.getaddrinfo
def _force_ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

socket.getaddrinfo = _force_ipv4_getaddrinfo

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
