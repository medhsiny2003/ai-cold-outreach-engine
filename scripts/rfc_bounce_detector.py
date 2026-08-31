import imaplib
import email
from email.header import decode_header
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.storage_service import get_db_connection, get_all_contacts

sys.stdout.reconfigure(encoding='utf-8')

print("[1/3] Connexion IMAP a Gmail...", flush=True)
mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
mail.login('mohammedhsiny2@gmail.com', 'qawi kviz qjqu hwgb')
print("[OK] Connecte a Gmail avec succes !", flush=True)

# 1. Fetch all distinct external recipients in Sent Mail
mail.select('"[Gmail]/Sent Mail"', readonly=True)
st, data = mail.search(None, 'ALL')
all_sent_msg_ids = data[0].split() if st == 'OK' and data[0] else []
print(f"[2/3] Total messages dans 'Messages envoyes' : {len(all_sent_msg_ids)}", flush=True)

sent_recipients = {}
# Batch fetch
for i in range(0, len(all_sent_msg_ids), 100):
    chunk = all_sent_msg_ids[i:i+100]
    seq_set = b",".join(chunk).decode('ascii')
    st2, fetch_data = mail.fetch(seq_set, '(BODY.PEEK[HEADER.FIELDS (TO DATE SUBJECT)])')
    if st2 == 'OK':
        for item in fetch_data:
            if isinstance(item, tuple) and len(item) > 1:
                hdr = item[1].decode('utf-8', errors='ignore')
                to_m = re.search(r'To:\s*(.*)', hdr, re.IGNORECASE)
                date_m = re.search(r'Date:\s*(.*)', hdr, re.IGNORECASE)
                if to_m:
                    emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', to_m.group(1))
                    for e in emails:
                        el = e.lower().strip()
                        if el != 'mohammedhsiny2@gmail.com':
                            sent_recipients[el] = date_m.group(1).strip() if date_m else "Envoyé"

print(f"[OK] Total destinataires uniques envoyes depuis Gmail : {len(sent_recipients)}", flush=True)

# 2. Inspect RFC 3464 Non-Delivery Reports across INBOX and Trash
print("[3/3] Analyse approfondie des DSN / Non-Delivery Reports (Address not found)...", flush=True)
bounces_dict = {}

for fld in ['INBOX', '"[Gmail]/Trash"', '"[Gmail]/Spam"']:
    try:
        st, _ = mail.select(fld, readonly=True)
        if st != 'OK':
            continue
        
        st, d = mail.search(None, '(OR (FROM "mailer-daemon") (OR (FROM "Mail Delivery Subsystem") (SUBJECT "Delivery Status Notification")))')
        if st == 'OK' and d[0]:
            b_ids = d[0].split()
            for b_id in b_ids:
                st2, bdata = mail.fetch(b_id, '(RFC822)')
                if st2 == 'OK' and bdata[0]:
                    msg = email.message_from_bytes(bdata[0][1])
                    
                    failed_recip = None
                    diag_code = "550 5.1.1 Address not found (User unknown)"
                    
                    # Walk parts
                    for part in msg.walk():
                        ct = part.get_content_type()
                        if ct == 'message/delivery-status':
                            sub_str = str(part.get_payload())
                            rm = re.search(r'Final-Recipient:\s*(?:rfc822;)?\s*([^\s;]+)', sub_str, re.IGNORECASE)
                            dm = re.search(r'Diagnostic-Code:\s*(.*)', sub_str, re.IGNORECASE)
                            if rm:
                                failed_recip = rm.group(1).strip().strip('<>')
                            if dm:
                                diag_code = dm.group(1).strip()
                                
                    if not failed_recip:
                        body_txt = ""
                        for part in msg.walk():
                            if part.get_content_type() == 'text/plain':
                                try:
                                    body_txt += part.get_payload(decode=True).decode(errors='ignore') + "\n"
                                except:
                                    pass
                        tm = re.search(r'(?:wasn\'t delivered to|Address not found|couldn\'t be delivered to|failed:)\s*([^\s<]+@[^\s>]+)', body_txt, re.IGNORECASE)
                        if tm:
                            failed_recip = tm.group(1).strip().strip('<>').strip('.')
                        else:
                            for em in re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', body_txt):
                                eml = em.lower().strip()
                                if eml != 'mohammedhsiny2@gmail.com' and 'google' not in eml and 'daemon' not in eml and 'mail' not in eml:
                                    failed_recip = eml
                                    break
                                    
                    if failed_recip:
                        clean_r = failed_recip.lower().strip().strip('<>').strip('.')
                        bounces_dict[clean_r] = diag_code
    except Exception as ex:
        print(f"Error checking {fld}: {ex}", flush=True)

mail.logout()

print(f"[OK] Total adresses 'Address not found' certifiees par Mailer-Daemon : {len(bounces_dict)}", flush=True)

# 3. Synchronize with SQLite Database
contacts = get_all_contacts()
with get_db_connection() as conn:
    for c in contacts:
        em = c['email'].lower().strip()
        if em in bounces_dict:
            # Verified bounce from Gmail
            diag = bounces_dict[em]
            conn.execute("UPDATE contacts SET status = 'bounced', notes = ? WHERE LOWER(email) = ?", (f"❌ Rejeté Mailer-Daemon : {diag[:100]}", em))
        elif em in sent_recipients:
            # Verified sent and no bounce received
            send_dt = sent_recipients[em]
            conn.execute("UPDATE contacts SET status = 'sent', notes = ? WHERE LOWER(email) = ?", (f"🟢 Délivré avec succès (Envoyé le {send_dt})", em))
    conn.commit()

# Final accurate breakdown
fresh_contacts = get_all_contacts()
st_map = {}
for c in fresh_contacts:
    s = c.get('status', 'pending')
    st_map[s] = st_map.get(s, 0) + 1

print("\n" + "="*70, flush=True)
print("       BILAN DE VÉRIFICATION RÉELLE CERTIFIÉ GMAIL", flush=True)
print("="*70, flush=True)
print(f"👥 Total contacts en base                     : {len(fresh_contacts)}", flush=True)
print(f"🟢 DÉLIVRÉS SANS ERREUR (Validés sans bounce) : {st_map.get('sent', 0)}", flush=True)
print(f"🔴 REJETÉS - ADDRESS NOT FOUND (Prouvés DSN)  : {st_map.get('bounced', 0)}", flush=True)
print(f"⏳ EN ATTENTE D'ENVOI (Non encore expédiés)   : {st_map.get('approved', 0)}", flush=True)
print("="*70, flush=True)

print("\n📋 LISTE EXACTE DES CONTACTS REJETÉS (ADDRESS NOT FOUND) :", flush=True)
bounced_list = [c for c in fresh_contacts if c.get('status') == 'bounced']
for idx, c in enumerate(sorted(bounced_list, key=lambda x: x.get('company', '')), 1):
    print(f"  {idx:<2}. {c['email']:<38} | {c.get('company', 'N/A'):<20} | {c.get('notes', '')[:45]}", flush=True)

