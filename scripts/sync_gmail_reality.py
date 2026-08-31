import imaplib
import email
from email.header import decode_header
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.storage_service import get_db_connection, get_all_contacts

sys.stdout.reconfigure(encoding='utf-8')

mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
mail.login('mohammedhsiny2@gmail.com', 'qawi kviz qjqu hwgb')

# 1. Check Sent Mail
status, _ = mail.select('"[Gmail]/Sent Mail"')
status, data = mail.search(None, 'ALL')
sent_msg_ids = data[0].split() if status == 'OK' and data[0] else []

print(f"[*] Total emails in Gmail Sent Mail: {len(sent_msg_ids)}")

sent_recipients = {}
for mid in sent_msg_ids:
    status, mdata = mail.fetch(mid, '(BODY.PEEK[HEADER.FIELDS (TO SUBJECT DATE)])')
    if status == 'OK' and mdata[0]:
        header_text = mdata[0][1].decode('utf-8', errors='ignore')
        # Extract To:
        to_match = re.search(r'To:\s*(.*)', header_text, re.IGNORECASE)
        subj_match = re.search(r'Subject:\s*(.*)', header_text, re.IGNORECASE)
        date_match = re.search(r'Date:\s*(.*)', header_text, re.IGNORECASE)
        if to_match:
            raw_to = to_match.group(1).strip()
            # Extract email address
            emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', raw_to)
            for e in emails:
                e_clean = e.lower().strip()
                if e_clean != 'mohammedhsiny2@gmail.com':
                    sent_recipients[e_clean] = {
                        'subject': subj_match.group(1).strip() if subj_match else '',
                        'date': date_match.group(1).strip() if date_match else ''
                    }

print(f"[*] Distinct external recipients actually sent from Gmail: {len(sent_recipients)}")

# 2. Check Bounces / Address not found across INBOX, Trash, Spam
all_bounced_recipients = set()

for folder in ['INBOX', '"[Gmail]/Trash"', '"[Gmail]/Spam"']:
    try:
        mail.select(folder)
        for q in ['(FROM "mailer-daemon@googlemail.com")', '(FROM "Mail Delivery Subsystem")', '(SUBJECT "Address not found")', '(SUBJECT "Delivery Status Notification")']:
            st, d = mail.search(None, q)
            if st == 'OK' and d[0]:
                for bmid in d[0].split():
                    st2, bdata = mail.fetch(bmid, '(RFC822)')
                    if st2 == 'OK' and bdata[0]:
                        msg = email.message_from_bytes(bdata[0][1])
                        btext = ""
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    try:
                                        btext += part.get_payload(decode=True).decode(errors="ignore") + "\n"
                                    except:
                                        pass
                        else:
                            try:
                                btext = msg.get_payload(decode=True).decode(errors="ignore")
                            except:
                                pass
                        
                        found = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', btext)
                        for f in found:
                            fl = f.lower().strip()
                            if fl != 'mohammedhsiny2@gmail.com' and 'google' not in fl and 'daemon' not in fl and 'mail' not in fl:
                                all_bounced_recipients.add(fl)
    except Exception as ex:
        print(f"Error checking {folder}: {ex}")

mail.logout()

print(f"[*] Total distinct bounced/rejected addresses found in Gmail: {len(all_bounced_recipients)}")

# 3. Synchronize with SQLite Database
db_contacts = get_all_contacts()
db_emails = {c['email'].lower().strip(): c for c in db_contacts}

print("\n--- SYNCHRONIZING REALITY INTO DATABASE ---")

synced_sent = 0
synced_bounced = 0

with get_db_connection() as conn:
    # First: Mark real bounced addresses
    for b in all_bounced_recipients:
        conn.execute("UPDATE contacts SET status = 'bounced', notes = 'Adresse introuvable / Rejetée (Mail Delivery Subsystem)' WHERE LOWER(email) = ?", (b,))
        synced_bounced += 1
        
    # Second: Mark real sent addresses (unless they bounced)
    for s_email, s_data in sent_recipients.items():
        if s_email in all_bounced_recipients:
            conn.execute("UPDATE contacts SET status = 'bounced', notes = 'Adresse introuvable / Rejetée (Mail Delivery Subsystem)' WHERE LOWER(email) = ?", (s_email,))
        else:
            conn.execute("UPDATE contacts SET status = 'sent' WHERE LOWER(email) = ?", (s_email,))
            synced_sent += 1
    conn.commit()

# Query final fresh stats
fresh_contacts = get_all_contacts()
st_counts = {}
for c in fresh_contacts:
    st_counts[c.get('status', 'unknown')] = st_counts.get(c.get('status', 'unknown'), 0) + 1

print("\n================ REAL SYNCHRONIZED STATS ================")
print(f"👥 Total contacts in database : {len(fresh_contacts)}")
for st, cnt in st_counts.items():
    print(f"   - Status '{st}': {cnt}")
print("=========================================================")
