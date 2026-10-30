with open('app.py', 'r', encoding='utf-8') as f:
    c = f.read()

old_block = '''        def_subjs = {
            "fr_rh": "Candidature – Stage PFE en systèmes embarqués et drones",
            "fr_ceo": f"Votre vision chez {man_company.strip() or '[Entreprise]'} – Étudiant passionné par les systèmes embarqués et les drones",
            "fr_eng": f"Candidature PFE Ingénieur – {man_company.strip() or '[Entreprise]'} – Mohammed HSINY",
            "en_rh": "Application – 6-Month Graduation Internship (PFE) in Embedded Systems & Drones",
            "en_ceo": f"Your vision at {man_company.strip() or '[Company]'} – Student passionate about embedded systems & drones",
            "en_eng": f"Your work at {man_company.strip() or '[Company]'} – Student passionate about embedded systems & drones",
        }'''

new_block = '''        def_subjs = {
            "fr_rh": f"Candidature Stage PFE Ingénieur – {man_company.strip() or '[Entreprise]'} – Mohammed HSINY",
            "fr_ceo": f"Candidature Stage PFE – {man_company.strip() or '[Entreprise]'} – Mohammed HSINY",
            "fr_eng": f"Candidature PFE Ingénieur – {man_company.strip() or '[Entreprise]'} – Mohammed HSINY",
            "en_rh": f"Application – 6-Month Graduation Internship (PFE) – {man_company.strip() or '[Company]'} – Mohammed HSINY",
            "en_ceo": f"Internship Application (PFE) – {man_company.strip() or '[Company]'} – Mohammed HSINY",
            "en_eng": f"Engineering Internship Application (PFE) – {man_company.strip() or '[Company]'} – Mohammed HSINY",
        }'''

if old_block in c:
    c = c.replace(old_block, new_block)
    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(c)
    print("app.py manual send subjects updated!")
else:
    print("Warning: old_block not found in app.py")
