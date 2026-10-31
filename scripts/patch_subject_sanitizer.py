import re

with open('app.py', 'r', encoding='utf-8') as f:
    code = f.read()

# 1. Sanitize studio_fixed_subject in text_input
target1 = '''        if "Format d'Objet Fixe" in subject_mode:
            studio_subject_pattern = st.text_input(
                "Modèle d'objet exact (balises : [Entreprise], [Prénom], [Nom], [Poste]) :",
                value=st.session_state.get("studio_fixed_subject", "Candidature Stage PFE – [Entreprise] – Mohammed HSINY"),
                key="studio_fixed_subject_input",
                help="Exemple : Candidature Stage PFE – [Entreprise] – Mohammed HSINY"
            )
            st.session_state["studio_fixed_subject"] = studio_subject_pattern'''

replacement1 = '''        if "Format d'Objet Fixe" in subject_mode:
            current_fixed = st.session_state.get("studio_fixed_subject", "Candidature Stage PFE – [Entreprise] – Mohammed HSINY")
            if any(b in current_fixed.lower() for b in ["your work", "votre parcours", "your vision", "votre vision"]):
                current_fixed = "Candidature Stage PFE – [Entreprise] – Mohammed HSINY"
                st.session_state["studio_fixed_subject"] = current_fixed

            studio_subject_pattern = st.text_input(
                "Modèle d'objet exact (balises : [Entreprise], [Prénom], [Nom], [Poste]) :",
                value=current_fixed,
                key="studio_fixed_subject_input",
                help="Exemple : Candidature Stage PFE – [Entreprise] – Mohammed HSINY"
            )
            if any(b in studio_subject_pattern.lower() for b in ["your work", "votre parcours", "your vision", "votre vision"]):
                studio_subject_pattern = "Candidature Stage PFE – [Entreprise] – Mohammed HSINY"
            st.session_state["studio_fixed_subject"] = studio_subject_pattern'''

assert target1 in code, "target1 not found in app.py"
code = code.replace(target1, replacement1)

# 2. Studio live test generator subject
target2 = '''                try:
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
                    st.session_state["studio_test_res_body"] = res_test.body'''

replacement2 = '''                try:
                    res_test = asyncio.run(test_gen())
                    chosen_mode = st.session_state.get("studio_subject_mode", subject_mode)
                    if "Format d'Objet Fixe" in chosen_mode or "Fixe" in chosen_mode:
                        active_pattern = (
                            st.session_state.get("studio_fixed_subject_input") or
                            st.session_state.get("studio_fixed_subject") or
                            "Candidature Stage PFE – [Entreprise] – Mohammed HSINY"
                        ).strip()
                        if any(b in active_pattern.lower() for b in ["your work", "votre parcours", "your vision", "votre vision"]):
                            active_pattern = "Candidature Stage PFE – [Entreprise] – Mohammed HSINY"
                            st.session_state["studio_fixed_subject"] = active_pattern
                        final_subj = substitute_placeholders(
                            text=active_pattern,
                            name=target_test_contact.get("name", ""),
                            company=target_test_contact.get("company", ""),
                            role=target_test_contact.get("role", ""),
                            language=res_test.language
                        )
                    else:
                        final_subj = res_test.subject

                    if not final_subj or any(b in final_subj.lower() for b in ["your work", "votre parcours", "your vision", "votre vision"]):
                        comp_clean = target_test_contact.get("company") or "[Entreprise]"
                        final_subj = f"Candidature Stage PFE – {comp_clean} – Mohammed HSINY" if res_test.language == "fr" else f"Internship Application (PFE) – {comp_clean} – Mohammed HSINY"

                    st.session_state["studio_test_res_subject"] = final_subj
                    st.session_state["studio_test_res_body"] = res_test.body'''

assert target2 in code, "target2 not found in app.py"
code = code.replace(target2, replacement2)

# 3. Batch generation sanitizer
target3 = '''                        if "Format d'Objet Fixe" in active_subj_mode or "Fixe" in active_subj_mode:
                            final_subject = substitute_placeholders(
                                text=active_pattern,
                                name=contact.get("name", ""),
                                company=contact.get("company", ""),
                                role=contact.get("role", ""),
                                language=res.language
                            )
                            contact["subject"] = final_subject
                        else:
                            contact["subject"] = res.subject'''

replacement3 = '''                        if any(b in active_pattern.lower() for b in ["your work", "votre parcours", "your vision", "votre vision"]):
                            active_pattern = "Candidature Stage PFE – [Entreprise] – Mohammed HSINY"

                        if "Format d'Objet Fixe" in active_subj_mode or "Fixe" in active_subj_mode:
                            final_subject = substitute_placeholders(
                                text=active_pattern,
                                name=contact.get("name", ""),
                                company=contact.get("company", ""),
                                role=contact.get("role", ""),
                                language=res.language
                            )
                            contact["subject"] = final_subject
                        else:
                            contact["subject"] = res.subject

                        if not contact.get("subject") or any(b in contact["subject"].lower() for b in ["your work", "votre parcours", "your vision", "votre vision"]):
                            comp_clean = contact.get("company") or contact.get("entreprise") or "[Entreprise]"
                            contact["subject"] = f"Candidature Stage PFE – {comp_clean} – Mohammed HSINY" if res.language == "fr" else f"Internship Application (PFE) – {comp_clean} – Mohammed HSINY"'''

assert target3 in code, "target3 not found in app.py"
code = code.replace(target3, replacement3)

with open('app.py', 'w', encoding='utf-8') as f:
    f.write(code)

print("Successfully patched app.py subject sanitizer!")
