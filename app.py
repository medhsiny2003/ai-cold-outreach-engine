import os
import sys
import asyncio
import time
import random
from pathlib import Path
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
from services.storage_service import (
    init_db, load_profile, save_profile, load_smtp_settings, save_smtp_settings,
    load_llm_settings, save_llm_settings, get_all_contacts, save_or_update_contact,
    save_contacts_bulk, approve_all_contacts, clear_all_contacts, log_sent_email, get_all_sent_logs
)
from services.contact_manager import parse_contacts_file, generate_sample_csv
from services.prompt_builder import determine_language
from services.llm_service import generate_email_for_contact
from services.email_sender import (
    test_smtp_connection, send_single_email, send_batch_emails,
    build_professional_html, LOGO_PATH
)
from services.gmail_cleaner import clean_gmail_bounces_and_sync_db, sync_sent_and_bounced_with_gmail
from services.analytics_service import compute_company_analytics, send_quality_report_email

# Initialize DB schema
init_db()

# Custom CSS for modern styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.2rem;
        font-weight: 800;
        background: linear-gradient(135deg, #1E88E5 0%, #1565C0 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.2rem;
    }
    .sub-header {
        color: #555;
        font-size: 1.05rem;
        margin-bottom: 1.5rem;
    }
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border-left: 4px solid #1E88E5;
        box-shadow: 0 2px 4px rgba(0,0,0,0.04);
    }
    .email-preview-box {
        background-color: #ffffff;
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 20px;
        font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        line-height: 1.6;
        color: #2c3e50;
    }
    .badge-status {
        padding: 3px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
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

# Sidebar
with st.sidebar:
    if LOGO_PATH.is_file():
        st.image(str(LOGO_PATH), width=110)
    else:
        st.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=64)
        
    st.title("Outreach Hub")
    st.markdown(f"### **{profile.name}**")
    st.caption("🏆 **Président Club RoboThings** | FSTM")
    st.caption(f"🎓 {profile.title_fr}")
    
    st.divider()
    
    # Active Attachments Check
    st.markdown("### 📎 Documents Attachés")
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
    st.markdown("### 🔗 Liens Officiels")
    st.markdown(f"- [🌐 Portfolio en ligne]({profile.portfolio_url})")
    st.markdown(f"- [💼 Profil LinkedIn]({profile.linkedin_url})")
    st.markdown(f"- ✉️ `{profile.email}`")
    st.markdown(f"- 📱 `{profile.phone}`")

# Live Real-Time Metrics
contacts = get_all_contacts()
total_contacts = len(contacts)
sent_count = sum(1 for c in contacts if c.get("status") == "sent")
approved_waiting_count = sum(1 for c in contacts if c.get("status") == "approved")
bounced_count = sum(1 for c in contacts if c.get("status") == "bounced")
pending_count = sum(1 for c in contacts if c.get("status") in ["pending", "failed"])

# Sidebar Live Monitor
with st.sidebar:
    st.divider()
    st.markdown("### 📊 Suivi en Temps Réel")
    st.markdown(f"- 🟢 **Délivrés sans erreur :** `{sent_count}`")
    st.markdown(f"- 🔴 **Rejetés (Address not found) :** `{bounced_count}`")
    st.markdown(f"- ⏳ **En attente d'envoi :** `{approved_waiting_count}`")
    st.markdown(f"- 👥 **Total Contacts :** `{total_contacts}`")

# Main Header
st.markdown('<div class="main-header">⚡ AI Cold Outreach Engine & Email Automation</div>', unsafe_allow_html=True)
st.markdown('<div class="sub-header">Générateur intelligent d\'emails de prospection pour stage PFE avec validation de délivrabilité Gmail certifiée (RFC 3464).</div>', unsafe_allow_html=True)

# Top Metrics Row
m1, m2, m3, m4 = st.columns(4)
with m1:
    st.metric("👥 Total Contacts", f"{total_contacts}", help="Total des contacts importés")
with m2:
    st.metric("🚀 Envoyés avec Succès", f"{sent_count}", help="Candidatures bien reçues sans bounce")
with m3:
    st.metric("❌ Address Not Found", f"{bounced_count}", help="Emails invalides certifiés par Mailer-Daemon (Bannis)")
with m4:
    st.metric("⏳ Restants à Envoyer", f"{approved_waiting_count}", help="Contacts qualifiés prêts à l'envoi")

st.write("")

# Navigation Tabs
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "👤 Mon Profil & CV",
    "👥 Contacts (CSV / Excel)",
    "🤖 Génération IA",
    "✍️ Revue & Édition",
    "🚀 Centre d'Envoi",
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
    
    # KPI Metrics Dashboard
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("📤 Déjà Envoyés", f"{len(sent_contacts)}")
    m2.metric("⏳ Restants à Envoyer", f"{len(approved_contacts)}")
    m3.metric("❌ Adresses Rejetées", f"{len(bounced_contacts)}")
    m4.metric("📊 Total Base Contacts", f"{len(contacts)}")
    
    st.divider()

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

    if not approved_contacts:
        if len(sent_contacts) > 0:
            st.success(f"🎉 Félicitations ! Tous vos contacts ont déjà reçu leur candidature ({len(sent_contacts)} envoyés au total).")
        else:
            st.info("Aucun email n'a le statut 'Approuvé'. Veuillez valider les emails dans l'onglet 'Revue & Édition'.")
    else:
        st.markdown(f"**📋 Liste des {len(approved_contacts)} candidatures prêtes à partir en continu :**")
        st.dataframe(pd.DataFrame(approved_contacts)[["name", "email", "company", "role", "subject"]], use_container_width=True)
        
        # Mode Selection: Immédiat vs Programmé
        send_mode = st.radio(
            "Mode d'expédition :",
            ["🚀 Envoi Immédiat en Continu", "⏰ Programmer un Envoi Différé (Date & Heure)"],
            horizontal=True
        )
        
        should_start_sending = False
        
        if "Immédiat" in send_mode:
            btn_launch = st.button(
                f"🚀 LANCER L'ENVOI IMMÉDIAT POUR LES {len(approved_contacts)} CONTACTS RESTANTS",
                type="primary",
                use_container_width=True,
                help="Envoie automatiquement tous les emails restants les uns après les autres sans interruption"
            )
            if btn_launch:
                should_start_sending = True
        else:
            col_sc1, col_sc2 = st.columns(2)
            with col_sc1:
                target_date = st.date_input("Date de lancement souhaitée", value=datetime.now().date())
            with col_sc2:
                target_time = st.time_input("Heure de lancement (ex: 08:30 au début des heures de bureau)", value=datetime.strptime("08:30", "%H:%M").time())
                
            scheduled_dt = datetime.combine(target_date, target_time)
            now_dt = datetime.now()
            
            if scheduled_dt <= now_dt:
                st.warning("⚠️ L'heure programmée est déjà passée. Veuillez choisir un créneau futur.")
            else:
                diff_seconds = int((scheduled_dt - now_dt).total_seconds())
                hours, remainder = divmod(diff_seconds, 3600)
                minutes, seconds = divmod(remainder, 60)
                st.info(f"⏳ **Envoi programmé le {scheduled_dt.strftime('%d/%m/%Y à %H:%M')}** (dans environ `{hours}h {minutes}min`).")
                
                if st.button("⏰ Activer le Programmateur Automatique", type="primary", use_container_width=True):
                    countdown_placeholder = st.empty()
                    for remaining in range(diff_seconds, 0, -1):
                        h, rem = divmod(remaining, 3600)
                        m, s = divmod(rem, 60)
                        countdown_placeholder.markdown(f"⏱️ **Compte à rebours avant expédition :** `{h:02d}h {m:02d}min {s:02d}s` restant...")
                        time.sleep(1)
                    countdown_placeholder.success("⏰ Heure programmée atteinte ! Lancement de l'expédition...")
                    should_start_sending = True
            
        if should_start_sending:
            if not smtp.app_password:
                st.error("Mot de passe d'application Gmail manquant. Rendez-vous dans l'onglet Paramètres.")
            else:
                progress_bar = st.progress(0)
                status_text = st.empty()
                live_stats_box = st.empty()
                
                success_count = 0
                fail_count = 0
                total_to_send = len(approved_contacts)
                
                for idx, item in enumerate(approved_contacts):
                    status_text.info(f"📤 Envoi en cours ({idx+1}/{total_to_send}) à **{item.get('name') or item['email']}** — *{item.get('company', 'N/A')}*...")
                    
                    lang = item.get("language", "fr")
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
                        item["status"] = "sent"
                        save_or_update_contact(item)
                        log_sent_email(item["email"], item["subject"], item["body"], "SUCCESS")
                        success_count += 1
                    else:
                        item["status"] = "failed"
                        save_or_update_contact(item)
                        log_sent_email(item["email"], item["subject"], item["body"], "FAILED", res.message)
                        fail_count += 1
                        
                    progress_bar.progress((idx + 1) / total_to_send)
                    live_stats_box.markdown(
                        f"📊 **Statistiques Session en Direct :** 🟢 `{success_count}` envoyés avec succès | "
                        f"🔴 `{fail_count}` échecs | ⏳ `{total_to_send - (idx + 1)}` restants à envoyer"
                    )
                    
                    # Inter-email jitter pause
                    if idx < total_to_send - 1:
                        sleep_time = random.uniform(smtp.min_delay_seconds, smtp.max_delay_seconds)
                        status_text.caption(f"⚡ Envoi continu en cours : pause de sécurité de {sleep_time:.1f}s avant le contact suivant...")
                        time.sleep(sleep_time)
                        
                st.success(f"🎉 Session d'envoi en continu terminée ! {success_count} emails envoyés avec succès ({fail_count} échecs).")
                st.session_state["show_session_report"] = True
                time.sleep(1.5)
                st.rerun()

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
# TAB 6: Paramètres & Gmail
# -------------------------------------------------------------
with tab6:
    st.header("⚙️ Configuration Gmail & Clés API")
    
    col_cfg1, col_cfg2 = st.columns(2)
    
    with col_cfg1:
        st.subheader("📧 Configuration SMTP Gmail")
        st.markdown("""
        > **Comment générer votre Mot de Passe d'Application Gmail (16 caractères) ?**
        > 1. Activez la **Validation en 2 étapes** sur votre compte Google : [Sécurité Google](https://myaccount.google.com/security)
        > 2. Rendez-vous sur : [Mots de passe des applications](https://myaccount.google.com/apppasswords)
        > 3. Entrez un nom (ex: `Outreach-App`) et cliquez sur **Créer**.
        > 4. Copiez le code de 16 lettres (ex: `abcd efgh ijkl mnop`) et collez-le ci-dessous.
        """)
        
        cfg_sender_name = st.text_input("Nom d'expéditeur", value=smtp.sender_name)
        cfg_sender_email = st.text_input("Adresse Gmail expéditrice", value=smtp.sender_email)
        cfg_app_pwd = st.text_input("Mot de passe d'application Gmail (16 caractères)", value=smtp.app_password, type="password")
        
        if st.button("🔍 Tester la connexion SMTP", type="primary"):
            smtp.sender_name = cfg_sender_name
            smtp.sender_email = cfg_sender_email
            smtp.app_password = cfg_app_pwd
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
        
        cfg_api_key = st.text_input("Clé API (Gemini / OpenAI / Groq / DeepSeek)", value=llm.api_key, type="password")
        
        if st.button("💾 Sauvegarder les paramètres API"):
            llm.api_key = cfg_api_key
            save_llm_settings(llm)
            smtp.sender_name = cfg_sender_name
            smtp.sender_email = cfg_sender_email
            smtp.app_password = cfg_app_pwd
            save_smtp_settings(smtp)
            st.success("Paramètres enregistrés avec succès !")
