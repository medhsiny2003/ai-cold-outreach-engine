import json
import re
import httpx
from typing import Dict, Any, Optional
from config import LLMSettings, CandidateProfile
from services.prompt_builder import (
    build_system_prompt,
    build_user_prompt,
    determine_language,
    build_template_adaptation_system_prompt,
    build_template_adaptation_user_prompt
)

__all__ = [
    "GeneratedEmail",
    "generate_email_for_contact",
    "generate_email_from_template",
    "adapt_template_offline",
    "clean_json_response"
]

class GeneratedEmail:
    def __init__(self, subject: str, body: str, language: str):
        self.subject = subject.strip()
        self.body = body.strip()
        self.language = language

    def to_dict(self) -> Dict[str, str]:
        return {
            "subject": self.subject,
            "body": self.body,
            "language": self.language
        }

def clean_json_response(raw_text: str) -> Dict[str, Any]:
    """Extracts and parses JSON from raw LLM output."""
    text = raw_text.strip()
    
    # Try finding markdown code block
    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if json_match:
        text = json_match.group(1).strip()
    else:
        # Try finding outer braces
        first_brace = text.find("{")
        last_brace = text.rfind("}")
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            text = text[first_brace:last_brace+1]
            
    try:
        return json.loads(text)
    except Exception as e:
        # Basic heuristic cleanup for unescaped newlines inside JSON string values
        try:
            # Replace raw newlines in string properties
            return json.loads(text.replace("\r\n", "\\n").replace("\n", "\\n"))
        except Exception:
            raise ValueError(f"Could not parse LLM JSON output: {e}\nRaw: {raw_text[:200]}")

async def call_gemini_api(api_key: str, model_name: str, system_prompt: str, user_prompt: str, temperature: float = 0.6) -> str:
    """Call Google Gemini REST API."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={api_key}"
    
    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": f"{system_prompt}\n\n{user_prompt}"}]
            }
        ],
        "generationConfig": {
            "temperature": temperature,
            "responseMimeType": "application/json"
        }
    }
    
    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(url, json=payload)
        if response.status_code != 200:
            error_data = response.text
            raise RuntimeError(f"Gemini API error ({response.status_code}): {error_data}")
            
        data = response.json()
        try:
            return data["candidates"][0]["content"]["parts"][0]["text"]
        except (KeyError, IndexError) as e:
            raise RuntimeError(f"Unexpected Gemini response structure: {data}")

async def call_openai_compatible_api(
    base_url: str,
    api_key: str,
    model_name: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0.6
) -> str:
    """Call OpenAI or OpenAI-compatible endpoint (Groq, DeepSeek, Ollama, OpenRouter)."""
    if not base_url.endswith("/chat/completions"):
        base_url = base_url.rstrip("/") + "/chat/completions"
        
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}" if api_key else "Bearer none"
    }
    
    payload = {
        "model": model_name,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt}
        ],
        "temperature": temperature,
        "response_format": {"type": "json_object"}
    }
    
    async with httpx.AsyncClient(timeout=45.0) as client:
        response = await client.post(base_url, headers=headers, json=payload)
        if response.status_code != 200:
            raise RuntimeError(f"API error ({response.status_code}): {response.text}")
            
        data = response.json()
        return data["choices"][0]["message"]["content"]

from services.prompt_builder import (
    build_system_prompt, 
    build_user_prompt, 
    determine_language, 
    detect_best_theme_for_company, 
    THEMES_CATALOG, 
    WRITING_STYLES
)

def generate_fallback_template(
    contact: Dict[str, Any], 
    profile: CandidateProfile, 
    language: str,
    theme: str = "auto",
    custom_instruction: str = ""
) -> GeneratedEmail:
    """Smart persona & theme-based fallback template when offline or without API key."""
    name = contact.get("name") or contact.get("nom") or ""
    first_name = contact.get("first_name") or contact.get("prenom") or (name.split()[0] if name else "")
    company = contact.get("company") or contact.get("entreprise") or contact.get("societe") or "votre entreprise"
    role = contact.get("role") or contact.get("poste") or ""
    industry = contact.get("industry") or contact.get("secteur") or ""
    role_lower = role.lower()
    
    # Resolve Theme
    effective_theme = theme
    if theme == "auto":
        effective_theme = detect_best_theme_for_company(company, role, industry)
        
    is_hr = any(k in role_lower for k in ["recrut", "talent", "rh", "hr", "campus", "people", "ressources humaines", "acquisition", "headhunter"])
    is_product = any(k in role_lower for k in ["produit", "product", "business", "bizdev", "commercial", "sales", "partenariat", "marketing", "consultant"])
    is_ceo = any(k in role_lower for k in ["ceo", "fondateur", "founder", "directeur général", "general manager", "president", "vp", "gerant", "managing director"])
    is_rd = any(k in role_lower for k in ["r&d", "recherche", "architect", "lead", "cto", "direction technique", "system engineer", "systèmes critiques", "expert", "scientifique", "innovation"])
    
    # Theme specific phrasing (FR)
    if effective_theme == "solar_energy":
        tech_intro_fr = "spécialisé en énergie solaire, photovoltaïque et gestion intelligente de l'énergie (dimensionnement PV, convertisseurs MPPT, micro-réseaux et modélisation Matlab/Simulink)"
        comp_hook_fr = f"Je suis particulièrement attentif aux projets de transition énergétique et d'ingénierie solaire portés par {company}"
        tech_intro_en = "specialized in solar PV, power converters, battery energy storage and microgrid modeling"
        comp_hook_en = f"I am genuinely inspired by {company}'s leadership in clean energy and solar engineering"
    elif effective_theme == "drones_robotics":
        tech_intro_fr = "passionné par les systèmes embarqués, la robotique mobile et les drones autonomes (Président du Club RoboThings FSTM, pilotage autonome Pixhawk/PX4, ROS/ROS2, vision OpenCV)"
        comp_hook_fr = f"Je suis très motivé par l'idée de rejoindre {company} et je suis sincèrement inspiré par vos innovations et votre expertise dans les systèmes aériens et autonomes"
        tech_intro_en = "passionate about autonomous UAVs, flight controllers (Pixhawk/PX4), ROS, computer vision and President of the RoboThings Club"
        comp_hook_en = f"I am deeply inspired by {company}'s pioneering work in autonomous robotics and aerospace systems"
    elif effective_theme == "automation_scada":
        tech_intro_fr = "spécialisé en automatisme industriel, contrôle commande et supervision SCADA (automates Siemens S7-1200/1500 TIA Portal, Schneider EcoStruxure, supervision WinCC, réseaux Profinet/Modbus)"
        comp_hook_fr = f"Je suis très motivé par les projets d'automatisation, d'optimisation de procédés et d'Industrie 4.0 développés chez {company}"
        tech_intro_en = "specialized in industrial automation, PLC programming (Siemens TIA Portal, Schneider) and SCADA systems"
        comp_hook_en = f"I am impressed by {company}'s expertise in industrial automation and smart manufacturing"
    elif effective_theme == "embedded_edge_ai":
        tech_intro_fr = "spécialisé en systèmes embarqués temps réel et Edge AI (microcontrôleurs STM32/ESP32, traitement d'images sur Jetson Nano/Raspberry Pi avec OpenCV/YOLO, protocoles IoT)"
        comp_hook_fr = f"Je suis admiratif des technologies embarquées de pointe et des solutions intelligentes conçues chez {company}"
        tech_intro_en = "specialized in real-time embedded systems (STM32, FreeRTOS), Edge AI on Jetson/Raspberry Pi and IoT"
        comp_hook_en = f"I am truly inspired by {company}'s advanced embedded architectures and intelligent hardware solutions"
    elif effective_theme == "electrical_power":
        tech_intro_fr = "passionné par l'électrotechnique, l'électronique de puissance et les réseaux électriques (machines électriques, variateurs de vitesse, schémas AutoCAD Electrical/EPLAN, distribution HT/BT)"
        comp_hook_fr = f"Je suis particulièrement impressionné par le savoir-faire et l'envergure des réalisations électriques chez {company}"
        tech_intro_en = "passionate about power electrical engineering, motor drives, power distribution and CAD design"
        comp_hook_en = f"I am genuinely motivated by {company}'s high-standard electrical engineering projects"
    else:
        tech_intro_fr = "passionné par les systèmes embarqués, la robotique et le contrôle commande. Je suis basé au Maroc et je prépare activement mon stage de fin d'études (PFE) de 6 mois"
        comp_hook_fr = f"Je suis très motivé par l'idée de rejoindre {company} et je suis sincèrement inspiré par vos projets et votre expertise dans le domaine"
        tech_intro_en = "passionate about embedded systems, robotics and industrial control. Currently preparing my 6-month final graduation internship (PFE)"
        comp_hook_en = f"I am genuinely motivated by the prospect of contributing to {company} and inspired by your technical achievements"

    if language == "fr":
        salutation = f"Bonjour {first_name}," if first_name else "Bonjour,"
        
        # 1. PROFIL R&D / LEAD TECH / ARCHITECTE SYSTÈME
        if is_rd:
            subject = "Stage PFE – Demande de conseil"
            body = f"""{salutation}

J'espère que vous allez bien.

Je suis étudiant en dernière année d'ingénierie en Génie Électrique & Contrôle Industriel, {tech_intro_fr}.

{comp_hook_fr}. En découvrant votre rôle en R&D, j'ai été particulièrement impressionné par la technicité et la complexité des défis que vous relevez.

Je me permets de vous contacter pour bénéficier de votre regard d'expert sur mon CV et mes projets techniques. Si vous avez un moment, je serais très reconnaissant d'avoir votre avis et vos conseils pour m'aider à progresser.

Je me demande également s'il y aurait des opportunités de stage PFE de 6 mois au sein de vos équipes.

Portfolio : https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Merci d'avance pour votre temps.

Bien cordialement,
Mohammed HSINY
+212 611 424 571
mohammedhsiny2@gmail.com"""

        # 2. RESPONSABLE RH / TALENT ACQUISITION
        elif is_hr:
            subject = "Stage PFE – Demande d'information"
            body = f"""{salutation}

J'espère que vous allez bien.

Je suis étudiant en dernière année d'ingénierie en Génie Électrique & Contrôle Industriel (FST Mohammedia), {tech_intro_fr}.

{comp_hook_fr}. En voyant votre rôle, j'ai été inspiré par la manière dont vous accompagnez les talents et soutenez la croissance des équipes.

Je me permets de vous contacter pour savoir s'il existe des opportunités de stage PFE (Projet de Fin d'Études de 6 mois) dans ces domaines. Je serais ravi d'échanger avec vous et de vous présenter mon profil.

Portfolio : https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Merci d'avance pour votre temps.

Bien cordialement,
Mohammed HSINY
+212 611 424 571
mohammedhsiny2@gmail.com"""

        # 3. CEO / DIRECTEUR GÉNÉRAL
        elif is_ceo:
            subject = "Stage PFE – Demande de conseil"
            body = f"""{salutation}

J'espère que vous allez bien.

Élève-ingénieur en Génie Électrique & Contrôle Industriel, {tech_intro_fr}.

{comp_hook_fr}. J'ai découvert les réalisations de votre structure et je suis admiratif de votre vision et de votre dynamique d'innovation.

Je me permets de solliciter vos précieux conseils d'entrepreneur/dirigeant sur mon profil et mon portfolio de projets, et voir si une collaboration dans le cadre de mon PFE de 6 mois pourrait s'envisager.

Portfolio : https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Merci d'avance pour votre écoute.

Bien cordialement,
Mohammed HSINY
+212 611 424 571
mohammedhsiny2@gmail.com"""

        # 4. RESPONSABLE PRODUIT / BUSINESS DEVELOPER
        elif is_product:
            subject = "Stage PFE – Demande d'information"
            body = f"""{salutation}

J'espère que vous allez bien.

Élève-ingénieur en Génie Électrique & Contrôle Industriel, {tech_intro_fr}.

{comp_hook_fr}. Votre travail et votre vision produit m'ont vivement intéressé.

Je me permets de vous contacter pour échanger sur vos projets actuels et voir s'il existerait des perspectives de stage PFE pour apporter mon énergie technique à vos développements.

Portfolio : https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Merci d'avance pour votre temps.

Bien cordialement,
Mohammed HSINY
+212 611 424 571
mohammedhsiny2@gmail.com"""

        # 5. INGÉNIEUR / CHEF DE PROJET TECHNIQUE (Défaut)
        else:
            subject = "Stage PFE – Demande de conseil"
            body = f"""{salutation}

J'espère que vous allez bien.

Je suis étudiant en dernière année d'ingénierie en Génie Électrique & Contrôle Industriel, {tech_intro_fr}.

{comp_hook_fr}. En découvrant votre parcours technique, j'ai été vivement inspiré par les projets sur lesquels vous intervenez.

Je me permets de vous contacter pour bénéficier de votre regard d'ingénieur sur mon portfolio de projets. Si vous avez un instant, je serais très reconnaissant d'avoir votre avis technique.

Je me demande également s'il y aurait des opportunités de stage PFE de 6 mois au sein de votre équipe.

Portfolio : https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Merci d'avance pour votre temps.

Bien cordialement,
Mohammed HSINY
+212 611 424 571
mohammedhsiny2@gmail.com"""

    else:
        salutation = f"Hi {first_name}," if first_name else "Hello,"
        if is_hr or is_product:
            subject = "PFE Internship – Information Request"
        else:
            subject = "PFE Internship – Advice Request"
            
        body = f"""{salutation}

I hope you are doing well.

I am a final-year Electrical & Industrial Control Engineering student, {tech_intro_en}.

{comp_hook_en}.

I would be truly grateful for your insights on my projects and online portfolio:
https://portfolio-mohammed-hsiny-ux7z.vercel.app/

I was also wondering if there might be graduation internship (PFE) opportunities within your team for a duration of 6 months.

Thank you very much for your time and guidance.

Best regards,
Mohammed HSINY
+212 611 424 571
mohammedhsiny2@gmail.com"""

    return GeneratedEmail(subject=subject, body=body, language=language)

async def generate_email_for_contact(
    contact: Dict[str, Any],
    profile: CandidateProfile,
    settings: LLMSettings,
    forced_lang: Optional[str] = None,
    theme: str = "auto",
    custom_instruction: str = "",
    tone: str = "persuasive_tech"
) -> GeneratedEmail:
    """Generates a deeply personalized email for a contact using LLM with theme & company context."""
    language = determine_language(contact, forced_lang)
    
    # If no API key is set, fallback to high-quality dynamic template
    if not settings.api_key and settings.provider != "ollama":
        return generate_fallback_template(
            contact=contact, 
            profile=profile, 
            language=language, 
            theme=theme, 
            custom_instruction=custom_instruction
        )
        
    system_prompt = build_system_prompt(theme=theme, tone=tone)
    user_prompt = build_user_prompt(
        contact=contact, 
        profile=profile, 
        language=language, 
        theme=theme, 
        custom_instruction=custom_instruction, 
        tone=tone
    )
    
    try:
        if settings.provider == "gemini":
            raw_text = await call_gemini_api(
                api_key=settings.api_key,
                model_name=settings.model_name or "gemini-2.0-flash",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=settings.temperature
            )
        elif settings.provider == "openai":
            base_url = settings.api_base_url or "https://api.openai.com/v1"
            raw_text = await call_openai_compatible_api(
                base_url=base_url,
                api_key=settings.api_key,
                model_name=settings.model_name or "gpt-4o-mini",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=settings.temperature
            )
        elif settings.provider == "groq":
            base_url = settings.api_base_url or "https://api.groq.com/openai/v1"
            raw_text = await call_openai_compatible_api(
                base_url=base_url,
                api_key=settings.api_key,
                model_name=settings.model_name or "llama-3.3-70b-versatile",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=settings.temperature
            )
        elif settings.provider == "deepseek":
            base_url = settings.api_base_url or "https://api.deepseek.com"
            raw_text = await call_openai_compatible_api(
                base_url=base_url,
                api_key=settings.api_key,
                model_name=settings.model_name or "deepseek-chat",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=settings.temperature
            )
        elif settings.provider == "ollama":
            base_url = settings.api_base_url or "http://localhost:11434/v1"
            raw_text = await call_openai_compatible_api(
                base_url=base_url,
                api_key="ollama",
                model_name=settings.model_name or "llama3.2",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=settings.temperature
            )
        elif settings.provider == "openrouter":
            base_url = settings.api_base_url or "https://openrouter.ai/api/v1"
            raw_text = await call_openai_compatible_api(
                base_url=base_url,
                api_key=settings.api_key,
                model_name=settings.model_name or "meta-llama/llama-3.3-70b-instruct",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=settings.temperature
            )
        else:
            raise ValueError(f"Unknown provider: {settings.provider}")
            
        parsed = clean_json_response(raw_text)
        subject = parsed.get("subject", "").strip()
        body = parsed.get("body_plain_text", parsed.get("body", "")).strip()
        
        if not subject or not body:
            raise ValueError("Parsed JSON missing 'subject' or 'body_plain_text'")
            
        return GeneratedEmail(subject=subject, body=body, language=language)
        
    except Exception as e:
        # In case of API failure, log and return high quality fallback
        print(f"[LLM Warning] Generation failed for {contact.get('email')}: {e}. Using fallback template.")
        return generate_fallback_template(
            contact=contact, 
            profile=profile, 
            language=language, 
            theme=theme, 
            custom_instruction=custom_instruction
        )

from services.prompt_builder import (
    build_template_adaptation_system_prompt,
    build_template_adaptation_user_prompt
)

def adapt_template_offline(template_text: str, contact: Dict[str, Any], profile: CandidateProfile, language: str) -> GeneratedEmail:
    """Smart offline template adaptation replacing all variables, company references and placeholders."""
    first_name = contact.get("first_name") or contact.get("prenom") or ""
    name = contact.get("name") or contact.get("nom") or ""
    if not first_name and name:
        first_name = name.split()[0]
    salutation_name = first_name if first_name else "Madame, Monsieur"
    company = contact.get("company") or contact.get("entreprise") or contact.get("societe") or "votre entreprise"
    role = contact.get("role") or contact.get("poste") or ""
    
    text = template_text
    replacements = {
        r"\[Prénom\]|\[Prenom\]|\{\{prenom\}\}|\{\{first_name\}\}": salutation_name,
        r"\[Nom\]|\{\{nom\}\}|\{\{last_name\}\}": name,
        r"\[Nom de l'entreprise\]|\[Entreprise\]|\[Société\]|\[Societe\]|\[Nom de l'organisme\]|\{\{entreprise\}\}|\{\{company\}\}": company,
        r"\[Poste\]|\[Titre\]|\{\{poste\}\}|\{\{role\}\}": role,
    }
    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        
    subject = "Stage PFE – Demande de conseil"
    lines = text.split("\n")
    body_lines = []
    for line in lines:
        if line.strip().lower().startswith(("objet :", "objet:", "subject :", "subject:")):
            subject = re.sub(r"^(?:objet|subject)\s*:\s*", "", line, flags=re.IGNORECASE).strip()
        else:
            body_lines.append(line)
            
    body = "\n".join(body_lines).strip()
    return GeneratedEmail(subject=subject, body=body, language=language)

async def generate_email_from_template(
    template_text: str,
    contact: Dict[str, Any],
    profile: CandidateProfile,
    settings: LLMSettings,
    forced_lang: Optional[str] = None,
    custom_instruction: str = ""
) -> GeneratedEmail:
    """Adapts a user-provided template text to a specific contact using LLM (or offline fallback)."""
    language = determine_language(contact, forced_lang)
    
    if not settings.api_key and settings.provider != "ollama":
        return adapt_template_offline(template_text, contact, profile, language)
        
    system_prompt = build_template_adaptation_system_prompt()
    user_prompt = build_template_adaptation_user_prompt(
        template_text=template_text,
        contact=contact,
        profile=profile,
        language=language,
        custom_instruction=custom_instruction
    )
    
    try:
        if settings.provider == "gemini":
            raw_text = await call_gemini_api(
                api_key=settings.api_key,
                model_name=settings.model_name or "gemini-2.0-flash",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=settings.temperature
            )
        elif settings.provider == "openai":
            base_url = settings.api_base_url or "https://api.openai.com/v1"
            raw_text = await call_openai_compatible_api(
                base_url=base_url,
                api_key=settings.api_key,
                model_name=settings.model_name or "gpt-4o-mini",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=settings.temperature
            )
        elif settings.provider == "groq":
            base_url = settings.api_base_url or "https://api.groq.com/openai/v1"
            raw_text = await call_openai_compatible_api(
                base_url=base_url,
                api_key=settings.api_key,
                model_name=settings.model_name or "llama-3.3-70b-versatile",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=settings.temperature
            )
        elif settings.provider == "deepseek":
            base_url = settings.api_base_url or "https://api.deepseek.com"
            raw_text = await call_openai_compatible_api(
                base_url=base_url,
                api_key=settings.api_key,
                model_name=settings.model_name or "deepseek-chat",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=settings.temperature
            )
        elif settings.provider == "ollama":
            base_url = settings.api_base_url or "http://localhost:11434/v1"
            raw_text = await call_openai_compatible_api(
                base_url=base_url,
                api_key="ollama",
                model_name=settings.model_name or "llama3.2",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=settings.temperature
            )
        elif settings.provider == "openrouter":
            base_url = settings.api_base_url or "https://openrouter.ai/api/v1"
            raw_text = await call_openai_compatible_api(
                base_url=base_url,
                api_key=settings.api_key,
                model_name=settings.model_name or "meta-llama/llama-3.3-70b-instruct",
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                temperature=settings.temperature
            )
        else:
            raise ValueError(f"Unknown provider: {settings.provider}")
            
        parsed = clean_json_response(raw_text)
        subject = parsed.get("subject", "").strip()
        body = parsed.get("body_plain_text", parsed.get("body", "")).strip()
        
        if not subject or not body:
            raise ValueError("Parsed JSON missing 'subject' or 'body_plain_text'")
            
        return GeneratedEmail(subject=subject, body=body, language=language)
    except Exception as e:
        print(f"[LLM Template Warning] Adapting template failed for {contact.get('email')}: {e}. Using offline replacement.")
        return adapt_template_offline(template_text, contact, profile, language)


