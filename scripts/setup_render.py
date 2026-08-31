import os

os.makedirs(".streamlit", exist_ok=True)

with open(".streamlit/config.toml", "w", encoding="utf-8") as f:
    f.write("[server]\nheadless = true\nenableCORS = false\nenableXsrfProtection = false\naddress = \"0.0.0.0\"\nport = 10000\n\n[browser]\ngatherUsageStats = false\n")

with open("render.yaml", "w", encoding="utf-8") as f:
    f.write("services:\n  - type: web\n    name: ai-cold-outreach-engine\n    runtime: python\n    plan: free\n    buildCommand: pip install -r requirements.txt\n    startCommand: streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true\n    envVars:\n      - key: PYTHON_VERSION\n        value: 3.12.0\n")

with open("Procfile", "w", encoding="utf-8") as f:
    f.write("web: streamlit run app.py --server.port $PORT --server.address 0.0.0.0 --server.headless true\n")

with open(".gitignore", "w", encoding="utf-8") as f:
    f.write("__pycache__/\n*.pyc\n.env\n.DS_Store\n")

print("[OK] Tous les fichiers de déploiement Render ont été générés avec succès !")
