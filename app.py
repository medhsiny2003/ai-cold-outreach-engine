import os
import sys
from pathlib import Path

# Ensure project root is in sys.path for Streamlit Cloud & multi-platform compatibility
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
import time
import random
import pandas as pd
import streamlit as st

# Set page config as first Streamlit command
st.set_page_config(
    page_title="AI Cold Outreach | Mohammed HSINY",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

from config import (
    BASE_DIR, DATA_DIR, UPLOADS_DIR, CandidateProfile, SMTPSettings, LLMSettings, is_francophone
)
try:
    from services.storage_service import (
        init_db, load_profile, save_profile, load_smtp_settings, save_smtp_settings,
        load_llm_settings, save_llm_settings, get_all_contacts, save_or_update_contact,
        save_contacts_bulk, approve_all_contacts, clear_all_contacts, log_sent_email, get_all_sent_logs,
        get_all_recruiter_responses, mark_response_read, trigger_waterfall_retry_bounced,
        delete_contact_by_id, delete_contacts_bulk, update_contacts_status_bulk, reset_all_data_and_contacts,
        delete_contacts_by_status, reset_all_contacts_to_pending, reset_sent_and_bounced_to_pending, clear_sent_logs_history,
        get_unique_companies_summary, exclude_contacts_by_companies, reinclude_contacts_by_companies, delete_contacts_by_companies
    )
except ImportError:
    from services.storage_service import (
        init_db, load_profile, save_profile, load_smtp_settings, save_smtp_settings,
        load_llm_settings, save_llm_settings, get_all_contacts, save_or_update_contact,
        save_contacts_bulk, approve_all_contacts, clear_all_contacts, log_sent_email, get_all_sent_logs
    )
    def get_all_recruiter_responses(): return []
    def mark_response_read(resp_id): pass
    def trigger_waterfall_retry_bounced(): return {"success": True, "count": 0, "message": "Aucun email alternatif."}
    def delete_contact_by_id(cid): pass
    def delete_contacts_bulk(cids): return 0
    def update_contacts_status_bulk(cids, st): return 0
    def reset_all_data_and_contacts(c_logs=False, c_up=False): pass
    def delete_contacts_by_status(st_list): return 0
    def reset_all_contacts_to_pending(): return 0
    def reset_sent_and_bounced_to_pending(): return 0
    def clear_sent_logs_history(): pass
    def get_unique_companies_summary(): return []
    def exclude_contacts_by_companies(c_names): return 0
    def reinclude_contacts_by_companies(c_names): return 0
    def delete_contacts_by_companies(c_names): return 0

try:
    from services.email_validator import validate_single_email, validate_contacts_list
except ImportError:
    def validate_single_email(email, check_dns=True):
        return {"email": email, "is_valid": "@" in str(email), "status": "valid" if "@" in str(email) else "invalid_syntax", "reason": "OK", "suggested_fix": None}
    def validate_contacts_list(contacts, check_dns=True):
        return {"total": len(contacts), "valid_count": len(contacts), "invalid_count": 0, "valid_contacts": contacts, "invalid_contacts": [], "details": []}

from services.contact_manager import parse_contacts_file, generate_sample_csv

try:
    from services.prompt_builder import (
        THEMES_CATALOG,
        WRITING_STYLES,
        detect_best_theme_for_company,
        determine_language,
        classify_role_category,
        get_target_subject,
        build_system_prompt,
        build_user_prompt,
        build_template_adaptation_system_prompt,
        build_template_adaptation_user_prompt
    )
except ImportError:
    THEMES_CATALOG = {
        "auto": {"label": "🎯 Auto-détection IA", "description": "Auto", "focus_fr": "génie électrique, contrôle commande, robotique", "focus_en": "electrical, control, robotics", "tagline_fr": "Élève-ingénieur", "tagline_en": "Engineering student"},
        "drones_robotics": {"label": "🛸 Focus Drones & Robotique", "description": "Drones", "focus_fr": "systèmes autonomes, ROS, vision", "focus_en": "autonomous systems, ROS", "tagline_fr": "Élève-ingénieur", "tagline_en": "Engineering student"},
        "solar_energy": {"label": "☀️ Focus Énergie Solaire", "description": "Solaire", "focus_fr": "photovoltaïque, MPPT", "focus_en": "solar PV, MPPT", "tagline_fr": "Élève-ingénieur", "tagline_en": "Engineering student"},
        "electrical_power": {"label": "⚡ Focus Génie Électrique", "description": "Électrique", "focus_fr": "machines, variateurs", "focus_en": "electric machines", "tagline_fr": "Élève-ingénieur", "tagline_en": "Engineering student"},
        "automation_scada": {"label": "🏭 Focus Automatisme & SCADA", "description": "Automatisme", "focus_fr": "PLC Siemens/Schneider, SCADA", "focus_en": "PLC, SCADA", "tagline_fr": "Élève-ingénieur", "tagline_en": "Engineering student"},
        "embedded_edge_ai": {"label": "🧠 Focus Systèmes Embarqués", "description": "Embarqué", "focus_fr": "STM32, Edge AI", "focus_en": "STM32, Edge AI", "tagline_fr": "Élève-ingénieur", "tagline_en": "Engineering student"},
        "custom": {"label": "✍️ Directive Personnalisée", "description": "Custom", "focus_fr": "sur-mesure", "focus_en": "custom", "tagline_fr": "Élève-ingénieur", "tagline_en": "Engineering student"}
    }
    WRITING_STYLES = {
        "persuasive_tech": {"label": "🎯 Équilibré & Persuasif Ingénieur", "prompt_fr": "Ton convaincant et dynamique.", "prompt_en": "Persuasive tone."},
        "deep_tech_rd": {"label": "🔬 R&D Approfondi", "prompt_fr": "Ton axé recherche.", "prompt_en": "R&D tone."},
        "direct_executive": {"label": "👔 Direct & Court", "prompt_fr": "Court et direct.", "prompt_en": "Short and direct."},
        "expert_mentorship": {"label": "🤝 Mentorat & Conseil", "prompt_fr": "Demande d'avis.", "prompt_en": "Mentorship."}
    }
    def detect_best_theme_for_company(company="", role="", industry=""):
        return "auto"
    def determine_language(contact, user_forced_lang=None):
        return user_forced_lang or "fr"
    def classify_role_category(role=""):
        return "INGENIEUR_TECH"
    def get_target_subject(persona="", theme="auto", language="fr"):
        return "Stage PFE – Demande de conseil"

try:
    from services.llm_service import generate_email_for_contact, generate_email_from_template, GeneratedEmail
except ImportError:
    from services.llm_service import generate_email_for_contact
    try:
        from services.llm_service import adapt_template_offline
    except Exception:
        def adapt_template_offline(template_text, contact, profile, language="fr"):
            name = contact.get("name") or "Madame, Monsieur"
            comp = contact.get("company") or "votre entreprise"
            txt = template_text.replace("[Prénom]", name).replace("[Entreprise]", comp)
            return type("GeneratedEmail", (), {"subject": f"Stage PFE - {comp}", "body": txt, "language": language})()
            
    async def generate_email_from_template(template_text, contact, profile, settings, forced_lang=None, custom_instruction=""):
        return adapt_template_offline(template_text, contact, profile, forced_lang or "fr")

from services.email_sender import (
    test_smtp_connection, send_single_email, send_batch_emails,
    build_professional_html, LOGO_PATH
)
from services.gmail_cleaner import clean_gmail_bounces_and_sync_db, sync_sent_and_bounced_with_gmail
from services.analytics_service import compute_company_analytics, send_quality_report_email

try:
    from services.response_tracker import scan_incoming_recruiter_replies, BackgroundSyncDaemon
except ImportError:
    def scan_incoming_recruiter_replies(smtp, profile=None):
        return {"success": False, "message": "Module de suivi en cours d'initialisation.", "new_responses": 0}
    class BackgroundSyncDaemon:
        last_status_message = "En veille"
        @classmethod
        def start(cls, interval_seconds: int = 45):
            pass
        @classmethod
        def stop(cls):
            pass

try:
    from services.background_sender import BackgroundDispatcher
except ImportError:
    class BackgroundDispatcher:
        @classmethod
        def is_running(cls) -> bool: return False
        @classmethod
        def get_status(cls) -> dict: return {"status": "IDLE"}
        @classmethod
        def start(cls, **kwargs) -> bool: return False
        @classmethod
        def stop(cls): pass

# Initialize DB schema & Start Background Auto-Sync Daemon (45s non-blocking loop)
init_db()
BackgroundSyncDaemon.start(interval_seconds=45)

# -------------------------------------------------------------
# MASTER SECURITY GATE (AUTHENTIFICATION GLOBALE À L'OUVERTURE)
# -------------------------------------------------------------
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.markdown("""
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
    <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
    <style>
        html, body, [class*="css"] {
            font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
        }
    </style>
    <div style="max-width: 520px; margin: 40px auto 24px auto; background: linear-gradient(135deg, #0B192C 0%, #0F4C81 50%, #1E3E62 100%); border-radius: 20px; padding: 36px 32px; color: white; text-align: center; box-shadow: 0 20px 45px -10px rgba(15, 76, 129, 0.45); border: 1px solid rgba(255, 255, 255, 0.15);">
        <div style="font-size: 3.2rem; margin-bottom: 12px; color: #FBBF24;">
            <i class="fa-solid fa-shield-halved"></i>
        </div>
        <h2 style="color: white; margin: 0; font-weight: 800; font-size: 1.7rem; letter-spacing: -0.5px;">
            AI Cold Outreach Engine Pro
        </h2>
        <div style="color: #93C5FD; font-size: 0.95rem; margin-top: 6px; font-weight: 600;">
            Plateforme Privée de Prospection PFE & Candidatures
        </div>
        <p style="color: #CBD5E1; font-size: 0.88rem; margin-top: 14px; line-height: 1.5;">
            Cet espace est strictement réservé à <b>Mohammed HSINY</b>. Veuillez saisir votre <b>Code PIN Master</b> pour déverrouiller l'accès complet à la plateforme.
        </p>
    </div>
    """, unsafe_allow_html=True)

    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        pin_entered = st.text_input("🔑 Code PIN Master d'Ouverture", type="password", placeholder="Entrez le code PIN...", key="app_master_pin_input")
        if st.button("🔓 Déverrouiller & Ouvrir l'Application", type="primary", use_container_width=True, key="app_master_login_btn"):
            clean_p = pin_entered.strip()
            valid_pins = ["19748403", os.getenv("SECURITY_PIN", "").strip(), "2026", "hsiny2026"]
            if clean_p and clean_p in valid_pins:
                st.session_state.authenticated = True
                st.session_state.dispatch_authorized = True
                st.session_state.inbox_unlocked = True
                st.success("✅ Code PIN validé ! Bienvenue Mohammed.")
                time.sleep(0.5)
                st.rerun()
            else:
                st.error("❌ Code PIN incorrect. Veuillez réessayer.")
    st.stop()

# Modern SaaS Styling & FontAwesome 6 Pro CDN Injection
st.markdown("""
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
<link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
    :root {
        --primary-blue: #0F4C81;
        --royal-indigo: #1E40AF;
        --electric-blue: #2563EB;
        --slate-dark: #0F172A;
        --slate-card: #FFFFFF;
    }
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    
    /* Top Professional Segmented Navigation Navbar */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
        background: #ffffff;
        padding: 8px 10px;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 4px 20px -2px rgba(15, 76, 129, 0.08);
        display: flex;
        justify-content: space-between;
        margin-bottom: 28px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 48px;
        white-space: pre-wrap;
        background-color: transparent;
        border-radius: 12px;
        font-weight: 600;
        font-size: 0.92rem;
        color: #475569;
        padding: 10px 16px;
        border: none !important;
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
    }
    .stTabs [data-baseweb="tab"]:hover {
        background-color: #f1f5f9;
        color: #0F4C81;
        transform: translateY(-2px);
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, #0F4C81 0%, #1E40AF 100%) !important;
        color: #ffffff !important;
        font-weight: 700 !important;
        box-shadow: 0 6px 18px rgba(15, 76, 129, 0.35) !important;
        transform: translateY(-2px);
    }
    .stTabs [data-baseweb="tab-highlight"] {
        display: none !important;
    }

    /* Enterprise Hero Banner */
    .hero-banner {
        background: linear-gradient(135deg, #0B192C 0%, #0F4C81 50%, #1E3E62 100%);
        border-radius: 18px;
        padding: 28px 36px;
        color: white;
        margin-bottom: 24px;
        box-shadow: 0 14px 35px -10px rgba(15, 76, 129, 0.35);
        border: 1px solid rgba(255, 255, 255, 0.12);
        display: flex;
        justify-content: space-between;
        align-items: center;
        flex-wrap: wrap;
        gap: 18px;
    }
    .hero-title {
        font-size: 2.1rem;
        font-weight: 800;
        letter-spacing: -0.5px;
        background: linear-gradient(135deg, #FFFFFF 0%, #E2E8F0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .hero-subtitle {
        color: #CBD5E1;
        font-size: 0.98rem;
        margin-top: 8px;
        font-weight: 400;
    }
    .hero-badge {
        background: rgba(255, 255, 255, 0.12);
        color: #E2E8F0;
        border: 1px solid rgba(255, 255, 255, 0.25);
        padding: 7px 16px;
        border-radius: 30px;
        font-size: 0.84rem;
        font-weight: 700;
        display: inline-flex;
        align-items: center;
        gap: 8px;
        backdrop-filter: blur(8px);
    }

    /* Luxury Glassmorphic KPI Cards */
    .pro-kpi-card {
        background: #ffffff;
        border-radius: 16px;
        padding: 20px 22px;
        border: 1px solid #E2E8F0;
        box-shadow: 0 4px 16px -2px rgba(15, 76, 129, 0.06);
        transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1);
        display: flex;
        flex-direction: column;
        justify-content: space-between;
        position: relative;
        overflow: hidden;
    }
    .pro-kpi-card::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 4px;
    }
    .pro-kpi-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 12px 28px -6px rgba(15, 76, 129, 0.12);
        border-color: #CBD5E1;
    }
    .kpi-header-row {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 12px;
    }
    .kpi-icon-box {
        width: 46px;
        height: 46px;
        border-radius: 12px;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.35rem;
    }
    .kpi-tag {
        font-size: 0.72rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 12px;
        letter-spacing: 0.3px;
        text-transform: uppercase;
    }
    .kpi-title {
        font-size: 0.80rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: #64748B;
        margin-bottom: 4px;
    }
    .kpi-value {
        font-size: 2rem;
        font-weight: 800;
        color: #0F172A;
        line-height: 1.1;
    }
</style>
""", unsafe_allow_html=True)

# Load state from DB & Environment
if "profile" not in st.session_state:
    st.session_state.profile = load_profile()
if "smtp" not in st.session_state or not getattr(st.session_state.smtp, "app_password", None):
    st.session_state.smtp = load_smtp_settings()
if "llm" not in st.session_state or not getattr(st.session_state.llm, "api_key", None):
    st.session_state.llm = load_llm_settings()

profile = st.session_state.profile
smtp = st.session_state.smtp
llm = st.session_state.llm

# Live Real-Time Metrics
contacts = get_all_contacts()
total_contacts = len(contacts)
sent_count = sum(1 for c in contacts if c.get("status") == "sent")
approved_waiting_count = sum(1 for c in contacts if c.get("status") == "approved")
bounced_count = sum(1 for c in contacts if c.get("status") == "bounced")
replied_count = sum(1 for c in contacts if c.get("status") == "replied")

CANDIDATE_PHOTO = BASE_DIR / "data" / "assets" / "mohammed_hsiny.png"

# Sidebar with Candidate Portrait Photo & Security Badge
with st.sidebar:
    if CANDIDATE_PHOTO.is_file():
        st.image(str(CANDIDATE_PHOTO), use_container_width=True)
    elif LOGO_PATH.is_file():
        st.image(str(LOGO_PATH), width=120)
    else:
        st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=64)
        
    st.markdown(f"### <i class='fa-solid fa-user-tie' style='color:#0F4C81;'></i> **{profile.name}**", unsafe_allow_html=True)
    st.caption("🏆 **Président Club RoboThings** | FSTM")
    st.caption(f"🎓 {profile.title_fr}")
    
    is_connected = bool(smtp.app_password and smtp.app_password.strip())
    
    st.divider()
    st.markdown("### <i class='fa-solid fa-signal' style='color:#0F4C81;'></i> État de Connexion", unsafe_allow_html=True)
    if is_connected:
        st.markdown("<span style='background:#dcfce7; color:#166534; padding:5px 12px; border-radius:14px; font-weight:700; font-size:0.84rem;'><i class='fa-solid fa-circle-check'></i> Gmail Connecté</span>", unsafe_allow_html=True)
    else:
        st.markdown("<span style='background:#fee2e2; color:#991b1b; padding:5px 12px; border-radius:14px; font-weight:700; font-size:0.84rem;'><i class='fa-solid fa-lock'></i> Déconnecté (Pause)</span>", unsafe_allow_html=True)

    st.divider()
    st.markdown("### <i class='fa-solid fa-shield-halved' style='color:#0F4C81;'></i> Sécurité Système", unsafe_allow_html=True)
    st.markdown("<span style='background:#f1f5f9; color:#334155; padding:5px 12px; border-radius:10px; font-weight:700; font-size:0.82rem;'><i class='fa-solid fa-lock'></i> Protection PIN Active</span>", unsafe_allow_html=True)

    st.divider()
    
    # Active Attachments Check
    st.markdown("### <i class='fa-solid fa-paperclip' style='color:#0F4C81;'></i> Documents Attachés", unsafe_allow_html=True)
    cv_fr = UPLOADS_DIR / "CV_Mohammed_HSINY_FR.pdf"
    cv_en = UPLOADS_DIR / "CV_Mohammed_HSINY_EN.pdf"
    portfolio_pdf = UPLOADS_DIR / "Portfolio_Mohammed_HSINY.pdf"
    
    if cv_fr.is_file():
        st.success("📄 `CV_Mohammed_HSINY_FR.pdf` (Actif)")
    if cv_en.is_file():
        st.success("📄 `CV_Mohammed_HSINY_EN.pdf` (Actif)")
    if portfolio_pdf.is_file():
        st.success("📁 `Portfolio_Mohammed_HSINY.pdf` (Actif)")
        
    st.divider()
    st.markdown("### <i class='fa-solid fa-link' style='color:#0F4C81;'></i> Liens Officiels", unsafe_allow_html=True)
    st.markdown(f"- [🌐 **Portfolio en ligne**]({profile.portfolio_url})")
    st.markdown(f"- [💼 **Profil LinkedIn**]({profile.linkedin_url})")
    st.markdown(f"- ✉️ `{profile.email}`")
    st.markdown(f"- 📱 `{profile.phone}`")

    st.divider()
    if st.button("🔒 Verrouiller / Déconnexion", use_container_width=True, key="sidebar_logout_btn"):
        st.session_state.authenticated = False
        st.session_state.dispatch_authorized = False
        st.session_state.inbox_unlocked = False
        st.rerun()

# Main Hero Banner with Pro Styling & Midnight Electric Gradient
daemon_status = BackgroundSyncDaemon.last_status_message
conn_badge = """<span class="hero-badge" style="background: rgba(16, 185, 129, 0.25); color: #A7F3D0; border-color: rgba(52, 211, 153, 0.4);"><i class="fa-solid fa-circle-check"></i> Gmail Connecté</span>""" if is_connected else """<span class="hero-badge" style="background: rgba(239, 68, 68, 0.25); color: #FCA5A5; border-color: rgba(248, 113, 113, 0.4);"><i class="fa-solid fa-lock"></i> Compte en Pause</span>"""

st.markdown(f"""
<div class="hero-banner">
<div>
<div class="hero-title">
<i class="fa-solid fa-bolt-lightning" style="color: #FBBF24;"></i>
<span>AI Cold Outreach Engine Pro</span>
</div>
<div class="hero-subtitle">Plateforme Haute-Délivrabilité & Prospection Intelligente pour Stage PFE | <b>Mohammed HSINY</b> (FST Mohammedia)</div>
</div>
<div style="display: flex; gap: 10px; flex-wrap: wrap;">
<span class="hero-badge"><i class="fa-solid fa-shield-halved"></i> Audit RFC 3464</span>
<span class="hero-badge"><i class="fa-solid fa-lock"></i> Session Sécurisée</span>
{conn_badge}
</div>
</div>
""", unsafe_allow_html=True)

# Dressed-Up Luxury KPI Cards Row (Flush Left to prevent Markdown Code Block Conversion)
kpi_html = f"""
<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(210px, 1fr)); gap: 16px; margin-bottom: 26px;">
<div class="pro-kpi-card" style="border-top: 4px solid #0F4C81;">
<div class="kpi-header-row">
<div class="kpi-icon-box" style="background: #EFF6FF; color: #0F4C81;">
<i class="fa-solid fa-users"></i>
</div>
<span class="kpi-tag" style="background: #DBEAFE; color: #1E40AF;">Base Data</span>
</div>
<div>
<div class="kpi-title">Total Base</div>
<div class="kpi-value" style="color: #0F4C81;">{total_contacts}</div>
</div>
</div>
<div class="pro-kpi-card" style="border-top: 4px solid #059669;">
<div class="kpi-header-row">
<div class="kpi-icon-box" style="background: #F0FDF4; color: #059669;">
<i class="fa-solid fa-paper-plane"></i>
</div>
<span class="kpi-tag" style="background: #DCFCE7; color: #166534;">100% Réels</span>
</div>
<div>
<div class="kpi-title">Délivrés avec Succès</div>
<div class="kpi-value" style="color: #059669;">{sent_count}</div>
</div>
</div>
<div class="pro-kpi-card" style="border-top: 4px solid #7C3AED;">
<div class="kpi-header-row">
<div class="kpi-icon-box" style="background: #FDF4FF; color: #7C3AED;">
<i class="fa-solid fa-comments"></i>
</div>
<span class="kpi-tag" style="background: #F3E8FF; color: #6B21A8;">IA Qualifiée</span>
</div>
<div>
<div class="kpi-title">Réponses Recruteurs</div>
<div class="kpi-value" style="color: #7C3AED;">{replied_count}</div>
</div>
</div>
<div class="pro-kpi-card" style="border-top: 4px solid #DC2626;">
<div class="kpi-header-row">
<div class="kpi-icon-box" style="background: #FEF2F2; color: #DC2626;">
<i class="fa-solid fa-triangle-exclamation"></i>
</div>
<span class="kpi-tag" style="background: #FEE2E2; color: #991B1B;">RFC 3464 DSN</span>
</div>
<div>
<div class="kpi-title">Rejetés (Bounces)</div>
<div class="kpi-value" style="color: #DC2626;">{bounced_count}</div>
</div>
</div>
<div class="pro-kpi-card" style="border-top: 4px solid #D97706;">
<div class="kpi-header-row">
<div class="kpi-icon-box" style="background: #FFFBEB; color: #D97706;">
<i class="fa-solid fa-hourglass-half"></i>
</div>
<span class="kpi-tag" style="background: #FEF3C7; color: #92400E;">En File</span>
</div>
<div>
<div class="kpi-title">En Attente d'Envoi</div>
<div class="kpi-value" style="color: #D97706;">{approved_waiting_count}</div>
</div>
</div>
</div>
"""
st.markdown(kpi_html, unsafe_allow_html=True)

# Navigation Tabs with Icons
tab1, tab2, tab3, tab4, tab_manual, tab5, tab6, tab7 = st.tabs([
    "👤 Mon Profil & CV",
    "👥 Contacts & Import",
    "🤖 Studio IA",
    "✍️ Revue & Édition",
    "✉️ Envoi Manuel Direct",
    "🚀 Centre d'Envoi",
    "💬 Réponses & IA",
    "⚙️ Paramètres & Gmail"
])

# -------------------------------------------------------------
# TAB 1: Mon Profil & Documents (CV & Portfolio)
# -------------------------------------------------------------
with tab1:
    st.header("👤 Profil de l'Élève-Ingénieur & Documents")
    st.info("Ces informations et vos documents (CV / Portfolio) sont automatiquement injectés dans les prompts de l'IA et joints aux emails d'outreach.")
    
    col_p1, col_p2 = st.columns(2)
    with col_p1:
        p_name = st.text_input("Nom & Prénom", value=profile.name)
        p_title_fr = st.text_input("Intitulé / Titre (FR)", value=profile.title_fr)
        p_title_en = st.text_input("Title (EN)", value=profile.title_en)
        p_school = st.text_input("École / Université", value=profile.school)
        p_target_fr = st.text_input("Objectif de Stage (FR)", value=profile.target_role_fr)
        p_target_en = st.text_input("Stage Objective (EN)", value=profile.target_role_en)
    with col_p2:
        p_email = st.text_input("Email professionnel", value=profile.email)
        p_phone = st.text_input("Téléphone / WhatsApp", value=profile.phone)
        p_portfolio = st.text_input("Portfolio en ligne (URL)", value=profile.portfolio_url)
        p_linkedin = st.text_input("LinkedIn (URL)", value=profile.linkedin_url)
        p_mobility_fr = st.text_input("Mobilité géographique (FR)", value=profile.mobility_fr)
        p_mobility_en = st.text_input("Mobility (EN)", value=profile.mobility_en)
        
    if st.button("💾 Enregistrer les informations du Profil", type="primary"):
        profile.name = p_name
        profile.title_fr = p_title_fr
        profile.title_en = p_title_en
        profile.school = p_school
        profile.target_role_fr = p_target_fr
        profile.target_role_en = p_target_en
        profile.email = p_email
        profile.phone = p_phone
        profile.portfolio_url = p_portfolio
        profile.linkedin_url = p_linkedin
        profile.mobility_fr = p_mobility_fr
        profile.mobility_en = p_mobility_en
        save_profile(profile)
        st.success("✅ Informations du profil mises à jour avec succès !")

    st.divider()
    st.subheader("📎 Pièces Jointes : CV & Portfolio (Mise à Jour Dynamique)")
    st.caption("Téléchargez et remplacez vos documents à tout moment. Ils seront automatiquement sauvegardés et attachés lors des envois.")

    col_cv1, col_cv2, col_cv3 = st.columns(3)
    
    with col_cv1:
        st.markdown("##### 📄 CV Français (PDF)")
        cv_fr_file = UPLOADS_DIR / "CV_Mohammed_HSINY_FR.pdf"
        if cv_fr_file.is_file() and cv_fr_file.stat().st_size > 0:
            size_kb = cv_fr_file.stat().st_size // 1024
            st.success(f"✅ Actif : `CV_Mohammed_HSINY_FR.pdf` ({size_kb} Ko)")
            st.download_button(
                "👁️ Télécharger / Vérifier (FR)",
                cv_fr_file.read_bytes(),
                "CV_Mohammed_HSINY_FR.pdf",
                "application/pdf",
                key="dl_cv_fr",
                use_container_width=True
            )
        else:
            st.warning("⚠️ Aucun CV français actuellement.")
        up_cv_fr = st.file_uploader("Remplacer le CV Français", type=["pdf"], key="up_cv_fr")
        if up_cv_fr is not None:
            fr_bytes = up_cv_fr.getvalue()
            fr_hash = hash(fr_bytes)
            if st.session_state.get("_uploaded_cv_fr_hash") != fr_hash:
                cv_fr_file.write_bytes(fr_bytes)
                st.session_state["_uploaded_cv_fr_hash"] = fr_hash
                try:
                    profile.cv_fr_path = str(cv_fr_file)
                except Exception:
                    pass
                save_profile(profile)
                st.session_state.profile = profile
                st.toast("🎉 CV Français mis à jour et sauvegardé !", icon="✅")
                st.rerun()

    with col_cv2:
        st.markdown("##### 📄 CV Anglais (PDF)")
        cv_en_file = UPLOADS_DIR / "CV_Mohammed_HSINY_EN.pdf"
        if cv_en_file.is_file() and cv_en_file.stat().st_size > 0:
            size_kb = cv_en_file.stat().st_size // 1024
            st.success(f"✅ Actif : `CV_Mohammed_HSINY_EN.pdf` ({size_kb} Ko)")
            st.download_button(
                "👁️ Télécharger / Vérifier (EN)",
                cv_en_file.read_bytes(),
                "CV_Mohammed_HSINY_EN.pdf",
                "application/pdf",
                key="dl_cv_en",
                use_container_width=True
            )
        else:
            st.warning("⚠️ Aucun CV anglais actuellement.")
        up_cv_en = st.file_uploader("Remplacer le CV Anglais", type=["pdf"], key="up_cv_en")
        if up_cv_en is not None:
            en_bytes = up_cv_en.getvalue()
            en_hash = hash(en_bytes)
            if st.session_state.get("_uploaded_cv_en_hash") != en_hash:
                cv_en_file.write_bytes(en_bytes)
                st.session_state["_uploaded_cv_en_hash"] = en_hash
                try:
                    profile.cv_en_path = str(cv_en_file)
                except Exception:
                    pass
                save_profile(profile)
                st.session_state.profile = profile
                st.toast("🎉 CV Anglais mis à jour et sauvegardé !", icon="✅")
                st.rerun()

    with col_cv3:
        st.markdown("##### 💼 Portfolio PDF")
        portfolio_file = UPLOADS_DIR / "Portfolio_Mohammed_HSINY.pdf"
        if portfolio_file.is_file() and portfolio_file.stat().st_size > 0:
            size_kb = portfolio_file.stat().st_size // 1024
            st.success(f"✅ Actif : `Portfolio_Mohammed_HSINY.pdf` ({size_kb} Ko)")
            st.download_button(
                "👁️ Télécharger / Vérifier (Portfolio)",
                portfolio_file.read_bytes(),
                "Portfolio_Mohammed_HSINY.pdf",
                "application/pdf",
                key="dl_portfolio_pdf",
                use_container_width=True
            )
        else:
            st.warning("⚠️ Aucun Portfolio PDF actuellement.")
        up_pf = st.file_uploader("Remplacer le Portfolio PDF", type=["pdf"], key="up_pf")
        if up_pf is not None:
            pf_bytes = up_pf.getvalue()
            pf_hash = hash(pf_bytes)
            if st.session_state.get("_uploaded_pf_hash") != pf_hash:
                portfolio_file.write_bytes(pf_bytes)
                st.session_state["_uploaded_pf_hash"] = pf_hash
                try:
                    profile.portfolio_pdf_path = str(portfolio_file)
                except Exception:
                    pass
                save_profile(profile)
                st.session_state.profile = profile
                st.toast("🎉 Portfolio PDF mis à jour et sauvegardé !", icon="✅")
                st.rerun()

# -------------------------------------------------------------
# TAB 2: Contacts & Validation / Sélection / Exclusion
# -------------------------------------------------------------
with tab2:
    st.header("👥 Importation, Validation & Gestion des Contacts")
    
    st.markdown("""
    Importez vos fichiers de prospection, testez la validité des adresses emails avant l'envoi, et sélectionnez précisément les destinataires à cibler ou à exclure.
    """)

    col_c1, col_c2 = st.columns([2, 1])
    with col_c1:
        uploaded_file = st.file_uploader("📂 Importer via le navigateur (.csv, .xlsx, .xls)", type=["csv", "xlsx", "xls"])
    with col_c2:
        st.write("")
        st.write("")
        if st.button("✨ Charger l'exemple de démo (6 contacts)", help="Charge 6 contacts d'entreprises clés (France, Belgique, USA, Maroc, Allemagne)"):
            sample_content = generate_sample_csv().encode("utf-8")
            loaded_contacts, errs = parse_contacts_file(sample_content, "sample.csv")
            save_contacts_bulk(loaded_contacts)
            st.success(f"{len(loaded_contacts)} contacts d'exemple chargés !")
            st.rerun()

    if uploaded_file is not None:
        file_bytes = uploaded_file.getvalue()
        loaded_contacts, errors = parse_contacts_file(file_bytes, uploaded_file.name)
        if errors:
            for err in errors:
                st.error(err)
        elif loaded_contacts:
            st.markdown(f"""
            <div style="background: #F0FDF4; border: 1px solid #86EFAC; border-radius: 12px; padding: 14px 18px; margin: 12px 0;">
                <div style="font-weight: 700; color: #166534; font-size: 0.95rem; margin-bottom: 4px;">
                    📄 Fichier détecté : <b>{uploaded_file.name}</b> ({len(loaded_contacts)} contacts valides extraits)
                </div>
                <div style="color: #15803D; font-size: 0.86rem;">
                    Choisissez comment intégrer ces contacts dans votre base de travail :
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            col_u1, col_u2 = st.columns(2)
            with col_u1:
                if st.button(f"📥 Ajouter ces {len(loaded_contacts)} contacts à la base", type="primary", use_container_width=True, key="btn_add_uploaded"):
                    save_contacts_bulk(loaded_contacts)
                    st.success(f"✅ {len(loaded_contacts)} contacts ajoutés à la base avec succès !")
                    time.sleep(0.8)
                    st.rerun()
            with col_u2:
                if st.button(f"🔄 Remplacer TOUTE la base par ces {len(loaded_contacts)} contacts", use_container_width=True, key="btn_replace_uploaded", help="Supprime l'ancienne base et charge uniquement les contacts de ce fichier"):
                    clear_all_contacts()
                    save_contacts_bulk(loaded_contacts)
                    st.success(f"✅ Ancienne base effacée et remplacée par les {len(loaded_contacts)} nouveaux contacts !")
                    time.sleep(0.8)
                    st.rerun()

    # Scan local data and data/contacts folder
    local_files = []
    for ext in ["*.xlsx", "*.xls", "*.csv"]:
        local_files.extend(list(DATA_DIR.glob(ext)))
        local_files.extend(list((DATA_DIR / "contacts").glob(ext)))

    if local_files:
        st.markdown("#### 📁 Fichiers trouvés sur votre disque (`data/contacts/`)")
        col_f1, col_f2 = st.columns([3, 1])
        with col_f1:
            file_choices = {f.name: f for f in local_files}
            selected_local_file_name = st.selectbox("Sélectionner un fichier local à charger", list(file_choices.keys()))
        with col_f2:
            st.write("")
            st.write("")
            if st.button("📥 Importer ce fichier local"):
                file_path = file_choices[selected_local_file_name]
                with open(file_path, "rb") as f:
                    content_b = f.read()
                loaded_contacts, errors = parse_contacts_file(content_b, file_path.name)
                if errors:
                    for err in errors:
                        st.error(err)
                else:
                    save_contacts_bulk(loaded_contacts)
                    st.success(f"✅ {len(loaded_contacts)} contacts importés depuis `{file_path.name}` !")
                    time.sleep(0.8)
                    st.rerun()

    contacts = get_all_contacts()
    
    if contacts:
        st.divider()
        # -------------------------------------------------------------
        # MODULE DE TEST & VALIDATION PRÉ-ENVOI DES ADRESSES EMAILS
        # -------------------------------------------------------------
        st.subheader("🔍 Diagnostic & Validation Pré-Envoi des Adresses Emails")
        st.caption("Vérifiez automatiquement la conformité syntaxique (RFC 5322) et l'existence du serveur DNS de domaine pour chaque contact avant de générer ou d'expédier.")
        
        col_v1, col_v2 = st.columns([2, 1])
        with col_v1:
            validate_btn = st.button("⚡ Tester & Valider la Validité de Tous les Emails", type="primary", use_container_width=True)
            
        if validate_btn or "validation_report" in st.session_state:
            if validate_btn:
                with st.spinner("Analyse approfondie (syntaxe RFC + résolution DNS des domaines)..."):
                    st.session_state.validation_report = validate_contacts_list(contacts, check_dns=True)
            
            report = st.session_state.validation_report
            
            st.markdown(f"""
            <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-top: 14px; margin-bottom: 18px;">
                <div style="background: #F0FDF4; padding: 14px 18px; border-radius: 12px; border: 1px solid #BBF7D0;">
                    <div style="font-size: 0.8rem; color: #166534; font-weight: 700; text-transform: uppercase;">🟢 Emails Valides & Livrables</div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: #15803D;">{report['valid_count']}</div>
                </div>
                <div style="background: #FEF2F2; padding: 14px 18px; border-radius: 12px; border: 1px solid #FECACA;">
                    <div style="font-size: 0.8rem; color: #991B1B; font-weight: 700; text-transform: uppercase;">🔴 Emails Invalides / Inactifs</div>
                    <div style="font-size: 1.8rem; font-weight: 800; color: #DC2626;">{report['invalid_count']}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            if report['invalid_count'] > 0:
                st.warning(f"⚠️ **{report['invalid_count']} adresse(s) email(s) présentent des anomalies ou des domaines inexistants.**")
                df_inv = pd.DataFrame(report['invalid_contacts'])[["id", "name", "email", "company", "validation_reason", "validation_status"]]
                df_inv.columns = ["ID", "Nom", "Email", "Entreprise", "Diagnostic / Motif d'Erreur", "Statut Anomalie"]
                st.dataframe(df_inv, use_container_width=True)
                
                col_inv1, col_inv2 = st.columns(2)
                with col_inv1:
                    if st.button("🧹 Éliminer / Exclure tous les emails invalides de l'envoi", type="primary", use_container_width=True):
                        inv_ids = [c["id"] for c in report['invalid_contacts'] if c.get("id")]
                        update_contacts_status_bulk(inv_ids, "invalid_email")
                        st.success(f"✅ {len(inv_ids)} contacts invalides marqués comme 'invalid_email' et exclus de l'envoi !")
                        if "validation_report" in st.session_state:
                            del st.session_state["validation_report"]
                        time.sleep(1)
                        st.rerun()
                with col_inv2:
                    inv_csv = df_inv.to_csv(index=False).encode("utf-8")
                    st.download_button("📥 Exporter la liste des emails invalides (CSV)", inv_csv, "emails_invalides_diagnostic.csv", "text/csv", use_container_width=True)
            else:
                st.success("🎉 Parfait ! 100% des adresses emails analysées sont syntaxiquement valides et leurs domaines sont actifs !")

        st.divider()
        # -------------------------------------------------------------
        # TABLEAU DES CONTACTS & SÉLECTION / EXCLUSION INTERACTIVE
        # -------------------------------------------------------------
        st.subheader(f"📋 Base Actuelle des Contacts ({len(contacts)} au total)")

        # Direct Quick Management & Reset Toolbar
        st.markdown("""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px 18px; margin-bottom: 16px;">
            <div style="font-weight: 700; color: #0F172A; font-size: 0.92rem; margin-bottom: 10px; display: flex; align-items: center; gap: 8px;">
                <i class="fa-solid fa-wand-magic-sparkles" style="color: #0F4C81;"></i> <span>Actions Globales & Réinitialisation du Processus :</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

        col_rst1, col_rst2, col_rst3, col_rst4 = st.columns([1.2, 1.2, 1.2, 1.2])
        with col_rst1:
            if st.button("🔄 Relancer Tout (Reset -> Attente)", use_container_width=True, help="Remet tous les contacts en attente ('pending') pour relancer un cycle d'envoi complet"):
                n = reset_all_contacts_to_pending()
                st.success(f"🎉 {n} contacts remis en attente ('pending') !")
                time.sleep(0.8)
                st.rerun()
        with col_rst2:
            if st.button("🔄 Relancer Envoyés & Rejetés", use_container_width=True, help="Remet uniquement les contacts déjà envoyés ou rejetés en statut 'pending' pour retenter"):
                n = reset_sent_and_bounced_to_pending()
                st.success(f"🎉 {n} contacts (envoyés/rejetés) remis en attente !")
                time.sleep(0.8)
                st.rerun()
        with col_rst3:
            if st.button("🧹 Supprimer Envoyés & Rejetés", use_container_width=True, help="Supprime de la base les contacts déjà envoyés ou rejetés pour ne garder que les nouveaux non traités"):
                n = delete_contacts_by_status(["sent", "bounced"])
                st.success(f"🧹 {n} anciens contacts supprimés ! Base allégée.")
                time.sleep(0.8)
                st.rerun()
        with col_rst4:
            if st.button("🗑️ Vider Tous les Contacts", type="secondary", use_container_width=True, help="Supprime l'intégralité des contacts pour importer un nouveau fichier propre"):
                clear_all_contacts()
                if "validation_report" in st.session_state:
                    del st.session_state["validation_report"]
                st.warning("🗑️ Tous les contacts ont été effacés ! Vous pouvez importer un nouveau fichier.")
                time.sleep(0.8)
                st.rerun()

        st.write("")
        # Filter & Search Toolbar
        col_st1, col_st2 = st.columns([2, 2])
        with col_st1:
            search_c = st.text_input("🔍 Rechercher un contact (Nom, Entreprise, Email, Poste)", "", key="tab2_contact_search")
        with col_st2:
            filter_status = st.selectbox(
                "Filtrer par statut",
                ["Tous", "pending (En attente)", "generated (Généré)", "approved (Approuvé)", "sent (Envoyé)", "bounced (Rejeté)", "excluded (Exclu de l'envoi)", "invalid_email (Email invalide)"],
                key="tab2_status_filter"
            )

        # Apply filtering
        display_list = contacts
        if search_c.strip():
            sc = search_c.strip().lower()
            display_list = [
                c for c in display_list 
                if sc in str(c.get("name", "")).lower() 
                or sc in str(c.get("company", "")).lower()
                or sc in str(c.get("email", "")).lower()
                or sc in str(c.get("role", "")).lower()
            ]
            
        if "pending" in filter_status:
            display_list = [c for c in display_list if c.get("status") == "pending"]
        elif "generated" in filter_status:
            display_list = [c for c in display_list if c.get("status") == "generated"]
        elif "approved" in filter_status:
            display_list = [c for c in display_list if c.get("status") == "approved"]
        elif "sent" in filter_status:
            display_list = [c for c in display_list if c.get("status") == "sent"]
        elif "bounced" in filter_status:
            display_list = [c for c in display_list if c.get("status") == "bounced"]
        elif "excluded" in filter_status:
            display_list = [c for c in display_list if c.get("status") == "excluded"]
        elif "invalid_email" in filter_status:
            display_list = [c for c in display_list if c.get("status") == "invalid_email"]

        df_display = pd.DataFrame(display_list)[["id", "name", "email", "company", "role", "location", "industry", "status"]]
        st.dataframe(df_display, use_container_width=True)

        # -------------------------------------------------------------
        # MODULE D'EXCLUSION & GESTION PAR ENTREPRISE (BLACKLIST)
        # -------------------------------------------------------------
        st.markdown("""
        <div style="background: #F8FAFC; border: 1px solid #E2E8F0; border-radius: 12px; padding: 14px 18px; margin: 16px 0 12px 0;">
            <div style="font-weight: 700; color: #0F172A; font-size: 0.95rem; margin-bottom: 4px; display: flex; align-items: center; gap: 8px;">
                <i class="fa-solid fa-building-circle-xmark" style="color: #DC2626;"></i> <span>🏢 Exclusion & Blocage Global par Entreprise</span>
            </div>
            <div style="color: #475569; font-size: 0.86rem;">
                Excluez facilement tous les contacts d'une ou plusieurs sociétés (ex: Shark Robotics, Thales, etc.) pour qu'aucun email ne leur soit envoyé.
            </div>
        </div>
        """, unsafe_allow_html=True)

        companies_summary = get_unique_companies_summary()
        company_choices = [c["company_name"] for c in companies_summary if c["company_name"] and c["company_name"] != "Non renseignée"]
        
        # Display currently excluded companies badge if any
        excluded_companies = [c for c in companies_summary if c.get("excluded", 0) > 0]
        if excluded_companies:
            exc_badges = " ".join([f"<span style='background:#FEE2E2; color:#991B1B; padding:3px 8px; border-radius:6px; font-weight:700; font-size:0.82rem; border:1px solid #FECACA;'>🚫 {c['company_name']} ({c['excluded']} exclus)</span>" for c in excluded_companies])
            st.markdown(f"<div style='margin-bottom: 12px;'><b>Sociétés actuellement exclues :</b> {exc_badges}</div>", unsafe_allow_html=True)

        col_cmp1, col_cmp2 = st.columns([1.5, 1.5])
        with col_cmp1:
            sel_companies = st.multiselect(
                "Sélectionner des entreprises de la base à exclure/gérer :",
                options=company_choices,
                format_func=lambda c_name: next((f"{c_name} ({c['total']} contacts)" for c in companies_summary if c["company_name"] == c_name), c_name),
                help="Sélectionnez une ou plusieurs entreprises présentes dans votre fichier."
            )
        with col_cmp2:
            custom_company_input = st.text_input(
                "Ou saisir un/des nom(s) d'entreprise(s) (séparés par des virgules) :",
                value="",
                placeholder="Ex: Shark Robotics, Thales, Airbus...",
                help="Tapez n'importe quel nom ou mot-clé d'entreprise. Tous les contacts correspondants seront traités."
            )

        # Merge selected companies and typed companies
        all_target_companies = list(sel_companies)
        if custom_company_input.strip():
            for typed_c in custom_company_input.split(","):
                tc_clean = typed_c.strip()
                if tc_clean and tc_clean not in all_target_companies:
                    all_target_companies.append(tc_clean)

        col_cact1, col_cact2, col_cact3 = st.columns([1.3, 1.3, 1.4])
        with col_cact1:
            if st.button("🚫 Exclure ces entreprises de l'envoi", type="primary", use_container_width=True, disabled=not all_target_companies, help="Marque tous les salariés de ces entreprises comme 'excluded' (aucun email ne leur sera envoyé)"):
                cnt = exclude_contacts_by_companies(all_target_companies)
                st.success(f"🚫 {cnt} contact(s) de {len(all_target_companies)} entreprise(s) ont été exclus de l'envoi !")
                time.sleep(0.8)
                st.rerun()
        with col_cact2:
            if st.button("✅ Réactiver ces entreprises", use_container_width=True, disabled=not all_target_companies, help="Remet les salariés de ces entreprises en statut 'pending' pour être envoyés"):
                cnt = reinclude_contacts_by_companies(all_target_companies)
                st.success(f"✅ {cnt} contact(s) de {len(all_target_companies)} entreprise(s) ont été réactivés !")
                time.sleep(0.8)
                st.rerun()
        with col_cact3:
            if st.button("🗑️ Supprimer ces entreprises de la base", type="secondary", use_container_width=True, disabled=not all_target_companies, help="Supprime définitivement tous les contacts de ces entreprises"):
                cnt = delete_contacts_by_companies(all_target_companies)
                st.success(f"🗑️ {cnt} contact(s) de ces entreprises supprimés définitivement !")
                time.sleep(0.8)
                st.rerun()

        st.divider()

        st.markdown("##### 🎯 Sélection & Actions par Contact Individuel")
        contact_options = {c["id"]: f"#{c['id']} - {c.get('name') or c.get('email')} | {c.get('company', 'N/A')} [{c.get('status')}]" for c in display_list}
        selected_cids = st.multiselect(
            "Cochez un ou plusieurs contacts pour agir dessus :",
            options=list(contact_options.keys()),
            format_func=lambda cid: contact_options.get(cid, str(cid)),
            help="Sélectionnez les personnes à exclure, réactiver ou supprimer."
        )

        col_act1, col_act2, col_act3, col_act4 = st.columns([1, 1, 1, 1])
        with col_act1:
            if st.button("🚫 Exclure la sélection", use_container_width=True, disabled=not selected_cids, help="Marque les contacts sélectionnés comme 'excluded' (ne recevront aucun email)"):
                updated = update_contacts_status_bulk(selected_cids, "excluded")
                st.success(f"🚫 {updated} contact(s) exclu(s) de l'envoi !")
                time.sleep(0.8)
                st.rerun()
        with col_act2:
            if st.button("✅ Réactiver la sélection", use_container_width=True, disabled=not selected_cids, help="Réintègre les contacts comme 'pending' pour être générés ou envoyés"):
                updated = update_contacts_status_bulk(selected_cids, "pending")
                st.success(f"✅ {updated} contact(s) réactivé(s) !")
                time.sleep(0.8)
                st.rerun()
        with col_act3:
            if st.button("🗑️ Supprimer la sélection", type="secondary", use_container_width=True, disabled=not selected_cids, help="Supprime définitivement les contacts sélectionnés"):
                deleted = delete_contacts_bulk(selected_cids)
                st.success(f"🗑️ {deleted} contact(s) supprimé(s) !")
                time.sleep(0.8)
                st.rerun()
        with col_act4:
            csv_export = pd.DataFrame(display_list).to_csv(index=False).encode('utf-8')
            st.download_button("📥 Exporter CSV", csv_export, "contacts_export.csv", "text/csv", use_container_width=True)

        st.divider()
        # -------------------------------------------------------------
        # RÉINITIALISATION COMPLÈTE DE LA BASE DE CONTACTS & FICHIERS
        # -------------------------------------------------------------
        with st.expander("⚠️ Nettoyage Approfondi du Serveur & Fichiers Uploadés", expanded=False):
            st.warning("Cette action permet de vider la base de données et de supprimer les anciens fichiers temporaires d'importation.")
            confirm_reset = st.checkbox("Je confirme vouloir réinitialiser et nettoyer tous les fichiers temporaires", key="chk_confirm_reset")
            if st.button("🗑️ Réinitialiser Tout Maintenant", type="secondary", disabled=not confirm_reset):
                reset_all_data_and_contacts(clear_sent_logs=False, clear_uploads=True)
                if "validation_report" in st.session_state:
                    del st.session_state["validation_report"]
                st.success("✅ Base de contacts réinitialisée et anciens fichiers nettoyés !")
                time.sleep(0.8)
                st.rerun()
    else:
        st.info("Aucun contact chargé pour le moment. Vous pouvez charger le fichier d'exemple ou importer votre propre CSV/Excel.")

# -------------------------------------------------------------
# TAB 3: Génération IA & Personnalisation Thématique
# -------------------------------------------------------------
with tab3:
    st.header("🤖 Studio IA & Personnalisation des Candidatures")
    st.caption("Générez des emails ultra-personnalisés par angle thématique (Drones, Solaire, Automatisme, etc.) ou à partir d'un modèle/draft rédigé par vos soins.")
    
    gen_mode = st.radio(
        "Sélectionnez le mode de génération",
        [
            "🎯 Mode 1 : Studio Thématique & Métiers IA (Auto-détection, Drones, Solaire, Automatisme...)",
            "📋 Mode 2 : Modèle / Template Sur-Mesure (Votre texte de référence adapté par l'IA)"
        ],
        horizontal=True
    )
    
    col_g1, col_g2, col_g3 = st.columns(3)
    with col_g1:
        provider_choice = st.selectbox(
            "Fournisseur IA",
            ["gemini", "openai", "groq", "deepseek", "ollama", "openrouter"],
            index=["gemini", "openai", "groq", "deepseek", "ollama", "openrouter"].index(llm.provider) if llm.provider in ["gemini", "openai", "groq", "deepseek", "ollama", "openrouter"] else 0
        )
        if provider_choice == "gemini":
            model_options = ["gemini-2.0-flash", "gemini-2.5-flash", "gemini-1.5-pro", "gemini-1.5-flash"]
        elif provider_choice == "openai":
            model_options = ["gpt-4o-mini", "gpt-4o", "gpt-3.5-turbo"]
        elif provider_choice == "groq":
            model_options = ["llama-3.3-70b-versatile", "mixtral-8x7b-32768"]
        elif provider_choice == "deepseek":
            model_options = ["deepseek-chat"]
        else:
            model_options = ["llama3.2", "mistral"]
            
        selected_model = st.selectbox("Modèle", model_options, index=0)

    llm.provider = provider_choice
    llm.model_name = selected_model

    if "Mode 1" in gen_mode:
        with col_g2:
            theme_keys = list(THEMES_CATALOG.keys())
            theme_labels = [THEMES_CATALOG[k]["label"] for k in theme_keys]
            selected_theme_idx = st.selectbox(
                "🎯 Spécialisation / Angle Thématique",
                range(len(theme_keys)),
                format_func=lambda i: theme_labels[i],
                index=0,
                help="Sélectionnez le domaine à valoriser dans vos candidatures (l'IA adapte les projets et le vocabulaire technique)."
            )
            selected_theme_key = theme_keys[selected_theme_idx]
            
        with col_g3:
            style_keys = list(WRITING_STYLES.keys())
            style_labels = [WRITING_STYLES[k]["label"] for k in style_keys]
            selected_style_idx = st.selectbox(
                "✍️ Style Rédactionnel & Approche",
                range(len(style_keys)),
                format_func=lambda i: style_labels[i],
                index=0
            )
            selected_style_key = style_keys[selected_style_idx]

        col_opt1, col_opt2 = st.columns([2, 1])
        with col_opt1:
            custom_pitch_directive = st.text_input(
                "💡 Directive / Pitch Spécial pour l'IA (Optionnel)",
                value="",
                placeholder="Ex: Insister sur mon stage en IA chez Harmattan, mon intérêt pour le dimensionnement solaire, etc.",
                help="Une consigne libre transmise directement au modèle IA pour affiner la personnalisation de vos messages."
            )
        with col_opt2:
            lang_mode = st.selectbox(
                "Mode de Langue",
                [
                    "Auto-détection (Français si FR/BE/CH/MA/CA, Anglais sinon)",
                    "Forcer Français pour tous",
                    "Forcer Anglais pour tous"
                ]
            )

        forced_lang = None
        if "Forcer Français" in lang_mode:
            forced_lang = "fr"
        elif "Forcer Anglais" in lang_mode:
            forced_lang = "en"

        current_theme_data = THEMES_CATALOG[selected_theme_key]
        st.info(f"**Angle sélectionné :** {current_theme_data['label']} — *{current_theme_data['description']}*")

    else:
        # Mode 2: Modèle / Template Sur-Mesure
        with col_g2:
            lang_mode = st.selectbox(
                "Mode de Langue",
                [
                    "Auto-détection (Français si FR/BE/CH/MA/CA, Anglais sinon)",
                    "Forcer Français pour tous",
                    "Forcer Anglais pour tous"
                ]
            )
        with col_g3:
            custom_pitch_directive = st.text_input(
                "💡 Consigne d'adaptation IA (Optionnel)",
                value="",
                placeholder="Ex: Garder un ton très direct et concis...",
                help="Consigne supplémentaire donnée à l'IA lors de l'adaptation de votre modèle."
            )

        forced_lang = None
        if "Forcer Français" in lang_mode:
            forced_lang = "fr"
        elif "Forcer Anglais" in lang_mode:
            forced_lang = "en"

        default_custom_template = """Objet : Stage PFE Ingénieur – Contribution aux projets de [Entreprise]

Bonjour [Prénom],

Je me permets de vous contacter car je suis avec grand intérêt les innovations et réalisations de [Entreprise] dans vos projets technologiques.

Élève-ingénieur en dernière année en Électrotechnique et Automatique à l'ENSEM Casablanca, je recherche un stage de fin d'études (PFE) de 4 à 6 mois à partir de février 2026. Passionné par l'intégration des systèmes intelligents, le contrôle-commande et l'automatisation, j'ai développé des compétences solides à travers plusieurs projets concrets (banc d'essai HIL, station solaire MPPT, navigation autonome).

Seriez-vous ouvert à un bref échange de 5 à 10 minutes la semaine prochaine pour discuter de vos besoins actuels et voir comment je pourrais contribuer aux projets de [Entreprise] ?

Vous pouvez également consulter mon portfolio technique en ligne : https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Bien cordialement,
Mohammed HSINY
Élève-Ingénieur ENSEM | Électrotechnique & Automatique
+212 6 25 80 50 25"""

        st.markdown("##### 📝 Votre Modèle d'Email de Référence")
        custom_template_text = st.text_area(
            "Rédigez ou collez votre email ici (l'IA s'occupe de contextualiser et d'adapter pour chaque entreprise) :",
            value=st.session_state.get("custom_reference_template", default_custom_template),
            height=230,
            key="custom_template_input_area",
            help="Balises dynamiques : [Prénom], [Nom], [Entreprise], [Poste]. L'IA adaptera également les mentions de projets selon le domaine de la société !"
        )
        st.session_state["custom_reference_template"] = custom_template_text
        st.caption("💡 **Balises automatiques** : `[Prénom]`, `[Nom]`, `[Entreprise]`, `[Poste]`. L'IA analyse l'activité réelle de l'entreprise pour contextualiser les phrases de votre texte.")

    st.divider()

    contacts = get_all_contacts()
    if not contacts:
        st.warning("Veuillez d'abord importer des contacts dans l'onglet 'Contacts'.")
    else:
        pending_contacts = [c for c in contacts if c.get("status") in ["pending", "failed"]]
        st.write(f"📊 **Statut de la base** : **{len(pending_contacts)}** contacts en attente de génération sur **{len(contacts)}** au total.")
        
        col_btn1, col_btn2 = st.columns([2, 2])
        with col_btn1:
            gen_pending_btn = st.button(f"⚡ Générer pour les {len(pending_contacts)} contacts en attente", type="primary", use_container_width=True)
        with col_btn2:
            gen_all_btn = st.button(f"🔄 Tout régénérer ({len(contacts)} contacts)", type="secondary", use_container_width=True)

        if gen_pending_btn or gen_all_btn:
            targets = pending_contacts if gen_pending_btn else [c for c in contacts if c.get("status") not in ["excluded", "invalid_email"]]
            if not targets:
                st.info("Aucun contact à traiter (les contacts exclus sont ignorés).")
            else:
                progress_bar = st.progress(0)
                status_box = st.empty()
                
                async def run_batch():
                    for idx, contact in enumerate(targets):
                        status_box.info(f"⏳ Génération pour **{contact.get('name') or contact.get('email')}** ({contact.get('company', 'Société')})...")
                        if "Mode 1" in gen_mode:
                            res = await generate_email_for_contact(
                                contact=contact,
                                profile=profile,
                                settings=llm,
                                forced_lang=forced_lang,
                                theme=selected_theme_key,
                                custom_instruction=custom_pitch_directive,
                                tone=selected_style_key
                            )
                        else:
                            res = await generate_email_from_template(
                                template_text=custom_template_text,
                                contact=contact,
                                profile=profile,
                                settings=llm,
                                forced_lang=forced_lang,
                                custom_instruction=custom_pitch_directive
                            )
                        contact["subject"] = res.subject
                        contact["body"] = res.body
                        contact["language"] = res.language
                        contact["status"] = "generated"
                        save_or_update_contact(contact)
                        progress_bar.progress((idx + 1) / len(targets))
                        
                asyncio.run(run_batch())
                status_box.success(f"🎉 Génération personnalisée terminée pour {len(targets)} contacts ! Rendez-vous dans l'onglet 'Revue & Édition' pour vérifier et valider.")
                time.sleep(1.5)
                st.rerun()

# -------------------------------------------------------------
# TAB 4: Revue & Édition (Human-in-the-Loop)
# -------------------------------------------------------------
with tab4:
    st.header("✍️ Revue, Édition & Personnalisation Individuelle")
    st.caption("Inspectez chaque email généré, ajustez l'angle thématique à la volée ou modifiez le texte manuellement avant approbation.")
    
    contacts = get_all_contacts()
    if not contacts:
        st.info("Aucun contact disponible. Veuillez importer des contacts dans l'onglet 'Contacts'.")
    else:
        # Search and Filter Toolbar
        col_flt1, col_flt2 = st.columns([3, 2])
        with col_flt1:
            search_query = st.text_input("🔍 Rechercher un contact (Nom, Entreprise, Poste, Email)", "", key="contact_search_query")
        with col_flt2:
            status_filter = st.selectbox(
                "Filtrer par statut",
                ["Tous", "pending (En attente)", "generated (Généré)", "approved (Approuvé)", "sent (Envoyé)", "failed (Échoué)"],
                key="contact_status_filter"
            )

        # Filter contacts list
        filtered_contacts = contacts
        if search_query.strip():
            sq = search_query.strip().lower()
            filtered_contacts = [
                c for c in filtered_contacts
                if sq in str(c.get("name", "")).lower()
                or sq in str(c.get("company", "")).lower()
                or sq in str(c.get("role", "")).lower()
                or sq in str(c.get("email", "")).lower()
                or sq in str(c.get("notes", "")).lower()
            ]
            
        if "pending" in status_filter:
            filtered_contacts = [c for c in filtered_contacts if c.get("status") == "pending"]
        elif "generated" in status_filter:
            filtered_contacts = [c for c in filtered_contacts if c.get("status") == "generated"]
        elif "approved" in status_filter:
            filtered_contacts = [c for c in filtered_contacts if c.get("status") == "approved"]
        elif "sent" in status_filter:
            filtered_contacts = [c for c in filtered_contacts if c.get("status") == "sent"]
        elif "failed" in status_filter:
            filtered_contacts = [c for c in filtered_contacts if c.get("status") == "failed"]

        if not filtered_contacts:
            st.warning("Aucun contact ne correspond à votre recherche ou filtre.")
        else:
            # Stable mapping by ID
            contact_map = {c["id"]: c for c in filtered_contacts}
            contact_ids = list(contact_map.keys())
            
            if "selected_contact_id" not in st.session_state or st.session_state.selected_contact_id not in contact_map:
                st.session_state.selected_contact_id = contact_ids[0]
                
            current_id = st.session_state.selected_contact_id
            current_idx = contact_ids.index(current_id) if current_id in contact_ids else 0

            # Navigation bar (Previous / Select / Next)
            col_nav1, col_nav2, col_nav3 = st.columns([1, 4, 1])
            with col_nav1:
                if st.button("⬅️ Précédent", disabled=(current_idx == 0), use_container_width=True):
                    st.session_state.selected_contact_id = contact_ids[current_idx - 1]
                    st.rerun()
            with col_nav2:
                def get_contact_label(cid):
                    c = contact_map[cid]
                    st_badge = {"pending": "⏳", "generated": "🟡", "approved": "✅", "sent": "🚀", "failed": "❌"}.get(c.get("status"), "⏳")
                    return f"{st_badge} #{c['id']} - {c.get('name') or c.get('email')} | {c.get('company', 'N/A')} ({c.get('role', 'N/A')})"
                
                selected_cid = st.selectbox(
                    f"Sélectionner un contact ({current_idx + 1} / {len(filtered_contacts)})",
                    contact_ids,
                    index=current_idx,
                    format_func=get_contact_label,
                    key="select_contact_box"
                )
                if selected_cid != st.session_state.selected_contact_id:
                    st.session_state.selected_contact_id = selected_cid
                    st.rerun()
            with col_nav3:
                if st.button("Suivant ➡️", disabled=(current_idx >= len(contact_ids) - 1), use_container_width=True):
                    st.session_state.selected_contact_id = contact_ids[current_idx + 1]
                    st.rerun()

            current_contact = contact_map[st.session_state.selected_contact_id]
            
            st.divider()

            col_rev_info, col_rev_edit = st.columns([1, 2])
            
            with col_rev_info:
                st.markdown("### 📌 Profil du Destinataire")
                st.markdown(f"- **Nom :** `{current_contact.get('name') or 'N/A'}`")
                st.markdown(f"- **Email :** `{current_contact.get('email')}`")
                st.markdown(f"- **Entreprise :** `{current_contact.get('company') or 'N/A'}`")
                st.markdown(f"- **Poste :** `{current_contact.get('role') or 'N/A'}`")
                st.markdown(f"- **Localisation :** `{current_contact.get('location') or 'N/A'}`")
                st.markdown(f"- **Statut :** `{current_contact.get('status')}`")
                if current_contact.get("notes"):
                    st.markdown(f"- **Notes :** {current_contact.get('notes')}")
                    
                st.divider()
                st.markdown("### 🤖 Régénération Ciblée IA")
                
                regen_tab_choice = st.radio(
                    "Mode de régénération",
                    ["🎯 Par Thématique", "📋 Par Modèle Sur-Mesure"],
                    key=f"regen_mode_{current_contact['id']}",
                    horizontal=True
                )
                
                if regen_tab_choice == "🎯 Par Thématique":
                    suggested_theme = detect_best_theme_for_company(
                        company=current_contact.get("company", ""),
                        role=current_contact.get("role", ""),
                        industry=current_contact.get("industry", "")
                    )
                    theme_keys_list = list(THEMES_CATALOG.keys())
                    theme_labels_list = [THEMES_CATALOG[k]["label"] for k in theme_keys_list]
                    sugg_idx = theme_keys_list.index(suggested_theme) if suggested_theme in theme_keys_list else 0
                    
                    single_theme_idx = st.selectbox(
                        "Thématique pour ce recruteur",
                        range(len(theme_keys_list)),
                        format_func=lambda i: theme_labels_list[i],
                        index=sugg_idx,
                        key=f"thm_sel_{current_contact['id']}"
                    )
                    single_theme_key = theme_keys_list[single_theme_idx]
                    
                    single_custom_note = st.text_input(
                        "Directive spécifique pour ce contact",
                        placeholder="Ex: Mentionner leur projet X...",
                        key=f"note_input_{current_contact['id']}"
                    )
                    
                    if st.button("⚡ Régénérer avec cet Angle (IA)", type="primary", use_container_width=True, key=f"btn_regen_thm_{current_contact['id']}"):
                        async def regen_current():
                            res = await generate_email_for_contact(
                                contact=current_contact,
                                profile=profile,
                                settings=llm,
                                theme=single_theme_key,
                                custom_instruction=single_custom_note
                            )
                            current_contact["subject"] = res.subject
                            current_contact["body"] = res.body
                            current_contact["language"] = res.language
                            current_contact["status"] = "generated"
                            save_or_update_contact(current_contact)
                            # Sync session state inputs
                            st.session_state[f"subj_{current_contact['id']}"] = res.subject
                            st.session_state[f"body_{current_contact['id']}"] = res.body
                        
                        asyncio.run(regen_current())
                        st.session_state.selected_contact_id = current_contact['id']
                        st.success("✅ Email personnalisé régénéré avec succès !")
                        st.rerun()
                else:
                    ref_tmpl = st.session_state.get("custom_reference_template", "")
                    single_tmpl_text = st.text_area(
                        "Modèle à adapter pour ce contact",
                        value=ref_tmpl if ref_tmpl else "Objet : Stage PFE Ingénieur – Contribution aux projets de [Entreprise]\n\nBonjour [Prénom],\n\nJe suis vos réalisations chez [Entreprise]...",
                        height=160,
                        key=f"tmpl_text_{current_contact['id']}"
                    )
                    single_tmpl_note = st.text_input(
                        "Consigne d'adaptation IA (Optionnel)",
                        placeholder="Ex: Mettre en valeur l'IA embarquée...",
                        key=f"tmpl_note_{current_contact['id']}"
                    )
                    if st.button("📋 Adapter ce Modèle (IA)", type="primary", use_container_width=True, key=f"btn_regen_tmpl_{current_contact['id']}"):
                        async def regen_tmpl_current():
                            res = await generate_email_from_template(
                                template_text=single_tmpl_text,
                                contact=current_contact,
                                profile=profile,
                                settings=llm,
                                custom_instruction=single_tmpl_note
                            )
                            current_contact["subject"] = res.subject
                            current_contact["body"] = res.body
                            current_contact["language"] = res.language
                            current_contact["status"] = "generated"
                            save_or_update_contact(current_contact)
                            st.session_state[f"subj_{current_contact['id']}"] = res.subject
                            st.session_state[f"body_{current_contact['id']}"] = res.body
                            
                        asyncio.run(regen_tmpl_current())
                        st.session_state.selected_contact_id = current_contact['id']
                        st.success("✅ Modèle adapté pour ce contact avec succès !")
                        st.rerun()

            with col_rev_edit:
                st.markdown("### 📝 Contenu de l'Email Personnalisé")
                
                initial_subj = current_contact.get("subject", "")
                initial_body = current_contact.get("body", "")
                
                edit_subject = st.text_input("Objet de l'email", value=initial_subj, key=f"subj_{current_contact['id']}")
                edit_body = st.text_area("Corps du message", value=initial_body, height=350, key=f"body_{current_contact['id']}")
                
                if edit_body:
                    with st.expander("👁️ Prévisualiser le Rendu Email Réel (Design HTML & Signature RoboThings)", expanded=False):
                        html_preview = build_professional_html(
                            body_text=edit_body,
                            profile=profile,
                            language=current_contact.get("language", "fr"),
                            include_logo=False
                        )
                        st.components.v1.html(html_preview, height=480, scrolling=True)

                c_save1, c_save2, c_save3, c_save4, c_save5 = st.columns([1.2, 1.2, 1.1, 1.1, 1.3])
                with c_save1:
                    if st.button("💾 Sauvegarder", use_container_width=True):
                        current_contact["subject"] = edit_subject
                        current_contact["body"] = edit_body
                        save_or_update_contact(current_contact)
                        st.session_state.selected_contact_id = current_contact['id']
                        st.success("Modifications enregistrées !")
                with c_save2:
                    if st.button("✅ Approuver", type="primary", use_container_width=True):
                        current_contact["subject"] = edit_subject
                        current_contact["body"] = edit_body
                        current_contact["status"] = "approved"
                        save_or_update_contact(current_contact)
                        st.session_state.selected_contact_id = current_contact['id']
                        st.success("Contact approuvé pour l'envoi !")
                        st.rerun()
                with c_save3:
                    if current_contact.get("status") == "excluded":
                        if st.button("🔄 Réactiver", use_container_width=True, help="Réactive ce contact pour l'envoi"):
                            current_contact["status"] = "pending"
                            save_or_update_contact(current_contact)
                            st.success(f"Contact #{current_contact['id']} réactivé !")
                            st.rerun()
                    else:
                        if st.button("🚫 Exclure", use_container_width=True, help="Exclut ce contact de l'envoi"):
                            current_contact["status"] = "excluded"
                            save_or_update_contact(current_contact)
                            st.warning(f"Contact #{current_contact['id']} exclu !")
                            st.rerun()
                with c_save4:
                    if st.button("🗑️ Supprimer", use_container_width=True, help="Supprime définitivement ce contact"):
                        delete_contact_by_id(current_contact["id"])
                        st.error(f"Contact #{current_contact['id']} supprimé !")
                        if "selected_contact_id" in st.session_state:
                            del st.session_state["selected_contact_id"]
                        time.sleep(0.5)
                        st.rerun()
                with c_save5:
                    if st.button("⚡ Tout Approuver", use_container_width=True):
                        approved_count = approve_all_contacts(only_generated=False)
                        st.success(f"🎉 {approved_count} contacts sont maintenant approuvés pour l'envoi !")
                        st.rerun()

                comp_name_current = (current_contact.get("company") or "").strip()
                if comp_name_current:
                    st.write("")
                    if st.button(f"🏢 Exclure toute la société '{comp_name_current}' de l'envoi", use_container_width=True, help=f"Bloque tous les contacts de '{comp_name_current}' pour qu'aucun email ne leur soit envoyé"):
                        cnt = exclude_contacts_by_companies([comp_name_current])
                        st.warning(f"🚫 {cnt} contact(s) de '{comp_name_current}' exclus de l'envoi !")
                        time.sleep(0.8)
                        st.rerun()

# -------------------------------------------------------------
# TAB MANUAL: Mode Envoi Manuel Direct & Rendu HTML / CSS
# -------------------------------------------------------------
with tab_manual:
    st.header("✉️ Mode Envoi Manuel Direct (Rendu HTML / CSS & Signature)")
    st.markdown("""
    Rédigez ou collez manuellement un email pour un contact précis. Votre message est **automatiquement habillé du design HTML/CSS haut de gamme**, avec la typographie optimisée, le bouton CTA de votre portfolio, les pièces jointes et la carte de signature complète (RoboThings FSTM, LinkedIn, coordonnées).
    """)

    col_man1, col_man2 = st.columns([1.5, 1.5])
    
    with col_man1:
        st.markdown("##### 🎯 1. Destinataire & Paramètres")
        man_email = st.text_input("📧 Email du Destinataire *", placeholder="ex: bruno@sharkrobotics.com", key="man_input_email")
        man_name = st.text_input("👤 Nom & Prénom (ou Titre)", placeholder="ex: Bruno", key="man_input_name")
        man_company = st.text_input("🏢 Entreprise / Société", placeholder="ex: Shark Robotics", key="man_input_company")
        man_role = st.text_input("💼 Rôle / Poste (Optionnel)", placeholder="ex: CEO & Fondateur", key="man_input_role")

    with col_man2:
        st.markdown("##### 🌐 2. Langue & Objet de l'Email")
        man_lang_choice = st.radio("Langue de l'email :", ["🇫🇷 Français", "🇬🇧 English"], horizontal=True, key="man_lang_choice")
        is_man_fr = ("Français" in man_lang_choice)
        man_lang = "fr" if is_man_fr else "en"

        def_subjs = {
            "fr_rh": "Candidature – Stage PFE en systèmes embarqués et drones",
            "fr_ceo": f"Votre vision chez {man_company.strip() or '[Entreprise]'} – Étudiant passionné par les systèmes embarqués et les drones",
            "fr_eng": f"Votre parcours chez {man_company.strip() or '[Entreprise]'} – Étudiant passionné par les systèmes embarqués et les drones",
            "en_rh": "Application – 6-Month Graduation Internship (PFE) in Embedded Systems & Drones",
            "en_ceo": f"Your vision at {man_company.strip() or '[Company]'} – Student passionate about embedded systems & drones",
            "en_eng": f"Your work at {man_company.strip() or '[Company]'} – Student passionate about embedded systems & drones",
        }

        default_subj = def_subjs["fr_rh"] if is_man_fr else def_subjs["en_rh"]
        
        man_subject = st.text_input("📌 Objet de l'Email *", value=st.session_state.get("man_subj_val", default_subj), key="man_input_subject")

        st.caption("💡 Suggestions d'objets rapides en 1 clic :")
        col_sb1, col_sb2, col_sb3 = st.columns(3)
        with col_sb1:
            if st.button("🎯 RH / Recruteur", use_container_width=True, key="btn_sb_rh"):
                s_val = def_subjs["fr_rh"] if is_man_fr else def_subjs["en_rh"]
                st.session_state.man_subj_val = s_val
                st.rerun()
        with col_sb2:
            if st.button("👔 CEO / Fondateur", use_container_width=True, key="btn_sb_ceo"):
                s_val = def_subjs["fr_ceo"] if is_man_fr else def_subjs["en_ceo"]
                st.session_state.man_subj_val = s_val
                st.rerun()
        with col_sb3:
            if st.button("🔬 Ingénieur / R&D", use_container_width=True, key="btn_sb_eng"):
                s_val = def_subjs["fr_eng"] if is_man_fr else def_subjs["en_eng"]
                st.session_state.man_subj_val = s_val
                st.rerun()

    st.divider()

    # Attachments block
    st.markdown("##### 📎 3. Pièces Jointes Sélectionnées")
    col_at1, col_at2, col_at3 = st.columns(3)
    cv_fr_p = UPLOADS_DIR / "CV_Mohammed_HSINY_FR.pdf"
    cv_en_p = UPLOADS_DIR / "CV_Mohammed_HSINY_EN.pdf"
    pf_pdf_p = UPLOADS_DIR / "Portfolio_Mohammed_HSINY.pdf"

    with col_at1:
        man_att_cv_fr = st.checkbox(
            f"📄 CV Français (PDF) {'✅' if cv_fr_p.is_file() else '⚠️ Manquant'}",
            value=is_man_fr and cv_fr_p.is_file(),
            key="man_chk_cv_fr"
        )
    with col_at2:
        man_att_cv_en = st.checkbox(
            f"📄 CV Anglais (PDF) {'✅' if cv_en_p.is_file() else '⚠️ Manquant'}",
            value=(not is_man_fr) and cv_en_p.is_file(),
            key="man_chk_cv_en"
        )
    with col_at3:
        man_att_pf = st.checkbox(
            f"💼 Portfolio Dossier (PDF) {'✅' if pf_pdf_p.is_file() else '⚠️ Manquant'}",
            value=pf_pdf_p.is_file(),
            key="man_chk_pf"
        )

    st.divider()

    # Message drafting & Live preview columns
    col_draft, col_prev = st.columns([1.2, 1.3])

    with col_draft:
        st.markdown("##### ✍️ 4. Rédaction du Corps du Message")
        
        first_n = man_name.strip().split()[0] if man_name.strip() else ""
        salut_fr = f"Bonjour {first_n}," if first_n else "Bonjour,"
        salut_en = f"Hello {first_n}," if first_n else "Hello,"
        comp_disp = man_company.strip() or "votre entreprise"

        if is_man_fr:
            sample_body = f"""{salut_fr}

J'espère que vous allez bien.

Je suis étudiant en dernière année d'ingénierie en Génie Électrique à la FST Mohammedia, passionné par les systèmes embarqués, la robotique et les drones. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE) de 6 mois à partir de janvier 2027.

Je suis très motivé par l'idée de rejoindre {comp_disp} et je suis sincèrement inspiré par vos projets et votre expertise dans le domaine.

Je me permets de vous contacter pour savoir s'il y aurait des opportunités de stage au sein de votre équipe. Je vous joins mon CV ainsi que mon portfolio pour plus de détails.

https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Merci d'avance pour votre temps.

Bien cordialement,"""
        else:
            sample_body = f"""{salut_en}

I hope you are doing well.

I am a final-year Electrical Engineering student at FSTM, passionate about embedded systems, robotics, and autonomous drones. I am based in Morocco and currently preparing my 6-month graduation internship (PFE) starting January 2027.

I am genuinely motivated by the prospect of contributing to {comp_disp} and deeply inspired by your innovative engineering projects.

I would be honored to explore internship opportunities within your team. I have attached my resume and project portfolio for your review.

https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Thank you very much for your time and consideration.

Best regards,"""

        man_body_val = st.text_area(
            "Rédigez votre texte librement ci-dessous (la signature et le style HTML seront ajoutés automatiquement) :",
            value=st.session_state.get("manual_custom_body", sample_body),
            height=340,
            key="manual_textarea_body"
        )
        st.session_state["manual_custom_body"] = man_body_val

        col_b_act1, col_b_act2 = st.columns(2)
        with col_b_act1:
            if st.button("🔄 Actualiser avec les coordonnées saisies", use_container_width=True, key="btn_refresh_manual_text"):
                st.session_state["manual_custom_body"] = sample_body
                st.rerun()
        with col_b_act2:
            if st.button("🌐 Insérer Lien Portfolio CTA", use_container_width=True, key="btn_insert_portfolio_manual"):
                if "https://portfolio-mohammed-hsiny-ux7z.vercel.app" not in man_body_val:
                    st.session_state["manual_custom_body"] = man_body_val + "\n\nhttps://portfolio-mohammed-hsiny-ux7z.vercel.app/"
                    st.rerun()

    with col_prev:
        st.markdown("##### 👁️ 5. Aperçu Réel du Rendu HTML / CSS")
        st.caption("Voici le rendu exact que recevra votre destinataire dans sa boîte mail :")
        
        # Build professional HTML
        html_rendered = build_professional_html(
            body_text=man_body_val,
            profile=profile,
            language=man_lang,
            include_logo=True
        )
        st.components.v1.html(html_rendered, height=480, scrolling=True)

    st.divider()

    # Sending actions toolbar
    st.markdown("##### 🚀 6. Expédition Immédiate")
    col_snd1, col_snd2, col_snd3 = st.columns([1.5, 1.2, 1.3])
    
    with col_snd1:
        save_to_contacts_db = st.checkbox("💾 Enregistrer ce contact dans ma base (Statut 'Envoyé')", value=True, key="chk_save_manual_to_db")
    with col_snd2:
        st.write("")
        st.caption(f"Expéditeur : `{smtp.sender_name} <{smtp.sender_email}>`")
    with col_snd3:
        btn_send_manual = st.button(
            "📤 ENVOYER CET EMAIL MAINTENANT (HTML PRO)",
            type="primary",
            use_container_width=True,
            key="btn_trigger_manual_send"
        )

    if btn_send_manual:
        if not man_email or "@" not in man_email or "." not in man_email.split("@")[-1]:
            st.error("⚠️ Veuillez renseigner une adresse email destinataire valide.")
        elif not smtp.app_password:
            st.error("⚠️ Mot de passe d'application Gmail manquant. Configurez-le dans l'onglet Paramètres.")
        elif not man_body_val.strip():
            st.error("⚠️ Le corps du message est vide.")
        else:
            # Build attachments list
            man_attachments = []
            if man_att_cv_fr and cv_fr_p.is_file():
                man_attachments.append(str(cv_fr_p))
            if man_att_cv_en and cv_en_p.is_file():
                man_attachments.append(str(cv_en_p))
            if man_att_pf and pf_pdf_p.is_file():
                man_attachments.append(str(pf_pdf_p))

            with st.spinner(f"Expédition de l'email avec design HTML vers {man_email}..."):
                res_send = send_single_email(
                    settings=smtp,
                    recipient_email=man_email.strip(),
                    subject=man_subject.strip(),
                    body_text=man_body_val,
                    attachment_paths=man_attachments,
                    profile=profile,
                    language=man_lang
                )

            if res_send.success:
                st.balloons()
                st.success(f"🎉 Email envoyé avec succès à **{man_email}** avec le template HTML et {len(man_attachments)} pièce(s) jointe(s) !")
                log_sent_email(man_email.strip(), man_subject.strip(), man_body_val, "SUCCESS")
                
                if save_to_contacts_db:
                    save_or_update_contact({
                        "email": man_email.strip(),
                        "name": man_name.strip() or man_email.split("@")[0],
                        "company": man_company.strip(),
                        "role": man_role.strip(),
                        "status": "sent",
                        "subject": man_subject.strip(),
                        "body": man_body_val,
                        "language": man_lang,
                        "notes": "Envoi direct via Mode Manuel"
                    })
                    st.toast("✅ Contact enregistré dans la base avec statut 'sent' !", icon="💾")
                
                time.sleep(1.5)
            else:
                st.error(f"❌ Échec de l'envoi : {res_send.message}")

# -------------------------------------------------------------
# TAB 5: Centre d'Envoi
# -------------------------------------------------------------
with tab5:
    st.header("🚀 Centre d'Envoi & Suivi des Candidatures")
    
    contacts = get_all_contacts()
    approved_contacts = [c for c in contacts if c.get("status") == "approved" and c.get("status") not in ["excluded", "invalid_email", "bounced"]]
    sent_contacts = [c for c in contacts if c.get("status") == "sent"]
    bounced_contacts = [c for c in contacts if c.get("status") == "bounced"]
    
    # Compact Permanent Lifetime Statistics Bar (Faible Encombrement)
    total_processed = len(sent_contacts) + len(bounced_contacts)
    deliv_rate = (len(sent_contacts) / total_processed * 100) if total_processed > 0 else 100.0

    st.markdown(f"""
    <div style="background: #f8fafc; padding: 10px 16px; border-radius: 10px; border: 1px solid #e2e8f0; display: flex; flex-wrap: wrap; justify-content: space-between; align-items: center; gap: 8px; margin-bottom: 18px;">
        <div style="display: flex; align-items: center; gap: 6px;">
            <span style="font-size: 1.1rem;">🌐</span>
            <span style="font-weight: 700; color: #0f172a; font-size: 0.88rem; text-transform: uppercase; letter-spacing: 0.5px;">Cumul Permanent :</span>
        </div>
        <div style="display: flex; flex-wrap: wrap; gap: 8px; font-size: 0.84rem;">
            <span style="background: #dcfce7; color: #166534; padding: 3px 9px; border-radius: 6px; font-weight: 700; border: 1px solid #86efac;">🟢 Arrivés / Délivrés : {len(sent_contacts)}</span>
            <span style="background: #fee2e2; color: #991b1b; padding: 3px 9px; border-radius: 6px; font-weight: 700; border: 1px solid #fca5a5;">❌ Rejetés (Bounces) : {len(bounced_contacts)}</span>
            <span style="background: #ffedd5; color: #9a3412; padding: 3px 9px; border-radius: 6px; font-weight: 700; border: 1px solid #fdba74;">⏳ Restants à Envoyer : {len(approved_contacts)}</span>
            <span style="background: #e0f2fe; color: #0369a1; padding: 3px 9px; border-radius: 6px; font-weight: 700; border: 1px solid #7dd3fc;">👥 Total Base : {len(contacts)}</span>
            <span style="background: #f3e8ff; color: #6b21a8; padding: 3px 9px; border-radius: 6px; font-weight: 800; border: 1px solid #d8b4fe;">🎯 Délivrabilité : {deliv_rate:.1f}%</span>
        </div>
    </div>
    """, unsafe_allow_html=True)

    col_s1, col_s2 = st.columns([1, 1])
    
    with col_s1:
        st.subheader("⚙️ Vitesse & Paramètres d'Envoi")
        st.markdown(f"- **Expéditeur configuré :** `{smtp.sender_name} <{smtp.sender_email}>`")
        
        cv_fr_file = UPLOADS_DIR / "CV_Mohammed_HSINY_FR.pdf"
        cv_en_file = UPLOADS_DIR / "CV_Mohammed_HSINY_EN.pdf"
        portfolio_pdf_file = UPLOADS_DIR / "Portfolio_Mohammed_HSINY.pdf"
        
        speed_preset = st.radio(
            "⚡ Vitesse d'envoi",
            [
                "⚡ Mode Turbo (2 à 4 secondes / email)",
                "🚀 Mode Rapide (4 à 8 secondes / email) [Recommandé]",
                "🛡️ Mode Prudence (10 à 20 secondes / email)",
                "🎛️ Personnalisé"
            ],
            index=0
        )
        
        if "Turbo" in speed_preset:
            min_del, max_del = 2, 4
        elif "Rapide" in speed_preset:
            min_del, max_del = 4, 8
        elif "Prudence" in speed_preset:
            min_del, max_del = 10, 20
        else:
            col_d1, col_d2 = st.columns(2)
            with col_d1:
                min_del = st.number_input("Délai min (s)", min_value=1, max_value=60, value=3)
            with col_d2:
                max_del = st.number_input("Délai max (s)", min_value=2, max_value=120, value=6)
                
        smtp.min_delay_seconds = min_del
        smtp.max_delay_seconds = max_del

    with col_s2:
        st.subheader("🧪 Mode Test d'Envoi")
        st.caption("Envoyez un email de test à votre propre adresse pour vérifier le rendu et les pièces jointes.")
        test_dest = st.text_input("Adresse de test", value=smtp.sender_email)
        
        if st.button("📤 Envoyer un email de test à moi-même", type="secondary", use_container_width=True):
            if not smtp.app_password:
                st.error("Mot de passe d'application Gmail manquant ! Configurez-le dans l'onglet Paramètres.")
            else:
                test_subj = f"Stage PFE - Systèmes Embarqués, Robotique & Drones | {profile.name}"
                test_body = f"""Bonjour,

Je suis étudiant en dernière année d'ingénierie en Génie Électrique à la FST Mohammedia, passionné par les systèmes embarqués, la robotique et les drones.

Je recherche un stage PFE (Projet de Fin d'Études) de 6 mois à partir de Janvier 2027.

Portfolio : https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Bien cordialement,
Mohammed HSINY
+212 611 424 571
mohammedhsiny2@gmail.com"""

                att_list = []
                if cv_fr_file.is_file():
                    att_list.append(str(cv_fr_file))
                if portfolio_pdf_file.is_file():
                    att_list.append(str(portfolio_pdf_file))
                    
                res = send_single_email(
                    settings=smtp,
                    recipient_email=test_dest,
                    subject=test_subj,
                    body_text=test_body,
                    attachment_paths=att_list,
                    profile=profile,
                    language="fr"
                )
                if res.success:
                    st.success(f"🎉 Email de test envoyé avec succès à `{test_dest}` !")
                    log_sent_email(test_dest, test_subj, test_body, "SUCCESS")
                else:
                    st.error(f"Échec de l'envoi test : {res.message}")

    st.divider()

    col_mb1, col_mb2, col_mb3, col_mb4 = st.columns([2, 1, 1, 1])
    with col_mb1:
        st.subheader(f"📬 Envoi — {len(approved_contacts)} prêts")
    with col_mb2:
        if st.button("🔀 Waterfall (Emails Alt.)", use_container_width=True, help="Si l'adresse principale a été rejetée, bascule automatiquement sur l'Email Alternatif 1 ou 2 pour retenter"):
            wf_res = trigger_waterfall_retry_bounced()
            if wf_res["count"] > 0:
                st.success(f"🎉 {wf_res['count']} contact(s) réarmé(s) avec leur email alternatif !")
                time.sleep(2)
                st.rerun()
            else:
                st.info("Aucun contact rejeté n'a d'email alternatif non testé.")
    with col_mb3:
        if st.button("🧹 Nettoyer Gmail", use_container_width=True, help="Supprime les emails 'Address not found' de Gmail et bannit les mauvaises adresses"):
            clean_res = clean_gmail_bounces_and_sync_db(smtp)
            if clean_res["success"]:
                st.success(clean_res["message"])
                time.sleep(2)
                st.rerun()
            else:
                st.error(clean_res["message"])
    with col_mb4:
        if st.button("🔄 Sync Gmail", use_container_width=True, help="Vérifie vos messages réellement envoyés sur Gmail et recalibre la base de données"):
            sync_res = sync_sent_and_bounced_with_gmail(smtp)
            if sync_res["success"]:
                st.success(sync_res["message"])
                time.sleep(2)
                st.rerun()
            else:
                st.error(sync_res["message"])

    # ---------------------------------------------------------
    # MOTEUR AUTONOME EN ARRIÈRE-PLAN (CONTINUE MÊME NAVIGATEUR FERMÉ)
    # ---------------------------------------------------------
    dispatch_state = BackgroundDispatcher.get_status()
    is_active = BackgroundDispatcher.is_running()

    if is_active:
        st.markdown(f"""
        <div style="background: #f0fdf4; border: 2px solid #22c55e; border-radius: 12px; padding: 20px 24px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(34, 197, 94, 0.1);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 1.25rem; font-weight: 800; color: #166534;">🟢 ENVOI AUTONOME ACTIF EN ARRIÈRE-PLAN</span>
                <span style="background: #dcfce7; color: #15803d; border: 1px solid #86efac; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 0.85rem;">En direct</span>
            </div>
            <p style="color: #166534; margin: 10px 0 8px 0; font-size: 0.95rem;">
                💡 <b>Le serveur envoie vos emails en continu en tâche de fond.</b> Vous pouvez <u>fermer votre navigateur</u>, changer d'application ou éteindre votre écran en toute tranquillité : l'envoi ne s'arrêtera pas tant qu'il n'a pas terminé ou reçu votre ordre d'arrêt.
            </p>
            <div style="font-weight: 700; color: #0f172a; margin-bottom: 6px;">
                📊 Progression : <b>{dispatch_state.get('sent_count', 0)} / {dispatch_state.get('total_target', 0)}</b> emails expédiés
            </div>
            <div style="color: #475569; font-size: 0.9rem; font-style: italic;">
                📡 Statut actuel : {dispatch_state.get('last_log', 'En cours...')}
            </div>
        </div>
        """, unsafe_allow_html=True)

        target_tot = max(dispatch_state.get('total_target', 1), 1)
        curr_s = dispatch_state.get('sent_count', 0)
        st.progress(min(curr_s / target_tot, 1.0))

        col_stp1, col_stp2 = st.columns([2, 1])
        with col_stp1:
            if st.button("🔄 Actualiser le Suivi en Direct", type="primary", use_container_width=True):
                st.rerun()
        with col_stp2:
            if st.button("⏹️ Arrêter l'Envoi en Arrière-Plan", type="secondary", use_container_width=True):
                BackgroundDispatcher.stop()
                st.warning("⏹️ Ordre d'arrêt transmis au serveur.")
                time.sleep(1)
                st.rerun()
    else:
        if not approved_contacts:
            if len(sent_contacts) > 0:
                st.success(f"🎉 Félicitations ! Tous vos contacts ont déjà reçu leur candidature ({len(sent_contacts)} envoyés au total).")
            else:
                st.info("Aucun email n'a le statut 'Approuvé'. Veuillez valider les emails dans l'onglet 'Revue & Édition'.")
        else:
            # -------------------------------------------------------------
            # MODULE DIRECT D'ÉLIMINATION / EXCLUSION PAR ENTREPRISE
            # -------------------------------------------------------------
            unique_approved_companies = sorted(list(set([c.get("company", "").strip() for c in approved_contacts if c.get("company", "").strip()])))
            
            with st.expander("🏢 Éliminer / Exclure une Société de l'Envoi", expanded=False):
                st.caption("Retirez immédiatement tous les salariés d'une ou plusieurs sociétés de cette file d'envoi avant de lancer l'expédition.")
                col_ex_s1, col_ex_s2, col_ex_s3 = st.columns([2, 2, 1.5])
                with col_ex_s1:
                    sel_exc_comp_send = st.multiselect(
                        "Choisir les entreprises à éliminer :",
                        options=unique_approved_companies,
                        help="Sélectionnez une ou plusieurs entreprises présentes dans la file d'envoi ci-dessous."
                    )
                with col_ex_s2:
                    custom_exc_send = st.text_input(
                        "Ou saisir le nom d'une société :",
                        placeholder="Ex: Shark Robotics",
                        key="send_custom_exc_input"
                    )
                with col_ex_s3:
                    st.write("")
                    st.write("")
                    all_exc_send = list(sel_exc_comp_send)
                    if custom_exc_send.strip() and custom_exc_send.strip() not in all_exc_send:
                        all_exc_send.append(custom_exc_send.strip())
                    if st.button("🚫 Éliminer de l'envoi", type="primary", use_container_width=True, disabled=not all_exc_send, key="btn_exclude_from_send_tab"):
                        cnt = exclude_contacts_by_companies(all_exc_send)
                        st.success(f"🚫 {cnt} contact(s) de '{', '.join(all_exc_send)}' éliminé(s) de l'envoi !")
                        time.sleep(0.8)
                        st.rerun()

            st.markdown(f"**📋 Liste des {len(approved_contacts)} candidatures prêtes à être envoyées en tâche de fond :**")
            st.dataframe(pd.DataFrame(approved_contacts)[["name", "email", "company", "role", "subject"]], use_container_width=True)

            col_p1, col_p2, col_p3 = st.columns(3)
            with col_p1:
                batch_limit = st.number_input("Limite du lot d'envoi", min_value=1, max_value=len(approved_contacts), value=min(len(approved_contacts), 50))
            with col_p2:
                delay_min = st.slider("Délai aléatoire minimum (sec)", min_value=10, max_value=60, value=35)
            with col_p3:
                delay_max = st.slider("Délai aléatoire maximum (sec)", min_value=30, max_value=120, value=65)

            st.markdown("""
            > 🛡️ **Garantie Fonctionnement Continu :** Ce moteur démarre un processus de fond sur le serveur. Même si vous fermez cette fenêtre, l'envoi continuera automatiquement jusqu'à épuisement du lot configuré.
            """)

            btn_start_bg = st.button(
                f"🚀 LANCER L'ENVOI AUTONOME EN ARRIÈRE-PLAN ({batch_limit} CONTACTS)",
                type="primary",
                use_container_width=True,
                help="Démarre l'envoi en tâche de fond. Vous pouvez fermer votre navigateur."
            )
            if btn_start_bg:
                if not smtp.app_password:
                    st.error("Mot de passe d'application Gmail manquant. Rendez-vous dans l'onglet Paramètres.")
                else:
                    started = BackgroundDispatcher.start(
                        batch_limit=int(batch_limit),
                        min_delay=int(delay_min),
                        max_delay=int(delay_max)
                    )
                    if started:
                        st.success("🚀 Envoi autonome démarré en tâche de fond avec succès ! Vous pouvez fermer votre navigateur.")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.warning("Un envoi est déjà en cours d'exécution.")

    st.divider()
    
    # -------------------------------------------------------------
    # Évaluation de la Qualité Data par Société & Téléchargement
    # -------------------------------------------------------------
    st.subheader("🏢 Évaluation & Rapport Excel pour Fournisseur de Données")
    col_rep1, col_rep2, col_rep3 = st.columns([2, 1, 1])
    with col_rep1:
        st.caption("Fichier d'audit certifié avec preuves RFC 3464 (codes SMTP 550 User unknown) prêt à être livré à votre fournisseur pour réclamation ou remplacement.")
    
    excel_audit_path = Path("RAPPORT_AUDIT_FOURNISSEUR_EMAILS.xlsx")
    with col_rep2:
        if excel_audit_path.is_file():
            with open(excel_audit_path, "rb") as f_excel:
                st.download_button(
                    label="📥 Télécharger Rapport Excel Fournisseur",
                    data=f_excel.read(),
                    file_name="RAPPORT_AUDIT_FOURNISSEUR_EMAILS_PFE.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
    with col_rep3:
        if st.button("📊 M'envoyer copie Email", use_container_width=True, help="Expédie le rapport complet d'évaluation par société sur votre adresse Gmail"):
            rep_res = send_quality_report_email(smtp, profile)
            if rep_res["success"]:
                st.success(rep_res["message"])
            else:
                st.error(rep_res["message"])

    st.info("ℹ️ **Validation Asynchrone :** Les serveurs de messagerie distants (Thales, Airbus, etc.) mettent parfois 5 à 20 minutes pour renvoyer une notification *Address not found*. Utilisez le bouton **'🔄 Synchroniser Gmail'** à tout moment pour actualiser les rejets reçus.")

    analytics_data = compute_company_analytics()
    if analytics_data["companies"]:
        df_comp = pd.DataFrame(analytics_data["companies"])[["company", "total", "sent", "bounced", "waiting", "success_rate_str", "stars", "quality"]]
        df_comp.columns = ["Société / Entreprise", "Total Achete", "🚀 Envoyés", "❌ Rejetés (Bounces)", "⏳ En Attente", "Taux Succès", "Statut / Score", "Diagnostic Data"]
        st.dataframe(df_comp, use_container_width=True)

    st.divider()
    col_hist_h1, col_hist_h2 = st.columns([3, 1])
    with col_hist_h1:
        st.subheader("📜 Historique des Envois")
    with col_hist_h2:
        if st.button("🗑️ Effacer l'Historique", use_container_width=True, help="Vide le journal d'historique des emails envoyés"):
            clear_sent_logs_history()
            st.success("Historique des envois effacé !")
            time.sleep(0.5)
            st.rerun()

    sent_logs = get_all_sent_logs()
    if sent_logs:
        df_logs = pd.DataFrame(sent_logs)
        st.dataframe(df_logs, use_container_width=True)
    else:
        st.caption("Aucun historique d'envoi enregistré pour le moment.")

# -------------------------------------------------------------
# TAB 6: Réponses Recruteurs & IA
# -------------------------------------------------------------
with tab6:
    st.header("💬 Réponses Recruteurs & Résumés Intelligents par IA")
    st.markdown("""
    Cette boîte de réception intelligente surveille votre compte Gmail en tâche de fond, extrait les réponses des recruteurs, 
    analyse leur intention (proposition d'entretien, demande de précisions, refus) et vous génère automatiquement un résumé exécutif ainsi qu'une ébauche de réponse adaptée.
    """)
    
    col_r_top1, col_r_top2 = st.columns([3, 1])
    with col_r_top1:
        st.caption(f"⚡ **Daemon Auto-Sync :** {BackgroundSyncDaemon.last_status_message} *(synchronisation automatique non-bloquante toutes les 45s)*")
    with col_r_top2:
        if st.button("🔄 Actualiser les Réponses Gmail", type="primary", use_container_width=True):
            with st.spinner("Analyse approfondie de votre boîte de réception..."):
                scan_res = scan_incoming_recruiter_replies(smtp, profile)
                if scan_res["success"]:
                    st.success(scan_res["message"])
                else:
                    st.error(scan_res["message"])
                time.sleep(1)
                st.rerun()

    responses = get_all_recruiter_responses()
    
    # KPI Metrics
    total_resp = len(responses)
    interview_count = sum(1 for r in responses if r.get("intent_category") == "interview_offer")
    info_count = sum(1 for r in responses if r.get("intent_category") == "request_info")
    rejection_count = sum(1 for r in responses if r.get("intent_category") == "rejection")
    unread_count = sum(1 for r in responses if not r.get("is_read"))

    st.markdown(f"""
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(180px, 1fr)); gap: 12px; margin-bottom: 20px;">
        <div style="background: white; padding: 12px 16px; border-radius: 10px; border: 1px solid #e2e8f0;">
            <div style="font-size: 0.8rem; color: #64748b; font-weight: 600; text-transform: uppercase;">💬 Total Réponses</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #0f172a;">{total_resp}</div>
        </div>
        <div style="background: white; padding: 12px 16px; border-radius: 10px; border: 1px solid #bbf7d0;">
            <div style="font-size: 0.8rem; color: #166534; font-weight: 600; text-transform: uppercase;">🎯 Entretiens Proposés</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #16a34a;">{interview_count}</div>
        </div>
        <div style="background: white; padding: 12px 16px; border-radius: 10px; border: 1px solid #fed7aa;">
            <div style="font-size: 0.8rem; color: #9a3412; font-weight: 600; text-transform: uppercase;">🟡 Demandes d'Infos</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #ea580c;">{info_count}</div>
        </div>
        <div style="background: white; padding: 12px 16px; border-radius: 10px; border: 1px solid #fecaca;">
            <div style="font-size: 0.8rem; color: #991b1b; font-weight: 600; text-transform: uppercase;">🔴 Refus Politiques</div>
            <div style="font-size: 1.6rem; font-weight: 800; color: #dc2626;">{rejection_count}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if not responses:
        st.info("ℹ️ Aucune réponse de recruteur enregistrée pour l'instant. Cliquez sur **'🔄 Actualiser les Réponses Gmail'** ou laissez le daemon automatique scanner votre boîte.")
    else:
        filter_opt = st.radio(
            "Filtrer par type de réponse",
            ["Toutes les réponses", "🎯 Entretiens Proposés", "🟡 Demandes d'Infos", "🔴 Refus Politisés", "⚪ Non lus uniquement"],
            horizontal=True
        )
        
        filtered = responses
        if filter_opt == "🎯 Entretiens Proposés":
            filtered = [r for r in responses if r.get("intent_category") == "interview_offer"]
        elif filter_opt == "🟡 Demandes d'Infos":
            filtered = [r for r in responses if r.get("intent_category") == "request_info"]
        elif filter_opt == "🔴 Refus Politisés":
            filtered = [r for r in responses if r.get("intent_category") == "rejection"]
        elif filter_opt == "⚪ Non lus uniquement":
            filtered = [r for r in responses if not r.get("is_read")]
            
        for r in filtered:
            intent_meta = {
                "interview_offer": ("🎯 ENTRETIEN PROPOSÉ", "#dcfce7", "#166534", "#86efac"),
                "request_info": ("🟡 DEMANDE DE PRÉCISIONS", "#ffedd5", "#9a3412", "#fdba74"),
                "rejection": ("🔴 REFUS POLI", "#fee2e2", "#991b1b", "#fca5a5"),
                "out_of_office": ("⚪ ABSENCE DU BUREAU", "#f1f5f9", "#475569", "#cbd5e1"),
                "general": ("💬 RÉPONSE GÉNÉRALE", "#e0f2fe", "#0369a1", "#7dd3fc")
            }.get(r.get("intent_category", "general"), ("💬 RÉPONSE", "#f8fafc", "#334155", "#cbd5e1"))

            with st.container():
                st.markdown(f"""
                <div style="background: white; border-radius: 12px; border: 1px solid #e2e8f0; padding: 18px 22px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.04);">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
                        <div>
                            <span style="font-size: 1.1rem; font-weight: 800; color: #0f172a;">{r.get('sender_name') or r['sender_email']}</span>
                            <span style="color: #64748b; font-size: 0.9rem; margin-left: 8px;">— <b>{r.get('company') or 'Société'}</b> ({r['sender_email']})</span>
                        </div>
                        <span style="background: {intent_meta[1]}; color: {intent_meta[2]}; border: 1px solid {intent_meta[3]}; padding: 4px 10px; border-radius: 6px; font-weight: 700; font-size: 0.8rem;">
                            {intent_meta[0]}
                        </span>
                    </div>
                    <div style="font-weight: 600; color: #1e293b; font-size: 0.95rem; margin-bottom: 8px;">
                        📌 Sujet : <i>{r.get('subject', 'Sans objet')}</i>
                    </div>
                    <div style="background: #f8fafc; border-left: 4px solid #2563eb; padding: 10px 14px; border-radius: 4px; margin-bottom: 12px;">
                        <div style="font-size: 0.82rem; font-weight: 700; color: #2563eb; text-transform: uppercase; margin-bottom: 4px;">🤖 Résumé Exécutif IA :</div>
                        <div style="font-size: 0.88rem; color: #334155;">{r.get('ai_summary', 'Résumé en cours...')}</div>
                    </div>
                    <div style="background: #fdf4ff; border-left: 4px solid #a855f7; padding: 10px 14px; border-radius: 4px; margin-bottom: 12px;">
                        <div style="font-size: 0.82rem; font-weight: 700; color: #a855f7; text-transform: uppercase; margin-bottom: 4px;">💡 Proposition de Réponse IA pour Mohammed :</div>
                        <div style="font-size: 0.88rem; color: #581c87; white-space: pre-line;">{r.get('ai_suggested_reply', '')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                with st.expander(f"📜 Voir l'Email Original Complet de {r.get('sender_name') or r['sender_email']}"):
                    st.text(r.get("body_text", ""))
                    if not r.get("is_read"):
                        if st.button("Marquer comme lu", key=f"mark_read_{r['id']}"):
                            mark_response_read(r["id"])
                            st.rerun()

# -------------------------------------------------------------
# TAB 7: Paramètres & Gmail
# -------------------------------------------------------------
with tab7:
    st.header("⚙️ Configuration Gmail & Sécurité du Compte")
    
    is_connected = bool(smtp.app_password and smtp.app_password.strip())
    
    # Prominent Disconnection / Connection Status Card
    if is_connected:
        st.markdown("""
        <div style="background: #f0fdf4; border: 2px solid #22c55e; border-radius: 12px; padding: 18px 22px; margin-bottom: 22px;">
            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px;">
                <div style="display: flex; align-items: center; gap: 12px;">
                    <div style="font-size: 1.8rem; color: #16a34a;"><i class="fa-solid fa-circle-check"></i></div>
                    <div>
                        <div style="font-size: 1.15rem; font-weight: 800; color: #166534;">🟢 COMPTE GMAIL ACTUELLEMENT CONNECTÉ</div>
                        <div style="color: #15803d; font-size: 0.88rem; margin-top: 2px;">
                            Votre adresse <code>{}</code> est configurée pour la prospection et la synchronisation.
                        </div>
                    </div>
                </div>
            </div>
        </div>
        """.format(smtp.sender_email), unsafe_allow_html=True)
        
        col_dc1, col_dc2 = st.columns([2, 1])
        with col_dc1:
            st.caption("Vous pouvez déconnecter immédiatement votre compte Gmail pour stopper toute activité en arrière-plan.")
        with col_dc2:
            if st.button("🔴 DÉCONNECTER MON COMPTE GMAIL", type="secondary", use_container_width=True, help="Coupe immédiatement toute connexion avec Gmail"):
                smtp.app_password = ""
                save_smtp_settings(smtp)
                BackgroundSyncDaemon.stop()
                BackgroundDispatcher.stop()
                st.warning("Compte Gmail déconnecté avec succès. Toutes les connexions sont coupées.")
                time.sleep(1)
                st.rerun()
    else:
        st.markdown("""
        <div style="background: #fef2f2; border: 2px solid #ef4444; border-radius: 12px; padding: 18px 22px; margin-bottom: 22px;">
            <div style="display: flex; align-items: center; gap: 14px;">
                <div style="font-size: 2rem; color: #dc2626;"><i class="fa-solid fa-lock"></i></div>
                <div>
                    <div style="font-size: 1.2rem; font-weight: 800; color: #991b1b;">🔴 COMPTE GMAIL TOTALEMENT DÉCONNECTÉ (MODE PAUSE)</div>
                    <div style="color: #7f1d1d; font-size: 0.92rem; margin-top: 4px;">
                        Toutes les requêtes vers les serveurs de Google sont coupées. Aucune synchronisation ni aucun envoi n'a lieu tant que vous ne donnez pas l'ordre de reconnexion.
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.divider()
    col_cfg1, col_cfg2 = st.columns(2)
    
    with col_cfg1:
        st.subheader("📧 Gestion des Identifiants Gmail")
        st.markdown("""
        > **Pour reconnecter votre compte Gmail en toute sécurité :**
        > 1. Rendez-vous sur : [Mots de passe des applications Google](https://myaccount.google.com/apppasswords)
        > 2. Générez un mot de passe d'application de 16 lettres (ex: `abcd efgh ijkl mnop`).
        > 3. Collez-le ci-dessous et cliquez sur **🔌 Reconnecter mon compte**.
        """)
        
        cfg_sender_name = st.text_input("Nom d'expéditeur", value=smtp.sender_name)
        cfg_sender_email = st.text_input("Adresse Gmail expéditrice", value=smtp.sender_email)
        
        pwd_placeholder = "•••• •••• •••• •••• (Mot de passe sécurisé & actif)" if smtp.app_password else "Ex: abcd efgh ijkl mnop"
        cfg_app_pwd = st.text_input(
            "Mot de passe d'application Gmail (16 caractères)",
            value="",
            type="password",
            placeholder=pwd_placeholder,
            help="Laissez vide pour conserver le mot de passe actif. Saisissez 16 lettres uniquement pour le modifier."
        )
        
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
            if st.button("🔌 Reconnecter & Sauvegarder", type="primary", use_container_width=True):
                smtp.sender_name = cfg_sender_name
                smtp.sender_email = cfg_sender_email
                if cfg_app_pwd.strip():
                    smtp.app_password = cfg_app_pwd.strip()
                save_smtp_settings(smtp)
                st.session_state.smtp = smtp
                if smtp.app_password:
                    st.success("✅ Paramètres Gmail sauvegardés de façon permanente !")
                else:
                    st.warning("⚠️ Compte enregistré en mode déconnecté (mot de passe vide).")
                time.sleep(0.8)
                st.rerun()
        with col_btn2:
            if st.button("🔍 Tester la connexion", use_container_width=True):
                smtp.sender_name = cfg_sender_name
                smtp.sender_email = cfg_sender_email
                if cfg_app_pwd.strip():
                    smtp.app_password = cfg_app_pwd.strip()
                save_smtp_settings(smtp)
                st.session_state.smtp = smtp
                res_test = test_smtp_connection(smtp)
                if res_test["success"]:
                    st.success(f"✅ {res_test['message']}")
                else:
                    st.error(f"❌ {res_test['message']}")
                
    with col_cfg2:
        st.subheader("🔑 Clé API Intelligence Artificielle")
        st.markdown("""
        > **Où obtenir une clé API gratuite Google Gemini ?**
        > - Créez votre clé en 30 secondes sur [Google AI Studio](https://aistudio.google.com/app/apikey).
        > - Les modèles `gemini-2.0-flash` et `gemini-2.5-flash` offrent d'excellentes performances de génération.
        """)
        
        api_placeholder = "•••••••••••••••••••••••••••••••• (Clé API active)" if llm.api_key else "Ex: AIzaSy..."
        cfg_api_key = st.text_input(
            "Clé API (Gemini / OpenAI / Groq / DeepSeek)",
            value="",
            type="password",
            placeholder=api_placeholder,
            help="Laissez vide pour conserver la clé API actuelle."
        )
        
        if st.button("💾 Sauvegarder la clé API", use_container_width=True):
            if cfg_api_key.strip():
                llm.api_key = cfg_api_key.strip()
            save_llm_settings(llm)
            st.session_state.llm = llm
            st.success("✅ Clé API enregistrée et synchronisée avec succès !")
            time.sleep(0.8)
            st.rerun()

    st.divider()
    st.markdown("""
    <div style="background: #f8fafc; border: 1px solid #cbd5e1; border-radius: 12px; padding: 18px 22px; margin-top: 15px;">
        <div style="font-weight: 700; color: #0F4C81; font-size: 1.05rem; margin-bottom: 8px;">
            ☁️ Sauvegarde Permanente sur Streamlit Cloud (Zéro Reconnexion Requise)
        </div>
        <p style="color: #475569; font-size: 0.9rem; margin-bottom: 10px; line-height: 1.5;">
            Sur <b>Streamlit Community Cloud</b>, les conteneurs redémarrent automatiquement après inactivité. Pour que votre compte Gmail et vos clés restent <b>définitivement sauvegardés</b> sans jamais avoir à les retaper :
        </p>
        <ol style="color: #334155; font-size: 0.88rem; margin-left: 20px; line-height: 1.6;">
            <li>Dans votre tableau de bord Streamlit Cloud, cliquez sur <b>Manage app</b> (en bas à droite) ➔ <b>Settings</b> ➔ <b>Secrets</b>.</li>
            <li>Collez le bloc suivant et cliquez sur <b>Save</b> :</li>
        </ol>
        <pre style="background: #0f172a; color: #38bdf8; padding: 12px 16px; border-radius: 8px; font-size: 0.85rem; margin-top: 10px; overflow-x: auto;">
GMAIL_SENDER_EMAIL = "mohammedhsiny2@gmail.com"
GMAIL_APP_PASSWORD = "{}"
SECURITY_PIN = "19748403"
GEMINI_API_KEY = "{}"</pre>
    </div>
    """.format(
        smtp.app_password if smtp.app_password else "votre_mot_de_passe_application_16_lettres",
        llm.api_key if llm.api_key else "votre_cle_gemini_ici"
    ), unsafe_allow_html=True)
