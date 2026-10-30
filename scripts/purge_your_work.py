import re

def purge():
    # 1. Update services/prompt_builder.py
    with open('services/prompt_builder.py', 'r', encoding='utf-8') as f:
        pb = f.read()

    old_pb_subj = '''    if language == "fr":
        if persona == "CEO_DIRECTEUR":
            return f"Votre vision chez {comp_name} – Étudiant passionné par {th_fr}"
        elif persona == "RH_TALENT":
            return f"Candidature – Stage PFE en {th_hr_fr}"
        elif persona in ["INGENIEUR_TECH", "RD_LEAD_ARCHITECT"]:
            return f"Votre parcours chez {comp_name} – Étudiant passionné par {th_fr}"
        else:
            return f"Stage PFE – Demande de conseil chez {comp_name}"
    else:
        if persona == "CEO_DIRECTEUR":
            return f"Your vision at {comp_name} – Student passionate about {th_en}"
        elif persona == "RH_TALENT":
            return f"Application – 6-Month Graduation Internship (PFE) in {th_hr_en}"
        elif persona in ["INGENIEUR_TECH", "RD_LEAD_ARCHITECT"]:
            return f"Your work at {comp_name} – Student passionate about {th_en}"
        else:
            return f"PFE Internship Opportunity at {comp_name}"'''

    new_pb_subj = '''    if language == "fr":
        if persona == "CEO_DIRECTEUR":
            return f"Candidature Stage PFE – {comp_name} – Mohammed HSINY"
        elif persona == "RH_TALENT":
            return f"Candidature Stage PFE Ingénieur – {comp_name} – Mohammed HSINY"
        elif persona in ["INGENIEUR_TECH", "RD_LEAD_ARCHITECT"]:
            return f"Candidature PFE Ingénieur – {comp_name} – Mohammed HSINY"
        else:
            return f"Candidature Stage PFE – {comp_name} – Mohammed HSINY"
    else:
        if persona == "CEO_DIRECTEUR":
            return f"Internship Application (PFE) – {comp_name} – Mohammed HSINY"
        elif persona == "RH_TALENT":
            return f"Application – 6-Month Graduation Internship (PFE) – {comp_name} – Mohammed HSINY"
        elif persona in ["INGENIEUR_TECH", "RD_LEAD_ARCHITECT"]:
            return f"Engineering Internship Application (PFE) – {comp_name} – Mohammed HSINY"
        else:
            return f"Graduation Internship Application – {comp_name} – Mohammed HSINY"'''

    if old_pb_subj in pb:
        pb = pb.replace(old_pb_subj, new_pb_subj)
        print("Replaced get_target_subject in prompt_builder.py")
    else:
        print("Warning: old_pb_subj not found verbatim, checking regex...")
        pb = re.sub(
            r'if language == "fr":\s+if persona == "CEO_DIRECTEUR":.*?else:\s+return f"PFE Internship Opportunity at \{comp_name\}"',
            new_pb_subj.strip(),
            pb,
            flags=re.DOTALL
        )

    pb = pb.replace('"Votre parcours chez [Entreprise] & opportunités PFE 2027"', '"Candidature PFE Ingénieur – [Entreprise] – Mohammed HSINY"')

    with open('services/prompt_builder.py', 'w', encoding='utf-8') as f:
        f.write(pb)

    # 2. Update services/llm_service.py
    with open('services/llm_service.py', 'r', encoding='utf-8') as f:
        llm_code = f.read()

    # Replace subject lines
    llm_code = llm_code.replace(
        'subject = f"Votre parcours chez {company} – Étudiant passionné par {th_short_fr}"',
        'subject = f"Candidature PFE Ingénieur – {company} – Mohammed HSINY"'
    )
    llm_code = llm_code.replace(
        'subject = f"Votre parcours chez {company} – Étudiant passionné par {th_short_fr}"',
        'subject = f"Candidature PFE Ingénieur – {company} – Mohammed HSINY"'
    )
    llm_code = llm_code.replace(
        'subject = f"Your work at {company} – Student passionate about {th_short_en}"',
        'subject = f"Engineering Internship Application (PFE) – {company} – Mohammed HSINY"'
    )
    llm_code = llm_code.replace(
        'subject = f"Your vision at {company} – Student passionate about {th_short_en}"',
        'subject = f"Internship Application (PFE) – {company} – Mohammed HSINY"'
    )
    llm_code = llm_code.replace(
        'subject = f"Votre vision chez {company} – Étudiant passionné par {th_short_fr}"',
        'subject = f"Candidature Stage PFE – {company} – Mohammed HSINY"'
    )
    llm_code = llm_code.replace(
        'subject = f"Candidature – Stage PFE en {th_hr_fr}"',
        'subject = f"Candidature Stage PFE – {company} – Mohammed HSINY"'
    )
    llm_code = llm_code.replace(
        'subject = f"Application – 6-Month Graduation Internship (PFE) in {th_hr_en}"',
        'subject = f"Application – 6-Month Graduation Internship (PFE) – {company} – Mohammed HSINY"'
    )

    # Replace phrases in body text
    llm_code = llm_code.replace(
        "En découvrant votre parcours, j'ai été vraiment inspiré par votre travail et par les projets sur lesquels vous intervenez.",
        "En découvrant les activités de {company}, j'ai été particulièrement intéressé par vos défis techniques et vos projets d'ingénierie."
    )
    llm_code = llm_code.replace(
        "Coming across your technical journey, I was truly inspired by your work and the engineering challenges you tackle at {company}.",
        "Learning about {company}'s engineering achievements, I was very impressed by the technical challenges you tackle."
    )

    with open('services/llm_service.py', 'w', encoding='utf-8') as f:
        f.write(llm_code)
    print("Purged 'Your work' and 'Votre parcours' from llm_service.py")

    # 3. Update app.py Manual Send mode
    with open('app.py', 'r', encoding='utf-8') as f:
        app_code = f.read()

    app_code = app_code.replace(
        '"fr_eng": f"Votre parcours chez {man_company.strip() or \'[Entreprise]\'} – Étudiant passionné par les systèmes embarqués et les drones"',
        '"fr_eng": f"Candidature PFE Ingénieur – {man_company.strip() or \'[Entreprise]\'} – Mohammed HSINY"'
    )
    app_code = app_code.replace(
        '"en_eng": f"Your work at {man_company.strip() or \'[Company]\'} – Student passionate about embedded systems & robotics"',
        '"en_eng": f"Engineering Internship Application (PFE) – {man_company.strip() or \'[Company]\'} – Mohammed HSINY"'
    )

    with open('app.py', 'w', encoding='utf-8') as f:
        f.write(app_code)
    print("Updated manual send in app.py")

if __name__ == '__main__':
    purge()
