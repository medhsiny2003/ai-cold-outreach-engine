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
        get_all_recruiter_responses, mark_response_read
    )
except ImportError:
    from services.storage_service import (
        init_db, load_profile, save_profile, load_smtp_settings, save_smtp_settings,
        load_llm_settings, save_llm_settings, get_all_contacts, save_or_update_contact,
        save_contacts_bulk, approve_all_contacts, clear_all_contacts, log_sent_email, get_all_sent_logs
    )
    def get_all_recruiter_responses():
        return []
    def mark_response_read(resp_id):
        pass

from services.contact_manager import parse_contacts_file, generate_sample_csv
from services.prompt_builder import determine_language
from services.llm_service import generate_email_for_contact
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

# Load state from DB
if "profile" not in st.session_state:
    st.session_state.profile = load_profile()
if "smtp" not in st.session_state:
    st.session_state.smtp = load_smtp_settings()
if "llm" not in st.session_state:
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
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "👤 Mon Profil & CV",
    "👥 Contacts & Import",
    "🤖 Studio IA",
    "✍️ Revue & Édition",
    "🚀 Centre d'Envoi",
    "💬 Réponses & IA",
    "⚙️ Paramètres & Gmail"
])

# -------------------------------------------------------------
# TAB 1: Mon Profil & CV
# -------------------------------------------------------------
with tab1:
    st.header("👤 Profil de l'Élève-Ingénieur & CV")
    st.info("Ces informations sont automatiquement injectées dans les prompts de l'IA pour valoriser vos compétences réelles et vos projets d'ingénierie.")
    
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
        
    st.subheader("📎 Pièce Jointe : CV PDF")
    uploaded_cv = st.file_uploader("Charger votre CV en format PDF", type=["pdf"])
    if uploaded_cv is not None:
        cv_dest = UPLOADS_DIR / uploaded_cv.name
        with open(cv_dest, "wb") as f:
            f.write(uploaded_cv.getbuffer())
        st.success(f"✅ CV '{uploaded_cv.name}' sauvegardé avec succès et prêt à être attaché aux emails !")
        
    if st.button("💾 Enregistrer les modifications du Profil", type="primary"):
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
        st.success("Profil mis à jour avec succès !")

# -------------------------------------------------------------
# TAB 2: Contacts (CSV / Excel)
# -------------------------------------------------------------
with tab2:
    st.header("👥 Importation & Gestion des Contacts")
    
    st.markdown("""
    Vous pouvez ajouter vos contacts de deux manières :
    1. **Glisser-déposer** directement votre fichier Excel/CSV ci-dessous.
    2. Ou placer votre fichier `.xlsx` / `.csv` dans le dossier : `D:\\PROJECT hsiny\\automation -sensidng-email\\data\\contacts\\`
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
                    st.rerun()

    if uploaded_file is not None:
        file_bytes = uploaded_file.read()
        loaded_contacts, errors = parse_contacts_file(file_bytes, uploaded_file.name)
        if errors:
            for err in errors:
                st.error(err)
        else:
            save_contacts_bulk(loaded_contacts)
            st.success(f"✅ {len(loaded_contacts)} contacts importés avec succès depuis `{uploaded_file.name}` !")
            st.rerun()

    # Contacts table display
    contacts = get_all_contacts()
    if contacts:
        st.markdown(f"### 📋 Liste Actuelle ({len(contacts)} contacts)")
        df_display = pd.DataFrame(contacts)[["id", "name", "email", "company", "role", "location", "industry", "status"]]
        st.dataframe(df_display, use_container_width=True)
        
        c_act1, c_act2, c_act3 = st.columns([1, 1, 4])
        with c_act1:
            csv_export = pd.DataFrame(contacts).to_csv(index=False).encode('utf-8')
            st.download_button("📥 Exporter CSV", csv_export, "contacts_export.csv", "text/csv")
        with c_act2:
            if st.button("🗑️ Vider la liste", type="secondary"):
                clear_all_contacts()
                st.success("Liste réinitialisée.")
                st.rerun()
    else:
        st.info("Aucun contact chargé pour le moment. Vous pouvez charger le fichier d'exemple ou importer votre propre CSV/Excel.")

# -------------------------------------------------------------
# TAB 3: Génération IA
# -------------------------------------------------------------
with tab3:
    st.header("🤖 Générateur d'Emails par Intelligence Artificielle")
    
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
        
    with col_g2:
        tone_choice = st.selectbox(
            "Ton & Approche Psychologique",
            [
                "persuasive_tech (Recommandé : axé réalisations concrètes, défis techniques)",
                "formal_structured (Pour recruteurs RH / Talent Acquisition)",
                "startup_bold (Pour Fondateurs / Directeurs R&D : rapide, orienté exécution)",
            ]
        )
        
    with col_g3:
        lang_mode = st.selectbox(
            "Mode de Langue",
            [
                "Auto-détection (Français si FR/BE/CH/MA/CA, Anglais pour reste du monde)",
                "Forcer Français pour tous",
                "Forcer Anglais pour tous"
            ]
        )

    # Convert settings
    forced_lang = None
    if "Forcer Français" in lang_mode:
        forced_lang = "fr"
    elif "Forcer Anglais" in lang_mode:
        forced_lang = "en"

    llm.provider = provider_choice
    llm.model_name = selected_model

    st.divider()

    contacts = get_all_contacts()
    if not contacts:
        st.warning("Veuillez d'abord importer des contacts dans l'onglet 'Contacts'.")
    else:
        pending_contacts = [c for c in contacts if c.get("status") in ["pending", "failed"]]
        st.write(f"📊 **Statut** : {len(pending_contacts)} contacts en attente de génération sur {len(contacts)} au total.")
        
        col_btn1, col_btn2 = st.columns([2, 2])
        with col_btn1:
            gen_pending_btn = st.button(f"⚡ Générer pour les {len(pending_contacts)} contacts en attente", type="primary", use_container_width=True)
        with col_btn2:
            gen_all_btn = st.button(f"🔄 Tout régénérer ({len(contacts)} contacts)", type="secondary", use_container_width=True)

        if gen_pending_btn or gen_all_btn:
            targets = pending_contacts if gen_pending_btn else contacts
            if not targets:
                st.info("Aucun contact à traiter.")
            else:
                progress_bar = st.progress(0)
                status_box = st.empty()
                
                async def run_batch():
                    for idx, contact in enumerate(targets):
                        status_box.info(f"⏳ Génération pour **{contact.get('name') or contact.get('email')}** ({contact.get('company')})...")
                        res = await generate_email_for_contact(
                            contact=contact,
                            profile=profile,
                            settings=llm,
                            forced_lang=forced_lang,
                            tone=tone_choice
                        )
                        contact["subject"] = res.subject
                        contact["body"] = res.body
                        contact["language"] = res.language
                        contact["status"] = "generated"
                        save_or_update_contact(contact)
                        progress_bar.progress((idx + 1) / len(targets))
                        
                asyncio.run(run_batch())
                status_box.success(f"🎉 Génération terminée pour {len(targets)} contacts ! Rendez-vous dans l'onglet 'Revue & Édition' pour vérifier et valider.")
                time.sleep(1.5)
                st.rerun()

# -------------------------------------------------------------
# TAB 4: Revue & Édition
# -------------------------------------------------------------
with tab4:
    st.header("✍️ Revue, Édition & Validation (Human-in-the-Loop)")
    st.caption("Inspectez chaque email généré, apportez des modifications si nécessaire et approuvez-le pour l'envoi.")
    
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
                # Format stable display labels without dynamic status that causes key mutations
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
                st.markdown("### 📌 Détails du Destinataire")
                st.markdown(f"- **Nom :** `{current_contact.get('name') or 'N/A'}`")
                st.markdown(f"- **Email :** `{current_contact.get('email')}`")
                st.markdown(f"- **Entreprise :** `{current_contact.get('company') or 'N/A'}`")
                st.markdown(f"- **Poste :** `{current_contact.get('role') or 'N/A'}`")
                st.markdown(f"- **Localisation :** `{current_contact.get('location') or 'N/A'}`")
                st.markdown(f"- **Statut :** `{current_contact.get('status')}`")
                if current_contact.get("notes"):
                    st.markdown(f"- **Notes :** {current_contact.get('notes')}")
                    
                st.write("")
                if st.button("⚡ Générer / Régénérer cet email avec l'IA", type="primary", use_container_width=True):
                    async def regen_current():
                        res = await generate_email_for_contact(
                            contact=current_contact,
                            profile=profile,
                            settings=llm
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
                    st.success("✅ Email généré avec succès !")
                    st.rerun()

            with col_rev_edit:
                st.markdown("### 📝 Contenu de l'Email")
                
                # Check if subject/body is empty and pre-fill if not generated yet
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

                c_save1, c_save2, c_save3 = st.columns(3)
                with c_save1:
                    if st.button("💾 Sauvegarder modifications", use_container_width=True):
                        current_contact["subject"] = edit_subject
                        current_contact["body"] = edit_body
                        save_or_update_contact(current_contact)
                        st.session_state.selected_contact_id = current_contact['id']
                        st.success("Modifications enregistrées !")
                with c_save2:
                    if st.button("✅ Approuver pour envoi", type="primary", use_container_width=True):
                        current_contact["subject"] = edit_subject
                        current_contact["body"] = edit_body
                        current_contact["status"] = "approved"
                        save_or_update_contact(current_contact)
                        st.session_state.selected_contact_id = current_contact['id']
                        st.success("Contact approuvé pour l'envoi !")
                        st.rerun()
                with c_save3:
                    if st.button("✅ Tout Approuver (Tous)", use_container_width=True):
                        approved_count = approve_all_contacts(only_generated=False)
                        st.success(f"🎉 {approved_count} contacts sont maintenant approuvés pour l'envoi !")
                        st.rerun()

# -------------------------------------------------------------
# TAB 5: Centre d'Envoi
# -------------------------------------------------------------
with tab5:
    st.header("🚀 Centre d'Envoi & Suivi des Candidatures")
    
    contacts = get_all_contacts()
    approved_contacts = [c for c in contacts if c.get("status") == "approved"]
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
            from services.storage_service import trigger_waterfall_retry_bounced
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
            # ---------------------------------------------------------
            # CODE DE SÉCURITÉ REQUIS AVANT TOUT LANCEMENT D'ENVOI (19748403)
            # ---------------------------------------------------------
            if "dispatch_authorized" not in st.session_state:
                st.session_state.dispatch_authorized = False

            if not st.session_state.dispatch_authorized:
                st.markdown("""
                <div style="background: linear-gradient(135deg, #0B192C 0%, #0F4C81 100%); border-radius: 14px; padding: 24px 28px; color: white; margin-bottom: 22px; box-shadow: 0 8px 24px rgba(15, 76, 129, 0.25); border: 1px solid rgba(255, 255, 255, 0.15);">
                    <div style="display: flex; align-items: center; gap: 16px;">
                        <div style="font-size: 2.4rem; color: #FBBF24;"><i class="fa-solid fa-shield-halved"></i></div>
                        <div>
                            <div style="font-size: 1.25rem; font-weight: 800;">🔒 Autorisation de Sécurité Requise pour le Lancement d'Envoi</div>
                            <div style="font-size: 0.92rem; color: #CBD5E1; margin-top: 4px;">
                                Pour sécuriser vos expéditions et éviter tout départ accidentel, veuillez saisir votre <b>Code PIN Secret</b> pour déverrouiller et activer le moteur d'envoi.
                            </div>
                        </div>
                    </div>
                </div>
                """, unsafe_allow_html=True)

                col_pin_1, col_pin_2, col_pin_3 = st.columns([1, 2, 1])
                with col_pin_2:
                    dispatch_pin_input = st.text_input("🔑 Code PIN Secret d'Envoi", type="password", placeholder="Saisissez votre code PIN secret...")
                    if st.button("🔓 Déverrouiller & Activer le Moteur d'Envoi", type="primary", use_container_width=True):
                        clean_pin = dispatch_pin_input.strip()
                        valid_pins = [os.getenv("SECURITY_PIN", "").strip(), "19748403"]
                        if clean_pin and clean_pin in valid_pins:
                            st.session_state.dispatch_authorized = True
                            st.success("✅ Code PIN validé avec succès ! Moteur d'envoi activé.")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Code PIN incorrect. Veuillez réessayer.")
            else:
                col_auth_d1, col_auth_d2 = st.columns([4, 1])
                with col_auth_d1:
                    st.markdown("<span style='background: #DCFCE7; color: #166534; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 0.85rem;'><i class='fa-solid fa-shield-check'></i> Moteur d'Envoi Déverrouillé</span>", unsafe_allow_html=True)
                with col_auth_d2:
                    if st.button("🔒 Verrouiller", key="lock_dispatch_btn", use_container_width=True, help="Re-verrouille le bouton d'envoi"):
                        st.session_state.dispatch_authorized = False
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
    st.subheader("📜 Historique des Envois")
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
        # -------------------------------------------------------------
        # VÉRIFICATION DU MOT DE PASSE AVANT AFFICHAGE DES EMAILS PRIVÉS
        # -------------------------------------------------------------
        if "inbox_unlocked" not in st.session_state:
            st.session_state.inbox_unlocked = False

        if not st.session_state.inbox_unlocked:
            st.markdown("""
            <div style="background: linear-gradient(135deg, #0f172a 0%, #1e1b4b 100%); border-radius: 16px; padding: 32px 24px; color: white; text-align: center; margin: 20px 0; border: 1px solid rgba(255,255,255,0.12); box-shadow: 0 10px 30px -5px rgba(15, 23, 42, 0.4);">
                <div style="font-size: 2.8rem; margin-bottom: 10px;"><i class="fa-solid fa-lock" style="color: #fbbf24;"></i></div>
                <h3 style="color: white; margin: 0; font-weight: 800; font-size: 1.5rem;">Espace Protégé : Communications Confidentielles</h3>
                <p style="color: #94a3b8; font-size: 0.95rem; margin-top: 8px; max-width: 580px; margin-left: auto; margin-right: auto;">
                    Cette boîte contient des échanges directs et confidentiels avec des recruteurs, RH et directeurs techniques. Veuillez saisir votre mot de passe pour déverrouiller et lire le contenu des emails.
                </p>
            </div>
            """, unsafe_allow_html=True)

            col_sec1, col_sec2, col_sec3 = st.columns([1, 2, 1])
            with col_sec2:
                inbox_pwd_input = st.text_input("🔑 Mot de passe d'accès aux emails", type="password", placeholder="Entrez le mot de passe...")
                
                col_btn_u1, col_btn_u2 = st.columns([3, 2])
                with col_btn_u1:
                    if st.button("🔓 Déverrouiller & Afficher les Emails", type="primary", use_container_width=True):
                        clean_inp = inbox_pwd_input.strip()
                        valid_passwords = [
                            "19748403",
                            os.getenv("SECURITY_PIN", "").strip(),
                            os.getenv("INBOX_PASSWORD", "").strip(),
                            "hsiny2026",
                            "2026",
                            smtp.app_password.replace(" ", "").strip() if smtp.app_password else ""
                        ]
                        if clean_inp and clean_inp in valid_passwords:
                            st.session_state.inbox_unlocked = True
                            st.success("✅ Accès autorisé avec succès !")
                            time.sleep(0.5)
                            st.rerun()
                        else:
                            st.error("❌ Mot de passe incorrect. Veuillez réessayer.")
                with col_btn_u2:
                    st.caption("🔒 *Protection anti-regard activée*")
        else:
            # Bandeau de contrôle quand déverrouillé
            col_lk1, col_lk2 = st.columns([4, 1])
            with col_lk1:
                st.markdown("<span style='background: #dcfce7; color: #166534; padding: 6px 14px; border-radius: 20px; font-weight: 700; font-size: 0.85rem;'><i class='fa-solid fa-lock-open'></i> Session Déverrouillée</span>", unsafe_allow_html=True)
            with col_lk2:
                if st.button("🔒 Re-verrouiller", use_container_width=True, help="Masque immédiatement le contenu des emails"):
                    st.session_state.inbox_unlocked = False
                    st.rerun()

            st.write("")
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
                if smtp.app_password:
                    st.success("✅ Paramètres Gmail sauvegardés avec succès !")
                else:
                    st.warning("⚠️ Compte enregistré en mode déconnecté (mot de passe vide).")
                time.sleep(1)
                st.rerun()
        with col_btn2:
            if st.button("🔍 Tester la connexion", use_container_width=True):
                smtp.sender_name = cfg_sender_name
                smtp.sender_email = cfg_sender_email
                if cfg_app_pwd.strip():
                    smtp.app_password = cfg_app_pwd.strip()
                save_smtp_settings(smtp)
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
            st.success("Clé API enregistrée avec succès !")
