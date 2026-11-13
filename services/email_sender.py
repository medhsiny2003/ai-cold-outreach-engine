import re
import smtplib
import ssl
import socket
import time
import random
import mimetypes
from pathlib import Path
from email.message import EmailMessage
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
from email.mime.image import MIMEImage
from typing import Optional, Dict, Any, List, Callable, Union
from config import BASE_DIR, SMTPSettings, CandidateProfile

# Force IPv4 resolution to eliminate [Errno 101] Network is unreachable in cloud containers
_orig_getaddrinfo = socket.getaddrinfo
def _force_ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    try:
        return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
    except Exception:
        return _orig_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = _force_ipv4_getaddrinfo

ASSETS_DIR = BASE_DIR / "data" / "assets"
UPLOADS_DIR = BASE_DIR / "data" / "uploads"
LOGO_PATH = ASSETS_DIR / "robothings_logo.png"

class SendResult:
    def __init__(self, recipient: str, success: bool, message: str, timestamp: float = None):
        self.recipient = recipient
        self.success = success
        self.message = message
        self.timestamp = timestamp or time.time()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "recipient": self.recipient,
            "success": self.success,
            "message": self.message,
            "timestamp": self.timestamp
        }

def test_smtp_connection(settings: SMTPSettings) -> Dict[str, Any]:
    """Tests the SMTP connection and login credentials with automatic dual-port check."""
    if not settings.sender_email or not settings.app_password:
        return {"success": False, "message": "Adresse email ou mot de passe d'application manquant."}
        
    clean_password = settings.app_password.replace(" ", "").strip()
    
    # Try Port 587 TLS first, then 465 SSL
    errors = []
    
    # 1. Test TLS 587
    try:
        with smtplib.SMTP(settings.smtp_host, 587, timeout=15) as server:
            server.ehlo()
            context = ssl.create_default_context()
            server.starttls(context=context)
            server.ehlo()
            server.login(settings.sender_email, clean_password)
            return {"success": True, "message": "Connexion SMTP Gmail validée avec succès (TLS Port 587) !"}
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "Erreur 535 : Mot de passe d'application invalide."}
    except Exception as e:
        errors.append(f"Port 587 ({e})")
        
    # 2. Test SSL 465
    try:
        context = ssl.create_default_context()
        with smtplib.SMTP_SSL(settings.smtp_host, 465, context=context, timeout=15) as server:
            server.login(settings.sender_email, clean_password)
            return {"success": True, "message": "Connexion SMTP Gmail validée avec succès (SSL Port 465) !"}
    except smtplib.SMTPAuthenticationError:
        return {"success": False, "message": "Erreur 535 : Mot de passe d'application invalide."}
    except Exception as e:
        errors.append(f"Port 465 ({e})")
        
    return {"success": False, "message": f"Échec de connexion SMTP : {'; '.join(errors)}"}

def sanitize_email_body_for_deliverability(text: str) -> str:
    """
    Supprime tous les liens URL, liens Markdown et mentions de club/ex-présidence
    pour garantir une délivrabilité maximale (Zéro SPAM) et positionner Mohammed
    strictement comme élève-ingénieur en dernière année (Final-Year Engineering Student).
    """
    if not text:
        return ""
        
    # 1. Supprimer les boutons ou ancres de portfolio markdown [Explorer mon Portfolio...](url)
    text = re.sub(r'\[(?:Explorer|Explore|Consulter|Voir)[^\]]*\]\([^\)]+\)', '', text, flags=re.IGNORECASE)
    # Supprimer les autres liens markdown [Texte](URL) en ne gardant que Texte
    text = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', text)
    
    # 2. Supprimer toute URL brute (http://, https://)
    text = re.sub(r'https?://[^\s<>"]+', '', text, flags=re.IGNORECASE)
    
    # 3. Supprimer toute mention de club ou d'ex-présidence
    text = re.sub(r'(?:ex-)?président\s+(?:et\s+team\s+leader\s+)?du\s+club\s+(?:robotique\s+)?robothings[^\n,.]*', 'élève-ingénieur en dernière année', text, flags=re.IGNORECASE)
    text = re.sub(r'(?:ex-)?president\s+(?:and\s+team\s+leader\s+)?of\s+(?:the\s+)?(?:robotics\s+club\s+)?robothings[^\n,.]*', 'final-year engineering student', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(?:ex-)?président\s+du\s+club\b', 'élève-ingénieur en dernière année', text, flags=re.IGNORECASE)
    text = re.sub(r'\b(?:ex-)?president\s+of\s+the\s+club\b', 'final-year student', text, flags=re.IGNORECASE)
    text = re.sub(r'\bRoboThings\b', 'Robotique', text, flags=re.IGNORECASE)
    text = re.sub(r'(?:en\s+tant\s+qu\'?|mon\s+rôle\s+d\'?)ex-?président[^\n,.]*', "élève-ingénieur en dernière année", text, flags=re.IGNORECASE)
    text = re.sub(r'(?:as\s+)?(?:ex-)?president\s+of[^\n,.]*', "final-year engineering student", text, flags=re.IGNORECASE)

    # 4. Nettoyer les lignes blanches consécutives
    lines = [l.strip() for l in text.split("\n")]
    cleaned = []
    prev_empty = False
    for l in lines:
        if not l:
            if not prev_empty:
                cleaned.append("")
                prev_empty = True
        else:
            cleaned.append(l)
            prev_empty = False
            
    return "\n".join(cleaned).strip()

def build_professional_html(
    body_text: str,
    profile: CandidateProfile,
    language: str = "fr",
    include_logo: bool = False
) -> str:
    """Génère un email HTML professionnel épuré, sans liens URL, sans logo ni badge club (100% Anti-Spam)."""
    clean_text = sanitize_email_body_for_deliverability(body_text)
    lines = clean_text.split("\n")
    html_paragraphs = []
    in_list = False
    is_english = (language == "en")
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_list:
                html_paragraphs.append("</ul>")
                in_list = False
            continue
            
        if stripped.startswith("- ") or stripped.startswith("• "):
            if not in_list:
                html_paragraphs.append('<ul style="margin: 8px 0 12px 18px; padding-left: 0; color: #2d3748; line-height: 1.65; font-size: 14.5px;">')
                in_list = True
            item_text = stripped[2:].strip()
            html_paragraphs.append(f'<li style="margin-bottom: 5px;">{item_text}</li>')
        else:
            if in_list:
                html_paragraphs.append("</ul>")
                in_list = False
                
            if stripped.startswith("Bien cordialement") or stripped.startswith("Best regards") or stripped.startswith("Cordialement") or stripped.startswith("Regards"):
                html_paragraphs.append(f'<p style="margin: 18px 0 6px 0; color: #2d3748; font-weight: 500; font-size: 14.5px;">{stripped}</p>')
                break
            else:
                html_paragraphs.append(f'<p style="margin: 0 0 12px 0; color: #2d3748; line-height: 1.65; font-size: 14.5px;">{stripped}</p>')
                
    if in_list:
        html_paragraphs.append("</ul>")
        
    formatted_body = "\n".join(html_paragraphs)
    
    if is_english:
        title_text = "Final-Year Electrical Engineering Student"
        school_text = "Faculty of Sciences and Technologies Mohammedia (FSTM)"
        phone_label = "Phone"
        email_label = "Email"
        attachment_notice = "📎 Resume (PDF) & Project Dossier (PDF) attached"
    else:
        title_text = "Élève-Ingénieur en Génie Électrique (Dernière Année)"
        school_text = "Faculté des Sciences et Techniques de Mohammedia (FSTM)"
        phone_label = "Tél"
        email_label = "Email"
        attachment_notice = "📎 CV (PDF) & Dossier de Projets (PDF) joints"

    html_content = f"""
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; background-color: #f8fafc; margin: 0; padding: 18px; color: #1e293b;">
    <table cellpadding="0" cellspacing="0" border="0" style="max-width: 620px; width: 100%; margin: 0 auto; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.05);">
        <tr>
            <td style="padding: 26px 28px;">
                <!-- Email Body (Zero Links - Maximum Deliverability) -->
                <div style="color: #2d3748;">
                    {formatted_body}
                </div>

                <!-- Subtle Attachments notice -->
                <div style="margin-top: 16px; margin-bottom: 20px; font-size: 12.5px; color: #64748b; font-style: italic;">
                    {attachment_notice}
                </div>

                <!-- Clean Professional Signature (Zero Club mentions, Zero Spam Links) -->
                <div style="padding-top: 18px; border-top: 1.5px solid #e2e8f0;">
                    <table cellpadding="0" cellspacing="0" border="0" style="width: 100%;">
                        <tr>
                            <td style="vertical-align: middle;">
                                <div style="font-size: 16px; font-weight: 700; color: #0f172a; letter-spacing: -0.2px;">
                                    {profile.name}
                                </div>
                                <div style="font-size: 13.5px; font-weight: 600; color: #0284c7; margin-top: 2px;">
                                    {title_text}
                                </div>
                                <div style="font-size: 12px; color: #64748b; margin-top: 1px;">
                                    {school_text}
                                </div>
                                
                                <!-- Contacts row (Phone & Email only - No tracking or suspicious links) -->
                                <div style="margin-top: 8px; font-size: 12px; color: #475569;">
                                    <span style="display: inline-block; margin-right: 14px;">📱 {phone_label} : <span style="color: #0f172a; font-weight: 500;">{profile.phone}</span></span>
                                    <span style="display: inline-block;">✉️ {email_label} : <span style="color: #0f172a; font-weight: 500;">{profile.email}</span></span>
                                </div>
                            </td>
                        </tr>
                    </table>
                </div>
            </td>
        </tr>
    </table>
</body>
</html>
"""
    return html_content

def create_email_message(
    sender_name: str,
    sender_email: str,
    recipient_email: str,
    subject: str,
    body_text: str,
    attachment_paths: Optional[Union[str, List[str]]] = None,
    profile: Optional[CandidateProfile] = None,
    language: str = "fr"
) -> MIMEMultipart:
    """Constructs a clean, deliverable MIME email message without spam-triggering links or images."""
    profile_obj = profile or CandidateProfile()
    
    # 1. Clean body text strictly (No links, No club/ex-president mentions)
    clean_body = sanitize_email_body_for_deliverability(body_text)
    
    # Root message is multipart/mixed to support body + attachments
    msg = MIMEMultipart("mixed")
    msg["From"] = f"{sender_name} <{sender_email}>" if sender_name else sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg["Reply-To"] = sender_email

    # Alternative part for (Plain text + HTML)
    msg_alt = MIMEMultipart("alternative")
    
    # Plain text version (Clean, zero links)
    msg_alt.attach(MIMEText(clean_body, "plain", "utf-8"))
    
    # HTML version (Clean, zero links, zero CID images)
    html_body = build_professional_html(clean_body, profile_obj, language=language, include_logo=False)
    msg_alt.attach(MIMEText(html_body, "html", "utf-8"))
    
    msg.attach(msg_alt)

    # Attach PDF files
    if attachment_paths:
        if isinstance(attachment_paths, str):
            attachment_paths = [attachment_paths]
            
        for att in attachment_paths:
            if not att:
                continue
            path = Path(att)
            if path.is_file():
                try:
                    ctype, encoding = mimetypes.guess_type(str(path))
                    if ctype is None or encoding is not None:
                        ctype = "application/octet-stream"
                    maintype, subtype = ctype.split("/", 1)
                    
                    with open(path, "rb") as f:
                        part = MIMEApplication(f.read(), _subtype=subtype)
                        part.add_header("Content-Disposition", "attachment", filename=path.name)
                        msg.attach(part)
                except Exception as e:
                    print(f"[Warning] Could not attach file {path.name}: {e}")
                    
    return msg

def send_single_email(
    settings: SMTPSettings,
    recipient_email: str,
    subject: str,
    body_text: str,
    attachment_paths: Optional[Union[str, List[str]]] = None,
    profile: Optional[CandidateProfile] = None,
    language: str = "fr"
) -> SendResult:
    """Sends a single executive email via SMTP."""
    if not recipient_email or "@" not in recipient_email:
        return SendResult(recipient=recipient_email, success=False, message="Adresse email destinataire invalide.")
        
    clean_password = settings.app_password.replace(" ", "").strip()
    
    # 1. Build MIME Message
    try:
        msg = create_email_message(
            sender_name=settings.sender_name,
            sender_email=settings.sender_email,
            recipient_email=recipient_email,
            subject=subject,
            body_text=body_text,
            attachment_paths=attachment_paths,
            profile=profile,
            language=language
        )
    except Exception as e:
        return SendResult(recipient=recipient_email, success=False, message=f"Erreur de création MIME : {str(e)}")

    # 2. Attempt Send with Dual-Port Cloud Fallback (587 TLS -> 465 SSL)
    last_err = None
    
    # Try configured mode first
    attempts = []
    if settings.use_ssl:
        attempts.append(("SSL", 465))
        attempts.append(("TLS", 587))
    else:
        attempts.append(("TLS", 587))
        attempts.append(("SSL", 465))
        
    for mode, port in attempts:
        try:
            if mode == "SSL" or port == 465:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(settings.smtp_host, 465, context=context, timeout=25) as server:
                    server.login(settings.sender_email, clean_password)
                    server.send_message(msg)
                    return SendResult(recipient=recipient_email, success=True, message="Email envoyé avec succès (SSL 465) !")
            else:
                with smtplib.SMTP(settings.smtp_host, 587, timeout=25) as server:
                    server.ehlo()
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    server.ehlo()
                    server.login(settings.sender_email, clean_password)
                    server.send_message(msg)
                    return SendResult(recipient=recipient_email, success=True, message="Email envoyé avec succès (TLS 587) !")
        except smtplib.SMTPAuthenticationError:
            return SendResult(recipient=recipient_email, success=False, message="Erreur 535 : Mot de passe d'application Gmail invalide.")
        except Exception as e:
            last_err = e
            # If 550 limit exceeded, do not retry other port as quota is account-level
            if "550" in str(e) or "limit" in str(e).lower():
                return SendResult(recipient=recipient_email, success=False, message=f"Quota Google 550 : {str(e)}")
            continue

    return SendResult(recipient=recipient_email, success=False, message=f"Échec de connexion SMTP ({last_err})")

def send_html_email(
    settings: SMTPSettings,
    recipient_email: str,
    subject: str,
    html_content: str
) -> SendResult:
    """Sends a direct rich HTML email (ideal for analytical reports and dashboards)."""
    try:
        clean_password = settings.app_password.replace(" ", "").strip()
        msg = MIMEMultipart("alternative")
        msg["From"] = f"{settings.sender_name} <{settings.sender_email}>" if settings.sender_name else settings.sender_email
        msg["To"] = recipient_email
        msg["Subject"] = subject
        msg.attach(MIMEText(html_content, "html", "utf-8"))
        
        if settings.use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, context=context, timeout=30) as server:
                server.login(settings.sender_email, clean_password)
                server.send_message(msg)
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=30) as server:
                server.ehlo()
                if settings.use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    server.ehlo()
                server.login(settings.sender_email, clean_password)
                server.send_message(msg)
                
        return SendResult(recipient=recipient_email, success=True, message="Rapport HTML envoyé avec succès !")
    except Exception as e:
        return SendResult(recipient=recipient_email, success=False, message=str(e))

def send_batch_emails(
    settings: SMTPSettings,
    emails_to_send: List[Dict[str, Any]],
    attachment_paths: Optional[Union[str, List[str]]] = None,
    profile: Optional[CandidateProfile] = None,
    progress_callback: Optional[Callable[[int, int, Dict[str, Any]], None]] = None,
    stop_check_callback: Optional[Callable[[], bool]] = None
) -> List[SendResult]:
    """Sends a batch of emails with randomized anti-spam delays."""
    results = []
    total = len(emails_to_send)
    
    for idx, item in enumerate(emails_to_send):
        if stop_check_callback and stop_check_callback():
            break
            
        recipient = item.get("email", "")
        subject = item.get("subject", "")
        body = item.get("body", "")
        lang = item.get("language", "fr")
        
        result = send_single_email(
            settings=settings,
            recipient_email=recipient,
            subject=subject,
            body_text=body,
            attachment_paths=attachment_paths,
            profile=profile,
            language=lang
        )
        results.append(result)
        
        if progress_callback:
            progress_callback(idx + 1, total, {
                "recipient": recipient,
                "success": result.success,
                "message": result.message
            })
            
        if idx < total - 1 and result.success:
            delay = random.uniform(settings.min_delay_seconds, settings.max_delay_seconds)
            time.sleep(delay)
            
    return results
