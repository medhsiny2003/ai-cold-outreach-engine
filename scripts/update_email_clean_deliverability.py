import re

# 1. Update services/email_sender.py
with open("services/email_sender.py", "r", encoding="utf-8") as f:
    sender_code = f.read()

# Add import re if needed
if "import re" not in sender_code:
    sender_code = "import re\n" + sender_code

# Add sanitize_email_body_for_deliverability before build_professional_html
sanitizer_def = '''def sanitize_email_body_for_deliverability(text: str) -> str:
    """
    Supprime tous les liens URL, liens Markdown et mentions de club/ex-présidence
    pour garantir une délivrabilité maximale (Zéro SPAM) et positionner Mohammed
    strictement comme élève-ingénieur en dernière année (Final-Year Engineering Student).
    """
    if not text:
        return ""
        
    # 1. Supprimer les boutons ou ancres de portfolio markdown [Explorer mon Portfolio...](url)
    text = re.sub(r'\\[(?:Explorer|Explore|Consulter|Voir)[^\\]]*\\]\\([^\\)]+\\)', '', text, flags=re.IGNORECASE)
    # Supprimer les autres liens markdown [Texte](URL) en ne gardant que Texte
    text = re.sub(r'\\[([^\\]]+)\\]\\([^\\)]+\\)', r'\\1', text)
    
    # 2. Supprimer toute URL brute (http://, https://)
    text = re.sub(r'https?://[^\\s<>"]+', '', text, flags=re.IGNORECASE)
    
    # 3. Supprimer toute mention de club ou d'ex-présidence
    text = re.sub(r'(?:ex-)?président\\s+(?:et\\s+team\\s+leader\\s+)?du\\s+club\\s+(?:robotique\\s+)?robothings[^\\n,.]*', 'élève-ingénieur en dernière année', text, flags=re.IGNORECASE)
    text = re.sub(r'(?:ex-)?president\\s+(?:and\\s+team\\s+leader\\s+)?of\\s+(?:the\\s+)?(?:robotics\\s+club\\s+)?robothings[^\\n,.]*', 'final-year engineering student', text, flags=re.IGNORECASE)
    text = re.sub(r'\\b(?:ex-)?président\\s+du\\s+club\\b', 'élève-ingénieur en dernière année', text, flags=re.IGNORECASE)
    text = re.sub(r'\\b(?:ex-)?president\\s+of\\s+the\\s+club\\b', 'final-year student', text, flags=re.IGNORECASE)
    text = re.sub(r'\\bRoboThings\\b', 'Robotique', text, flags=re.IGNORECASE)
    text = re.sub(r'(?:en\\s+tant\\s+qu\\\'?|mon\\s+rôle\\s+d\\\'?)ex-?président[^\\n,.]*', "élève-ingénieur en dernière année", text, flags=re.IGNORECASE)
    text = re.sub(r'(?:as\\s+)?(?:ex-)?president\\s+of[^\\n,.]*', "final-year engineering student", text, flags=re.IGNORECASE)

    # 4. Nettoyer les lignes blanches consécutives
    lines = [l.strip() for l in text.split("\\n")]
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
            
    return "\\n".join(cleaned).strip()

'''

if "def sanitize_email_body_for_deliverability" not in sender_code:
    # Insert right before def build_professional_html
    sender_code = sender_code.replace("def build_professional_html(", sanitizer_def + "def build_professional_html(")

# Replace build_professional_html function
old_html_builder_pattern = re.search(r'def build_professional_html\(.*?return html_content', sender_code, re.DOTALL)
if old_html_builder_pattern:
    new_html_builder = '''def build_professional_html(
    body_text: str,
    profile: CandidateProfile,
    language: str = "fr",
    include_logo: bool = False
) -> str:
    """Génère un email HTML professionnel épuré, sans liens URL, sans logo ni badge club (100% Anti-Spam)."""
    clean_text = sanitize_email_body_for_deliverability(body_text)
    lines = clean_text.split("\\n")
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
        
    formatted_body = "\\n".join(html_paragraphs)
    
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
    return html_content'''
    sender_code = sender_code[:old_html_builder_pattern.start()] + new_html_builder + sender_code[old_html_builder_pattern.end():]

# Update create_email_message to sanitize body and remove CID logo
old_create_msg = re.search(r'def create_email_message\(.*?return msg', sender_code, re.DOTALL)
if old_create_msg:
    new_create_msg = '''def create_email_message(
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
                    
    return msg'''
    sender_code = sender_code[:old_create_msg.start()] + new_create_msg + sender_code[old_create_msg.end():]

with open("services/email_sender.py", "w", encoding="utf-8") as f:
    f.write(sender_code)

print("Updated services/email_sender.py successfully!")
