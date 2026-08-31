import imaplib
import email
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.storage_service import get_db_connection, get_all_contacts

sys.stdout.reconfigure(encoding='utf-8')

print("1. Connexion a Gmail IMAP...", flush=True)
mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
mail.login('mohammedhsiny2@gmail.com', 'qawi kviz qjqu hwgb')
print("[OK] Connecte a Gmail !", flush=True)

# 1. Sent Mail
mail.select('"[Gmail]/Sent Mail"', readonly=True)
status, data = mail.search(None, 'ALL')
all_ids = data[0].split() if status == 'OK' and data[0] else []
print(f"2. Total emails dans 'Messages envoyes' Gmail: {len(all_ids)}", flush=True)

all_sent_recipients = set()
for mid in all_ids:
    st, mdata = mail.fetch(mid, '(BODY.PEEK[HEADER.FIELDS (TO SUBJECT)])')
    if st == 'OK' and mdata[0]:
        for item in mdata:
            if isinstance(item, tuple) and len(item) > 1:
                hdr = item[1].decode('utf-8', errors='ignore')
                for e in re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', hdr):
                    el = e.lower().strip()
                    if el != 'mohammedhsiny2@gmail.com' and 'google' not in el:
                        all_sent_recipients.add(el)

print(f"[OK] Total destinataires uniques envoyes depuis Gmail : {len(all_sent_recipients)}", flush=True)

# 2. Inspect ALL failure/bounce emails in INBOX and Trash
bounced_recipients = set()
for fld in ['INBOX', '"[Gmail]/Trash"', '"[Gmail]/Spam"']:
    try:
        mail.select(fld, readonly=True)
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
                        for fe in re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', btext):
                            fel = fe.lower().strip()
                            if fel != 'mohammedhsiny2@gmail.com' and 'google' not in fel and 'daemon' not in fel and 'mail' not in fel and 'smtp' not in fel:
                                bounced_recipients.add(fel)
    except Exception as ex:
        pass

mail.logout()

print(f"[OK] Total adresses 'Address not found' / Rejetees detectees dans Gmail : {len(bounced_recipients)}", flush=True)

# 3. Match against contacts in Excel Database
db_contacts = get_all_contacts()
db_emails = {c['email'].lower().strip(): c for c in db_contacts}

excel_sent_good = set()
excel_bounced = set()
excel_remaining = set()

with get_db_connection() as conn:
    for c in db_contacts:
        em = c['email'].lower().strip()
        if em in bounced_recipients:
            excel_bounced.add(em)
            conn.execute("UPDATE contacts SET status = 'bounced', notes = 'Adresse introuvable / Rejetee' WHERE LOWER(email) = ?", (em,))
        elif em in all_sent_recipients:
            excel_sent_good.add(em)
            conn.execute("UPDATE contacts SET status = 'sent' WHERE LOWER(email) = ?", (em,))
        else:
            excel_remaining.add(em)
    conn.commit()

print("\n=======================================================", flush=True)
print("             BILAN AUDIT COMPLET GMAIL & EXCEL", flush=True)
print("=======================================================", flush=True)
print(f"👥 Total contacts dans votre fichier Excel : {len(db_contacts)}", flush=True)
print(f"🚀 Emails ENVOYES avec SUCCES (Délivrés)   : {len(excel_sent_good)}", flush=True)
print(f"❌ Emails ADDRESS NOT FOUND (Rejetés)      : {len(excel_bounced)}", flush=True)
print(f"⏳ Emails RESTANTS A ENVOYER               : {len(excel_remaining)}", flush=True)
print("=======================================================", flush=True)

if excel_bounced:
    print("\n📋 Detail des adresses rejetées (Address not found) :", flush=True)
    for idx, em in enumerate(sorted(excel_bounced), 1):
        c_info = db_emails.get(em, {})
        print(f"  {idx}. {em} | {c_info.get('name', 'N/A')} ({c_info.get('company', 'N/A')})", flush=True)

if excel_sent_good:
    print(f"\n📋 Apercu des 10 derniers emails envoyes avec succes :", flush=True)
    for idx, em in enumerate(list(sorted(excel_sent_good))[:10], 1):
        c_info = db_emails.get(em, {})
        print(f"  {idx}. {em} | {c_info.get('name', 'N/A')} ({c_info.get('company', 'N/A')})", flush=True)

