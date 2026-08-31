import imaplib
import email
from email.header import decode_header
import re
import sys
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import SMTPSettings
from services.storage_service import load_smtp_settings, get_db_connection

def clean_bounced_emails():
    smtp = load_smtp_settings()
    if not smtp.app_password:
        print("[!] Mot de passe d'application Gmail manquant.")
        return

    print(f"[*] Connexion IMAP à {smtp.sender_email}...")
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(smtp.sender_email, smtp.app_password)
        print("[OK] Connecté à Gmail avec succès !")
    except Exception as e:
        print(f"[!] Erreur de connexion IMAP : {e}")
        return

    # Select INBOX
    mail.select("INBOX")

    # Search for Mail Delivery Subsystem / Address not found / Delivery Status Notification
    search_queries = [
        '(FROM "mailer-daemon@googlemail.com")',
        '(FROM "Mail Delivery Subsystem")',
        '(SUBJECT "Address not found")',
        '(SUBJECT "Delivery Status Notification (Failure)")'
    ]

    found_msg_ids = set()
    for query in search_queries:
        status, data = mail.search(None, query)
        if status == "OK" and data[0]:
            for num in data[0].split():
                found_msg_ids.add(num)

    print(f"[*] Trouvé {len(found_msg_ids)} message(s) d'erreur / bounce dans la boîte de réception.")

    bounced_emails = set()

    for msg_id in found_msg_ids:
        status, msg_data = mail.fetch(msg_id, "(RFC822)")
        if status != "OK":
            continue

        raw_email = msg_data[0][1]
        msg = email.message_from_bytes(raw_email)
        
        # Try to extract the failed recipient email from message text
        body_text = ""
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                if content_type == "text/plain":
                    try:
                        body_text += part.get_payload(decode=True).decode(errors="ignore") + "\n"
                    except Exception:
                        pass
        else:
            try:
                body_text = msg.get_payload(decode=True).decode(errors="ignore")
            except Exception:
                pass

        # Regex search for bounced email addresses
        emails_found = re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", body_text)
        for e in emails_found:
            e_lower = e.lower().strip()
            if e_lower != smtp.sender_email.lower() and "google" not in e_lower and "daemon" not in e_lower and "mail" not in e_lower:
                bounced_emails.add(e_lower)

        # Move message to Trash (Gmail Trash folder is '[Gmail]/Trash' or '[Gmail]/Corbeille')
        # In Gmail IMAP, store +FLAGS (\Deleted) or move to Trash
        mail.store(msg_id, "+FLAGS", "\\Deleted")

    # Expunge deleted messages
    mail.expunge()

    # Also check [Gmail]/Spam or other folders if needed
    mail.close()
    mail.logout()

    print(f"[OK] {len(found_msg_ids)} message(s) d'erreur supprimé(s) de votre boîte de réception !")
    
    if bounced_emails:
        print(f"[*] Adresses email identifiées comme invalides/introuvables ({len(bounced_emails)}) :")
        for b in sorted(bounced_emails):
            print(f"   - {b}")

        # Update status in SQLite to 'bounced' / 'failed'
        with get_db_connection() as conn:
            for b in bounced_emails:
                conn.execute("UPDATE contacts SET status = 'bounced', notes = 'Adresse introuvable / rejetée' WHERE email = ?", (b,))
            conn.commit()
        print("[OK] Base de données mise à jour : ces contacts sont désormais marqués 'bounced' pour ne plus jamais leur réécrire.")

if __name__ == "__main__":
    clean_bounced_emails()
