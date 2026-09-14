import json
import re
from typing import Dict, Any, Optional
from config import CandidateProfile, is_francophone

__all__ = [
    "THEMES_CATALOG",
    "WRITING_STYLES",
    "detect_best_theme_for_company",
    "determine_language",
    "classify_role_category",
    "get_target_subject",
    "substitute_placeholders",
    "build_system_prompt",
    "build_user_prompt",
    "build_template_adaptation_system_prompt",
    "build_template_adaptation_user_prompt",
]

def substitute_placeholders(
    text: str,
    name: str = "",
    company: str = "",
    role: str = "",
    language: str = "fr"
) -> str:
    """Replaces all variations of placeholders ([Entreprise], {Entreprise}, {{Entreprise}}, [Prénom], {Prenom}, etc.)
    with actual values cleanly and safely.
    """
    if not text:
        return ""
    
    clean_name = (name or "").strip()
    first_name = clean_name.split()[0].capitalize() if clean_name else ("" if language == "fr" else "")
    salutation_name = first_name if first_name else ("Madame, Monsieur" if language == "fr" else "Hiring Team")
    
    clean_company = (company or "").strip()
    if not clean_company or clean_company.lower() in ["votre entreprise", "n/a", "none", "null"]:
        clean_company = "votre entreprise" if language == "fr" else "your company"
        
    clean_role = (role or "").strip()
    if not clean_role:
        clean_role = "Responsable" if language == "fr" else "Hiring Manager"

    replacements = [
        # Prénom / First name
        (r"\[(?:Prénom|Prenom|First\s*Name|FirstName)\]|\{\{?(?:prenom|prénom|first_name)\}?\}", first_name if first_name else salutation_name),
        # Nom complet / Last name
        (r"\[(?:Nom|Nom\s+complet|Last\s*Name|LastName|Full\s*Name)\]|\{\{?(?:nom|nom_complet|last_name|full_name|name)\}?\}", clean_name if clean_name else salutation_name),
        # Entreprise / Company / Société
        (r"\[(?:Nom\s+de\s+l['’]entreprise|Entreprise|Société|Societe|Company|Organization|Nom\s+de\s+l['’]organisme)\]|\{\{?(?:entreprise|societe|société|company|organization)\}?\}", clean_company),
        # Poste / Rôle / Title
        (r"\[(?:Poste|Titre|Rôle|Role|Title|Job\s*Title)\]|\{\{?(?:poste|titre|role|rôle|title)\}?\}", clean_role),
    ]

    result = text
    for pattern, repl in replacements:
        result = re.sub(pattern, repl, result, flags=re.IGNORECASE)

    return result

THEMES_CATALOG = {
    "auto": {
        "label": "🎯 Auto-détection IA Intelligente",
        "description": "L'IA analyse l'entreprise et adapte automatiquement le meilleur angle technique (Drones, Solaire, Automatisme, ou Électrique).",
        "tagline_fr": "Élève-ingénieur en Génie Électrique & Contrôle Industriel",
        "tagline_en": "Final-year Electrical & Industrial Control Engineering student",
        "focus_fr": "systèmes embarqués, robotique, énergie et contrôle industriel",
        "focus_en": "embedded systems, robotics, energy and industrial control"
    },
    "drones_robotics": {
        "label": "🛸 Focus Drones, UAV & Robotique Mobile",
        "description": "Met en avant l'autonomie de vol Pixhawk/PX4, ROS, la vision par ordinateur et la présidence du Club RoboThings.",
        "tagline_fr": "Élève-ingénieur passionné par les drones autonomes et la robotique",
        "tagline_en": "Final-year Engineer passionate about autonomous drones & robotics",
        "focus_fr": "systèmes de vol autonomes (Pixhawk/PX4/Ardupilot), ROS/ROS2, vision par ordinateur (OpenCV/YOLO) et présidence du Club RoboThings FSTM",
        "focus_en": "autonomous flight systems (Pixhawk/PX4), ROS/ROS2, computer vision (OpenCV/YOLO) and President of RoboThings Club FSTM"
    },
    "solar_energy": {
        "label": "☀️ Focus Énergie Solaire & Énergies Renouvelables",
        "description": "Met en avant le dimensionnement photovoltaïque, les convertisseurs MPPT, micro-réseaux et l'efficacité énergétique.",
        "tagline_fr": "Élève-ingénieur en Génie Électrique spécialisé en Énergie Solaire & Photovoltaïque",
        "tagline_en": "Electrical Engineering student specialized in Solar PV & Renewable Energy",
        "focus_fr": "dimensionnement d'installations photovoltaïques (raccordées et autonomes), convertisseurs d'énergie MPPT, stockage batteries, micro-réseaux et modélisation Matlab/Simulink",
        "focus_en": "solar PV system sizing, MPPT power converters, battery energy storage, microgrids and Matlab/Simulink modeling"
    },
    "electrical_power": {
        "label": "⚡ Focus Génie Électrique, Électrotechnique & Réseaux",
        "description": "Met en avant les machines électriques, variateurs de vitesse, schémas AutoCAD Electrical/EPLAN et distribution HT/BT.",
        "tagline_fr": "Élève-ingénieur en Génie Électrique & Électrotechnique",
        "tagline_en": "Final-year Electrical & Power Engineering student",
        "focus_fr": "machines électriques, variateurs de vitesse, distribution HT/BT, bilans de puissance et schémas industriels (AutoCAD Electrical / EPLAN)",
        "focus_en": "electric machines, variable speed drives, MV/LV power distribution and industrial CAD (AutoCAD Electrical / EPLAN)"
    },
    "automation_scada": {
        "label": "🏭 Focus Automatisme Industriel & SCADA",
        "description": "Met en avant la programmation d'automates PLC Siemens (TIA Portal), Schneider (EcoStruxure) et supervision SCADA.",
        "tagline_fr": "Élève-ingénieur en Automatisme Industriel & Contrôle Commande",
        "tagline_en": "Industrial Automation & Control Systems Engineering student",
        "focus_fr": "programmation d'automates PLC (Siemens TIA Portal S7-1200/1500, Schneider EcoStruxure), supervision SCADA (WinCC) et réseaux industriels (Modbus, Profinet)",
        "focus_en": "PLC programming (Siemens TIA Portal S7-1200/1500, Schneider EcoStruxure), SCADA supervision (WinCC) and industrial fieldbuses (Modbus, Profinet)"
    },
    "embedded_edge_ai": {
        "label": "🧠 Focus Systèmes Embarqués, Edge AI & IoT",
        "description": "Met en avant les microcontrôleurs STM32/ESP32, le traitement d'images sur Jetson/Raspberry Pi et les protocoles IoT.",
        "tagline_fr": "Élève-ingénieur en Systèmes Embarqués Temps Réel & Edge AI",
        "tagline_en": "Embedded Systems & Edge AI Engineering student",
        "focus_fr": "développement temps réel (STM32, C/C++, FreeRTOS), Edge AI sur Raspberry Pi & Jetson Nano (OpenCV), protocoles IoT (MQTT, LoRaWAN)",
        "focus_en": "real-time embedded systems (STM32, C/C++, FreeRTOS), Edge AI on Jetson/Raspberry Pi (OpenCV), and IoT protocols (MQTT, LoRaWAN)"
    },
    "custom": {
        "label": "✍️ Directive Personnalisée Libre",
        "description": "Applique une directive ou un pitch sur-mesure saisi par l'utilisateur.",
        "tagline_fr": "Élève-ingénieur en Génie Électrique & Contrôle Industriel",
        "tagline_en": "Final-year Electrical & Industrial Control Engineering student",
        "focus_fr": "ingénierie appliquée, innovation et projets sur-mesure",
        "focus_en": "applied engineering, innovation and tailored projects"
    }
}

WRITING_STYLES = {
    "persuasive_tech": {
        "label": "🎯 Équilibré & Persuasif Ingénieur (Recommandé)",
        "prompt_fr": "Adopte un ton naturel, dynamique, humble mais très technique et convaincant. Montre une réelle admiration pour le travail de l'entreprise.",
        "prompt_en": "Adopt a natural, dynamic, humble yet highly technical and compelling tone. Demonstrate genuine admiration for the company's work."
    },
    "deep_tech_rd": {
        "label": "🔬 R&D & Technique Approfondi",
        "prompt_fr": "Adopte un ton axé recherche appliquée, défis de modélisation, architecture système et rigueur scientifique.",
        "prompt_en": "Adopt an R&D-oriented tone focusing on modeling challenges, system architecture, and scientific precision."
    },
    "direct_executive": {
        "label": "👔 Direct, Court & Percutant (Executive)",
        "prompt_fr": "Reste très concis (moins de 120 mots), direct au but, mettant immédiatement en valeur le profil et la valeur ajoutée.",
        "prompt_en": "Keep it ultra-concise (under 120 words), direct to the point, highlighting immediate value proposition."
    },
    "expert_mentorship": {
        "label": "🤝 Demande de Conseil & Mentorat",
        "prompt_fr": "Adopte une posture d'apprentissage, sollicitant l'avis d'un expert/aîné sur son portfolio avant de sonder les opportunités de stage.",
        "prompt_en": "Adopt a learning posture, asking for an expert's advice on the portfolio before inquiring about internship opportunities."
    }
}

def detect_best_theme_for_company(company: str = "", role: str = "", industry: str = "") -> str:
    """Intelligently detects the most matching technical theme based on company name, industry, and role."""
    combined = f"{company} {role} {industry}".lower()
    
    # Solar & Renewable Energy Keywords
    if any(k in combined for k in [
        "solar", "solaire", "photovolta", "pv", "energie", "energy", "renewable", "renouvelable", 
        "totalenergies", "engie", "edf", "voltalia", "neoen", "cegelec", "green", "climat", "eolien"
    ]):
        return "solar_energy"
        
    # Drones, Aeronautics & Defense Keywords
    if any(k in combined for k in [
        "drone", "uav", "robot", "parrot", "novadem", "delair", "atec", "skydio", "skydrone", "cerbair",
        "hexadrone", "airbus", "thales", "dassault", "mbda", "seaber", "sbg", "sonaca", "volocopter", "aero", "aérien", "defense", "défense", "spatial"
    ]):
        return "drones_robotics"
        
    # Automation, PLC & SCADA Keywords
    if any(k in combined for k in [
        "automati", "scada", "plc", "automate", "siemens", "schneider", "rockwell", "abb", "ocp", 
        "usine", "process", "manufactur", "production", "industrie 4", "instrumentation"
    ]):
        return "automation_scada"
        
    # Embedded Systems & Edge AI Keywords
    if any(k in combined for k in [
        "embarqu", "embedded", "stm32", "microcontrol", "firmware", "iot", "edge", "computer vision", "vision", "harmattan", "capgemini", "altran"
    ]):
        return "embedded_edge_ai"
        
    # Power & Electrical Engineering Keywords
    if any(k in combined for k in [
        "electr", "électr", "puissance", "variateur", "transformateur", "reseau", "réseau", "distribution", "bt", "ht"
    ]):
        return "electrical_power"
        
    return "auto"

def determine_language(contact: Dict[str, Any], user_forced_lang: Optional[str] = None) -> str:
    """Returns 'fr' or 'en' based on preference or contact location."""
    if user_forced_lang in ["fr", "en"]:
        return user_forced_lang
    
    country = str(contact.get("country", "") or contact.get("location", "") or contact.get("pays", "") or contact.get("ville", ""))
    
    lang_col = str(contact.get("language", "") or contact.get("lang", "")).strip().lower()
    if "en" in lang_col or "anglais" in lang_col:
        return "en"
    if "fr" in lang_col or "francais" in lang_col:
        return "fr"
        
    return "fr" if is_francophone(country) else "en"

def classify_role_category(role: str) -> str:
    """Classifies a job title into one of the strategic outreach personas."""
    r = (role or "").lower()
    if any(k in r for k in ["recrut", "talent", "rh", "hr", "campus", "people", "ressources humaines", "acquisition", "headhunter", "chasseur", "staffing"]):
        return "RH_TALENT"
    elif any(k in r for k in ["ceo", "fondateur", "founder", "directeur général", "directeur general", "general manager", "president", "président", "vp", "gerant", "gérant", "managing director", "co-founder", "pdg", "dg", "dirigeant", "associé", "partner", "chief executive"]):
        return "CEO_DIRECTEUR"
    elif any(k in r for k in ["r&d", "recherche", "architect", "lead", "cto", "direction technique", "system engineer", "systèmes critiques", "expert", "scientifique", "innovation", "tech lead"]):
        return "RD_LEAD_ARCHITECT"
    elif any(k in r for k in ["ingenieur", "ingénieur", "engineer", "chef de projet", "software", "hardware", "embarque", "embarqué", "robotique", "drones", "automatisme", "developpeur", "développeur"]):
        return "INGENIEUR_TECH"
    elif any(k in r for k in ["produit", "product", "business", "bizdev", "commercial", "sales", "partenariat", "marketing", "consultant"]):
        return "PRODUCT_BIZDEV"
    return "INGENIEUR_TECH"

def get_target_subject(persona: str, theme: str = "auto", company: str = "", language: str = "fr") -> str:
    """Returns an attractive, persona-tailored subject line."""
    if theme == "drones_robotics":
        th_fr, th_hr_fr = "les systèmes embarqués et les drones", "systèmes embarqués et drones"
        th_en, th_hr_en = "embedded systems & robotics", "Embedded Systems & Drones"
    elif theme == "solar_energy":
        th_fr, th_hr_fr = "l'énergie solaire photovoltaïque", "énergie solaire et génie électrique"
        th_en, th_hr_en = "solar energy", "Solar Energy & Power Systems"
    elif theme == "automation_scada":
        th_fr, th_hr_fr = "l'automatisme industriel & SCADA", "automatisme industriel et SCADA"
        th_en, th_hr_en = "industrial automation", "Industrial Automation & SCADA"
    elif theme == "embedded_edge_ai":
        th_fr, th_hr_fr = "les systèmes embarqués temps réel", "systèmes embarqués et Edge AI"
        th_en, th_hr_en = "embedded systems", "Embedded Systems & Edge AI"
    elif theme == "electrical_power":
        th_fr, th_hr_fr = "le génie électrique et l'électrotechnique", "génie électrique et électrotechnique"
        th_en, th_hr_en = "electrical engineering", "Electrical Engineering & Power Systems"
    else:
        th_fr, th_hr_fr = "les systèmes embarqués et les drones", "systèmes embarqués et drones"
        th_en, th_hr_en = "embedded systems & robotics", "Embedded Systems & Drones"

    comp_name = company.strip() if company.strip() and company.strip().lower() not in ["votre entreprise", "n/a", ""] else "[Entreprise]"

    if language == "fr":
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
            return f"PFE Internship Opportunity at {comp_name}"

def build_system_prompt(theme: str = "auto", tone: str = "persuasive_tech") -> str:
    theme_info = THEMES_CATALOG.get(theme, THEMES_CATALOG["auto"])
    style_info = WRITING_STYLES.get(tone, WRITING_STYLES["persuasive_tech"])
    
    return f"""Tu es un assistant expert de haut niveau en prospection personnalisée et en communication d'ingénierie pour Mohammed HSINY.
Ton rôle est de générer des emails de prospection froide (Cold Outreach) pour sa recherche de stage de fin d'études (PFE) de 6 mois (Génie Électrique & Contrôle Industriel - FST Mohammedia).

PROFIL CANDIDAT :
- Nom : Mohammed HSINY
- Formation : Élève-Ingénieur en Génie Électrique & Contrôle Industriel (FST Mohammedia, Maroc)
- Rôle associatif : Président du Club Robotique & Innovation RoboThings (FSTM)
- Portfolio en ligne : https://portfolio-mohammed-hsiny-ux7z.vercel.app/
- Disponibilité : Stage PFE de 6 mois à partir de Janvier 2027

THÉMATIQUE TECHNIQUE SÉLECTIONNÉE :
- Thème : {theme_info['label']}
- Compétences & projets clés à valoriser : {theme_info['focus_fr']}

STYLE RÉDACTIONNEL :
- {style_info['prompt_fr']}

STRUCTURE STRICTE SELON LE RÔLE (PERSONA DU DESTINATAIRE) :

1. VERSION POUR UN CEO / FONDATEUR / DIRIGEANT (CEO_DIRECTEUR) :
   - Objet : Votre vision chez [Nom de l'entreprise] – Étudiant passionné par [Thématique]
   - Salutation : Bonjour [Prénom],
   - Paragraphe 1 : J'espère que vous allez bien.
   - Paragraphe 2 : Je suis étudiant en dernière année d'ingénierie en Génie Électrique, passionné par [Thématique]. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE).
   - Paragraphe 3 : Je suis très motivé par l'idée de rejoindre [Nom de l'entreprise] et je suis sincèrement inspiré par votre vision et les projets que vous portez. Votre parcours et votre expertise dans le domaine sont pour moi une source de motivation.
   - Paragraphe 4 : Je me permets de vous contacter pour bénéficier de votre regard sur mon CV et mon portfolio. Si vous avez un moment, je serais très reconnaissant d'avoir votre avis pour m'aider à progresser.
   - Paragraphe 5 : Je me demande aussi s'il y aurait des opportunités de stage au sein de votre équipe ou dans vos services.
   - Lien : [Explorer mon Portfolio Interactif ↗](https://portfolio-mohammed-hsiny-ux7z.vercel.app/)
   - Clôture : Merci d'avance pour votre temps.\n\nBien cordialement,

2. VERSION POUR UN RH / RECRUTEUR / TALENT ACQUISITION (RH_TALENT) :
   - Objet : Candidature – Stage PFE en [Thématique]
   - Salutation : Bonjour [Prénom],
   - Paragraphe 1 : J'espère que vous allez bien.
   - Paragraphe 2 : Je suis étudiant en dernière année d'ingénierie en Génie Électrique, passionné par [Thématique]. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE).
   - Paragraphe 3 : Je suis très motivé par l'idée de rejoindre [Nom de l'entreprise] et je suis sincèrement inspiré par vos projets et votre expertise dans le domaine.
   - Paragraphe 4 : Je me permets de vous contacter pour savoir s'il y aurait des opportunités de stage au sein de votre entreprise. Je suis disponible pour un PFE de 6 mois à partir de janvier 2027.
   - Paragraphe 5 : Je vous joins mon CV et mon portfolio pour plus de détails.
   - Lien : [Explorer mon Portfolio Interactif ↗](https://portfolio-mohammed-hsiny-ux7z.vercel.app/)
   - Clôture : Merci d'avance pour votre temps.\n\nBien cordialement,

3. VERSION POUR UN INGÉNIEUR / CHEF DE PROJET / TECH LEAD / R&D (INGENIEUR_TECH / RD_LEAD_ARCHITECT) :
   - Objet : Votre parcours chez [Nom de l'entreprise] – Étudiant passionné par [Thématique]
   - Salutation : Bonjour [Prénom],
   - Paragraphe 1 : J'espère que vous allez bien.
   - Paragraphe 2 : Je suis étudiant en dernière année d'ingénierie en Génie Électrique, passionné par [Thématique]. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE).
   - Paragraphe 3 : En découvrant votre parcours, j'ai été vraiment inspiré par votre travail et par les projets sur lesquels vous intervenez. Votre expertise dans le domaine est pour moi une source de motivation.
   - Paragraphe 4 : Je me permets de vous contacter pour bénéficier de votre regard sur mon CV et mon portfolio. Si vous avez un moment, je serais très reconnaissant d'avoir votre avis pour m'aider à progresser.
   - Paragraphe 5 : Je me demande aussi s'il y aurait des opportunités de stage au sein de votre équipe.
   - Lien : [Explorer mon Portfolio Interactif ↗](https://portfolio-mohammed-hsiny-ux7z.vercel.app/)
   - Clôture : Merci d'avance pour votre temps.\n\nBien cordialement,

RÈGLES D'OR ABSOLUES :
1. TOUJOURS insérer le prénom réel du contact (ou 'Madame, Monsieur' si absent).
2. TOUJOURS insérer le vrai nom de l'entreprise cible (remplacer dynamiquement toute mention de société).
3. AUCUNE phrase répétée ou redondante.
4. Terminer toujours par 'Bien cordialement,' sans signature texte superflue (la signature électronique complète est insérée automatiquement).

FORMAT DE SORTIE (JSON STRICT OBLIGATOIRE) :
```json
{{
  "subject": "Objet adapté selon le persona et l'entreprise",
  "body_plain_text": "Le texte complet et fluide de l'email"
}}
```
"""

def build_user_prompt(
    contact: Dict[str, Any], 
    profile: CandidateProfile, 
    language: str = "fr", 
    theme: str = "auto",
    custom_instruction: str = "",
    tone: str = "persuasive_tech"
) -> str:
    first_name = contact.get("first_name") or contact.get("prenom") or ""
    last_name = contact.get("last_name") or contact.get("nom") or ""
    full_name = contact.get("name") or f"{first_name} {last_name}".strip() or "Madame, Monsieur"
    if not first_name and full_name and full_name != "Madame, Monsieur":
        first_name = full_name.split()[0]
        
    role = contact.get("role") or contact.get("poste") or contact.get("title") or "Ingénieur"
    company = contact.get("company") or contact.get("entreprise") or contact.get("societe") or "votre entreprise"
    industry = contact.get("industry") or contact.get("secteur") or ""
    persona = classify_role_category(role)
    salutation_name = first_name if first_name else "Madame, Monsieur"
    
    # Auto-detect theme if requested
    effective_theme = theme
    if theme == "auto":
        effective_theme = detect_best_theme_for_company(company, role, industry)

    theme_meta = THEMES_CATALOG.get(effective_theme, THEMES_CATALOG["auto"])
    
    custom_block = f"\nDIRECTIVE SPÉCIALE UTILISATEUR : {custom_instruction}\n" if custom_instruction.strip() else ""

    if language == "fr":
        return f"""
DONNÉES DU DESTINATAIRE (ISSUES DU FICHIER EXCEL) :
- Prénom : {first_name}
- Nom complet : {full_name}
- Salutation exacte : Bonjour {salutation_name},
- Poste exact : {role}
- Persona détecté : {persona} (CEO_DIRECTEUR / RH_TALENT / INGENIEUR_TECH)
- Société cible : {company}
- Secteur / Industrie : {industry}

ANGLE TECHNIQUE :
- Thème : {theme_meta['label']}
- Compétences à valoriser : {theme_meta['focus_fr']}
{custom_block}
Rédige l'email parfait pour {salutation_name} chez {company} en respectant strictement la structure adaptée à son persona ({persona}).

FORMAT DE SORTIE JSON STRICT :
```json
{{
  "subject": "Objet selon le persona et la thématique",
  "body_plain_text": "Texte complet de l'email"
}}
```
"""
    else:
        return f"""
RECIPIENT DATA (FROM EXCEL FILE):
- First Name: {first_name}
- Full Name: {full_name}
- Salutation: Hi {salutation_name},
- Exact Role: {role}
- Persona Category: {persona} (CEO_DIRECTEUR / RH_TALENT / INGENIEUR_TECH)
- Target Company: {company}
- Industry: {industry}

TECHNICAL FOCUS ANGLE:
- Theme: {theme_meta['label']}
- Highlights: {theme_meta['focus_en']}
{custom_block}
Write the perfect outreach email in English for {salutation_name} at {company} following the precise structure for persona {persona}.

JSON STRICT OUTPUT:
```json
{{
  "subject": "Persona-aligned subject line",
  "body_plain_text": "Full email body"
}}
```
"""

def build_template_adaptation_system_prompt() -> str:
    return """Tu es un assistant expert en communication professionnelle et cold outreach pour Mohammed HSINY.
L'utilisateur te fournit un MODÈLE D'EMAIL DE RÉFÉRENCE (un template ou exemple rédigé par ses soins).

TON RÔLE :
Adapter intelligemment cet email de référence pour CHAQUE destinataire cible :
1. **Remplacement Intégral des Noms & Salutations** : Si le modèle contient 'Bonjour Bruno,' ou tout autre prénom/nom, remplace-le OBLIGATOIREMENT par le prénom du contact cible ('Bonjour [Prénom],').
2. **Remplacement Intégral de l'Entreprise** : Si le modèle contient 'Shark Robotics' ou toute autre entreprise, remplace-le OBLIGATOIREMENT par la société réelle du contact.
3. **Adaptation par Rôle / Persona (Excel)** :
   - Si le contact est un **CEO / Dirigeant** : adapter le message pour parler de sa vision et solliciter son regard de dirigeant.
   - Si le contact est un **RH / Recruteur** : adapter le message en candidature directe pour un PFE de 6 mois à partir de janvier 2027.
   - Si le contact est un **Ingénieur / Technique / R&D** : adapter le message pour valoriser son parcours technique et demander son avis d'ingénieur/expert.
4. **Thématique & Activité** : Adapter les mentions techniques selon le secteur d'activité réel de l'entreprise (Drones, Solaire, Automatisme, Systèmes Embarqués, Génie Électrique).
5. **Propreté** : Aucun crochet résiduel `[...]`, aucun doublon de phrase.

FORMAT DE SORTIE (JSON STRICT OBLIGATOIRE) :
```json
{
  "subject": "Objet adapté à l'entreprise et au persona",
  "body_plain_text": "Le texte complet de l'email adapté"
}
```
"""

def build_template_adaptation_user_prompt(
    template_text: str,
    contact: Dict[str, Any],
    profile: CandidateProfile,
    language: str = "fr",
    custom_instruction: str = ""
) -> str:
    first_name = contact.get("first_name") or contact.get("prenom") or ""
    last_name = contact.get("last_name") or contact.get("nom") or ""
    full_name = contact.get("name") or f"{first_name} {last_name}".strip() or "Madame, Monsieur"
    if not first_name and full_name and full_name != "Madame, Monsieur":
        first_name = full_name.split()[0]
        
    role = contact.get("role") or contact.get("poste") or contact.get("title") or "Responsable Technique"
    company = contact.get("company") or contact.get("entreprise") or contact.get("societe") or "votre entreprise"
    industry = contact.get("industry") or contact.get("secteur") or ""
    persona = classify_role_category(role)
    salutation_name = first_name if first_name else "Madame, Monsieur"
    
    custom_block = f"\nDIRECTIVE SUPPLÉMENTAIRE : {custom_instruction}\n" if custom_instruction.strip() else ""

    return f"""
MODÈLE D'EMAIL DE RÉFÉRENCE FOURNI PAR MOHAMMED :
\"\"\"
{template_text}
\"\"\"

DONNÉES DU DESTINATAIRE CIBLE :
- Prénom : {first_name}
- Nom complet : {full_name}
- Salutation à utiliser : {salutation_name}
- Poste exact : {role} (Catégorie : {persona})
- Société / Entreprise : {company}
- Secteur d'activité : {industry}
{custom_block}
Adapte ce modèle de référence spécifiquement pour {salutation_name} chez {company}. 
Remplace toutes les variables et personnalise les références à l'entreprise et à son secteur tout en conservant le style du modèle.

FORMAT DE SORTIE JSON STRICT :
```json
{{
  "subject": "Objet de l'email adapté",
  "body_plain_text": "Texte complet de l'email adapté"
}}
```
"""

