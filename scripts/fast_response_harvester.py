import imaplib
import email
from email.header import decode_header
import re
import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from services.storage_service import (
    load_smtp_settings, get_all_contacts, save_recruiter_response,
    get_all_recruiter_responses, get_db_connection, init_db
)
from services.response_tracker import analyze_recruiter_email_with_ai

sys.stdout.reconfigure(encoding='utf-8')

smtp = load_smtp_settings()
mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
clean_pwd = smtp.app_password.replace(' ', '').strip()
mail.login(smtp.sender_email, clean_pwd)

mail.select('INBOX', readonly=True)

# 1. Search for non-daemon incoming messages
st, data = mail.search(None, 'X-GM-RAW', '"-from:mailer-daemon -from:postmaster -from:mohammedhsiny2@gmail.com -from:google.com -from:notifications -from:noreply -from:linkedin -from:github"')
msg_ids = data[0].split() if st == 'OK' and data[0] else []
print(f"Total candidate incoming messages in INBOX: {len(msg_ids)}")

contacts = get_all_contacts()
contacts_by_email = {c["email"].lower().strip(): c for c in contacts if "@" in c["email"]}
contacts_by_domain = {c["email"].split("@")[1].lower().strip(): c for c in contacts if "@" in c["email"]}

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
        return " ".join(res).strip()
    except Exception:
        return str(v).strip()

existing_responses = get_all_recruiter_responses()
existing_pairs = {(r["sender_email"].lower().strip(), r["subject"].strip()) for r in existing_responses}

new_found = []

# Process last 60 non-daemon messages
for mid in msg_ids[-60:]:
    try:
        st_h, h_data = mail.fetch(mid, '(BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE)])')
        if st_h != 'OK' or not h_data or not isinstance(h_data[0], tuple):
            continue
            
        hdr_msg = email.message_from_bytes(h_data[0][1])
        from_val = decode_mime(hdr_msg.get('From', ''))
        subj_val = decode_mime(hdr_msg.get('Subject', 'Sans objet'))
        date_val = hdr_msg.get('Date', '')
        
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', from_val)
        if not emails:
            continue
        sender_email = emails[0].lower().strip()
        sender_domain = sender_email.split('@')[1].lower() if '@' in sender_email else ""
        
        # Match with target database or PFE keywords
        matched_contact = contacts_by_email.get(sender_email)
        if not matched_contact and sender_domain in contacts_by_domain:
            matched_contact = contacts_by_domain[sender_domain]
            
        is_relevant = False
        if matched_contact:
            is_relevant = True
        elif any(k in subj_val.lower() for k in ["stage", "pfe", "candidature", "entretien", "hsiny", "robotique", "ingénieur", "re:"]):
            is_relevant = True
            
        # Filter spam / job aggregator blasts
        if any(ign in sender_email for ign in ["indeed", "sponta", "workday", "hellowork", "welcometothejungle", "jobi", "glassdoor"]):
            is_relevant = False
            
        if is_relevant:
            # Fetch message body
            st_b, b_data = mail.fetch(mid, '(RFC822)')
            body_text = ""
            if st_b == 'OK' and b_data and isinstance(b_data[0], tuple):
                full_msg = email.message_from_bytes(b_data[0][1])
                if full_msg.is_multipart():
                    for part in full_msg.walk():
                        ct = part.get_content_type()
                        cd = str(part.get('Content-Disposition', ''))
                        if ct == 'text/plain' and 'attachment' not in cd:
                            pl = part.get_payload(decode=True)
                            if pl:
                                body_text += pl.decode(part.get_content_charset() or 'utf-8', errors='ignore') + "\n"
                        elif ct == 'text/html' and not body_text and 'attachment' not in cd:
                            pl = part.get_payload(decode=True)
                            if pl:
                                raw_h = pl.decode(part.get_content_charset() or 'utf-8', errors='ignore')
                                body_text = re.sub(r'<[^>]+>', ' ', raw_h)
                else:
                    pl = full_msg.get_payload(decode=True)
                    if pl:
                        body_text = pl.decode(full_msg.get_content_charset() or 'utf-8', errors='ignore')
                        
            sender_name = re.sub(r'<[^>]+>', '', from_val).strip().strip('"').strip("'")
            company_name = matched_contact.get("company", "") if matched_contact else ""
            
            new_found.append({
                "sender_email": sender_email,
                "sender_name": sender_name,
                "company": company_name,
                "subject": subj_val,
                "body_text": body_text[:2000],
                "date": date_val
            })
    except Exception as e:
        print('Error processing mid', mid, e)

print(f"\n🎉 HARVESTED {len(new_found)} RECRUITER RESPONSES SUCCESSFULLY!")
for r in new_found:
    print(f"[{r['company'] or 'Contact'}] {r['sender_name']} <{r['sender_email']}> | SUBJ: {r['subject']}")
    print(f"   BODY PREVIEW: {r['body_text'][:120].replace(chr(10), ' ')}...\n")

mail.logout()
