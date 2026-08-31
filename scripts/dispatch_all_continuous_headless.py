import sys
import os
import time
import random
from pathlib import Path

# Add project root to path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from config import SMTPSettings, CandidateProfile, UPLOADS_DIR
from services.storage_service import init_db, get_all_contacts, save_or_update_contact, log_sent_email, load_profile, load_smtp_settings
from services.email_sender import send_single_email

sys.stdout.reconfigure(encoding='utf-8')

print("="*80)
print("   ☁️ GITHUB ACTIONS CLOUD DISPATCH RUNNER - MOHAMMED HSINY (PFE 2027)")
print("="*80)

init_db()
profile = load_profile()
smtp = load_smtp_settings()

# Allow override via environment variables from GitHub Secrets
if os.getenv("GMAIL_SENDER_EMAIL"):
    smtp.sender_email = os.getenv("GMAIL_SENDER_EMAIL")
if os.getenv("GMAIL_APP_PASSWORD"):
    smtp.app_password = os.getenv("GMAIL_APP_PASSWORD")

if not smtp.app_password:
    print("[ERREUR CRITIQUE] Mot de passe d'application Gmail manquant.")
    sys.exit(1)

contacts = get_all_contacts()
approved = [c for c in contacts if c.get("status") == "approved"]

print(f"[*] Expéditeur         : {smtp.sender_name} <{smtp.sender_email}>")
print(f"[*] Total Contacts     : {len(contacts)}")
print(f"[*] Candidatures Prêtes: {len(approved)} prêtes dans la file d'attente Cloud")

if not approved:
    print("[INFO] Aucun contact avec statut 'approved'. Rien à envoyer.")
    sys.exit(0)

cv_fr_file = UPLOADS_DIR / "CV_Mohammed_HSINY_FR.pdf"
cv_en_file = UPLOADS_DIR / "CV_Mohammed_HSINY_EN.pdf"
portfolio_pdf_file = UPLOADS_DIR / "Portfolio_Mohammed_HSINY.pdf"

print(f"[*] CV Français        : {'✅ Présent' if cv_fr_file.is_file() else '❌ Manquant'}")
print(f"[*] CV Anglais         : {'✅ Présent' if cv_en_file.is_file() else '❌ Manquant'}")
print(f"[*] Portfolio PDF      : {'✅ Présent' if portfolio_pdf_file.is_file() else '❌ Manquant'}")

# Set batch limit if needed (e.g. max 100 per run to respect Google quota)
max_batch_env = os.getenv("BATCH_LIMIT")
max_batch = int(max_batch_env) if max_batch_env and max_batch_env.isdigit() else len(approved)
targets = approved[:max_batch]

print(f"\n[*] 🚀 Démarrage de l'envoi Cloud pour {len(targets)} contacts...\n")

success_count = 0
fail_count = 0
total = len(targets)

for idx, item in enumerate(targets, 1):
    rec_name = item.get("name") or item["email"]
    company = item.get("company", "N/A")
    lang = item.get("language", "fr")
    
    print(f"[{idx:03d}/{total:03d}] 📤 {rec_name} ({item['email']}) — {company}...", end=" ", flush=True)
    
    selected_cv = str(cv_fr_file) if (lang == "fr" and cv_fr_file.is_file()) else str(cv_en_file if cv_en_file.is_file() else cv_fr_file)
    att_list = []
    if Path(selected_cv).is_file():
        att_list.append(selected_cv)
    if portfolio_pdf_file.is_file():
        att_list.append(str(portfolio_pdf_file))
        
    res = send_single_email(
        settings=smtp,
        recipient_email=item["email"],
        subject=item["subject"],
        body_text=item["body"],
        attachment_paths=att_list,
        profile=profile,
        language=lang
    )
    
    if res.success:
        print(f"✅ SUCCÈS ({res.message})")
        item["status"] = "sent"
        save_or_update_contact(item)
        log_sent_email(item["email"], item["subject"], item["body"], "SUCCESS")
        success_count += 1
    else:
        print(f"❌ ÉCHEC ({res.message})")
        item["status"] = "failed"
        save_or_update_contact(item)
        log_sent_email(item["email"], item["subject"], item["body"], "FAILED", res.message)
        fail_count += 1
        
    # Inter-email pause (3 to 6s)
    if idx < total:
        time.sleep(random.uniform(3.5, 6.0))

print("\n" + "="*80)
print(f"🎉 SESSION CLOUD TERMINÉE : {success_count} réussis | {fail_count} échecs sur {total} contacts.")
print("="*80)
