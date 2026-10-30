import re

def update_app():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update the subject mode section in Studio IA
    old_studio_obj = '''    col_obj1, col_obj2 = st.columns([1.5, 2.5])
    with col_obj1:
        subject_mode = st.radio(
            "Mode de formulation de l'Objet :",
            [
                "🤖 Objet Intelligent IA (sur-mesure par entreprise & persona)",
                "✍️ Format d'Objet Fixe avec Balises ([Entreprise], etc.)",
                "💡 Consigne Spécifique pour l'IA sur l'Objet"
            ],
            key="studio_subject_mode"
        )
    
    with col_obj2:
        if "Format d'Objet Fixe" in subject_mode:
            studio_subject_pattern = st.text_input(
                "Modèle d'objet exact (balises : [Entreprise], [Prénom], [Nom], [Poste]) :",
                value=st.session_state.get("studio_fixed_subject", "Candidature PFE Ingénieur – [Entreprise] – Mohammed HSINY"),
                key="studio_fixed_subject_input",
                help="Exemple : Candidature PFE Ingénieur – [Entreprise] – Mohammed HSINY"
            )
            st.session_state["studio_fixed_subject"] = studio_subject_pattern
            st.caption("💡 Exemple d'aperçu : *Candidature PFE Ingénieur – Thales – Mohammed HSINY*")
        elif "Consigne Spécifique" in subject_mode:
            studio_subject_directive = st.text_input(
                "Consigne imposée à l'IA pour rédiger l'objet :",
                value=st.session_state.get("studio_subject_directive", "Mentionner impérativement mon projet de Centrale Solaire 1 MW et [Entreprise]"),
                key="studio_subject_directive_input",
                help="Donnez un ordre strict à l'IA sur les mots ou projets à inclure dans l'objet."
            )
            st.session_state["studio_subject_directive"] = studio_subject_directive
            st.caption("💡 L'IA respectera scrupuleusement cet ordre pour formuler chaque objet.")
        else:
            st.info("ℹ️ **Mode Intelligent Actif :** L'IA adapte l'objet pour chaque destinataire selon son persona (CEO, RH ou Ingénieur Tech) et le secteur de l'entreprise.")'''

    new_studio_obj = '''    col_obj1, col_obj2 = st.columns([1.5, 2.5])
    with col_obj1:
        subject_mode = st.radio(
            "Mode de formulation de l'Objet :",
            [
                "✍️ Format d'Objet Fixe avec Balises ([Entreprise], etc.)",
                "🤖 Objet Intelligent IA (sur-mesure par entreprise & persona)",
                "💡 Consigne Spécifique pour l'IA sur l'Objet"
            ],
            index=0,
            key="studio_subject_mode"
        )
    
    with col_obj2:
        if "Format d'Objet Fixe" in subject_mode:
            studio_subject_pattern = st.text_input(
                "Modèle d'objet exact (balises : [Entreprise], [Prénom], [Nom], [Poste]) :",
                value=st.session_state.get("studio_fixed_subject", "Candidature Stage PFE – [Entreprise] – Mohammed HSINY"),
                key="studio_fixed_subject_input",
                help="Exemple : Candidature Stage PFE – [Entreprise] – Mohammed HSINY"
            )
            st.session_state["studio_fixed_subject"] = studio_subject_pattern
            st.caption("💡 Aperçu : *Candidature Stage PFE – Thales – Mohammed HSINY*")
            
            if st.button("⚡ Remplacer l'Objet de TOUS les contacts de la base par ce format", key="btn_apply_obj_to_all_db"):
                all_cts = get_all_contacts()
                up_cnt = 0
                for c in all_cts:
                    c["subject"] = substitute_placeholders(
                        text=studio_subject_pattern,
                        name=c.get("name", ""),
                        company=c.get("company", ""),
                        role=c.get("role", ""),
                        language=c.get("language", "fr")
                    )
                    save_or_update_contact(c)
                    up_cnt += 1
                st.success(f"🎉 L'objet a été mis à jour pour les {up_cnt} contacts dans la base !")
                time.sleep(0.8)
                st.rerun()

        elif "Consigne Spécifique" in subject_mode:
            studio_subject_directive = st.text_input(
                "Consigne imposée à l'IA pour rédiger l'objet :",
                value=st.session_state.get("studio_subject_directive", "Mentionner impérativement mon projet de Centrale Solaire 1 MW et [Entreprise]"),
                key="studio_subject_directive_input",
                help="Donnez un ordre strict à l'IA sur les mots ou projets à inclure dans l'objet."
            )
            st.session_state["studio_subject_directive"] = studio_subject_directive
            st.caption("💡 L'IA respectera scrupuleusement cet ordre pour formuler chaque objet.")
        else:
            st.info("ℹ️ **Mode Intelligent Actif :** L'IA génère des objets professionnels (ex: *Candidature Stage PFE – [Entreprise] – Mohammed HSINY*).")'''

    if old_studio_obj in content:
        content = content.replace(old_studio_obj, new_studio_obj)
        print("Updated studio object controls!")
    else:
        print("Warning: old_studio_obj not found verbatim")

    # 2. Update run_batch in Studio IA
    old_batch_subj = '''                        # Apply Subject Guidance
                        if "Format d'Objet Fixe" in subject_mode and st.session_state.get("studio_fixed_subject"):
                            final_subject = substitute_placeholders(
                                text=st.session_state.get("studio_fixed_subject"),
                                name=contact.get("name", ""),
                                company=contact.get("company", ""),
                                role=contact.get("role", ""),
                                language=res.language
                            )
                            contact["subject"] = final_subject
                        else:
                            contact["subject"] = res.subject'''

    new_batch_subj = '''                        # Apply Subject Guidance (100% strict & guaranteed)
                        active_subj_mode = st.session_state.get("studio_subject_mode", subject_mode)
                        active_pattern = (
                            st.session_state.get("studio_fixed_subject_input") or
                            st.session_state.get("studio_fixed_subject") or
                            "Candidature Stage PFE – [Entreprise] – Mohammed HSINY"
                        ).strip()

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
                            contact["subject"] = res.subject'''

    if old_batch_subj in content:
        content = content.replace(old_batch_subj, new_batch_subj)
        print("Updated batch generation subject handler!")
    else:
        print("Warning: old_batch_subj not found verbatim")

    # 3. Add bulk subject updater in Tab 4 (Revue & Édition)
    target_tab4_banner = 'col_hdr1, col_hdr2 = st.columns([3, 2])'
    tab4_bulk_toolbar = '''        # Quick Bulk Subject Update Toolbar
        with st.expander("🏷️ Modifier en 1 clic l'Objet de Tous les Contacts (ex: Candidature Stage PFE – [Entreprise] – Mohammed HSINY)", expanded=False):
            col_so1, col_so2 = st.columns([3, 1])
            with col_so1:
                tab4_bulk_pattern = st.text_input(
                    "Format d'objet global (avec balise [Entreprise]) :",
                    value="Candidature Stage PFE – [Entreprise] – Mohammed HSINY",
                    key="tab4_bulk_subject_pattern"
                )
            with col_so2:
                st.write("")
                st.write("")
                if st.button("⚡ Remplacer pour Tous", key="btn_tab4_replace_all_subjects", use_container_width=True):
                    up_cnt = 0
                    for c in contacts:
                        c["subject"] = substitute_placeholders(
                            text=tab4_bulk_pattern,
                            name=c.get("name", ""),
                            company=c.get("company", ""),
                            role=c.get("role", ""),
                            language=c.get("language", "fr")
                        )
                        save_or_update_contact(c)
                        up_cnt += 1
                    st.success(f"🎉 Objet mis à jour pour les {up_cnt} contacts !")
                    time.sleep(0.8)
                    st.rerun()

        '''

    if target_tab4_banner in content:
        content = content.replace(target_tab4_banner, tab4_bulk_toolbar + target_tab4_banner, 1)
        print("Added tab4 bulk subject toolbar!")
    else:
        print("Warning: target_tab4_banner not found")

    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)

if __name__ == '__main__':
    update_app()
