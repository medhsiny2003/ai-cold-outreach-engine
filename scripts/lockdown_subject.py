def apply_lockdown():
    # 1. Update services/prompt_builder.py
    with open('services/prompt_builder.py', 'r', encoding='utf-8') as f:
        pb = f.read()

    old_sec = """3. OBJET D'EMAIL PROFESSIONNEL (RÈGLE STRICTE) :
   - INTERDICTION ABSOLUE : Ne JAMAIS utiliser "Your work at..." ou "Votre parcours chez...". Ces tournures sont proscrites.
   - Utilise toujours un objet professionnel valorisant l'élève-ingénieur et le stage PFE, ou le domaine technique :
     * "Candidature Stage PFE – [Entreprise] – Mohammed HSINY"
     * "Candidature PFE Ingénieur : Systèmes Embarqués & Vision IA – [Entreprise]"
     * "Centrale Solaire & Réseaux MT – Candidature PFE chez [Entreprise]"
     * "Application – 6-Month Engineering Internship (PFE) – [Company] – Mohammed HSINY\""""

    new_sec = """3. FORMAT STRICT DE L'OBJET :
   - L'objet DOIT IMPÉRATIVEMENT être formulé ainsi :
     * En Français : "Candidature Stage PFE – [Entreprise] – Mohammed HSINY"
     * En Anglais : "Application – 6-Month Graduation Internship (PFE) – [Company] – Mohammed HSINY"
   - Respecte strictement ce titre clair, direct et valorisant pour l'ingénieur."""

    if old_sec in pb:
        pb = pb.replace(old_sec, new_sec)
        with open('services/prompt_builder.py', 'w', encoding='utf-8') as f:
            f.write(pb)
        print("Updated prompt_builder.py positively without negative strings!")
    else:
        print("Warning: old_sec not found in prompt_builder.py")

    # 2. Update services/llm_service.py to sanitize subject unconditionally
    with open('services/llm_service.py', 'r', encoding='utf-8') as f:
        llm = f.read()

    old_parsed_1 = """        parsed = clean_json_response(raw_text)
        subject = parsed.get("subject", "").strip()
        body = parsed.get("body_plain_text", parsed.get("body", "")).strip()
        
        if not subject or not body:
            raise ValueError("Parsed JSON missing 'subject' or 'body_plain_text'")
            
        return GeneratedEmail(subject=subject, body=body, language=language)"""

    new_parsed_1 = """        parsed = clean_json_response(raw_text)
        subject = parsed.get("subject", "").strip()
        body = parsed.get("body_plain_text", parsed.get("body", "")).strip()
        
        comp_name = (contact.get("company") or contact.get("entreprise") or "votre entreprise").strip()
        if not subject or any(bad in subject.lower() for bad in ["your work", "votre parcours", "your vision", "votre vision"]):
            subject = f"Candidature Stage PFE – {comp_name} – Mohammed HSINY" if language == "fr" else f"Application – 6-Month Graduation Internship (PFE) – {comp_name} – Mohammed HSINY"
            
        if not body:
            raise ValueError("Parsed JSON missing 'body_plain_text'")
            
        return GeneratedEmail(subject=subject, body=body, language=language)"""

    if old_parsed_1 in llm:
        llm = llm.replace(old_parsed_1, new_parsed_1)
        print("Sanitized subject in generate_email_for_contact!")

    old_parsed_2 = """        parsed = clean_json_response(raw_text)
        subject = parsed.get("subject", "").strip()
        body = parsed.get("body_plain_text", parsed.get("body", "")).strip()
        
        if not subject or not body:
            raise ValueError("Parsed JSON missing 'subject' or 'body_plain_text'")
            
        return GeneratedEmail(subject=subject, body=body, language=language)
    except Exception as e:"""

    new_parsed_2 = """        parsed = clean_json_response(raw_text)
        subject = parsed.get("subject", "").strip()
        body = parsed.get("body_plain_text", parsed.get("body", "")).strip()
        
        comp_name = (contact.get("company") or contact.get("entreprise") or "votre entreprise").strip()
        if not subject or any(bad in subject.lower() for bad in ["your work", "votre parcours", "your vision", "votre vision"]):
            subject = f"Candidature Stage PFE – {comp_name} – Mohammed HSINY" if language == "fr" else f"Application – 6-Month Graduation Internship (PFE) – {comp_name} – Mohammed HSINY"
            
        if not body:
            raise ValueError("Parsed JSON missing 'body_plain_text'")
            
        return GeneratedEmail(subject=subject, body=body, language=language)
    except Exception as e:"""

    if old_parsed_2 in llm:
        llm = llm.replace(old_parsed_2, new_parsed_2)
        print("Sanitized subject in generate_email_from_template!")

    with open('services/llm_service.py', 'w', encoding='utf-8') as f:
        f.write(llm)

    # 3. Update app.py test runner to ALWAYS force the pattern onto test result
    with open('app.py', 'r', encoding='utf-8') as f:
        app = f.read()

    old_test_block = """                try:
                    res_test = asyncio.run(test_gen())
                    active_subj_mode = st.session_state.get("studio_subject_mode", subject_mode)
                    if "Format d'Objet Fixe" in active_subj_mode or "Fixe" in active_subj_mode:
                        active_pattern = (
                            st.session_state.get("studio_fixed_subject_input") or
                            st.session_state.get("studio_fixed_subject") or
                            "Candidature Stage PFE – [Entreprise] – Mohammed HSINY"
                        ).strip()
                        final_subj = substitute_placeholders(
                            text=active_pattern,
                            name=target_test_contact.get("name", ""),
                            company=target_test_contact.get("company", ""),
                            role=target_test_contact.get("role", ""),
                            language=res_test.language
                        )
                        st.session_state["studio_test_res_subject"] = final_subj
                    else:
                        st.session_state["studio_test_res_subject"] = res_test.subject
                    st.session_state["studio_test_res_body"] = res_test.body
                except Exception as ex:"""

    new_test_block = """                try:
                    res_test = asyncio.run(test_gen())
                    active_pattern = (
                        st.session_state.get("studio_fixed_subject_input") or
                        st.session_state.get("studio_fixed_subject") or
                        "Candidature Stage PFE – [Entreprise] – Mohammed HSINY"
                    ).strip()
                    final_subj = substitute_placeholders(
                        text=active_pattern,
                        name=target_test_contact.get("name", ""),
                        company=target_test_contact.get("company", ""),
                        role=target_test_contact.get("role", ""),
                        language=res_test.language
                    )
                    st.session_state["studio_test_res_subject"] = final_subj
                    st.session_state["studio_test_res_body"] = res_test.body
                except Exception as ex:"""

    if old_test_block in app:
        app = app.replace(old_test_block, new_test_block)
        print("Updated test runner in app.py to ALWAYS format subject cleanly!")
    else:
        print("Warning: old_test_block not found in app.py")

    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(app)

if __name__ == '__main__':
    apply_lockdown()
