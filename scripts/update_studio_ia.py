import re

def update_studio_ia():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update ENSEM Casablanca default template to FSTM
    content = content.replace(
        "Élève-ingénieur en dernière année en Électrotechnique et Automatique à l'ENSEM Casablanca, je recherche",
        "Élève-ingénieur en dernière année en Génie Électrique & Contrôle Industriel à la Faculté des Sciences et Techniques de Mohammedia (FSTM), je recherche"
    )
    content = content.replace(
        "Élève-Ingénieur ENSEM | Électrotechnique & Automatique",
        "Élève-Ingénieur FSTM | Génie Électrique & Contrôle Industriel"
    )

    # 2. Add Subject Guidance and Studio Live Copilot directly into Tab 3
    # Look for where `contacts = get_all_contacts()` appears in Tab 3 (around line 1221)
    target_marker = 'contacts = get_all_contacts()\n    if not contacts:'
    
    studio_supercharge = '''# =============================================================
    # 🎯 GUIDAGE DE L'OBJET & COPILOTE DIRECT DANS LE STUDIO IA
    # =============================================================
    st.divider()
    
    # 1. Pilotage de l'Objet de l'Email pour la Génération en Masse
    st.subheader("🏷️ Contrôle & Guidage de l'Objet de l'Email (Pour la Génération en Masse)")
    st.caption("Personnalisez ou imposez la façon dont l'objet (sujet) de vos emails sera formulé pour tous vos contacts.")

    col_obj1, col_obj2 = st.columns([1.5, 2.5])
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
            st.info("ℹ️ **Mode Intelligent Actif :** L'IA adapte l'objet pour chaque destinataire selon son persona (CEO, RH ou Ingénieur Tech) et le secteur de l'entreprise.")

    st.markdown("---")

    # 2. Assistant Copilote & Test en Direct DANS le Studio IA (Même Fenêtre)
    with st.expander("💬 Parler à l'IA & Tester un email en direct dans le Studio (Sans changer de fenêtre)", expanded=False):
        st.caption("Testez vos idées, donnez vos ordres à l'IA sur un projet ou une cible, et appliquez instantanément l'objet ou le texte à votre génération en masse !")
        
        all_contacts_for_test = get_all_contacts()
        contact_choices = ["(Exemple général)"] + [f"#{c.get('id')} - {c.get('name') or c.get('email')} ({c.get('company', 'Entreprise')})" for c in all_contacts_for_test]
        
        col_t1, col_t2 = st.columns([2, 1])
        with col_t1:
            selected_test_contact_label = st.selectbox("Sélectionner un contact cible de votre base :", contact_choices, key="studio_test_contact_sel")
        with col_t2:
            st.write("⚡ **Focus Projets Rapides :**")
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                if st.button("☀️ Solaire 1 MW", key="btn_f_sol", use_container_width=True):
                    st.session_state["studio_live_prompt"] = "Rédige un email mettant en avant mon projet de Centrale Solaire PV de 1 MW (PVsyst, réseaux MT/BT, onduleurs) pour cette cible."
            with col_f2:
                if st.button("🛸 Drone & ASRS", key="btn_f_dro", use_container_width=True):
                    st.session_state["studio_live_prompt"] = "Rédige un email mettant en valeur mon Drone d'Inspection HT YOLOv8 et mon Robot ASRS SkyPharma de délivrance de médicaments."

        target_test_contact = None
        if selected_test_contact_label != "(Exemple général)":
            try:
                sel_cid = int(selected_test_contact_label.split(" - ")[0].replace("#", ""))
                target_test_contact = next((c for c in all_contacts_for_test if c.get("id") == sel_cid), None)
            except Exception:
                pass

        if target_test_contact is None:
            target_test_contact = {
                "name": "Jean Dupont",
                "first_name": "Jean",
                "role": "Directeur Technique R&D",
                "company": "Entreprise Cible",
                "industry": "Robotique & Énergie",
                "country": "France"
            }

        live_user_order = st.text_area(
            "Votre ordre ou consigne pour l'IA :",
            value=st.session_state.get("studio_live_prompt", "Essaie de faire un email orienté vers l'innovation mécatronique, en citant mon robot ASRS SkyPharma et mon rôle d'Ex-Président de RoboThings."),
            height=80,
            key="studio_live_order_area"
        )
        st.session_state["studio_live_prompt"] = live_user_order

        if st.button("🚀 Tester & Générer la Prévisualisation", type="secondary", key="btn_run_studio_test"):
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
                    )
                try:
                    res_test = asyncio.run(test_gen())
                    st.session_state["studio_test_res_subject"] = res_test.subject
                    st.session_state["studio_test_res_body"] = res_test.body
                except Exception as ex:
                    st.error(f"Erreur lors de l'essai : {ex}")

        if "studio_test_res_subject" in st.session_state:
            st.success("✅ **Essai généré avec succès !**")
            st.markdown(f"**Objet généré :** `{st.session_state['studio_test_res_subject']}`")
            st.text_area("Corps du message généré :", value=st.session_state["studio_test_res_body"], height=160, key="studio_test_body_display")
            
            col_apply1, col_apply2 = st.columns(2)
            with col_apply1:
                if st.button("🏷️ Imposer cet Objet pour Tous les Envois en Masse", key="btn_apply_obj"):
                    st.session_state["studio_fixed_subject"] = st.session_state["studio_test_res_subject"]
                    st.success("Objet copié dans le champ de format d'objet pour la génération en masse !")
                    time.sleep(0.8)
                    st.rerun()
            with col_apply2:
                if st.button("📋 Copier ce Texte dans le Modèle de Référence (Mode 2)", key="btn_apply_body"):
                    st.session_state["custom_reference_template"] = f"Objet : {st.session_state['studio_test_res_subject']}\\n\\n{st.session_state['studio_test_res_body']}"
                    st.success("Texte copié dans le Modèle de Référence (Mode 2) !")
                    time.sleep(0.8)
                    st.rerun()

    st.divider()

    '''

    if target_marker in content:
        content = content.replace(target_marker, studio_supercharge + target_marker)
        print("Inserted studio_supercharge before contacts list!")
    else:
        print("Error: target_marker not found!")

    # 3. Update the batch generation execution to apply the chosen subject mode!
    old_batch_run = '''                        if "Mode 1" in gen_mode:
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
                        contact["subject"] = res.subject'''

    new_batch_run = '''                        # Compile effective custom instruction (including subject directive if any)
                        effective_directive = custom_pitch_directive or ""
                        if "Consigne Spécifique" in subject_mode and st.session_state.get("studio_subject_directive"):
                            effective_directive += f"\\nCONSIGNE STRICTE POUR L'OBJET : {st.session_state.get('studio_subject_directive')}"

                        if "Mode 1" in gen_mode:
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
                            )

                        # Apply Subject Guidance
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

    if old_batch_run in content:
        content = content.replace(old_batch_run, new_batch_run)
        print("Updated batch generation loop with custom subject guidance!")
    else:
        print("Error: old_batch_run not found!")

    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("app.py successfully updated with Studio IA direct copilot & subject guidance!")

if __name__ == '__main__':
    update_studio_ia()
