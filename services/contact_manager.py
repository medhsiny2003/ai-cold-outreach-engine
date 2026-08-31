import io
import re
import pandas as pd
from typing import List, Dict, Any, Tuple
from pathlib import Path

COMPANY_DEFAULT_LOCATIONS = {
    "parrot": ("Paris, France", "Drones Civils & Autonomie"),
    "thales": ("France", "Défense & Systèmes Critiques Embarqués"),
    "novadem": ("Aix-en-Provence, France", "Drones Captifs & Systèmes Aériens"),
    "dassault aviation": ("Saint-Cloud, France", "Aéronautique & Défense"),
    "atechsys": ("Pourrières, France", "Drones Professionnels & R&D"),
    "airbus": ("Toulouse, France", "Aéronautique & Systèmes de Vol"),
    "mbda": ("Le Plessis-Robinson, France", "Systèmes de Guidage & Électronique de Précision"),
    "seaber": ("Lorient, France", "Micro-AUV & Robotique Sous-Marine Autonome"),
    "delair": ("Toulouse, France", "Drones Industriels & Traitement d'Images"),
    "skydrone robotics": ("La Rochelle, France", "Robotique Aérienne & Drones Lourds"),
    "drone volt": ("Villepinte, France", "Drones Professionnels & IA Embarquée"),
    "cerbair": ("Montrouge, France", "Systèmes Anti-Drones & Traitement Signal"),
    "hexadrone": ("Saint-Just-Malmont, France", "Conception & Intégration de Drones Modulaires"),
    "naval group": ("Paris, France", "Défense Navale & Systèmes Embarqués Autonomes"),
    "sbg systems": ("Rueil-Malmaison, France", "Capteurs Inertiels MEMS, Navigation & Guidage"),
    "ocp": ("Maroc", "Industrie & Automatisation SCADA"),
    "sonaca": ("Gosselies, Belgique", "Aéronautique & Mécatronique"),
    "volocopter": ("Bruchsal, Germany", "Urban Air Mobility & eVTOL"),
    "skydio": ("San Mateo, CA, USA", "Autonomous Drones & Computer Vision")
}

COLUMN_PRIORITIES = {
    "email": [
        "email certifié (prêt à l'envoi)", "email certifié", "email_certifie", "email certifie",
        "proposed_email", "primary_email", "email", "mail", "e-mail", "courriel", 
        "adresse email", "contact email", "email pro", "pro_email", "work_email",
        "alt_email_1", "alt_email_2", "email alternatif 1", "email alternatif 2", "emails"
    ],
    "first_name": ["first_name", "firstname", "prenom", "prénom", "first name", "prenom contact"],
    "last_name": ["last_name", "lastname", "nom de famille", "nom", "last name", "nom contact"],
    "name": ["name", "full name", "nom complet", "destinataire", "contact", "personne", "nom & prénom", "nom et prenom"],
    "company": ["company", "entreprise", "societe", "société", "boite", "boîte", "organization", "organisation", "structure"],
    "role": ["job_title", "job title", "poste", "role", "rôle", "titre", "title", "position", "fonction", "job", "poste_actuel", "poste occupé", "cible recrutement stage"],
    "location": ["location", "pays", "country", "ville", "city", "localisation", "region", "domaine mail certifié"],
    "industry": ["industry", "secteur", "domaine", "field", "activite", "activité"],
    "language": ["language", "langue", "lang"],
    "notes": ["matched_keywords", "notes", "remarques", "commentaires", "note", "contexte", "profile_url", "ancien email utilisé"]
}

def clean_person_name(name_str: str) -> str:
    """Normalizes person name, removes honorifics (M., Mme, Dr., etc.) and fixes casing."""
    if not name_str:
        return ""
    # Remove honorific prefixes
    cleaned = re.sub(r'^(?:M\.|Mme|Mr\.|Dr\.|Prof\.|Ing\.)\s+', '', name_str, flags=re.IGNORECASE).strip()
    # If uppercase or lowercase, convert to Title Case
    if cleaned.isupper() or cleaned.islower():
        cleaned = cleaned.title()
    return cleaned

def extract_best_email(row: pd.Series, company: str = "") -> str:
    """Extracts all valid emails from all relevant columns, selects the best corporate email."""
    candidate_emails = []
    
    # 1. Inspect all columns
    for col_name in row.index:
        col_str = str(col_name).strip().lower()
        val_str = str(row[col_name]).strip()
        if not val_str or val_str.lower() == "nan":
            continue
            
        found = re.findall(r'[\w\.-]+@[\w\.-]+\.[a-zA-Z]{2,}', val_str)
        for e in found:
            e_clean = e.lower().strip().strip(".")
            if e_clean not in candidate_emails:
                candidate_emails.append(e_clean)
                
    if not candidate_emails:
        return ""
        
    # 2. Prioritize email matching company domain if available
    comp_clean = re.sub(r'[^a-zA-Z0-9]', '', company.lower()) if company else ""
    if comp_clean:
        for em in candidate_emails:
            domain_part = em.split("@")[-1]
            if comp_clean in domain_part.replace("-", "").replace(".", ""):
                return em
                
    # 3. Prioritize non-generic emails over gmail/yahoo/hotmail
    for em in candidate_emails:
        domain = em.split("@")[-1].lower()
        if not any(g in domain for g in ["gmail", "yahoo", "hotmail", "outlook", "live", "orange"]):
            return em
            
    return candidate_emails[0]

def get_row_value(row: pd.Series, possible_keys: List[str]) -> str:
    """Safely extracts the first non-null string value matching possible column keys."""
    index_map = {str(k).strip().lower(): k for k in row.index}
    
    for key in possible_keys:
        k_lower = key.strip().lower()
        if k_lower in index_map:
            actual_key = index_map[k_lower]
            val = row[actual_key]
            if isinstance(val, pd.Series):
                val = val.dropna().iloc[0] if not val.dropna().empty else ""
            if pd.notna(val):
                s_val = str(val).strip()
                if s_val and s_val.lower() != "nan":
                    return s_val
    return ""

def parse_contacts_file(file_content: bytes, filename: str) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Parses any CSV or Excel file with smart column fuzzy-matching, multi-email resolution, and data cleaning."""
    errors = []
    try:
        if filename.endswith(".csv"):
            try:
                df = pd.read_csv(io.BytesIO(file_content), encoding="utf-8")
            except UnicodeDecodeError:
                df = pd.read_csv(io.BytesIO(file_content), encoding="latin-1")
        elif filename.endswith((".xlsx", ".xls")):
            df = pd.read_excel(io.BytesIO(file_content))
        else:
            return [], [f"Format de fichier non supporté : {filename}. Utilisez CSV ou Excel (.xlsx, .xls)"]
    except Exception as e:
        return [], [f"Erreur lors de la lecture du fichier : {str(e)}"]

    contacts = []
    seen_emails = set()

    for idx, row in df.iterrows():
        company = get_row_value(row, COLUMN_PRIORITIES["company"])
        email_clean = extract_best_email(row, company)
        
        if not email_clean or "@" not in email_clean:
            continue
            
        if email_clean in seen_emails:
            continue
        seen_emails.add(email_clean)

        first_name = get_row_value(row, COLUMN_PRIORITIES["first_name"])
        last_name = get_row_value(row, COLUMN_PRIORITIES["last_name"])
        name = get_row_value(row, COLUMN_PRIORITIES["name"])
        
        if not name:
            if first_name or last_name:
                name = f"{first_name} {last_name}".strip()
                
        name = clean_person_name(name)
        role = get_row_value(row, COLUMN_PRIORITIES["role"])
        location = get_row_value(row, COLUMN_PRIORITIES["location"])
        industry = get_row_value(row, COLUMN_PRIORITIES["industry"])
        language = get_row_value(row, COLUMN_PRIORITIES["language"])
        notes = get_row_value(row, COLUMN_PRIORITIES["notes"])

        # Auto-infer location & industry from known company if missing
        comp_lower = company.lower()
        for known_comp, (default_loc, default_ind) in COMPANY_DEFAULT_LOCATIONS.items():
            if known_comp in comp_lower:
                if not location:
                    location = default_loc
                if not industry:
                    industry = default_ind
                break

        contact = {
            "id": idx + 1,
            "email": email_clean,
            "name": name,
            "company": company,
            "role": role,
            "location": location,
            "industry": industry,
            "language": language,
            "notes": notes,
            "status": "pending",
            "subject": "",
            "body": ""
        }
        contacts.append(contact)

    if not contacts:
        return [], ["Aucun email valide trouvé dans le fichier. Le moteur a scanné toutes les colonnes sans succès."]

    return contacts, errors

def generate_sample_csv() -> str:
    """Generates valid RFC-compliant sample CSV data."""
    return '''name,email,company,role,location,industry,notes
"Julien Moreau","julien.moreau@parrot.com","Parrot","CTO / Head of Embedded Software","Paris, France","Drones & Systèmes Autonomes","Équipe R&D drones civils et micro-drones"
"Sarah Jenkins","s.jenkins@skydio.com","Skydio","Senior Technical Recruiter","San Mateo, CA, USA","Autonomous Drones & AI","Looking for Embedded / Computer Vision interns"
"Alexandre Dubois","a.dubois@thalesgroup.com","Thales","Responsable Recrutement R&D & Systèmes Critiques","Vélizy, France","Défense & Aéronautique","Recherche profils C++ / STM32 / Temps Réel"
"Marc Van den Bossche","m.vandenbossche@sonaca.com","Sonaca Group","Engineering Manager - Mechatronics","Gosselies, Belgique","Aéronautique & Systèmes Embarqués","Intégration mécatronique et bancs de test"
"Michael Weber","m.weber@volocopter.com","Volocopter","Lead Flight Control Engineer","Bruchsal, Germany","Urban Air Mobility & eVTOL","Flight control firmware & sensor fusion"
"Karim Bennani","k.bennani@ocpgroup.ma","Groupe OCP","Chef de Département Automatisme & Digitalisation","Jorf Lasfar, Maroc","Industrie & Automatisation","Projets SCADA et modernisation automates M580"
'''
