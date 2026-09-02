import imaplib
import email
from email.header import decode_header
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.storage_service import load_smtp_settings, get_all_contacts

sys.stdout.reconfigure(encoding='utf-8')

smtp = load_smtp_settings()
mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
clean_pwd = smtp.app_password.replace(' ', '').strip()
mail.login(smtp.sender_email, clean_pwd)

mail.select('INBOX', readonly=True)

# 1. Search for non-daemon incoming messages
st, data = mail.search(None, 'X-GM-RAW', '"-from:mailer-daemon -from:postmaster -from:mohammedhsiny2@gmail.com"')
msg_ids = data[0].split() if st == 'OK' and data[0] else []
print(f"Total non-daemon incoming messages in INBOX: {len(msg_ids)}")

contacts = get_all_contacts()
all_companies = {c.get('company', '').lower().strip() for c in contacts if c.get('company')}
all_domains = {c['email'].split('@')[1].lower().strip() for c in contacts if '@' in c['email']}
all_emails = {c['email'].lower().strip() for c in contacts if '@' in c['email']}

print(f"Tracking {len(all_emails)} target emails across {len(all_domains)} companies...")

found_replies = []

def decode_mime(v):
    if not v:
        return ""
    try:
        parts = decode_header(v)
        res = []
        for p, enc in parts:
            if isinstance(p, bytes):
                res.append(p.decode(enc or 'utf-8', errors='ignore'))
            else:
                res.append(str(p))
        return " ".join(res)
    except Exception:
        return str(v)

# Check the last 150 incoming messages
for mid in msg_ids[-150:]:
    try:
        st_f, f_data = mail.fetch(mid, '(RFC822)')
        if st_f != 'OK' or not f_data or not isinstance(f_data[0], tuple):
            continue
        msg = email.message_from_bytes(f_data[0][1])
        from_hdr = decode_mime(msg.get('From', ''))
        subj_hdr = decode_mime(msg.get('Subject', ''))
        date_hdr = msg.get('Date', '')
        
        # Extract sender email address
        emails_found = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', from_hdr)
        sender_email = emails_found[0].lower().strip() if emails_found else ""
        sender_domain = sender_email.split('@')[1].lower() if '@' in sender_email else ""
        
        # Check if matched with our outreach target contacts or domains or relevant PFE subject
        is_recruiter = False
        match_type = ""
        
        if sender_email in all_emails:
            is_recruiter = True
            match_type = "DIRECT_CONTACT"
        elif sender_domain in all_domains:
            is_recruiter = True
            match_type = "COMPANY_DOMAIN"
        elif any(k in subj_hdr.lower() for k in ["stage", "pfe", "candidature", "entretien", "hsiny", "robotique", "embarqué", "ingénieur"]):
            is_recruiter = True
            match_type = "SUBJECT_KEYWORD"

        # Ignore automated spam/newsletters
        if any(ign in sender_email for ign in ["google.com", "linkedin.com", "github.com", "facebook.com", "notifications", "newsletter", "billing", "uber", "spotify", "indeed", "sponta"]):
            if match_type != "DIRECT_CONTACT":
                is_recruiter = False

        if is_recruiter:
            body_text = ""
            if msg.is_multipart():
                for part in msg.walk():
                    ctype = part.get_content_type()
                    cdispo = str(part.get('Content-Disposition', ''))
                    if ctype == 'text/plain' and 'attachment' not in cdispo:
                        payload = part.get_payload(decode=True)
                        if payload:
                            body_text += payload.decode(part.get_content_charset() or 'utf-8', errors='ignore') + "\n"
                    elif ctype == 'text/html' and not body_text and 'attachment' not in cdispo:
                        payload = part.get_payload(decode=True)
                        if payload:
                            raw_html = payload.decode(part.get_content_charset() or 'utf-8', errors='ignore')
                            body_text = re.sub(r'<[^>]+>', ' ', raw_html)
            else:
                payload = msg.get_payload(decode=True)
                if payload:
                    body_text = payload.decode(msg.get_content_charset() or 'utf-8', errors='ignore')

            found_replies.append({
                "id": mid.decode(),
                "date": date_hdr,
                "from": from_hdr,
                "email": sender_email,
                "subject": subj_hdr,
                "match": match_type,
                "snippet": body_text[:200].replace('\n', ' ')
            })
    except Exception as e:
        pass

print(f"\n=== FOUND {len(found_replies)} RECRUITER / RELEVANT INBOX REPLIES ===")
for r in found_replies:
    print(f"[{r['match']}] {r['from']} | SUBJ: {r['subject']}")
    print(f"   -> SNIPPET: {r['snippet']}\n")

mail.logout()
