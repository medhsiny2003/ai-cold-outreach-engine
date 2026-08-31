import sys
import os
import time
import importlib
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

print("="*80)
print("   🔄 BOUCLE DE VALIDATION CONTINUE (5 CYCLES SANS AUCUNE ERREUR)")
print("="*80)

modules = [
    'config',
    'services.storage_service',
    'services.contact_manager',
    'services.prompt_builder',
    'services.llm_service',
    'services.email_sender',
    'services.gmail_cleaner',
    'services.analytics_service',
    'services.response_tracker',
    'app'
]

for cycle in range(1, 6):
    print(f"\n[*] 🌀 CYCLE DE CONTRÔLE {cycle}/5...")
    all_ok = True
    for m in modules:
        try:
            if m in sys.modules:
                del sys.modules[m]
            importlib.import_module(m)
            print(f"    ✅ {m:<35} : OK")
        except Exception as e:
            print(f"    ❌ {m:<35} : ERREUR -> {e}")
            all_ok = False
            
    if not all_ok:
        print(f"❌ Échec lors du cycle {cycle} !")
        sys.exit(1)
    else:
        print(f"  🎉 Cycle {cycle}/5 validé avec succès (0 erreur) !")
    time.sleep(1)

print("\n" + "="*80)
print("🏆 TOUS LES 5 CYCLES DE VALIDATION ONT RÉUSSI AVEC ZÉRO ERREUR !")
print("="*80)
