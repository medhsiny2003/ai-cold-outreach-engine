def remove_tab4_duplicate():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # Find start of tab4
    tab4_header = 'with tab4:\n    st.header("✍️ Revue, Édition & Personnalisation Individuelle")\n    st.caption("Inspectez chaque email généré, ajustez l\'angle thématique à la volée ou modifiez le texte manuellement avant approbation.")'
    
    # Target duplicate block inside tab4
    dup_start = '# =============================================================\n    # 🎯 GUIDAGE DE L\'OBJET & COPILOTE DIRECT DANS LE STUDIO IA'
    
    # The normal start of tab4 contacts
    tab4_contacts = 'contacts = get_all_contacts()\n    if not contacts:\n        st.info("Aucun contact disponible.'

    # Locate positions
    pos_tab4 = content.find(tab4_header)
    if pos_tab4 == -1:
        print("Error: tab4_header not found")
        return

    # In the portion after tab4_header, find dup_start
    after_tab4 = content[pos_tab4:]
    pos_dup = after_tab4.find(dup_start)
    pos_contacts = after_tab4.find(tab4_contacts)

    if pos_dup != -1 and pos_contacts != -1 and pos_dup < pos_contacts:
        # Cut out everything between tab4_header and tab4_contacts in that section
        new_after_tab4 = after_tab4[:pos_dup] + '\n    ' + after_tab4[pos_contacts:]
        content = content[:pos_tab4] + new_after_tab4
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Duplicate block inside tab4 successfully removed!")
    else:
        print("Error: positions not matched properly", pos_dup, pos_contacts)

if __name__ == '__main__':
    remove_tab4_duplicate()
