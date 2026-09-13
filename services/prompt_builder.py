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
    "build_system_prompt",
    "build_user_prompt",
    "build_template_adaptation_system_prompt",
    "build_template_adaptation_user_prompt",
]

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
    """Classifies a job title into one of the 5 strategic outreach personas."""
    r = (role or "").lower()
    if any(k in r for k in ["recrut", "talent", "rh", "hr", "campus", "people", "ressources humaines", "acquisition", "headhunter", "chasseur"]):
        return "RH_TALENT"
    elif any(k in r for k in ["produit", "product", "business", "bizdev", "commercial", "sales", "partenariat", "marketing", "consultant"]):
        return "PRODUCT_BIZDEV"
    elif any(k in r for k in ["ceo", "fondateur", "founder", "directeur général", "general manager", "president", "vp", "gerant", "managing director", "co-founder"]):
        return "CEO_DIRECTEUR"
    elif any(k in r for k in ["r&d", "recherche", "architect", "lead", "cto", "direction technique", "system engineer", "systèmes critiques", "expert", "scientifique", "innovation"]):
        return "RD_LEAD_ARCHITECT"
    elif any(k in r for k in ["ingenieur", "ingénieur", "engineer", "chef de projet", "software", "hardware", "embarque", "embarqué", "robotique", "drones", "automatisme", "developpeur", "développeur"]):
        return "INGENIEUR_TECH"
    return "INGENIEUR_TECH"

def get_target_subject(persona: str, theme: str = "auto", language: str = "fr") -> str:
    """Returns an attractive, contextualized subject line."""
    if language == "fr":
        if persona in ["INGENIEUR_TECH", "RD_LEAD_ARCHITECT", "CEO_DIRECTEUR"]:
            return "Stage PFE – Demande de conseil"
        else:
            return "Stage PFE – Demande d'information"
    else:
        if persona in ["INGENIEUR_TECH", "RD_LEAD_ARCHITECT", "CEO_DIRECTEUR"]:
            return "PFE Internship – Advice Request"
        else:
            return "PFE Internship – Information Request"

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
- Contact : mohammedhsiny2@gmail.com | +212 611 424 571

THÉMATIQUE TECHNIQUE SÉLECTIONNÉE :
- Thème : {theme_info['label']}
- Compétences & projets clés à valoriser : {theme_info['focus_fr']}

STYLE RÉDACTIONNEL :
- {style_info['prompt_fr']}

RÈGLES D'OR DE PERSONNALISATION PROFONDE :
1. **Accroche Contextualisée sur l'Entreprise** : Ne te contente JAMAIS d'un copier-coller générique. Analyse l'activité de l'entreprise et montre précisément pourquoi Mohammed s'intéresse à leurs projets, leurs défis techniques ou leurs réalisations.
2. **Alignement des Compétences** : Si l'entreprise fait du Solaire/Énergie, oriente les arguments vers le photovoltaïque, les convertisseurs et les réseaux. Si elle fait des Drones/Robotique, oriente vers l'autonomie Pixhawk/ROS et RoboThings. Si elle fait de l'Automatisme, oriente vers Siemens/Schneider PLC et SCADA.
3. **Approche Psychologique par Rôle** :
   - *Ingénieur / Chef de projet* : Demander son regard technique d'aîné/expert sur le portfolio avant de mentionner un stage.
   - *Directeur R&D / Lead Tech* : Parler d'innovation, de défis de conception et de systèmes complexes.
   - *RH / Talent Acquisition* : Parler de motivation, d'adéquation au projet d'entreprise et de période de stage PFE (6 mois).
   - *CEO / Fondateur* : Message court, direct, inspiré par sa vision d'entreprise et orienté création de valeur.
4. **Variations Humaines** : Varie la tournure des phrases, évite les formules robotiques répétitives.
5. **Lien Portfolio & Coordonnées** : Insère toujours le lien du portfolio et la signature propre.

FORMAT DE SORTIE (JSON STRICT OBLIGATOIRE) :
```json
{{
  "subject": "Objet percutant et professionnel",
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
        
    role = contact.get("role") or contact.get("poste") or contact.get("title") or "Responsable Technique"
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
DONNÉES DU DESTINATAIRE :
- Prénom : {first_name}
- Nom complet : {full_name}
- Poste exact : {role}
- Catégorie de profil : {persona}
- Société / Entreprise : {company}
- Secteur / Domaine : {industry}

ANGLE TECHNIQUE À ADOPTER :
- Thème : {theme_meta['label']}
- Piliers à mettre en avant : {theme_meta['focus_fr']}
{custom_block}
Rédige un email ultra-personnalisé en français pour {salutation_name} chez {company}. L'email doit être chaleureux, professionnel, valoriser les projets de {company} et mettre en avant les compétences de Mohammed adaptées à cette entreprise.

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
RECIPIENT DATA:
- First Name: {first_name}
- Full Name: {full_name}
- Role / Job Title: {role}
- Persona: {persona}
- Company: {company}
- Industry: {industry}

TECHNICAL FOCUS ANGLE:
- Theme: {theme_meta['label']}
- Key highlights: {theme_meta['focus_en']}
{custom_block}
Write a highly personalized cold outreach email in English for {salutation_name} at {company}. The email should be engaging, technical, highlight why {company}'s work is inspiring, and present Mohammed's tailored value proposition.

JSON STRICT OUTPUT:
```json
{{
  "subject": "Compelling subject line",
  "body_plain_text": "Full email body"
}}
```
"""

def build_template_adaptation_system_prompt() -> str:
    return """Tu es un assistant expert en communication professionnelle et cold outreach pour Mohammed HSINY.
L'utilisateur te fournit un MODÈLE D'EMAIL DE RÉFÉRENCE (un template rédigé par ses soins).

TON RÔLE :
Conserver fidèlement le style, la structure et la logique du texte de référence fourni par Mohammed, tout en ADAPTANT ET CONTEXTUALISANT intelligemment pour chaque destinataire :
1. **Identité du Destinataire** : Remplacer les formules de salutation ([Prénom], [Nom], Madame, Monsieur) de façon naturelle.
2. **Entreprise Cible** : Remplacer [Entreprise], [Société], et contextualiser les phrases qui mentionnent l'activité ou les projets de cette société.
3. **Activité & Projets** : Si le texte mentionne des projets, adapte-les à ce que fait réellement l'entreprise (Drones, Solaire, Automatisme, Électrique, etc.).
4. **Fluidité & Qualité** : Garantir un texte parfait sans balises résiduelles (supprimer les crochets `[...]` ou `{{...}}`).
5. **Signature** : Conserver la signature de Mohammed HSINY avec le lien de son portfolio (https://portfolio-mohammed-hsiny-ux7z.vercel.app/).

FORMAT DE SORTIE (JSON STRICT OBLIGATOIRE) :
```json
{
  "subject": "Objet adapté à l'entreprise",
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

