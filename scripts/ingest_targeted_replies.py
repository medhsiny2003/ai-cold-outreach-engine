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

# Highly targeted query: Matches our outreach topics, replies and recruiter domains
query = '\"(subject:(stage OR PFE OR candidature OR entretien OR conseil OR information) OR from:(flyrenov OR harmattan OR mbda OR thales OR parrot OR cegelec OR airbus OR exail OR delair OR flyingeye OR shark OR skydrone)) -from:mailer-daemon -from:postmaster -from:mohammedhsiny2@gmail.com\"'
st, data = mail.search(None, 'X-GM-RAW', query)
msg_ids = data[0].split() if st == 'OK' and data[0] else []
print(f"Direct matching recruiter messages in INBOX: {len(msg_ids)}")

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

new_added = 0
for mid in msg_ids:
    try:
        st_b, b_data = mail.fetch(mid, '(RFC822)')
        if st_b != 'OK' or not b_data or not isinstance(b_data[0], tuple):
            continue
        msg = email.message_from_bytes(b_data[0][1])
        from_val = decode_mime(msg.get('From', ''))
        subj_val = decode_mime(msg.get('Subject', 'Sans objet'))
        
        emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', from_val)
        if not emails:
            continue
        sender_em = emails[0].lower().strip()
        sender_domain = sender_em.split('@')[1].lower() if '@' in sender_em else ""
        
        if (sender_em, subj_val) in existing_pairs:
            continue
            
        matched_contact = contacts_by_email.get(sender_em)
        if not matched_contact and sender_domain in contacts_by_domain:
            matched_contact = contacts_by_domain[sender_domain]
            
        body_text = ""
        if msg.is_multipart():
            for part in msg.walk():
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
            pl = msg.get_payload(decode=True)
            if pl:
                body_text = pl.decode(msg.get_content_charset() or 'utf-8', errors='ignore')
                
        sender_name = re.sub(r'<[^>]+>', '', from_val).strip().strip('"').strip("'")
        company_name = matched_contact.get("company", "") if matched_contact else sender_domain.split(".")[0].capitalize()
        
        ai_analysis = analyze_recruiter_email_with_ai(
            sender_name=sender_name,
            company=company_name,
            subject=subj_val,
            body_text=body_text[:1200],
            profile=None,
            llm_settings=None
        )
        
        save_recruiter_response({
            "contact_id": matched_contact["id"] if matched_contact else None,
            "sender_email": sender_em,
            "sender_name": sender_name,
            "company": company_name,
            "subject": subj_val,
            "body_text": body_text[:2500],
            "received_at": time.time(),
            "intent_category": ai_analysis["intent_category"],
            "sentiment_label": ai_analysis["sentiment_label"],
            "ai_summary": ai_analysis["ai_summary"],
            "ai_suggested_reply": ai_analysis["ai_suggested_reply"],
            "is_read": 0
        })
        existing_pairs.add((sender_em, subj_val))
        new_added += 1
        print(f"✅ Added reply from {sender_name} ({company_name}) - Intent: {ai_analysis['intent_category']}")
    except Exception as e:
        print('Error on mid', mid, e)

mail.logout()
print(f"Done. Newly ingested recruiter responses: {new_added}")
