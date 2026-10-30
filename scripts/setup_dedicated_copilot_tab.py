import re

def update_app():
    with open('app.py', 'r', encoding='utf-8') as f:
        content = f.read()

    # 1. Update the tabs definition
    old_tabs = '''# Navigation Tabs with Icons
tab1, tab2, tab3, tab4, tab_manual, tab5, tab6, tab7 = st.tabs([
    "👤 Mon Profil & CV",
    "👥 Contacts & Import",
    "🤖 Studio IA & Copilote Interactif",
    "✍️ Revue & Édition",
    "✉️ Envoi Manuel Direct",
    "🚀 Centre d'Envoi",
    "💬 Réponses & IA",
    "⚙️ Paramètres & Gmail"
])'''

    new_tabs = '''# Navigation Tabs with Icons
tab1, tab2, tab3, tab_copilot, tab4, tab_manual, tab5, tab6, tab7 = st.tabs([
    "👤 Mon Profil & CV",
    "👥 Contacts & Import",
    "🤖 Studio IA (Génération en Masse)",
    "💬 Copilote IA (Discussion & Ordres)",
    "✍️ Revue & Édition",
    "✉️ Envoi Manuel Direct",
    "🚀 Centre d'Envoi",
    "💬 Réponses & IA",
    "⚙️ Paramètres & Gmail"
])'''

    content = content.replace(old_tabs, new_tabs)

    # 2. In tab3 header
    content = content.replace(
        'st.header("🤖 Studio IA & Personnalisation des Candidatures")',
        'st.header("🤖 Studio IA : Génération & Personnalisation en Masse")'
    )

    # 3. Transform the Copilot block into `with tab_copilot:`
    copilot_marker = '    # -------------------------------------------------------------\n    # Copilote IA Interactif Intégré au Studio IA\n    # -------------------------------------------------------------'
    
    # Let's find where the copilot block starts
    if copilot_marker in content:
        # Split at copilot_marker
        parts = content.split(copilot_marker)
        before_copilot = parts[0]
        # Find where TAB 4 starts
        after_parts = parts[1].split('# -------------------------------------------------------------\n# TAB 4: Revue & Édition')
        copilot_code = after_parts[0]
        tab4_and_rest = '# -------------------------------------------------------------\n# TAB 4: Revue & Édition' + after_parts[1]

        # In copilot_code, dedent 4 spaces so it fits under `with tab_copilot:`
        lines = copilot_code.split('\n')
        dedented_lines = []
        for line in lines:
            if line.startswith('    '):
                dedented_lines.append(line[4:])
            else:
                dedented_lines.append(line)
        cleaned_copilot_code = '\n'.join(dedented_lines)

        tab_copilot_block = f"""
# -------------------------------------------------------------
# TAB COPILOTE IA : Discussion Directe, Ordres & Co-Rédaction
# -------------------------------------------------------------
with tab_copilot:
    st.header("💬 Copilote IA Interactif : Votre Binôme & Assistant Dédié")
    st.caption("Donnez directement vos ordres à l'IA en temps réel. Demandez-lui d'analyser une entreprise cible, d'ajuster vos emails vers le Solaire 1 MW, les Drones HT, le Robot ASRS SkyPharma ou l'Automatisme, ou de co-rédiger le message parfait.")

{cleaned_copilot_code}
"""

        content = before_copilot + tab_copilot_block + tab4_and_rest
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Dedicated tab_copilot restored successfully!")
    else:
        print("Error: copilot_marker not found")

if __name__ == '__main__':
    update_app()
