def enhance():
    # 1. Update services/prompt_builder.py to add the strict anti-"your work" rule to the LLM system prompt
    with open('services/prompt_builder.py', 'r', encoding='utf-8') as f:
        pb = f.read()

    anti_rule = """3. OBJET D'EMAIL PROFESSIONNEL (RÈGLE STRICTE) :
   - INTERDICTION ABSOLUE : Ne JAMAIS utiliser "Your work at..." ou "Votre parcours chez...". Ces tournures sont proscrites.
   - Utilise toujours un objet professionnel valorisant l'élève-ingénieur et le stage PFE, ou le domaine technique :
     * "Candidature Stage PFE – [Entreprise] – Mohammed HSINY"
     * "Candidature PFE Ingénieur : Systèmes Embarqués & Vision IA – [Entreprise]"
     * "Centrale Solaire & Réseaux MT – Candidature PFE chez [Entreprise]"
     * "Application – 6-Month Engineering Internship (PFE) – [Company] – Mohammed HSINY"
"""
    old_rule_start = "3. OBJET D'EMAIL CAPTIVANT ET NATUREL (ANTI-SPAM) :"
    if old_rule_start in pb:
        # Replace the rule section
        old_rule_full = """3. OBJET D'EMAIL CAPTIVANT ET NATUREL (ANTI-SPAM) :
   - L'objet doit être varié, court (5 à 9 mots), pertinent et intrigant.
   - Exemples : "Vos défis en robotique d'intervention chez [Entreprise] – Mohammed HSINY", "Échange technique & Portfolio – PFE Systèmes Embarqués & Drones", "Centrale Solaire & Réseaux MT – PFE Mohammed HSINY chez [Entreprise]"."""
        pb = pb.replace(old_rule_full, anti_rule)
        with open('services/prompt_builder.py', 'w', encoding='utf-8') as f:
            f.write(pb)
        print("prompt_builder.py updated with anti-'your work' strict prompt rule!")

    # 2. Update test runner in app.py
    with open('app.py', 'r', encoding='utf-8') as f:
        app_text = f.read()

    old_test_res = '''                try:
                    res_test = asyncio.run(test_gen())
                    st.session_state["studio_test_res_subject"] = res_test.subject
                    st.session_state["studio_test_res_body"] = res_test.body
                except Exception as ex:
                    st.error(f"Erreur lors de l'essai : {ex}")'''

    new_test_res = '''                try:
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
                except Exception as ex:
                    st.error(f"Erreur lors de l'essai : {ex}")'''

    if old_test_res in app_text:
        app_text = app_text.replace(old_test_res, new_test_res)
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(app_text)
        print("app.py test generator updated to honor fixed subject!")
    else:
        print("Warning: old_test_res not found in app.py")

if __name__ == '__main__':
    enhance()
