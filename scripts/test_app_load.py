import subprocess
import sys

res = subprocess.run([sys.executable, "-c", "import app; print('APP_LOAD_OK')"], capture_output=True, text=True)
print("Returncode:", res.returncode)
print("Output:", res.stdout.strip())
if res.returncode != 0:
    print("Stderr:", res.stderr)
    sys.exit(1)
print("🎉 app.py loads perfectly in a fresh subprocess without any ImportError!")
