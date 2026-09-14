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
    build_template_adaptation_user_prompt,
    classify_role_category,
    detect_best_theme_for_company,
    get_target_subject,
    THEMES_CATALOG,
    WRITING_STYLES,
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


def generate_fallback_template(
    contact: Dict[str, Any], 
    profile: CandidateProfile, 
    language: str,
    theme: str = "auto",
    custom_instruction: str = ""
) -> GeneratedEmail:
    """Smart persona & theme-based fallback template when offline or without API key."""
    name = (contact.get("name") or contact.get("nom") or "").strip()
    first_name = (contact.get("first_name") or contact.get("prenom") or "").strip()
    if not first_name and name:
        first_name = name.split()[0].capitalize()
    
    company = (contact.get("company") or contact.get("entreprise") or contact.get("societe") or "").strip()
    if not company or company.lower() in ["votre entreprise", "n/a", ""]:
        company = "votre entreprise"
        
    role = (contact.get("role") or contact.get("poste") or "").strip()
    industry = (contact.get("industry") or contact.get("secteur") or "").strip()
    
    # Resolve Theme
    effective_theme = theme
    if theme == "auto":
        effective_theme = detect_best_theme_for_company(company, role, industry)
        
    persona = classify_role_category(role)
    is_ceo = (persona == "CEO_DIRECTEUR")
    is_hr = (persona == "RH_TALENT")
    
    # Technical Theme Phrases
    # Technical Theme Phrases
    if effective_theme == "drones_robotics":
        th_short_fr = "les drones et la robotique"
        th_hr_fr = "Drones, Robotique & Systèmes Embarqués"
        th_tag_fr = "les systèmes embarqués, la robotique et les drones"
        th_short_en = "drones & robotics"
        th_hr_en = "Drones, Robotics & Embedded Systems"
        th_tag_en = "embedded systems, robotics and autonomous drones"
    elif effective_theme == "solar_energy":
        th_short_fr = "l'énergie solaire"
        th_hr_fr = "Énergie Solaire & Génie Électrique"
        th_tag_fr = "le génie électrique et l'énergie solaire photovoltaïque"
        th_short_en = "solar energy"
        th_hr_en = "Solar PV & Electrical Systems"
        th_tag_en = "electrical engineering and solar PV systems"
    elif effective_theme == "automation_scada":
        th_short_fr = "l'automatisme industriel & SCADA"
        th_hr_fr = "Automatisme Industriel & SCADA"
        th_tag_fr = "l'automatisme industriel, le contrôle-commande et les systèmes SCADA"
        th_short_en = "industrial automation & SCADA"
        th_hr_en = "Industrial Automation & SCADA"
        th_tag_en = "industrial automation, PLC programming and SCADA"
    elif effective_theme == "embedded_edge_ai":
        th_short_fr = "les systèmes embarqués"
        th_hr_fr = "Systèmes Embarqués & Edge AI"
        th_tag_fr = "les systèmes embarqués temps réel et l'Edge AI"
        th_short_en = "embedded systems"
        th_hr_en = "Embedded Systems & Edge AI"
        th_tag_en = "real-time embedded systems and Edge AI"
    elif effective_theme == "electrical_power":
        th_short_fr = "le génie électrique"
        th_hr_fr = "Génie Électrique & Électrotechnique"
        th_tag_fr = "le génie électrique, l'électrotechnique et la puissance"
        th_short_en = "electrical engineering"
        th_hr_en = "Electrical & Power Engineering"
        th_tag_en = "electrical power engineering and energy distribution"
    else:
        th_short_fr = "les systèmes embarqués et les drones"
        th_hr_fr = "Génie Électrique & Systèmes Embarqués"
        th_tag_fr = "les systèmes embarqués, la robotique et les drones"
        th_short_en = "embedded systems & robotics"
        th_hr_en = "Electrical & Embedded Systems"
        th_tag_en = "embedded systems, robotics and autonomous drones"

    portfolio_url = profile.portfolio_url or "https://portfolio-mohammed-hsiny-ux7z.vercel.app/"
    
    if language == "fr":
        salutation = f"Bonjour {first_name}," if first_name else "Bonjour,"
        
        # 1. VERSION CEO / FONDATEUR / DIRIGEANT
        if is_ceo:
            subject = f"Votre vision chez {company} – Étudiant passionné par {th_short_fr}"
            body = f"""{salutation}

J'espère que vous allez bien.

Je suis étudiant en dernière année d'ingénierie en Génie Électrique, passionné par {th_tag_fr}. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE).

Je suis très motivé par l'idée de rejoindre {company} et je suis sincèrement inspiré par votre vision et les projets que vous portez. Votre parcours et votre expertise dans le domaine sont pour moi une source de motivation.

Je me permets de vous contacter pour bénéficier de votre regard sur mon CV et mon portfolio. Si vous avez un moment, je serais très reconnaissant d'avoir votre avis pour m'aider à progresser.

Je me demande aussi s'il y aurait des opportunités de stage au sein de votre équipe ou dans vos services.

[Explorer mon Portfolio Interactif ↗]({portfolio_url})

Merci d'avance pour votre temps.

Bien cordialement,"""

        # 2. VERSION RH / RECRUTEUR / TALENT ACQUISITION
        elif is_hr:
            subject = f"Candidature – Stage PFE en {th_hr_fr}"
            body = f"""{salutation}

J'espère que vous allez bien.

Je suis étudiant en dernière année d'ingénierie en Génie Électrique, passionné par {th_tag_fr}. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE).

Je suis très motivé par l'idée de rejoindre {company} et je suis sincèrement inspiré par vos projets et votre expertise dans le domaine.

Je me permets de vous contacter pour savoir s'il y aurait des opportunités de stage au sein de votre entreprise. Je suis disponible pour un PFE de 6 mois à partir de janvier 2027.

Je vous joins mon CV et mon portfolio pour plus de détails.

[Explorer mon Portfolio Interactif ↗]({portfolio_url})

Merci d'avance pour votre temps.

Bien cordialement,"""

        # 3. VERSION INGÉNIEUR / CHEF DE PROJET / TECH LEAD / R&D (Défaut)
        else:
            subject = f"Votre parcours chez {company} – Étudiant passionné par {th_short_fr}"
            body = f"""{salutation}

J'espère que vous allez bien.

Je suis étudiant en dernière année d'ingénierie en Génie Électrique, passionné par {th_tag_fr}. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE).

En découvrant votre parcours, j'ai été vraiment inspiré par votre travail et par les projets sur lesquels vous intervenez. Votre expertise dans le domaine est pour moi une source de motivation.

Je me permets de vous contacter pour bénéficier de votre regard sur mon CV et mon portfolio. Si vous avez un moment, je serais très reconnaissant d'avoir votre avis pour m'aider à progresser.

Je me demande aussi s'il y aurait des opportunités de stage au sein de votre équipe.

[Explorer mon Portfolio Interactif ↗]({portfolio_url})

Merci d'avance pour votre temps.

Bien cordialement,"""

    else:
        salutation = f"Hi {first_name}," if first_name else "Hello,"
        if is_ceo:
            subject = f"Your vision at {company} – Student passionate about {th_short_en}"
            body = f"""{salutation}

I hope you are doing well.

I am a final-year Electrical Engineering student, passionate about {th_tag_en}. I am based in Morocco and currently preparing my 6-month graduation internship (PFE).

I am genuinely motivated by the prospect of contributing to {company} and deeply inspired by your leadership and vision.

I would be very grateful for your insights and valuable feedback on my projects and online portfolio.

I was also wondering if there might be graduation internship opportunities within your teams.

[Explore my Interactive Portfolio ↗]({portfolio_url})

Thank you very much for your time.

Best regards,"""
        elif is_hr:
            subject = f"Application – 6-Month Graduation Internship (PFE) in {th_hr_en}"
            body = f"""{salutation}

I hope you are doing well.

I am a final-year Electrical Engineering student, passionate about {th_tag_en}. I am based in Morocco and currently preparing my final graduation internship (PFE).

I am very excited about {company}'s innovative projects and would love to explore internship opportunities within your organization for a 6-month period starting January 2027.

I have attached my resume and portfolio dossier for your review.

[Explore my Interactive Portfolio ↗]({portfolio_url})

Thank you very much for your consideration.

Best regards,"""
        else:
            subject = f"Your work at {company} – Student passionate about {th_short_en}"
            body = f"""{salutation}

I hope you are doing well.

I am a final-year Electrical Engineering student, passionate about {th_tag_en}. I am based in Morocco and currently preparing my 6-month graduation internship (PFE).

Coming across your technical journey, I was truly inspired by your work and the engineering challenges you tackle at {company}.

I would be honored to get your expert feedback on my CV and project portfolio.

I was also wondering if there might be 6-month PFE internship opportunities within your engineering team.

[Explore my Interactive Portfolio ↗]({portfolio_url})

Thank you very much for your time and guidance.

Best regards,"""

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
    """Smart offline template adaptation replacing all variables, company references, persona blocks and placeholders."""
    if not template_text or not template_text.strip():
        return generate_fallback_template(contact, profile, language)
        
    first_name = (contact.get("first_name") or contact.get("prenom") or "").strip()
    name = (contact.get("name") or contact.get("nom") or "").strip()
    if not first_name and name:
        first_name = name.split()[0].capitalize()
    salutation_name = first_name if first_name else "Madame, Monsieur"
    
    company = (contact.get("company") or contact.get("entreprise") or contact.get("societe") or "").strip()
    if not company or company.lower() in ["votre entreprise", "n/a", ""]:
        company = "votre entreprise"
        
    role = (contact.get("role") or contact.get("poste") or "").strip()
    industry = (contact.get("industry") or contact.get("secteur") or "").strip()
    persona = classify_role_category(role)
    
    # Check if template contains multiple persona sections (CEO / RH / Ingénieur)
    text = template_text
    lower_text = text.lower()
    if "version pour un" in lower_text or "version ceo" in lower_text or "version rh" in lower_text or "version ingénieur" in lower_text:
        if persona == "CEO_DIRECTEUR":
            match = re.search(r"(?:version\s+pour\s+(?:un\s+)?(?:ceo|directeur|fondateur)[^\n]*\n)(.*?)(?=(?:📧|📝|\*|\#)?\s*version|\Z)", text, flags=re.IGNORECASE | re.DOTALL)
            if match and match.group(1).strip():
                text = match.group(1).strip()
        elif persona == "RH_TALENT":
            match = re.search(r"(?:version\s+pour\s+(?:un\s+)?(?:rh|recruteur|talent)[^\n]*\n)(.*?)(?=(?:📧|📝|\*|\#)?\s*version|\Z)", text, flags=re.IGNORECASE | re.DOTALL)
            if match and match.group(1).strip():
                text = match.group(1).strip()
        else:
            match = re.search(r"(?:version\s+pour\s+(?:un\s+)?(?:ingénieur|ingenieur|tech|lead|r&d)[^\n]*\n)(.*?)(?=(?:📧|📝|\*|\#)?\s*version|\Z)", text, flags=re.IGNORECASE | re.DOTALL)
            if match and match.group(1).strip():
                text = match.group(1).strip()

    # Dynamic Variable Replacements
    replacements = {
        r"\[Prénom\]|\[Prenom\]|\{\{prenom\}\}|\{\{first_name\}\}": salutation_name,
        r"\[Nom\]|\{\{nom\}\}|\{\{last_name\}\}": name if name else salutation_name,
        r"\[Nom de l'entreprise\]|\[Entreprise\]|\[Société\]|\[Societe\]|\[Nom de l'organisme\]|\{\{entreprise\}\}|\{\{company\}\}": company,
        r"\[Poste\]|\[Titre\]|\{\{poste\}\}|\{\{role\}\}": role,
    }
    for pattern, repl in replacements.items():
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
        
    # Replace static greeting like "Bonjour Bruno," or "Bonjour Alexandre," with current contact's salutation
    text = re.sub(r"^(?:Bonjour|Bonsoir|Hi|Hello)\s+[A-Za-zÀ-ÿ-]+,", f"Bonjour {salutation_name}," if language == 'fr' else f"Hi {salutation_name},", text, flags=re.MULTILINE)
    
    # Replace previous static company names like "Shark Robotics" if company is different
    if company and company.lower() != "shark robotics":
        text = re.sub(r"\bShark\s+Robotics\b", company, text, flags=re.IGNORECASE)
        
    # Extract Subject Line
    theme = detect_best_theme_for_company(company, role, industry)
    subject = get_target_subject(persona, theme=theme, company=company, language=language)
    
    lines = text.split("\n")
    body_lines = []
    for line in lines:
        stripped = line.strip()
        if stripped.lower().startswith(("objet :", "objet:", "subject :", "subject:")):
            extracted_subj = re.sub(r"^(?:objet|subject)\s*:\s*", "", stripped, flags=re.IGNORECASE).strip()
            if extracted_subj:
                extracted_subj = re.sub(r"\[Nom de l'entreprise\]|\[Entreprise\]|\[Société\]|\[Societe\]|Shark Robotics", company, extracted_subj, flags=re.IGNORECASE)
                extracted_subj = re.sub(r"\[Prénom\]|\[Prenom\]", salutation_name, extracted_subj, flags=re.IGNORECASE)
                subject = extracted_subj
        elif stripped.lower() in ["text", "```", "```text", "```markdown"]:
            continue
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


