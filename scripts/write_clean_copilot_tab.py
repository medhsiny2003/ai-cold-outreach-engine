import sys

copilot_code = '''# -------------------------------------------------------------
# TAB COPILOTE IA : Discussion Directe, Ordres & Co-Rédaction
# -------------------------------------------------------------
with tab_copilot:
    st.header("💬 Copilote IA Interactif : Votre Binôme & Assistant Dédié")
    st.caption("Donnez directement vos ordres à l'IA en temps réel. Demandez-lui d'analyser une entreprise cible, d'ajuster vos emails vers le Solaire 1 MW, les Drones HT, le Robot ASRS SkyPharma ou l'Automatisme, ou de co-rédiger le message parfait.")

    contacts_list_for_copilot = get_all_contacts()

    col_cp1, col_cp2 = st.columns([1.8, 1.2])
    with col_cp1:
        st.markdown("##### 🎯 Cible ou Sujet de Discussion")
        c_opts = ["(Aucun contact particulier - Discussion générale)"]
        for c in contacts_list_for_copilot:
            c_opts.append(f"#{c.get('id')} - {c.get('name') or c.get('email')} ({c.get('company', 'Entreprise')})")
        
        selected_c_opt = st.selectbox("Sélectionner un contact de votre base à analyser :", c_opts, key="copilot_selected_contact")
        
        target_contact_info = ""
        if selected_c_opt != c_opts[0]:
            try:
                cid = int(selected_c_opt.split(" - ")[0].replace("#", ""))
                matched_c = next((c for c in contacts_list_for_copilot if c.get("id") == cid), None)
                if matched_c:
                    target_contact_info = f"Destinataire : {matched_c.get('name', 'N/A')}, Poste : {matched_c.get('role', 'N/A')}, Société : {matched_c.get('company', 'N/A')}, Secteur : {matched_c.get('industry', 'N/A')}, Email : {matched_c.get('email', '')}"
                    st.info(f"📌 **Contexte injecté :** {target_contact_info}")
            except Exception:
                pass

    with col_cp2:
        st.markdown("##### ⚡ Suggestions Rapides en 1 Clic")
        col_sug1, col_sug2 = st.columns(2)
        with col_sug1:
            if st.button("💡 5 Objets Accrocheurs", use_container_width=True, key="btn_sug_obj"):
                st.session_state.copilot_pending_prompt = f"Propose-moi 5 idées d'objets d'email très variés, percutants et naturels (sans formules robotiques) pour ma candidature PFE. {target_contact_info}"
        with col_sug2:
            if st.button("☀️ Focus Solaire 1 MW", use_container_width=True, key="btn_sug_sol"):
                st.session_state.copilot_pending_prompt = f"Rédige un email mettant en valeur mon projet d'étude et dimensionnement de la Centrale Solaire Photovoltaïque de 1 MW (PVsyst, réseaux MT/BT, onduleurs, bilan de puissance) adapté à cette entreprise : {target_contact_info or 'entreprise du secteur énergie/électrique'}"
        
        col_sug3, col_sug4 = st.columns(2)
        with col_sug3:
            if st.button("🛸 Focus Drones & ASRS", use_container_width=True, key="btn_sug_dron"):
                st.session_state.copilot_pending_prompt = f"Rédige un email mettant en avant mon Drone Quadricoptère d'Inspection HT (YOLOv8, ArduPilot, carbone CNC) et mon Robot Cartésien ASRS SkyPharma de dispensation de médicaments, ainsi que mon rôle d'Ex-Président du Club RoboThings. {target_contact_info}"
        with col_sug4:
            if st.button("🔄 Effacer Historique", use_container_width=True, key="btn_sug_clr"):
                st.session_state.copilot_messages = []
                st.rerun()

    st.markdown("---")

    # Chat Messages History
    if "copilot_messages" not in st.session_state:
        st.session_state.copilot_messages = [
            {
                "role": "assistant",
                "content": "Bonjour Mohammed ! ⚡ Je suis ton Copilote IA pour ta recherche de stage PFE (Dernière Année Génie Électrique & Contrôle Industriel à la FSTM).\\n\\nJe maîtrise l'intégralité de ton profil :\\n- ☀️ **Centrale Solaire PV 1 MW** (calpinage, onduleurs, postes MT/BT, PVsyst)\\n- 🛸 **Drone d'Inspection HT** (YOLOv8 vision IA, ArduPilot, carbone CNC)\\n- 💊 **Robot ASRS SkyPharma** (cinématique cartésienne H-Bot, SQLite/Python)\\n- 💧 **Projet Tawfir IoT** & Flotte Multi-Robots ADAS\\n- 🏆 **Ex-Président du Club RoboThings (FSTM)** & Lauréat de 3 prix nationaux de robotique\\n- 🏭 Stages OCP (Poste MT/M580), PAYPER PROD, Marsa Maroc, Ciments du Maroc\\n- 🌐 [Portfolio interactif en ligne](https://portfolio-mohammed-hsiny-ux7z.vercel.app/)\\n\\nSur quelle entreprise ou quel projet veux-tu que nous travaillions ?"
            }
        ]

    for msg in st.session_state.copilot_messages:
        with st.chat_message(msg["role"], avatar="🤖" if msg["role"] == "assistant" else "👤"):
            st.markdown(msg["content"])

    # Chat Input
    user_chat_input = st.chat_input("Donnez vos ordres au Copilote IA (ex: 'Rends le texte plus court', 'Oriente vers le solaire 1 MW', 'Adapte pour telle société')...")
    
    # Handle pending prompt from one-click buttons
    if st.session_state.get("copilot_pending_prompt"):
        user_chat_input = st.session_state.pop("copilot_pending_prompt")

    if user_chat_input:
        st.session_state.copilot_messages.append({"role": "user", "content": user_chat_input})
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_chat_input)

        with st.chat_message("assistant", avatar="🤖"):
            with st.spinner("Réflexion et exécution de votre ordre..."):
                copilot_system_prompt = """Tu es le Copilote IA personnel et mentor expert en cold outreach de Mohammed HSINY.
Mohammed est élève-ingénieur en dernière année en Génie Électrique & Contrôle Industriel (Final-Year Electrical Engineering Student) à la Faculté des Sciences et Techniques de Mohammedia (FSTM).
Il recherche un stage PFE de 6 mois à partir de Janvier 2027. Mobilité internationale totale.
Portfolio en ligne : https://portfolio-mohammed-hsiny-ux7z.vercel.app/

RÉPERTOIRE DES COMPÉTENCES & PROJETS MAJEURS DE MOHAMMED :
1. Centrale Solaire Photovoltaïque 1 MW : Étude technico-économique et dimensionnement complet d'une centrale solaire PV raccordée MT/BT, calpinage PVsyst, bilans de puissance, choix onduleurs et modélisation des pertes.
2. Drone d'Inspection HT : Châssis carbone usiné CNC, avionique ArduPilot/Pixhawk, vision IA YOLOv8 pour détection temps réel d'anomalies sur isolateurs et points chauds.
3. SkyPharma – Robot ASRS Pharmaceutique : Robot cartésien automatisé cinématique H-Bot pour l'indexation, le tri et la dispensation sécurisée de médicaments en milieu hospitalier (contrôle-commande temps réel Python/SQLite).
4. Projet Tawfir (Distribution d'Eau Intelligente & IoT) : Détection acoustique prédictive de micro-fuites invisibles sous pression (ESP32/STM32, LoRaWAN).
5. Flotte Multi-Robots Mobiles ADAS : FreeRTOS, communication maillée ultra-rapide ESP-NOW, asservissement PID et évitement d'obstacles.
6. Bras Manipulateur Robotisé 6-DOF : Modélisation SolidWorks, cinématique inverse (IK), asservissement STM32.
7. Robot Suiveur de Ligne Haute Vitesse : Asservissement PID ultra-rapide sur STM32.
8. Drone FPV Long-Range 7 pouces : Électronique ESC/BLDC, filtrage Betaflight/INAV.
9. Automatisme & Énergie Industrielle : Groupe OCP (supervision SCADA Poste MT, M580, Ignition, Sepam 80), PAYPER PROD, Marsa Maroc, Ciments du Maroc.
10. Leadership & Compétitions :
    - Ex-Président & Team Leader du Club RoboThings (FSTM). (Préciser Ex-Président ou Ancien Président, pas de présidence en cours).
    - 1er Prix International Summer School (ENSEM / FSTM / ENSAO / FSBM).
    - 2e Prix Compétition Nationale de Robotique (ENSA Khouribga / ENIM Rabat).
    - 3e Prix Compétition Nationale de Robotique (EMI Rabat / ENSA El Jadida).

DIRECTIVES POUR LE COPILOTE :
- Sois réactif aux ordres de Mohammed : s'il te demande de modifier, raccourcir, changer de ton ou orienter l'argumentation, applique immédiatement ses directives.
- Adapte immédiatement les arguments selon la cible (Solaire/Énergie -> Centrale 1 MW & OCP ; Drones/Robotique -> Drone HT YOLOv8 & SkyPharma ASRS ; Embarqué -> STM32/FreeRTOS/Tawfir ; Industrie -> Automatisme M580 & SCADA).
- Pour chaque rédaction proposée, fournis :
  1. Un objet percutant, fluide et naturel.
  2. Un corps de message aéré (paragraphes de 2-3 lignes), enthousiaste et humble.
  3. Une explication succincte de la stratégie d'argumentation choisie.
"""
                chat_history_text = ""
                for m in st.session_state.copilot_messages[-6:]:
                    chat_history_text += f"\\n[{m['role'].upper()}] : {m['content']}\\n"

                async def run_copilot_turn():
                    from services.llm_service import call_gemini_api
                    # Resilient API key resolution (Session -> DB -> Env -> Secrets)
                    active_key = (llm.api_key or "").strip()
                    if not active_key:
                        from services.storage_service import load_llm_settings
                        active_key = (load_llm_settings().api_key or "").strip()
                    if not active_key:
                        active_key = os.getenv("GEMINI_API_KEY", "").strip()
                    if not active_key:
                        raise ValueError("Aucune clé API Gemini trouvée. Veuillez renseigner votre clé dans l'onglet Paramètres.")

                    active_model = llm.model_name or "gemini-3.5-flash"
                    return await call_gemini_api(
                        api_key=active_key,
                        model_name=active_model,
                        system_prompt=copilot_system_prompt,
                        user_prompt=f"HISTORIQUE DE LA CONVERSATION :\\n{chat_history_text}\\n\\nORDRE OU DEMANDE DE MOHAMMED :\\n{user_chat_input}",
                        temperature=0.7
                    )

                try:
                    import asyncio
                    reply_text = asyncio.run(run_copilot_turn())
                except Exception as e:
                    reply_text = f"Désolé Mohammed, une erreur s'est produite lors de la connexion à l'IA : {e}"

                st.markdown(reply_text)
                st.session_state.copilot_messages.append({"role": "assistant", "content": reply_text})
'''

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx1 = text.find('# TAB COPILOTE IA')
idx2 = text.find('# TAB 4: Revue & Édition')

if idx1 != -1 and idx2 != -1:
    before = text[:idx1]
    after = text[idx2:]
    new_text = before + copilot_code + '\n\n' + after
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(new_text)
    print("app.py successfully rewritten with clean tab_copilot block!")
else:
    print("Error: Could not locate markers in app.py")
