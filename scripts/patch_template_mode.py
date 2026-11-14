import re

print("Patching template mode and robust placeholder substitutions...")

# ==============================================================================
# 1. UPDATE services/prompt_builder.py
# ==============================================================================
with open("services/prompt_builder.py", "r", encoding="utf-8") as f:
    pb_code = f.read()

new_substitute_placeholders = '''def substitute_placeholders(
    text: str,
    name: str = "",
    company: str = "",
    role: str = "",
    language: str = "fr"
) -> str:
    """
    Remplace 100% des balises de façon ultra-robuste :
    [Entreprise], {Entreprise}, {{Entreprise}}, <Entreprise>, [Nom Entreprise], [Société], [Company], etc.
    Ainsi que [Prénom], [Nom], [Poste].
    """
    if not text:
        return ""
    
    clean_name = (name or "").strip()
    first_name = ""
    if clean_name and clean_name.lower() not in ["madame, monsieur", "madame monsieur", "n/a", "none"]:
        parts = clean_name.split()
        first_name = parts[0].capitalize()
        
    salutation_name = first_name if first_name else ("Madame, Monsieur" if language == "fr" else "Hiring Team")
    
    clean_company = (company or "").strip()
    if not clean_company or clean_company.lower() in ["votre entreprise", "n/a", "none", "null", "[entreprise]", "{entreprise}", "company"]:
        clean_company = "votre entreprise" if language == "fr" else "your company"
        
    clean_role = (role or "").strip()
    if not clean_role:
        clean_role = "Responsable" if language == "fr" else "Hiring Manager"

    result = text

    # 1. Traitement intelligent des salutations "Bonjour [Prénom]," quand le prénom est absent
    if not first_name:
        result = re.sub(r'^(?:Bonjour|Bonsoir)\s+\[\s*(?:Prénom|Prenom|First\s*Name)\s*\]\s*,', 'Bonjour,', result, flags=re.IGNORECASE | re.MULTILINE)
        result = re.sub(r'^(?:Hi|Hello)\s+\[\s*(?:Prénom|Prenom|First\s*Name)\s*\]\s*,', 'Hello,', result, flags=re.IGNORECASE | re.MULTILINE)

    # 2. Remplacement exhaustif des balises Entreprise / Société / Company
    company_regexes = [
        r'\\[\\s*(?:nom\\s+(?:de\\s+(?:l[\\\'’]|la\\s+)?)?)?(?:entreprise|société|societe|company|organisme|organization|boîte|boite|structure)(?:\\s+(?:cible|target|name))?\\s*\\]',
        r'\\{\\{?\\s*(?:nom\\s+(?:de\\s+(?:l[\\\'’]|la\\s+)?)?)?(?:entreprise|société|societe|company|organisme|organization|boîte|boite|structure)(?:\\s+(?:cible|target|name))?\\s*\\}?}',
        r'<\\s*(?:nom\\s+(?:de\\s+(?:l[\\\'’]|la\\s+)?)?)?(?:entreprise|société|societe|company|organisme|organization|boîte|boite|structure)(?:\\s+(?:cible|target|name))?\\s*>',
        r'%\\s*(?:entreprise|company|societe|société)\\s*%'
    ]
    for c_reg in company_regexes:
        result = re.sub(c_reg, clean_company, result, flags=re.IGNORECASE)

    # 3. Remplacement exhaustif des balises Prénom / First Name
    firstname_regexes = [
        r'\\[\\s*(?:prénom|prenom|first\\s*name|firstname)\\s*\\]',
        r'\\{\\{?\\s*(?:prénom|prenom|first\\s*name|firstname)\\s*\\}?}',
        r'<\\s*(?:prénom|prenom|first\\s*name|firstname)\\s*>'
    ]
    fn_replacement = first_name if first_name else ("" if "bonjour" in result.lower() else salutation_name)
    for fn_reg in firstname_regexes:
        result = re.sub(fn_reg, fn_replacement, result, flags=re.IGNORECASE)

    # Nettoyage d'espaces doubles ou virgules orphelines
    result = re.sub(r'Bonjour\\s+,', 'Bonjour,', result, flags=re.IGNORECASE)
    result = re.sub(r'Hi\\s+,', 'Hello,', result, flags=re.IGNORECASE)
    result = re.sub(r'Hello\\s+,', 'Hello,', result, flags=re.IGNORECASE)

    # 4. Remplacement exhaustif des balises Nom complet / Last Name
    name_regexes = [
        r'\\[\\s*(?:nom\\s+complet|full\\s*name|last\\s*name|lastname|nom)\\s*\\]',
        r'\\{\\{?\\s*(?:nom\\s+complet|full\\s*name|last\\s*name|lastname|nom)\\s*\\}?}',
        r'<\\s*(?:nom\\s+complet|full\\s*name|last\\s*name|lastname|nom)\\s*>'
    ]
    for n_reg in name_regexes:
        result = re.sub(n_reg, clean_name if clean_name else salutation_name, result, flags=re.IGNORECASE)

    # 5. Remplacement exhaustif des balises Poste / Titre / Role
    role_regexes = [
        r'\\[\\s*(?:poste|titre|rôle|role|title|job\\s*title)\\s*\\]',
        r'\\{\\{?\\s*(?:poste|titre|rôle|role|title|job\\s*title)\\s*\\}?}',
        r'<\\s*(?:poste|titre|rôle|role|title|job\\s*title)\\s*>'
    ]
    for r_reg in role_regexes:
        result = re.sub(r_reg, clean_role, result, flags=re.IGNORECASE)

    return result'''

old_sub_match = re.search(r'def substitute_placeholders\(.*?\n    return result\n', pb_code, re.DOTALL)
if old_sub_match:
    pb_code = pb_code[:old_sub_match.start()] + new_substitute_placeholders + pb_code[old_sub_match.end():]
    print("Updated substitute_placeholders in services/prompt_builder.py")

with open("services/prompt_builder.py", "w", encoding="utf-8") as f:
    f.write(pb_code)

# ==============================================================================
# 2. UPDATE services/contact_manager.py
# ==============================================================================
with open("services/contact_manager.py", "r", encoding="utf-8") as f:
    cm_code = f.read()

cm_code = cm_code.replace(
    '"company": ["company", "entreprise", "societe", "société", "boite", "boîte", "organization", "organisation", "structure"],',
    '"company": ["company", "company name", "nom entreprise", "nom de l\'entreprise", "nom de la société", "entreprise", "societe", "société", "société / entreprise", "entreprise cible", "société cible", "compagnie", "boite", "boîte", "organization", "organisation", "structure", "employeur", "employer", "account", "account name", "client"],'
)

with open("services/contact_manager.py", "w", encoding="utf-8") as f:
    f.write(cm_code)
print("Updated company column priorities in services/contact_manager.py")

# ==============================================================================
# 3. UPDATE services/llm_service.py
# ==============================================================================
with open("services/llm_service.py", "r", encoding="utf-8") as f:
    llm_code = f.read()

# Add substitute_placeholders to imports in llm_service
if "substitute_placeholders" not in llm_code:
    llm_code = llm_code.replace(
        "from services.prompt_builder import (",
        "from services.prompt_builder import (\n    substitute_placeholders,"
    )

# Update adapt_template_offline to always clean and substitute
old_adapt_match = re.search(r'def adapt_template_offline\(.*?\n    return GeneratedEmail\(subject=subject, body=body, language=language\)', llm_code, re.DOTALL)
if old_adapt_match:
    new_adapt = '''def adapt_template_offline(template_text: str, contact: Dict[str, Any], profile: CandidateProfile, language: str) -> GeneratedEmail:
    """Smart offline template adaptation with 100% guaranteed variable substitution and zero freezing."""
    if not template_text or not template_text.strip():
        return generate_fallback_template(contact, profile, language)
        
    first_name = (contact.get("first_name") or contact.get("prenom") or "").strip()
    name = (contact.get("name") or contact.get("nom") or "").strip()
    if not first_name and name:
        first_name = name.split()[0].capitalize()
    salutation_name = first_name if first_name else "Madame, Monsieur"
    
    company = (contact.get("company") or contact.get("entreprise") or contact.get("societe") or contact.get("société") or "").strip()
    if not company or company.lower() in ["votre entreprise", "n/a", "none", "null"]:
        company = "votre entreprise" if language == "fr" else "your company"
        
    role = (contact.get("role") or contact.get("poste") or "").strip()
    industry = (contact.get("industry") or contact.get("secteur") or "").strip()
    persona = classify_role_category(role)
    
    # Check if template contains multiple persona sections (CEO / RH / Ingénieur)
    text = template_text
    lower_text = text.lower()
    if "version pour un" in lower_text or "version ceo" in lower_text or "version rh" in lower_text or "version ingénieur" in lower_text:
        if persona == "CEO_DIRECTEUR":
            match = re.search(r"(?:version\\s+pour\\s+(?:un\\s+)?(?:ceo|directeur|fondateur)[^\\n]*\\n)(.*?)(?=(?:📧|📝|\\*|\\#)?\\s*version|\\Z)", text, flags=re.IGNORECASE | re.DOTALL)
            if match and match.group(1).strip():
                text = match.group(1).strip()
        elif persona == "RH_TALENT":
            match = re.search(r"(?:version\\s+pour\\s+(?:un\\s+)?(?:rh|recruteur|talent)[^\\n]*\\n)(.*?)(?=(?:📧|📝|\\*|\\#)?\\s*version|\\Z)", text, flags=re.IGNORECASE | re.DOTALL)
            if match and match.group(1).strip():
                text = match.group(1).strip()
        else:
            match = re.search(r"(?:version\\s+pour\\s+(?:un\\s+)?(?:ingénieur|ingenieur|tech|lead|r&d)[^\\n]*\\n)(.*?)(?=(?:📧|📝|\\*|\\#)?\\s*version|\\Z)", text, flags=re.IGNORECASE | re.DOTALL)
            if match and match.group(1).strip():
                text = match.group(1).strip()

    # Dynamic Variable Replacements on full text
    text = substitute_placeholders(text, name=name, company=company, role=role, language=language)
        
    # Replace static greeting like "Bonjour Bruno," with current contact's salutation
    text = re.sub(r"^(?:Bonjour|Bonsoir|Hi|Hello)\\s+[A-Za-zÀ-ÿ-]+,", f"Bonjour {salutation_name}," if language == 'fr' else f"Hi {salutation_name},", text, flags=re.MULTILINE)
    
    # Replace previous static company names if company is different
    if company and company.lower() not in ["shark robotics", "votre entreprise", "your company"]:
        text = re.sub(r"\\b(?:Shark\\s+Robotics|Entreprise\\s+Cible)\\b", company, text, flags=re.IGNORECASE)
        
    # Extract Subject Line
    theme = detect_best_theme_for_company(company, role, industry)
    subject = get_target_subject(persona, theme=theme, company=company, language=language)
    
    lines = text.split("\\n")
    body_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith(("objet :", "objet:", "subject :", "subject:")):
            extracted_subj = re.sub(r"^(?:objet|subject)\\s*:\\s*", "", stripped, flags=re.IGNORECASE).strip()
            if extracted_subj:
                extracted_subj = substitute_placeholders(extracted_subj, name=name, company=company, role=role, language=language)
                extracted_subj = re.sub(r"\\b(?:Shark\\s+Robotics|Entreprise\\s+Cible)\\b", company, extracted_subj, flags=re.IGNORECASE)
                subject = extracted_subj
        elif stripped.lower() in ["text", "```", "```text", "```markdown"]:
            continue
        else:
            body_lines.append(line)
            
    body = "\\n".join(body_lines).strip()
    body = sanitize_email_body_for_deliverability(body)
    # Guaranteed final pass for placeholders
    body = substitute_placeholders(body, name=name, company=company, role=role, language=language)
    subject = substitute_placeholders(subject, name=name, company=company, role=role, language=language)
    return GeneratedEmail(subject=subject, body=body, language=language)'''
    llm_code = llm_code[:old_adapt_match.start()] + new_adapt + llm_code[old_adapt_match.end():]
    print("Updated adapt_template_offline in services/llm_service.py")

# Update generate_email_from_template to have 12s timeout and post-substitution
old_gen_template_match = re.search(r'async def generate_email_from_template\(.*?\n        return adapt_template_offline\(template_text, contact, profile, language\)', llm_code, re.DOTALL)
if old_gen_template_match:
    new_gen_template = '''async def generate_email_from_template(
    template_text: str,
    contact: Dict[str, Any],
    profile: CandidateProfile,
    settings: LLMSettings,
    forced_lang: Optional[str] = None,
    custom_instruction: str = ""
) -> GeneratedEmail:
    """Adapts a user-provided template text to a specific contact using LLM with strict 12s timeout and guaranteed substitution."""
    language = determine_language(contact, forced_lang)
    
    if not settings.api_key and settings.provider != "ollama":
        return adapt_template_offline(template_text, contact, profile, language)
        
    system_prompt = build_template_adaptation_system_prompt()
    user_prompt = build_template_adaptation_user_prompt(
        template_text=template_text,
        contact=contact,
        profile=profile,
        language=language,
        custom_instruction=custom_instruction
    )
    
    import asyncio
    
    async def _call_llm_worker():
        if settings.provider == "gemini":
            return await call_gemini_api(
                api_key=settings.api_key,
                model_name=settings.model_name or "gemini-3.5-flash",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=settings.temperature
            )
        elif settings.provider == "openai":
            base_url = settings.api_base_url or "https://api.openai.com/v1"
            return await call_openai_compatible_api(
                base_url=base_url,
                api_key=settings.api_key,
                model_name=settings.model_name or "gpt-4o-mini",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=settings.temperature
            )
        elif settings.provider == "groq":
            base_url = settings.api_base_url or "https://api.groq.com/openai/v1"
            return await call_openai_compatible_api(
                base_url=base_url,
                api_key=settings.api_key,
                model_name=settings.model_name or "llama-3.3-70b-versatile",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=settings.temperature
            )
        elif settings.provider == "deepseek":
            base_url = settings.api_base_url or "https://api.deepseek.com"
            return await call_openai_compatible_api(
                base_url=base_url,
                api_key=settings.api_key,
                model_name=settings.model_name or "deepseek-chat",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=settings.temperature
            )
        elif settings.provider == "ollama":
            base_url = settings.api_base_url or "http://localhost:11434/v1"
            return await call_openai_compatible_api(
                base_url=base_url,
                api_key="ollama",
                model_name=settings.model_name or "llama3.2",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=settings.temperature
            )
        elif settings.provider == "openrouter":
            base_url = settings.api_base_url or "https://openrouter.ai/api/v1"
            return await call_openai_compatible_api(
                base_url=base_url,
                api_key=settings.api_key,
                model_name=settings.model_name or "meta-llama/llama-3.3-70b-instruct",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=settings.temperature
            )
        else:
            raise ValueError(f"Unknown provider: {settings.provider}")

    try:
        # Strict 12s timeout to prevent freezing
        raw_text = await asyncio.wait_for(_call_llm_worker(), timeout=12.0)
            
        parsed = clean_json_response(raw_text)
        subject = parsed.get("subject", "").strip()
        body = sanitize_email_body_for_deliverability(parsed.get("body_plain_text", parsed.get("body", "")).strip())
        
        comp_name = (contact.get("company") or contact.get("entreprise") or contact.get("societe") or "votre entreprise").strip()
        if not subject or any(bad in subject.lower() for bad in ["your work", "votre parcours", "your vision", "votre vision"]):
            subject = f"Candidature Stage PFE – {comp_name} – Mohammed HSINY" if language == "fr" else f"Application – 6-Month Graduation Internship (PFE) – {comp_name} – Mohammed HSINY"
            
        if not body:
            raise ValueError("Parsed JSON missing 'body_plain_text'")
            
        # GUARANTEED POST-SUBSTITUTION: Ensure no bracket survived LLM output
        body = substitute_placeholders(
            text=body,
            name=contact.get("name", ""),
            company=comp_name,
            role=contact.get("role", ""),
            language=language
        )
        subject = substitute_placeholders(
            text=subject,
            name=contact.get("name", ""),
            company=comp_name,
            role=contact.get("role", ""),
            language=language
        )
            
        return GeneratedEmail(subject=subject, body=body, language=language)
    except Exception as e:
        print(f"[LLM Template Warning] Adapting template failed/timed out for {contact.get('email')}: {e}. Using instant offline replacement.")
        return adapt_template_offline(template_text, contact, profile, language)'''
    llm_code = llm_code[:old_gen_template_match.start()] + new_gen_template + llm_code[old_gen_template_match.end():]
    print("Updated generate_email_from_template in services/llm_service.py")

with open("services/llm_service.py", "w", encoding="utf-8") as f:
    f.write(llm_code)

# ==============================================================================
# 4. UPDATE app.py
# ==============================================================================
with open("app.py", "r", encoding="utf-8") as f:
    app_code = f.read()

# Update substitute_placeholders fallback in app.py
old_app_sub = re.search(r'def substitute_placeholders\(text, name="", company="", role="", language="fr"\):.*?return t\n', app_code, re.DOTALL)
if old_app_sub:
    new_app_sub = '''def substitute_placeholders(text, name="", company="", role="", language="fr"):
        try:
            from services.prompt_builder import substitute_placeholders as _sp
            return _sp(text, name=name, company=company, role=role, language=language)
        except Exception:
            c = company or "votre entreprise"
            n = name or ""
            fn = n.split()[0] if n else ""
            import re
            t = re.sub(r'\\[\\s*(?:nom\\s+(?:de\\s+l[\'’]?)?)?(?:entreprise|société|societe|company)\\s*\\]', c, text, flags=re.I)
            t = re.sub(r'\\{\\{?(?:nom\\s+(?:de\\s+l[\'’]?)?)?(?:entreprise|société|societe|company)\\}?\\}', c, t, flags=re.I)
            t = re.sub(r'\\[\\s*(?:prénom|prenom)\\s*\\]', fn if fn else "", t, flags=re.I)
            t = re.sub(r'Bonjour\\s+,', 'Bonjour,', t, flags=re.I)
            return t
'''
    app_code = app_code[:old_app_sub.start()] + new_app_sub + app_code[old_app_sub.end():]
    print("Updated substitute_placeholders in app.py fallback")

# Make sure adapt_template_offline is imported in app.py
if "adapt_template_offline" not in app_code:
    app_code = app_code.replace(
        "from services.llm_service import generate_email_for_contact, generate_email_from_template, GeneratedEmail",
        "from services.llm_service import generate_email_for_contact, generate_email_from_template, GeneratedEmail, adapt_template_offline"
    )

# Add Mode 2 sub-mode radio button in app.py
target_m2_header = """        # Mode 2: Modèle / Template Sur-Mesure
        with col_g2:
            lang_mode = st.selectbox("""

replacement_m2_header = """        # Mode 2: Modèle / Template Sur-Mesure
        st.info("💡 **Mode Modèle / Template Actif :** Vos emails conserveront fidèlement votre texte en remplaçant automatiquement `[Entreprise]`, `[Prénom]`, etc. pour chaque destinataire.")
        
        col_m2_opt1, col_m2_opt2 = st.columns([1.8, 1.2])
        with col_m2_opt1:
            template_sub_mode = st.radio(
                "⚡ Méthode d'application de votre modèle :",
                [
                    "⚡ Remplacement Direct & Instantané (Recommandé : 0 seconde d'attente, Zéro blocage, 100% Garanti)",
                    "🤖 Adaptation & Contextualisation IA (L'IA contextualise les phrases selon l'activité de l'entreprise)"
                ],
                index=0,
                key="studio_template_sub_mode",
                help="Le mode Direct remplace instantanément [Entreprise] et vos balises sans appel API (idéal pour 50+ contacts sans jamais se bloquer)."
            )
        with col_m2_opt2:
            lang_mode = st.selectbox("""

if target_m2_header in app_code:
    app_code = app_code.replace(target_m2_header, replacement_m2_header)
    print("Added template_sub_mode radio in app.py")

# Update Studio test button to test template when Mode 2 is selected
target_test_btn = """        if st.button("🚀 Tester & Générer la Prévisualisation", type="secondary", key="btn_run_studio_test"):
            with st.spinner("L'IA génère votre essai..."):
                async def test_gen():
                    return await generate_email_for_contact(
                        contact=target_test_contact,
                        profile=profile,
                        settings=llm,
                        forced_lang=forced_lang,
                        theme=selected_theme_key if "Mode 1" in gen_mode else "auto",
                        custom_instruction=live_user_order,
                        tone=selected_style_key if "Mode 1" in gen_mode else "persuasive_tech"
                    )"""

replacement_test_btn = """        if st.button("🚀 Tester & Générer la Prévisualisation", type="secondary", key="btn_run_studio_test"):
            with st.spinner("Génération de l'essai en direct..."):
                async def test_gen():
                    if "Mode 2" in gen_mode:
                        is_direct = "Direct" in st.session_state.get("studio_template_sub_mode", "Direct")
                        if is_direct:
                            return adapt_template_offline(
                                template_text=custom_template_text,
                                contact=target_test_contact,
                                profile=profile,
                                language=forced_lang or "fr"
                            )
                        else:
                            return await generate_email_from_template(
                                template_text=custom_template_text,
                                contact=target_test_contact,
                                profile=profile,
                                settings=llm,
                                forced_lang=forced_lang,
                                custom_instruction=live_user_order
                            )
                    else:
                        return await generate_email_for_contact(
                            contact=target_test_contact,
                            profile=profile,
                            settings=llm,
                            forced_lang=forced_lang,
                            theme=selected_theme_key,
                            custom_instruction=live_user_order,
                            tone=selected_style_key
                        )"""

if target_test_btn in app_code:
    app_code = app_code.replace(target_test_btn, replacement_test_btn)
    print("Updated Studio test button for Mode 2 in app.py")

# Update run_batch in app.py to respect Direct Mode 2 and post-substitute
target_batch_m2 = """                        if "Mode 1" in gen_mode:
                            res = await generate_email_for_contact(
                                contact=contact,
                                profile=profile,
                                settings=llm,
                                forced_lang=forced_lang,
                                theme=selected_theme_key,
                                custom_instruction=effective_directive,
                                tone=selected_style_key
                            )
                        else:
                            res = await generate_email_from_template(
                                template_text=custom_template_text,
                                contact=contact,
                                profile=profile,
                                settings=llm,
                                forced_lang=forced_lang,
                                custom_instruction=effective_directive
                            )"""

replacement_batch_m2 = """                        if "Mode 1" in gen_mode:
                            res = await generate_email_for_contact(
                                contact=contact,
                                profile=profile,
                                settings=llm,
                                forced_lang=forced_lang,
                                theme=selected_theme_key,
                                custom_instruction=effective_directive,
                                tone=selected_style_key
                            )
                        else:
                            is_direct_tpl = "Direct" in st.session_state.get("studio_template_sub_mode", "Direct")
                            if is_direct_tpl:
                                res = adapt_template_offline(
                                    template_text=custom_template_text,
                                    contact=contact,
                                    profile=profile,
                                    language=forced_lang or contact.get("language", "fr")
                                )
                            else:
                                res = await generate_email_from_template(
                                    template_text=custom_template_text,
                                    contact=contact,
                                    profile=profile,
                                    settings=llm,
                                    forced_lang=forced_lang,
                                    custom_instruction=effective_directive
                                )"""

if target_batch_m2 in app_code:
    app_code = app_code.replace(target_batch_m2, replacement_batch_m2)
    print("Updated batch generation for Mode 2 in app.py")

# Ensure post-substitution on body in run_batch
target_save_body = """                        contact["body"] = res.body
                        contact["language"] = res.language"""

replacement_save_body = """                        # Guaranteed final placeholder substitution on body
                        contact["body"] = substitute_placeholders(
                            text=res.body,
                            name=contact.get("name", ""),
                            company=contact.get("company", ""),
                            role=contact.get("role", ""),
                            language=res.language
                        )
                        contact["language"] = res.language"""

if target_save_body in app_code:
    app_code = app_code.replace(target_save_body, replacement_save_body)
    print("Added guaranteed body placeholder substitution to run_batch")

with open("app.py", "w", encoding="utf-8") as f:
    f.write(app_code)

print("Patching completed successfully!")
