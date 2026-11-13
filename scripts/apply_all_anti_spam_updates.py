import re

print("Starting complete anti-spam and clean format update...")

# ==============================================================================
# 1. UPDATE config.py
# ==============================================================================
with open("config.py", "r", encoding="utf-8") as f:
    config_code = f.read()

# Remove Ex-Président from leadership_and_awards
config_code = re.sub(
    r'\s*"Ex-Président & Team Leader du Club RoboThings[^\n]*\n',
    '\n',
    config_code
)

with open("config.py", "w", encoding="utf-8") as f:
    f.write(config_code)
print("✅ config.py updated!")

# ==============================================================================
# 2. UPDATE services/prompt_builder.py
# ==============================================================================
with open("services/prompt_builder.py", "r", encoding="utf-8") as f:
    pb_code = f.read()

# Replace leadership block in system prompt
old_leadership_pb = re.search(
    r'- Leadership & Distinctions de Compétitions :.*?- Disponibilité :',
    pb_code,
    re.DOTALL
)

if old_leadership_pb:
    new_leadership_pb = """- Leadership & Distinctions de Compétitions :
  * 1er Prix International Summer School (ENSEM / FSTM / ENSAO / FSBM) – Innovation technologique & projets émergents.
  * 2e Prix Compétition Nationale de Robotique (ENSA Khouribga / ENIM Rabat) – Systèmes autonomes & navigation.
  * 3e Prix Compétition Nationale de Robotique (EMI Rabat / ENSA El Jadida) – Défis mécatroniques de haute précision.
- RÈGLE STRICTE SUR LE STATUT : Présenter Mohammed STRICTEMENT comme élève-ingénieur en dernière année en Génie Électrique (Final-Year Electrical Engineering Student). Ne JAMAIS mentionner d'ex-présidence ou de club de robotique.
- RÈGLE ANTI-SPAM ABSOLUE (ZÉRO LIEN) : NE JAMAIS INCLURE DE LIEN WEB NI D'URL (aucun lien https://, aucun lien de portfolio ou lien cliquable dans le texte) afin de garantir une délivrabilité maximale à 100% dans la boîte de réception principale et d'éviter les filtres anti-spam d'entreprise. Mentionner simplement que le CV et le dossier de projets sont joints au message.
- Disponibilité :"""
    pb_code = pb_code[:old_leadership_pb.start()] + new_leadership_pb + pb_code[old_leadership_pb.end():]

# Replace portfolio link instruction in section 4
pb_code = re.sub(
    r'-\s*Intègre naturellement le lien vers le portfolio[^\n]*',
    '- ZÉRO LIEN DANS LE TEXTE (Délivrabilité Max) : N\'ajoute AUCUN lien hypertexte ni URL web. Indique simplement que le CV et le dossier de projets sont joints au message.',
    pb_code
)

# Update template adaptation prompt
if "Aucun Lien URL ni Mention de Club" not in pb_code:
    pb_code = pb_code.replace(
        "5. **Propreté** : Aucun crochet résiduel `[...]`, aucun doublon de phrase.",
        "5. **Propreté** : Aucun crochet résiduel `[...]`, aucun doublon de phrase.\n6. **Délivrabilité Maximale (Anti-Spam)** : Ne JAMAIS inclure de lien web, ni d'URL (aucun https://). Supprimer toute mention d'ex-président ou de club de robotique. Présenter Mohammed strictement comme élève-ingénieur en dernière année (Final-Year Engineering Student)."
    )

with open("services/prompt_builder.py", "w", encoding="utf-8") as f:
    f.write(pb_code)
print("✅ services/prompt_builder.py updated!")

# ==============================================================================
# 3. UPDATE services/llm_service.py
# ==============================================================================
with open("services/llm_service.py", "r", encoding="utf-8") as f:
    llm_code = f.read()

# Import sanitizer if not present
if "from services.email_sender import sanitize_email_body_for_deliverability" not in llm_code:
    llm_code = "from services.email_sender import sanitize_email_body_for_deliverability\n" + llm_code

# Remove portfolio link lines from fallback templates
llm_code = re.sub(r'\[Explorer mon Portfolio Interactif ↗\]\([^\)]+\)', 'Mon CV ainsi que mon dossier de projets sont joints à ce message pour votre consultation.', llm_code)
llm_code = re.sub(r'\[Explore my Interactive Portfolio ↗\]\([^\)]+\)', 'My resume and detailed project portfolio are attached to this email for your review.', llm_code)

# Pass generated bodies through sanitizer in generate_email_for_contact and generate_email_from_template
llm_code = llm_code.replace(
    'body = parsed.get("body_plain_text", parsed.get("body", "")).strip()',
    'body = sanitize_email_body_for_deliverability(parsed.get("body_plain_text", parsed.get("body", "")).strip())'
)

with open("services/llm_service.py", "w", encoding="utf-8") as f:
    f.write(llm_code)
print("✅ services/llm_service.py updated!")

# ==============================================================================
# 4. UPDATE app.py
# ==============================================================================
with open("app.py", "r", encoding="utf-8") as f:
    app_code = f.read()

# Import sanitizer in app.py if needed
if "sanitize_email_body_for_deliverability" not in app_code:
    app_code = app_code.replace(
        "from services.email_sender import (",
        "from services.email_sender import (\n    sanitize_email_body_for_deliverability,"
    )

# 4.1 Update custom reference template in Studio IA
app_code = app_code.replace(
    "Vous pouvez également consulter mon portfolio technique en ligne : https://portfolio-mohammed-hsiny-ux7z.vercel.app/",
    "Mon CV ainsi que mon dossier de projets d'ingénierie sont joints à ce message pour votre consultation."
)

# 4.2 Update live prompt default in Studio IA
app_code = app_code.replace(
    "Essaie de faire un email orienté vers l'innovation mécatronique, en citant mon robot ASRS SkyPharma et mon rôle d'Ex-Président de RoboThings.",
    "Essaie de faire un email orienté vers l'innovation mécatronique, en citant mon robot ASRS SkyPharma et mon statut d'élève-ingénieur en dernière année."
)

# 4.3 Update quick suggestion buttons in Studio IA
app_code = app_code.replace(
    'st.session_state["studio_live_prompt"] = "Rédige un email mettant en avant mon Drone Quadricoptère d\'Inspection HT (YOLOv8, ArduPilot, carbone CNC) et mon Robot Cartésien ASRS SkyPharma de dispensation de médicaments, ainsi que mon rôle d\'Ex-Président du Club RoboThings."',
    'st.session_state["studio_live_prompt"] = "Rédige un email mettant en avant mon Drone Quadricoptère d\'Inspection HT (YOLOv8, ArduPilot, carbone CNC) et mon Robot Cartésien ASRS SkyPharma de dispensation de médicaments, en tant qu\'élève-ingénieur en dernière année."'
)

# 4.4 Update Copilot prompt & welcome message in Tab 3
app_code = app_code.replace(
    "et mon rôle d'Ex-Président du Club RoboThings.",
    "en tant qu'élève-ingénieur en dernière année."
)
app_code = app_code.replace(
    "- 🏆 **Ex-Président du Club RoboThings (FSTM)** & Lauréat de 3 prix nationaux de robotique",
    "- 🏆 **Lauréat de 3 prix nationaux de robotique** (International Summer School, ENSA, EMI)"
)
app_code = app_code.replace(
    "- 🌐 [Portfolio interactif en ligne](https://portfolio-mohammed-hsiny-ux7z.vercel.app/)\n",
    ""
)
app_code = app_code.replace(
    "Portfolio en ligne : https://portfolio-mohammed-hsiny-ux7z.vercel.app/\n",
    ""
)
app_code = app_code.replace(
    "- Ex-Président & Team Leader du Club RoboThings (FSTM). (Préciser Ex-Président ou Ancien Président, pas de présidence en cours).\n",
    ""
)

# Add anti-spam directive to Copilot system prompt
if "RÈGLE ANTI-SPAM ABSOLUE (ZÉRO LIEN)" not in app_code:
    app_code = app_code.replace(
        "DIRECTIVES POUR LE COPILOTE :",
        """RÈGLE ANTI-SPAM ABSOLUE (ZÉRO LIEN) : Ne JAMAIS inclure d'URL ni de lien web dans les emails. Supprimer toute mention d'ex-président ou de club de robotique. Présenter Mohammed STRICTEMENT comme élève-ingénieur en dernière année en Génie Électrique (Final-Year Electrical Engineering Student).

DIRECTIVES POUR LE COPILOTE :"""
    )

# 4.5 Update Manual Send in Tab 4 (Sample text & sanitization)
old_manual_sample_fr = """        if is_man_fr:
            sample_body = f\"\"\"{salut_fr}

J'espère que vous allez bien.

Je suis étudiant en dernière année d'ingénierie en Génie Électrique à la FST Mohammedia, passionné par les systèmes embarqués, la robotique et les drones. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE) de 6 mois à partir de janvier 2027.

Je suis très motivé par l'idée de rejoindre {comp_disp} et je suis sincèrement inspiré par vos projets et votre expertise dans le domaine.

Je me permets de vous contacter pour savoir s'il y aurait des opportunités de stage au sein de votre équipe. Je vous joins mon CV ainsi que mon portfolio pour plus de détails.

https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Merci d'avance pour votre temps.

Bien cordialement,\"\"\""""

new_manual_sample_fr = """        if is_man_fr:
            sample_body = f\"\"\"{salut_fr}

J'espère que vous allez bien.

Je suis étudiant en dernière année d'ingénierie en Génie Électrique à la FST Mohammedia, passionné par les systèmes embarqués, la robotique et les drones. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE) de 6 mois à partir de janvier 2027.

Je suis très motivé par l'idée de rejoindre {comp_disp} et je suis sincèrement intéressé par vos projets innovants et votre expertise technique.

Je me permets de vous contacter pour savoir s'il y aurait des opportunités de stage au sein de votre équipe. Mon CV ainsi que mon dossier de projets d'ingénierie sont joints à ce message pour votre consultation.

Merci d'avance pour votre temps et votre considération.

Bien cordialement,\"\"\""""

if old_manual_sample_fr in app_code:
    app_code = app_code.replace(old_manual_sample_fr, new_manual_sample_fr)
    print("Replaced manual sample FR")

old_manual_sample_en = """        else:
            sample_body = f\"\"\"{salut_en}

I hope you are doing well.

I am a final-year Electrical Engineering student at FSTM, passionate about embedded systems, robotics, and autonomous drones. I am based in Morocco and currently preparing my 6-month graduation internship (PFE) starting January 2027.

I am genuinely motivated by the prospect of contributing to {comp_disp} and deeply inspired by your innovative engineering projects.

I would be honored to explore internship opportunities within your team. I have attached my resume and project portfolio for your review.

https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Thank you very much for your time and consideration.

Best regards,\"\"\""""

new_manual_sample_en = """        else:
            sample_body = f\"\"\"{salut_en}

I hope you are doing well.

I am a final-year Electrical Engineering student at FSTM, passionate about embedded systems, robotics, and autonomous drones. I am based in Morocco and currently preparing my 6-month graduation internship (PFE) starting January 2027.

I am genuinely motivated by the prospect of contributing to {comp_disp} and deeply inspired by your innovative engineering projects.

I would be honored to explore internship opportunities within your team. My resume and engineering project dossier are attached to this message for your review.

Thank you very much for your time and consideration.

Best regards,\"\"\""""

if old_manual_sample_en in app_code:
    app_code = app_code.replace(old_manual_sample_en, new_manual_sample_en)
    print("Replaced manual sample EN")

# 4.6 Manual send HTML preview: disable logo and CID
app_code = app_code.replace(
    """        # Build professional HTML
        html_rendered = build_professional_html(
            body_text=final_preview_body,
            profile=profile,
            language=man_lang,
            include_logo=True
        )""",
    """        # Build professional clean HTML (Zero Links, Zero Spam Triggers)
        html_rendered = build_professional_html(
            body_text=final_preview_body,
            profile=profile,
            language=man_lang,
            include_logo=False
        )"""
)

# 4.7 Send single email in manual mode: sanitize body strictly
app_code = app_code.replace(
    """            with st.spinner(f"Expédition de l'email avec design HTML vers {man_email}..."):
                res_send = send_single_email(
                    settings=smtp,
                    recipient_email=man_email.strip(),
                    subject=final_preview_subj.strip(),
                    body_text=final_preview_body,
                    attachment_paths=man_attachments,
                    profile=profile,
                    language=man_lang
                )""",
    """            clean_manual_body = sanitize_email_body_for_deliverability(final_preview_body)
            with st.spinner(f"Expédition de l'email avec design épuré vers {man_email}..."):
                res_send = send_single_email(
                    settings=smtp,
                    recipient_email=man_email.strip(),
                    subject=final_preview_subj.strip(),
                    body_text=clean_manual_body,
                    attachment_paths=man_attachments,
                    profile=profile,
                    language=man_lang
                )"""
)

# 4.8 Replace "Signature RoboThings" label
app_code = app_code.replace("Signature RoboThings", "Signature Pro Épurée")

# 4.9 Add 1-Click "Nettoyer TOUS les emails de la base" button in Tab 3 (Revue & Édition)
btn_cleanup_marker = 'if st.button("⚡ Remplacer l\'Objet de TOUS les contacts de la base par ce format", key="btn_apply_obj_to_all_db"):'
if btn_cleanup_marker in app_code and "btn_clean_all_emails_antispam" not in app_code:
    cleanup_code = '''            if st.button("🧹 Nettoyer TOUS les Emails de la base (Supprimer liens & mentions club pour délivrabilité max)", key="btn_clean_all_emails_antispam"):
                all_cts = get_all_contacts()
                up_cnt = 0
                for c in all_cts:
                    if c.get("body"):
                        c["body"] = sanitize_email_body_for_deliverability(c["body"])
                    save_or_update_contact(c)
                    up_cnt += 1
                st.success(f"🎉 Les emails des {up_cnt} contacts ont été nettoyés (Zéro lien, Zéro mention club, délivrabilité maximale) !")
                time.sleep(1.0)
                st.rerun()

'''
    app_code = app_code.replace(btn_cleanup_marker, cleanup_code + "            " + btn_cleanup_marker)

with open("app.py", "w", encoding="utf-8") as f:
    f.write(app_code)
print("✅ app.py updated!")

print("All anti-spam & clean format updates applied successfully!")
