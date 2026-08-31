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

print("="*75)
print("   🚀 MOTEUR D'EXPÉDITION CONTINUE HAUTE PERFORMANCE (ZÉRO BLOCAGE)")
print("="*75)

init_db()
profile = load_profile()
smtp = load_smtp_settings()

if not smtp.app_password:
    print("[ERREUR] Mot de passe d'application Gmail manquant dans config/db.")
    sys.exit(1)

contacts = get_all_contacts()
approved = [c for c in contacts if c.get("status") == "approved"]

print(f"\n[*] Profil Actif       : {profile.name} ({profile.email})")
print(f"[*] Contacts Prêts     : {len(approved)} candidatures dans la file d'attente")

if not approved:
    print("[INFO] Aucun contact en attente d'envoi. Tous les contacts sont traités !")
    sys.exit(0)

cv_fr_file = UPLOADS_DIR / "CV_Mohammed_HSINY_FR.pdf"
cv_en_file = UPLOADS_DIR / "CV_Mohammed_HSINY_EN.pdf"
portfolio_pdf_file = UPLOADS_DIR / "Portfolio_Mohammed_HSINY.pdf"

print(f"[*] CV Français        : {'✅ Présent' if cv_fr_file.is_file() else '❌ Manquant'}")
print(f"[*] CV Anglais         : {'✅ Présent' if cv_en_file.is_file() else '❌ Manquant'}")
print(f"[*] Portfolio PDF      : {'✅ Présent' if portfolio_pdf_file.is_file() else '❌ Manquant'}")

print("\n" + "-"*75)
input("👉 Appuyez sur ENTRÉE pour démarrer l'envoi continu...")
print("-"*75 + "\n")

success_count = 0
fail_count = 0
total = len(approved)

for idx, item in enumerate(approved, 1):
    rec_name = item.get("name") or item["email"]
    company = item.get("company", "N/A")
    lang = item.get("language", "fr")
    
    print(f"[{idx}/{total}] 📤 Envoi à {rec_name} ({item['email']}) — {company}...", end=" ", flush=True)
    
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
        print("✅ SUCCÈS")
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
        
    # Security jitter delay
    if idx < total:
        delay = random.uniform(3.0, 6.0)
        time.sleep(delay)

print("\n" + "="*75)
print(f"🎉 EXPÉDITION TERMINÉE : {success_count} réussis | {fail_count} échecs sur {total} contacts.")
print("="*75)
