import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import CandidateProfile, SMTPSettings, UPLOADS_DIR
from services.email_sender import send_single_email
from services.storage_service import load_smtp_settings, load_profile, save_profile

profile = load_profile()
profile.leadership_and_awards = [
    "Président & Team Leader du Club RoboThings (FST Mohammedia)",
    "1er Prix International Summer School (ENSEM / FSTM)",
    "2e Prix Compétition Nationale Robotique"
]
save_profile(profile)
smtp = load_smtp_settings()

cv_fr = str(UPLOADS_DIR / "CV_Mohammed_HSINY_FR.pdf")
cv_en = str(UPLOADS_DIR / "CV_Mohammed_HSINY_EN.pdf")
portfolio_pdf = str(UPLOADS_DIR / "Portfolio_Mohammed_HSINY.pdf")

# 1. Send French test email
print("\n[1/2] Envoi de l'email de test (FRANÇAIS)...")
test_body_fr = f"""Bonjour,

Élève-ingénieur en Génie Électrique & Contrôle Industriel à la {profile.school} et Président du Club RoboThings, je suis activement à la recherche d'un stage PFE de 6 mois à partir de Janvier 2027.

Rigoureux, dynamique et doté d'une forte culture d'ingénierie collaborative, j'ai développé une grande capacité d'adaptation et de leadership à travers la direction de projets technologiques et associatifs.

Pour découvrir concrètement mes réalisations (drones autonomes, robotique communicante, automatismes industriels), je vous invite à explorer mon portfolio interactif :
{profile.portfolio_url}

Mon CV complet ainsi que mon dossier portfolio sont joints à cet email. Seriez-vous disponible pour un court échange téléphonique ou visio de 10 minutes ?

Bien cordialement,"""

res_fr = send_single_email(
    settings=smtp,
    recipient_email=profile.email,
    subject=f"[TEST FR] Stage PFE 2027 - Génie Électrique & Systèmes Autonomes | {profile.name}",
    body_text=test_body_fr,
    attachment_paths=[cv_fr, portfolio_pdf],
    profile=profile,
    language="fr"
)
print("-> Résultat FR :", res_fr.to_dict())

# 2. Send English test email
print("\n[2/2] Envoi de l'email de test (ANGLAIS)...")
test_body_en = f"""Hello,

As an Electrical Engineering & Industrial Control student at {profile.school} and President of the RoboThings Club, I am actively seeking a 6-month graduation internship (PFE) starting January 2027.

Motivated, agile, and team-oriented, I combine a strong engineering mindset with demonstrated leadership and quick problem-solving capabilities.

To give you an immediate overview of my background and hands-on projects (autonomous drones, mobile robotics, R&D systems), please feel free to explore my interactive portfolio:
{profile.portfolio_url}

My Resume and Portfolio Dossier are attached. Would you be open to a brief 10-minute call next week to explore potential opportunities?

Best regards,"""

res_en = send_single_email(
    settings=smtp,
    recipient_email=profile.email,
    subject=f"[TEST EN] 6-Month PFE Internship (Jan 2027) - Electrical & Embedded Engineering | {profile.name}",
    body_text=test_body_en,
    attachment_paths=[cv_en, portfolio_pdf],
    profile=profile,
    language="en"
)
print("-> Résultat EN :", res_en.to_dict())
