import imaplib
import email
from email.header import decode_header
import re
import sys
from pathlib import Path
from datetime import datetime

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.storage_service import get_db_connection, get_all_contacts

sys.stdout.reconfigure(encoding='utf-8')

print("==========================================================")
print("       AUDIT APPROFONDI DE TOUT LE COMPTE GMAIL")
print("==========================================================")

mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
mail.login('mohammedhsiny2@gmail.com', 'qawi kviz qjqu hwgb')

# 1. Inspect ALL sent emails from "[Gmail]/Sent Mail" (no limit)
status, count_data = mail.select('"[Gmail]/Sent Mail"', readonly=True)
total_sent_in_box = int(count_data[0]) if count_data and count_data[0] else 0
print(f"[*] Total absolu d'emails dans 'Messages envoyés' Gmail : {total_sent_in_box}")

# Search specifically for emails sent with subject containing "Stage PFE" or "PFE" or all sent
status, data = mail.search(None, 'ALL')
all_sent_ids = data[0].split() if status == 'OK' and data[0] else []

pfe_sent_emails = []
all_sent_recipients = {}

print(f"[*] Analyse des {len(all_sent_ids)} messages envoyés...")

# Batch fetch headers
chunk_size = 100
for i in range(0, len(all_sent_ids), chunk_size):
    chunk = all_sent_ids[i:i+chunk_size]
    seq_set = b",".join(chunk).decode('ascii')
    st, fetch_data = mail.fetch(seq_set, '(BODY.PEEK[HEADER.FIELDS (TO SUBJECT DATE)])')
    if st == 'OK':
        for item in fetch_data:
            if isinstance(item, tuple) and len(item) > 1:
                hdr_text = item[1].decode('utf-8', errors='ignore')
                to_m = re.search(r'To:\s*(.*)', hdr_text, re.IGNORECASE)
                subj_m = re.search(r'Subject:\s*(.*)', hdr_text, re.IGNORECASE)
                date_m = re.search(r'Date:\s*(.*)', hdr_text, re.IGNORECASE)
                
                subj = subj_m.group(1).strip() if subj_m else ""
                date_str = date_m.group(1).strip() if date_m else ""
                
                if to_m:
                    found_to = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', to_m.group(1))
                    for e in found_to:
                        el = e.lower().strip()
                        if el != 'mohammedhsiny2@gmail.com':
                            all_sent_recipients[el] = {
                                'subject': subj,
                                'date': date_str
                            }
                            if "pfe" in subj.lower() or "stage" in subj.lower():
                                pfe_sent_emails.append((el, subj, date_str))

print(f"[*] Total destinataires distincts envoyés : {len(all_sent_recipients)}")
print(f"[*] Total emails envoyés spécifiquement avec 'PFE / Stage' : {len(pfe_sent_emails)}")

# 2. Inspect ALL Bounces / Address not found across ALL folders
all_folders = ['INBOX', '"[Gmail]/All Mail"', '"[Gmail]/Trash"', '"[Gmail]/Spam"']
bounced_details = {}

for fld in all_folders:
    try:
        status, cdata = mail.select(fld, readonly=True)
        if status != 'OK':
            continue
        
        # Search for failure notices
        for q in ['(FROM "mailer-daemon@googlemail.com")', '(FROM "Mail Delivery Subsystem")', '(SUBJECT "Address not found")', '(SUBJECT "Delivery Status Notification")']:
            st, d = mail.search(None, q)
            if st == 'OK' and d[0]:
                b_ids = d[0].split()
                for b_id in b_ids:
                    st2, bdata = mail.fetch(b_id, '(RFC822)')
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
                        for fe in found:
                            fel = fe.lower().strip()
                            if fel != 'mohammedhsiny2@gmail.com' and 'google' not in fel and 'daemon' not in fel and 'mail' not in fel and 'smtp' not in fel:
                                bounced_details[fel] = fld
    except Exception as ex:
        pass

mail.logout()

print(f"[*] Total adresses 'Address not found' / Rejetées détectées dans Gmail : {len(bounced_details)}")

# 3. Synchronize with Database
print("\n[3/3] Synchronisation complète avec la base de données...")
with get_db_connection() as conn:
    # First: Mark real bounced addresses
    for b_email in bounced_details.keys():
        conn.execute("UPDATE contacts SET status = 'bounced', notes = 'Adresse introuvable / Rejetée (Mail Delivery Subsystem)' WHERE LOWER(email) = ?", (b_email,))
        
    # Second: Mark real sent addresses (unless they bounced)
    for s_email in all_sent_recipients.keys():
        if s_email in bounced_details:
            conn.execute("UPDATE contacts SET status = 'bounced', notes = 'Adresse introuvable / Rejetée (Mail Delivery Subsystem)' WHERE LOWER(email) = ?", (s_email,))
        else:
            conn.execute("UPDATE contacts SET status = 'sent' WHERE LOWER(email) = ?", (s_email,))
    conn.commit()

# Current DB breakdown
contacts = get_all_contacts()
st_counts = {}
for c in contacts:
    st = c.get('status', 'pending')
    st_counts[st] = st_counts.get(st, 0) + 1

print("\n=======================================================")
print("             RÉSULTATS DE L'AUDIT COMPLET GMAIL")
print("=======================================================")
print(f"👥 Total des contacts dans la base Excel        : {len(contacts)}")
print(f"🚀 Emails RÉELLEMENT ENVOYÉS et DÉLIVRÉS (Bons) : {st_counts.get('sent', 0)}")
print(f"❌ Emails ADDRESS NOT FOUND / REJETÉS (Bannis)  : {st_counts.get('bounced', 0)}")
print(f"⏳ Emails VALIDÉS & RESTANTS À ENVOYER          : {st_counts.get('approved', 0)}")
print(f"📝 Emails en attente de génération              : {st_counts.get('pending', 0)}")
print("=======================================================")

print("\n📋 LISTE DES ADRESSES 'ADDRESS NOT FOUND' DÉTECTÉES :")
for idx, (b_email, fld) in enumerate(sorted(bounced_details.items()), 1):
    print(f"  {idx}. {b_email}")

