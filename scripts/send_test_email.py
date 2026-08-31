import sys
from pathlib import Path

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import CandidateProfile, SMTPSettings, UPLOADS_DIR
from services.email_sender import send_single_email
from services.storage_service import load_smtp_settings, load_profile

profile = load_profile()
smtp = load_smtp_settings()

cv_fr = str(UPLOADS_DIR / "CV_Mohammed_HSINY_FR.pdf")
portfolio_pdf = str(UPLOADS_DIR / "Portfolio_Mohammed_HSINY.pdf")

test_subject = f"Stage PFE - Systèmes Embarqués, Robotique & Drones | {profile.name}"
test_body = f"""Bonjour,

Je suis élève-ingénieur en Génie Électrique & Contrôle Industriel à la FST Mohammedia, passionné par les systèmes embarqués critiques, la robotique et les drones autonomes.

Je recherche un stage PFE (Projet de Fin d'Études) de 6 mois à partir de Janvier 2027 au sein de vos équipes R&D.

Mes réalisations clés comprennent notamment :
- La conception d'un drone autonome pour l'inspection de lignes HT avec détection d'anomalies par IA (YOLO, ArduPilot, Python).
- Le développement d'une plateforme multi-robots communicants ADAS (ESP-NOW, FreeRTOS, asservissement PID).
- La conception mécanique et le contrôle-commande d'un bras manipulateur 6 DOF (STM32, SolidWorks, C++).
- Des immersions industrielles solides (Supervision SCADA M580 chez Groupe OCP, IoT & maintenance chez Marsa Maroc).

Vous trouverez ci-joint mon CV ainsi que mon Dossier Portfolio complet (PDF). Vous pouvez également tester mes prototypes et visualiser mes démonstrations interactives sur mon portfolio en ligne :
👉 {profile.portfolio_url}

Seriez-vous ouvert à un court échange de 10 à 15 minutes pour discuter de vos défis techniques et voir comment je pourrais y contribuer ?

Bien cordialement,
"""

print("[*] Envoi de l'email de test avec CV PDF, Portfolio PDF et Signature RoboThings...")
res = send_single_email(
    settings=smtp,
    recipient_email=profile.email,
    subject=test_subject,
    body_text=test_body,
    attachment_paths=[cv_fr, portfolio_pdf],
    profile=profile,
    language="fr"
)

print("[*] Résultat :", res.to_dict())
if res.success:
    print("\n[SUCCÈS] L'email de vérification a été envoyé directement à", profile.email)
else:
    print("\n[ERREUR]", res.message)
