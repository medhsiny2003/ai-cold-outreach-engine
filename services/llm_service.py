import json
import re
import httpx
from typing import Dict, Any, Optional
from config import LLMSettings, CandidateProfile
from services.prompt_builder import build_system_prompt, build_user_prompt, determine_language

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

def generate_fallback_template(contact: Dict[str, Any], profile: CandidateProfile, language: str) -> GeneratedEmail:
    """Smart persona-based fallback template when offline or without API key."""
    name = contact.get("name") or contact.get("nom") or ""
    first_name = contact.get("first_name") or contact.get("prenom") or (name.split()[0] if name else "")
    company = contact.get("company") or contact.get("entreprise") or contact.get("societe") or "votre entreprise"
    role = contact.get("role") or contact.get("poste") or ""
    role_lower = role.lower()
    
    is_hr = any(k in role_lower for k in ["recrut", "talent", "rh", "hr", "campus", "people", "ressources humaines", "acquisition"])
    is_product = any(k in role_lower for k in ["produit", "product", "business", "bizdev", "commercial", "sales", "partenariat", "marketing"])
    is_ceo = any(k in role_lower for k in ["ceo", "fondateur", "founder", "directeur général", "general manager", "president", "vp", "gerant", "managing director"])
    is_rd = any(k in role_lower for k in ["r&d", "recherche", "architect", "lead", "cto", "direction technique", "system engineer", "systèmes critiques", "expert", "scientifique", "innovation"])
    
    if language == "fr":
        salutation = f"Bonjour {first_name}," if first_name else "Bonjour,"
        
        # 1. PROFIL R&D / LEAD TECH / ARCHITECTE SYSTÈME
        if is_rd:
            subject = "Stage PFE – Demande de conseil"
            body = f"""{salutation}

J'espère que vous allez bien.

Je suis étudiant en dernière année d'ingénierie en Génie Électrique, passionné par les systèmes embarqués, la robotique et les drones. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE).

Je suis très motivé par l'idée de rejoindre {company} et je suis sincèrement inspiré par vos projets R&D, vos défis d'ingénierie et l'innovation technologique que vous portez.

En découvrant votre parcours et votre rôle en R&D, j'ai été particulièrement impressionné par la technicité et la complexité des systèmes que vous développez.

Je me permets de vous contacter pour bénéficier de votre regard d'expert sur mon CV et mon portfolio de projets. Si vous avez un moment, je serais très reconnaissant d'avoir votre avis et vos conseils pour m'aider à progresser.

Je me demande également s'il y aurait des opportunités de stage PFE au sein de vos équipes R&D ou de conception.

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

Je suis étudiant en dernière année d'ingénierie en Génie Électrique, passionné par les systèmes embarqués, la robotique et les drones. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE).

Je suis très motivé par l'idée de rejoindre {company} et je suis sincèrement inspiré par votre vision et votre impact dans le secteur.

En voyant votre parcours, j'ai été vraiment inspiré par votre rôle et par la manière dont vous contribuez à faire évoluer les talents dans ce domaine.

Je me permets de vous contacter pour savoir s'il existe des opportunités de stage dans les domaines qui me passionnent. Je serais ravi d'avoir votre regard sur mon profil et de discuter des possibilités au sein de votre entreprise.

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

Je suis étudiant en dernière année d'ingénierie en Génie Électrique, passionné par les systèmes embarqués, la robotique et les drones. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE).

Je suis très motivé par l'idée de rejoindre {company} et je suis sincèrement inspiré par votre vision et l'ambition de vos projets.

J'ai eu l'occasion de découvrir votre travail et je suis vraiment admiratif de ce que vous accomplissez.

Je me permets de vous contacter pour bénéficier de votre regard sur mon parcours. Si vous avez un moment, je serais ravi d'avoir vos conseils pour évoluer dans ce secteur.

Portfolio : https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Merci d'avance pour votre temps.

Bien cordialement,
Mohammed HSINY
+212 611 424 571
mohammedhsiny2@gmail.com"""

        # 4. RESPONSABLE PRODUIT / BUSINESS DEVELOPER
        elif is_product:
            subject = "Stage PFE – Demande d'information"
            body = f"""{salutation}

J'espère que vous allez bien.

Je suis étudiant en dernière année d'ingénierie en Génie Électrique, passionné par les systèmes embarqués et la robotique. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE).

Je suis très motivé par l'idée de rejoindre {company} et je suis sincèrement inspiré par votre approche produit et votre vision du marché.

Votre travail m'a beaucoup intéressé et je serais ravi d'échanger avec vous sur vos projets et les opportunités pour un jeune ingénieur passionné.

Portfolio : https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Merci d'avance.

Bien cordialement,
Mohammed HSINY
+212 611 424 571
mohammedhsiny2@gmail.com"""

        # 5. INGÉNIEUR / CHEF DE PROJET TECHNIQUE (Défaut)
        else:
            subject = "Stage PFE – Demande de conseil"
            body = f"""{salutation}

J'espère que vous allez bien.

Je suis étudiant en dernière année d'ingénierie en Génie Électrique, passionné par les systèmes embarqués, la robotique et les drones. Je suis basé au Maroc et je prépare actuellement mon stage de fin d'études (PFE).

Je suis très motivé par l'idée de rejoindre {company} et je suis sincèrement inspiré par vos projets et votre expertise dans le domaine.

En découvrant votre parcours, j'ai été vraiment inspiré par votre travail et par les projets sur lesquels vous intervenez.

Je me permets de vous contacter pour bénéficier de votre regard sur mon CV et mon portfolio. Si vous avez un moment, je serais très reconnaissant d'avoir votre avis pour m'aider à progresser.

Je me demande aussi s'il y aurait des opportunités de stage au sein de votre équipe ou dans vos services.

Portfolio : https://portfolio-mohammed-hsiny-ux7z.vercel.app/

Merci d'avance pour votre temps.

Bien cordialement,
Mohammed HSINY
+212 611 424 571
mohammedhsiny2@gmail.com"""

    else:
        salutation = f"Hi {first_name}," if first_name else "Hello,"
        if is_hr or is_product:
            subject = "Stage PFE – Demande d'information"
        else:
            subject = "Stage PFE – Demande de conseil"
            
        body = f"""{salutation}

I hope you are doing well.

I am a final-year Electrical Engineering student passionate about embedded systems, robotics, and drones. I am based in Morocco and currently preparing for my final graduation internship (PFE).

I am genuinely motivated by the prospect of contributing to {company} and truly inspired by your vision and projects.

I would be grateful for your feedback on my Resume and online portfolio:
https://portfolio-mohammed-hsiny-ux7z.vercel.app/

I was also wondering if there might be internship opportunities within your team.

Thank you very much for your time.

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
    tone: str = "persuasive_tech"
) -> GeneratedEmail:
    """Generates an email for a contact using LLM with fallback handling."""
    language = determine_language(contact, forced_lang)
    
    # If no API key is set, fallback to high-quality dynamic template
    if not settings.api_key and settings.provider != "ollama":
        return generate_fallback_template(contact, profile, language)
        
    system_prompt = build_system_prompt()
    user_prompt = build_user_prompt(contact, profile, language=language, tone=tone)
    
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
        return generate_fallback_template(contact, profile, language)
