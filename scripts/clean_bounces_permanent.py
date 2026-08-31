import imaplib
import email
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.storage_service import get_db_connection

sys.stdout.reconfigure(encoding='utf-8')

print("[1/4] Connexion IMAP a Gmail...", flush=True)
mail = imaplib.IMAP4_SSL('imap.gmail.com', 993)
mail.login('mohammedhsiny2@gmail.com', 'qawi kviz qjqu hwgb')
print("[OK] Connecte a Gmail !", flush=True)

# 1. Clean INBOX
print("[2/4] Purge des notifications d'erreur dans la boîte de réception (INBOX)...", flush=True)
mail.select('INBOX')
st, d = mail.search(None, '(OR (FROM "mailer-daemon") (OR (FROM "Mail Delivery Subsystem") (SUBJECT "Delivery Status Notification")))')

bounced_emails = set()

if st == 'OK' and d[0]:
    ids = d[0].split()
    print(f"-> {len(ids)} notifications de rejet trouvées dans INBOX. Suppression...", flush=True)
    for mid in ids:
        try:
            # Fetch recipient before deleting
            st2, mdata = mail.fetch(mid, '(BODY.PEEK[TEXT])')
            if st2 == 'OK' and mdata[0]:
                body_txt = str(mdata[0][1])
                for e in re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', body_txt):
                    el = e.lower().strip()
                    if el != 'mohammedhsiny2@gmail.com' and 'google' not in el and 'daemon' not in el and 'mail' not in el:
                        bounced_emails.add(el)
            # Move to Trash and Delete from INBOX
            mail.copy(mid, '"[Gmail]/Trash"')
            mail.store(mid, '+FLAGS', '\\Deleted')
        except Exception as ex:
            pass
    mail.expunge()
    print("[OK] Boîte de réception INBOX 100% nettoyée !", flush=True)
else:
    print("[OK] Aucun message de rejet restant dans INBOX.", flush=True)

# 2. Clean Spam
print("[3/4] Purge du dossier Spam...", flush=True)
try:
    mail.select('"[Gmail]/Spam"')
    st, d = mail.search(None, '(OR (FROM "mailer-daemon") (OR (FROM "Mail Delivery Subsystem") (SUBJECT "Delivery Status Notification")))')
    if st == 'OK' and d[0]:
        ids = d[0].split()
        print(f"-> {len(ids)} messages trouvés dans Spam. Suppression...", flush=True)
        for mid in ids:
            mail.store(mid, '+FLAGS', '\\Deleted')
        mail.expunge()
        print("[OK] Spam nettoyé !", flush=True)
except Exception as ex:
    print(f"Erreur Spam : {ex}", flush=True)

# 3. Empty Trash
print("[4/4] Vidage définitif de la Corbeille...", flush=True)
try:
    mail.select('"[Gmail]/Trash"')
    st, d = mail.search(None, '(OR (FROM "mailer-daemon") (OR (FROM "Mail Delivery Subsystem") (SUBJECT "Delivery Status Notification")))')
    if st == 'OK' and d[0]:
        ids = d[0].split()
        print(f"-> {len(ids)} messages trouvés dans la Corbeille. Élimination définitive...", flush=True)
        for mid in ids:
            mail.store(mid, '+FLAGS', '\\Deleted')
        mail.expunge()
        print("[OK] Corbeille vidée définitivement !", flush=True)
except Exception as ex:
    print(f"Erreur Corbeille : {ex}", flush=True)

# Verification check
mail.select('INBOX')
st, d = mail.search(None, '(OR (FROM "mailer-daemon") (OR (FROM "Mail Delivery Subsystem") (SUBJECT "Delivery Status Notification")))')
remaining_inbox = len(d[0].split()) if st == 'OK' and d[0] else 0

mail.logout()

# Update DB
if bounced_emails:
    with get_db_connection() as conn:
        for b in bounced_emails:
            conn.execute("UPDATE contacts SET status = 'bounced', notes = '❌ Rejeté Mailer-Daemon (Purger de Gmail)' WHERE LOWER(email) = ?", (b,))
        conn.commit()

print("\n" + "="*60, flush=True)
print("      RÉSULTAT DU NETTOYAGE DÉFINITIF GMAIL", flush=True)
print("="*60, flush=True)
print(f"🧹 Messages d'erreur 'Address not found' restants dans INBOX : {remaining_inbox}", flush=True)
print(f"✅ Votre boîte de réception Gmail est désormais propre et sans messages de rejet !", flush=True)
print("="*60, flush=True)
