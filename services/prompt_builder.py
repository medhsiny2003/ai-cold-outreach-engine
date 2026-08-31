import json
from typing import Dict, Any, Optional
from config import CandidateProfile, is_francophone

def determine_language(contact: Dict[str, Any], user_forced_lang: Optional[str] = None) -> str:
    """Returns 'fr' or 'en' based on preference or contact location."""
    if user_forced_lang in ["fr", "en"]:
        return user_forced_lang
    
    country = str(contact.get("country", "") or contact.get("location", "") or contact.get("pays", "") or contact.get("ville", ""))
    company = str(contact.get("company", "") or contact.get("entreprise", "") or contact.get("societe", ""))
    
    lang_col = str(contact.get("language", "") or contact.get("lang", "")).strip().lower()
    if "en" in lang_col or "anglais" in lang_col:
        return "en"
    if "fr" in lang_col or "francais" in lang_col:
        return "fr"
        
    return "fr" if is_francophone(country) else "en"

def classify_role_category(role: str) -> str:
    """Classifies a job title into one of the 5 strategic outreach personas."""
    r = role.lower()
    if any(k in r for k in ["recrut", "talent", "rh", "hr", "campus", "people", "ressources humaines", "acquisition"]):
        return "RH_TALENT"
    elif any(k in r for k in ["produit", "product", "business", "bizdev", "commercial", "sales", "partenariat", "marketing"]):
        return "PRODUCT_BIZDEV"
    elif any(k in r for k in ["ceo", "fondateur", "founder", "directeur général", "general manager", "president", "vp", "gerant", "managing director"]):
        return "CEO_DIRECTEUR"
    elif any(k in r for k in ["r&d", "recherche", "architect", "lead", "cto", "direction technique", "system engineer", "systèmes critiques", "expert", "scientifique", "innovation"]):
        return "RD_LEAD_ARCHITECT"
    elif any(k in r for k in ["ingenieur", "ingénieur", "engineer", "chef de projet", "software", "hardware", "embarque", "embarqué", "robotique", "drones", "automatisme", "developpeur", "développeur"]):
        return "INGENIEUR_TECH"
    return "INGENIEUR_TECH"

def get_target_subject(persona: str, language: str = "fr") -> str:
    """Returns the exact required subject line based on persona and language."""
    if persona in ["INGENIEUR_TECH", "RD_LEAD_ARCHITECT", "CEO_DIRECTEUR"]:
        return "Stage PFE – Demande de conseil"
    else:
        return "Stage PFE – Demande d'information"

def build_system_prompt() -> str:
    return """Tu es un assistant expert dans la rédaction d'emails professionnels pour la recherche de stage PFE pour Mohammed HSINY.

Voici les 5 MODÈLES DE RÉFÉRENCE ABSOLUS que tu dois adapter avec précision selon le profil du destinataire :

---
1. POUR UN INGÉNIEUR / CHEF DE PROJET TECHNIQUE
Objet : Stage PFE – Demande de conseil
Corps :
Bonjour [Prénom],

J'espère que vous allez bien.

Je suis étudiant en dernière année d'ingénierie en Génie Électrique, passionné par les systèmes embarqués, la robotique et les drones. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE).

Je suis très motivé par l'idée de rejoindre [Nom de l'entreprise] et je suis sincèrement inspiré par vos projets et votre expertise dans le domaine.

En découvrant votre parcours, j'ai été vraiment inspiré par votre travail et par les projets sur lesquels vous intervenez.

Je me permets de vous contacter pour bénéficier de votre regard sur mon CV et mon portfolio. Si vous avez un moment, je serais très reconnaissant d'avoir votre avis pour m'aider à progresser.

Je me demande aussi s'il y aurait des opportunités de stage au sein de votre équipe ou dans vos services.

Portfolio : https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Merci d'avance pour votre temps.

Bien cordialement,
Mohammed HSINY
+212 611 424 571
mohammedhsiny2@gmail.com

---
2. POUR UN PROFIL R&D / LEAD TECH / ARCHITECTE SYSTÈME
Objet : Stage PFE – Demande de conseil
Corps :
Bonjour [Prénom],

J'espère que vous allez bien.

Je suis étudiant en dernière année d'ingénierie en Génie Électrique, passionné par les systèmes embarqués, la robotique et les drones. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE).

Je suis très motivé par l'idée de rejoindre [Nom de l'entreprise] et je suis sincèrement inspiré par vos projets R&D, vos défis d'ingénierie et l'innovation technologique que vous portez.

En découvrant votre parcours et votre rôle en R&D, j'ai été particulièrement impressionné par la technicité et la complexité des systèmes que vous développez.

Je me permets de vous contacter pour bénéficier de votre regard d'expert sur mon CV et mon portfolio de projets. Si vous avez un moment, je serais très reconnaissant d'avoir votre avis et vos conseils pour m'aider à progresser.

Je me demande également s'il y aurait des opportunités de stage PFE au sein de vos équipes R&D ou de conception.

Portfolio : https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Merci d'avance pour votre temps.

Bien cordialement,
Mohammed HSINY
+212 611 424 571
mohammedhsiny2@gmail.com

---
3. POUR UN RESPONSABLE RH / TALENT ACQUISITION
Objet : Stage PFE – Demande d'information
Corps :
Bonjour [Prénom],

J'espère que vous allez bien.

Je suis étudiant en dernière année d'ingénierie en Génie Électrique, passionné par les systèmes embarqués, la robotique et les drones. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE).

Je suis très motivé par l'idée de rejoindre [Nom de l'entreprise] et je suis sincèrement inspiré par votre vision et votre impact dans le secteur.

En voyant votre parcours, j'ai été vraiment inspiré par votre rôle et par la manière dont vous contribuez à faire évoluer les talents dans ce domaine.

Je me permets de vous contacter pour savoir s'il existe des opportunités de stage dans les domaines qui me passionnent. Je serais ravi d'avoir votre regard sur mon profil et de discuter des possibilités au sein de votre entreprise.

Portfolio : https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Merci d'avance pour votre temps.

Bien cordialement,
Mohammed HSINY
+212 611 424 571
mohammedhsiny2@gmail.com

---
4. POUR UN CEO / DIRECTEUR GÉNÉRAL
Objet : Stage PFE – Demande de conseil
Corps :
Bonjour [Prénom],

J'espère que vous allez bien.

Je suis étudiant en dernière année d'ingénierie en Génie Électrique, passionné par les systèmes embarqués, la robotique et les drones. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE).

Je suis très motivé par l'idée de rejoindre [Nom de l'entreprise] et je suis sincèrement inspiré par votre vision et l'ambition de vos projets.

J'ai eu l'occasion de découvrir votre travail et je suis vraiment admiratif de ce que vous accomplissez.

Je me permets de vous contacter pour bénéficier de votre regard sur mon parcours. Si vous avez un moment, je serais ravi d'avoir vos conseils pour évoluer dans ce secteur.

Portfolio : https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Merci d'avance pour votre temps.

Bien cordialement,
Mohammed HSINY
+212 611 424 571
mohammedhsiny2@gmail.com

---
5. POUR UN RESPONSABLE PRODUIT / BUSINESS DEVELOPER
Objet : Stage PFE – Demande d'information
Corps :
Bonjour [Prénom],

J'espère que vous allez bien.

Je suis étudiant en dernière année d'ingénierie en Génie Électrique, passionné par les systèmes embarqués et la robotique. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE).

Je suis très motivé par l'idée de rejoindre [Nom de l'entreprise] et je suis sincèrement inspiré par votre approche produit et votre vision du marché.

Votre travail m'a beaucoup intéressé et je serais ravi d'échanger avec vous sur vos projets et les opportunités pour un jeune ingénieur passionné.

Portfolio : https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Merci d'avance.

Bien cordialement,
Mohammed HSINY
+212 611 424 571
mohammedhsiny2@gmail.com

---
FORMAT DE SORTIE (JSON STRICT) :
```json
{
  "subject": "L'objet exact selon le profil",
  "body_plain_text": "Le texte complet de l'email avec les remplacements"
}
```
"""

def build_user_prompt(contact: Dict[str, Any], profile: CandidateProfile, language: str = "fr", tone: str = "persuasive_tech") -> str:
    first_name = contact.get("first_name") or contact.get("prenom") or ""
    last_name = contact.get("last_name") or contact.get("nom") or ""
    full_name = contact.get("name") or f"{first_name} {last_name}".strip() or "Madame, Monsieur"
    if not first_name and full_name and full_name != "Madame, Monsieur":
        first_name = full_name.split()[0]
        
    role = contact.get("role") or contact.get("poste") or contact.get("title") or "Responsable"
    company = contact.get("company") or contact.get("entreprise") or contact.get("societe") or "votre entreprise"
    persona = classify_role_category(role)

    salutation_name = first_name if first_name else "Madame, Monsieur"

    if language == "fr":
        return f"""
DESTINATAIRE :
- Prénom : {first_name}
- Nom complet : {full_name}
- Poste / Titre : {role}
- Catégorie : {persona}
- Société / Entreprise : {company}

Génère l'email correspondant exactement au modèle '{persona}' pour {salutation_name} chez {company}.

FORMAT DE SORTIE JSON STRICT :
```json
{{
  "subject": "Objet selon le profil",
  "body_plain_text": "Texte exact avec les remplacements de [Prénom] et [Nom de l'entreprise]"
}}
```
"""
    else:
        return f"""
RECIPIENT:
- First Name: {first_name}
- Full Name: {full_name}
- Role: {role}
- Persona: {persona}
- Company: {company}

Generate the corresponding outreach email in English for {salutation_name} at {company}.

JSON OUTPUT:
```json
{{
  "subject": "Subject line",
  "body_plain_text": "Full email text"
}}
```
"""
