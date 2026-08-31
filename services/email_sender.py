import smtplib
import ssl
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
    """Tests the SMTP connection and login credentials."""
    if not settings.sender_email or not settings.app_password:
        return {"success": False, "message": "Adresse email ou mot de passe d'application manquant."}
        
    clean_password = settings.app_password.replace(" ", "").strip()
    
    try:
        if settings.use_ssl:
            context = ssl.create_default_context()
            with smtplib.SMTP_SSL(settings.smtp_host, settings.smtp_port, context=context, timeout=20) as server:
                server.login(settings.sender_email, clean_password)
                return {"success": True, "message": "Connexion SMTP réussie (SSL) !"}
        else:
            with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
                server.ehlo()
                if settings.use_tls:
                    context = ssl.create_default_context()
                    server.starttls(context=context)
                    server.ehlo()
                server.login(settings.sender_email, clean_password)
                return {"success": True, "message": "Connexion SMTP réussie (TLS) !"}
    except smtplib.SMTPAuthenticationError as e:
        return {
            "success": False,
            "message": "Erreur d'authentification Gmail (535) : Mot de passe d'application invalide."
        }
    except Exception as e:
        return {"success": False, "message": f"Erreur de connexion SMTP : {str(e)}"}

def build_professional_html(
    body_text: str,
    profile: CandidateProfile,
    language: str = "fr",
    include_logo: bool = True
) -> str:
    """Generates an executive, highly polished HTML email with modern signature and embedded logo."""
    lines = body_text.strip().split("\n")
    html_paragraphs = []
    in_list = False
    
    is_english = (language == "en")
    
    btn_text = "🌐 Explorer mon Portfolio Interactif ↗" if not is_english else "🌐 Explore My Interactive Portfolio ↗"
    
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
                
            # If line mentions portfolio URL, render as high-impact centered CTA button
            if "portfolio-mohammed-hsiny" in stripped:
                html_paragraphs.append(f'''
                <div style="margin: 20px 0; text-align: center;">
                    <a href="{profile.portfolio_url}" target="_blank" style="display: inline-block; background-color: #0b5ed7; color: #ffffff; text-decoration: none; padding: 11px 24px; border-radius: 6px; font-weight: 600; font-size: 14px; letter-spacing: 0.2px; box-shadow: 0 2px 6px rgba(11,94,215,0.25);">
                        {btn_text}
                    </a>
                </div>
                ''')
            elif stripped.startswith("Bien cordialement") or stripped.startswith("Best regards") or stripped.startswith("Cordialement") or stripped.startswith("Regards"):
                html_paragraphs.append(f'<p style="margin: 18px 0 6px 0; color: #2d3748; font-weight: 500; font-size: 14.5px;">{stripped}</p>')
                # Stop body text here to let the rich signature render cleanly
                break
            else:
                html_paragraphs.append(f'<p style="margin: 0 0 12px 0; color: #2d3748; line-height: 1.65; font-size: 14.5px;">{stripped}</p>')
                
    if in_list:
        html_paragraphs.append("</ul>")
        
    formatted_body = "\n".join(html_paragraphs)
    
    # Localized texts for signature
    if is_english:
        title_text = "Electrical Engineering & Industrial Control Student"
        school_text = "Faculty of Sciences and Technologies Mohammedia (FSTM)"
        club_title = "President & Team Leader — RoboThings Club (FSTM)"
        phone_label = "Phone"
        email_label = "Email"
        portfolio_label = "Online Portfolio"
        linkedin_label = "LinkedIn"
        attachment_notice = "📎 Resume (PDF) & Portfolio Dossier (PDF) attached"
    else:
        title_text = "Élève-Ingénieur en Génie Électrique & Contrôle Industriel"
        school_text = "Faculté des Sciences et Techniques de Mohammedia (FSTM)"
        club_title = "Président & Team Leader — Club RoboThings (FSTM)"
        phone_label = "Tél"
        email_label = "Email"
        portfolio_label = "Portfolio en ligne"
        linkedin_label = "LinkedIn"
        attachment_notice = "📎 CV (PDF) & Dossier Portfolio (PDF) joints"

    # Logo tag for signature footer (discreet size: 52px width, rounded)
    logo_tag = ''
    if include_logo and LOGO_PATH.is_file():
        logo_tag = f'''
        <td style="vertical-align: top; width: 62px; padding-right: 14px;">
            <img src="cid:robothings_logo" alt="RoboThings FSTM" width="52" height="52" style="display:block; border-radius: 6px; border: 1px solid #e2e8f0; object-fit: contain; background: #ffffff; padding: 2px;" />
        </td>
        '''

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
                <!-- Email Body (NO logo at top) -->
                <div style="color: #2d3748;">
                    {formatted_body}
                </div>

                <!-- Subtle Attachments notice -->
                <div style="margin-top: 16px; margin-bottom: 20px; font-size: 12.5px; color: #64748b; font-style: italic;">
                    {attachment_notice}
                </div>

                <!-- Executive Signature Block -->
                <div style="padding-top: 18px; border-top: 1.5px solid #e2e8f0;">
                    <table cellpadding="0" cellspacing="0" border="0" style="width: 100%;">
                        <tr>
                            {logo_tag}
                            <td style="vertical-align: middle;">
                                <div style="font-size: 16px; font-weight: 700; color: #0f172a; letter-spacing: -0.2px;">
                                    {profile.name}
                                </div>
                                <div style="font-size: 13px; font-weight: 600; color: #0284c7; margin-top: 2px;">
                                    {title_text}
                                </div>
                                <div style="font-size: 12px; color: #334155; margin-top: 2px; font-weight: 500;">
                                    🏆 <strong>{club_title}</strong>
                                </div>
                                <div style="font-size: 11.5px; color: #64748b; margin-top: 1px;">
                                    {school_text}
                                </div>
                                
                                <!-- Links & Contacts row -->
                                <div style="margin-top: 8px; font-size: 12px; color: #475569;">
                                    <span style="display: inline-block; margin-right: 12px;">📱 {phone_label} : <a href="tel:{profile.phone}" style="color: #0284c7; text-decoration: none; font-weight: 500;">{profile.phone}</a></span>
                                    <span style="display: inline-block; margin-right: 12px;">✉️ {email_label} : <a href="mailto:{profile.email}" style="color: #0284c7; text-decoration: none; font-weight: 500;">{profile.email}</a></span>
                                    <span style="display: inline-block; margin-right: 12px;">🌐 <a href="{profile.portfolio_url}" style="color: #0b5ed7; font-weight: 600; text-decoration: none;">{portfolio_label}</a></span>
                                    <span style="display: inline-block;">💼 <a href="{profile.linkedin_url}" style="color: #0077b5; font-weight: 600; text-decoration: none;">{linkedin_label}</a></span>
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
    """Constructs a rich MIME email message with HTML formatting, embedded CID logo and PDF attachments."""
    profile_obj = profile or CandidateProfile()
    
    # Root message is multipart/mixed to support body + attachments
    msg = MIMEMultipart("mixed")
    msg["From"] = f"{sender_name} <{sender_email}>" if sender_name else sender_email
    msg["To"] = recipient_email
    msg["Subject"] = subject
    msg["Reply-To"] = sender_email

    # Alternative part for (Plain text + HTML)
    msg_alt = MIMEMultipart("alternative")
    
    # Plain text version
    msg_alt.attach(MIMEText(body_text, "plain", "utf-8"))
    
    # HTML version (embedded inside multipart/related for inline logo)
    msg_related = MIMEMultipart("related")
    html_body = build_professional_html(body_text, profile_obj, language=language, include_logo=True)
    msg_related.attach(MIMEText(html_body, "html", "utf-8"))
    
    # Attach RoboThings inline logo with Content-ID for signature
    if LOGO_PATH.is_file():
        try:
            with open(LOGO_PATH, "rb") as img_f:
                img_data = img_f.read()
                img_part = MIMEImage(img_data, _subtype="png")
                img_part.add_header("Content-ID", "<robothings_logo>")
                img_part.add_header("Content-Disposition", "inline", filename="robothings_logo.png")
                msg_related.attach(img_part)
        except Exception as e:
            print(f"[Warning] Could not attach inline logo: {e}")
            
    msg_alt.attach(msg_related)
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
                    with open(path, "rb") as f:
                        part = MIMEApplication(f.read(), _subtype="pdf")
                        part.add_header("Content-Disposition", "attachment", filename=path.name)
                        msg.attach(part)
                except Exception as e:
                    print(f"[Warning] Failed to attach {path.name}: {e}")
                    
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
                
        return SendResult(recipient=recipient_email, success=True, message="Email envoyé avec succès !")
    except Exception as e:
        return SendResult(recipient=recipient_email, success=False, message=str(e))

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
