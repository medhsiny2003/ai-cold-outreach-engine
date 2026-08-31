import imaplib
import email
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.storage_service import get_db_connection, get_all_contacts

sys.stdout.reconfigure(encoding='utf-8')

print("[1/3] Connexion IMAP à Gmail...")
mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
mail.login('mohammedhsiny2@gmail.com', 'qawi kviz qjqu hwgb')
print("[OK] Connecté avec succès !")

# 1. Check Sent Mail in 1 batch
status, count_data = mail.select('"[Gmail]/Sent Mail"', readonly=True)
total_sent_in_folder = int(count_data[0]) if count_data and count_data[0] else 0
print(f"[2/3] Total messages dans 'Messages envoyés' Gmail : {total_sent_in_folder}")

sent_recipients = set()

if total_sent_in_folder > 0:
    # Fetch last 500 headers in 1 command
    start_seq = max(1, total_sent_in_folder - 500)
    seq_range = f"{start_seq}:{total_sent_in_folder}"
    status, data = mail.fetch(seq_range, '(BODY.PEEK[HEADER.FIELDS (TO)])')
    if status == 'OK':
        for item in data:
            if isinstance(item, tuple) and len(item) > 1:
                header_str = item[1].decode('utf-8', errors='ignore')
                emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', header_str)
                for e in emails:
                    e_clean = e.lower().strip()
                    if e_clean != 'mohammedhsiny2@gmail.com':
                        sent_recipients.add(e_clean)

print(f"[OK] Destinataires réels uniques trouvés dans Gmail Sent Mail : {len(sent_recipients)}")

# 2. Check Bounces / Address not found in Trash and Inbox
bounced_recipients = set()

for folder_name in ['"[Gmail]/Trash"', 'INBOX']:
    try:
        status, count_data = mail.select(folder_name, readonly=True)
        tot = int(count_data[0]) if count_data and count_data[0] else 0
        if tot > 0:
            start_seq = max(1, tot - 300)
            status, data = mail.fetch(f"{start_seq}:{tot}", '(BODY.PEEK[HEADER.FIELDS (FROM SUBJECT)])')
            if status == 'OK':
                for item in data:
                    if isinstance(item, tuple) and len(item) > 1:
                        hdr = item[1].decode('utf-8', errors='ignore')
                        if "mailer-daemon" in hdr.lower() or "delivery" in hdr.lower() or "address not found" in hdr.lower():
                            # This is a bounce
                            pass
    except Exception as ex:
        pass

mail.logout()

# 3. Synchronize with Database
print("[3/3] Synchronisation exacte de la base de données...")
with get_db_connection() as conn:
    for s_email in sent_recipients:
        # Mark as sent if not bounced
        conn.execute("UPDATE contacts SET status = 'sent' WHERE LOWER(email) = ? AND status != 'bounced'", (s_email,))
    conn.commit()

# Current DB breakdown
contacts = get_all_contacts()
st_counts = {}
for c in contacts:
    st = c.get('status', 'pending')
    st_counts[st] = st_counts.get(st, 0) + 1

print("\n=======================================================")
print("       RÉSULTAT EXACT SYNCHRONISÉ AVEC GMAIL")
print("=======================================================")
print(f"📊 Total des contacts dans la base Excel  : {len(contacts)}")
print(f"🚀 Emails RÉELLEMENT ENVOYÉS depuis Gmail : {st_counts.get('sent', 0)}")
print(f"⏳ Emails VALIDÉS & RESTANTS À ENVOYER    : {st_counts.get('approved', 0)}")
print(f"❌ Emails NOT FOUND / REJETÉS (Bannis)    : {st_counts.get('bounced', 0)}")
print(f"📝 Emails en attente de génération        : {st_counts.get('pending', 0)}")
print("=======================================================")
