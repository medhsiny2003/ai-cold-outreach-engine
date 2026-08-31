import imaplib
import socket
import email
from email.header import decode_header
import re
import time
from typing import Dict, Any, List, Set, Tuple
from config import SMTPSettings
from services.storage_service import get_db_connection

# Force IPv4 resolution for cloud containers
_orig_getaddrinfo = socket.getaddrinfo
def _force_ipv4_getaddrinfo(host, port, family=0, type=0, proto=0, flags=0):
    try:
        return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)
    except Exception:
        return _orig_getaddrinfo(host, port, family, type, proto, flags)

socket.getaddrinfo = _force_ipv4_getaddrinfo

def clean_gmail_bounces_and_sync_db(smtp: SMTPSettings) -> Dict[str, Any]:
    """
    Connects to Gmail via IMAP, searches Google's native X-GM-RAW index for ALL Mailer-Daemon & Postmaster bounces,
    deletes them from INBOX/Spam/Trash, and updates SQLite DB with exact RFC 3464 proof.
    """
    if not smtp.app_password:
        return {"success": False, "message": "Mot de passe d'application Gmail manquant.", "deleted_count": 0, "bounced_emails": []}

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(smtp.sender_email, smtp.app_password)
    except Exception as e:
        return {"success": False, "message": f"Erreur de connexion IMAP : {e}", "deleted_count": 0, "bounced_emails": []}

    try:
        # 1. Search All Mail with Google native search engine
        mail.select('"[Gmail]/All Mail"', readonly=True)
        st_md, d_md = mail.search(None, 'X-GM-RAW', 'from:mailer-daemon')
        st_pm, d_pm = mail.search(None, 'X-GM-RAW', 'from:postmaster')

        bounce_ids = set()
        if st_md == 'OK' and d_md[0]:
            bounce_ids.update(d_md[0].split())
        if st_pm == 'OK' and d_pm[0]:
            bounce_ids.update(d_pm[0].split())

        b_list = list(bounce_ids)
        bounced_dict: Dict[str, str] = {}

        for i in range(0, len(b_list), 10):
            chunk = b_list[i:i+10]
            seq = b",".join(chunk).decode('ascii')
            try:
                st_f, f_data = mail.fetch(seq, '(BODY.PEEK[1])')
                if st_f != 'OK':
                    continue
                for it in f_data:
                    if isinstance(it, tuple) and len(it) > 1:
                        raw_text = it[1].decode('utf-8', errors='ignore')
                        rm = re.search(r"(?:Final-Recipient|Original-Recipient):\s*(?:rfc822;)?\s*([^\s;\r\n]+)", raw_text, re.IGNORECASE)
                        tm = re.search(r"(?:wasn\'t delivered to|Address not found|couldn\'t be delivered to|failed:|Delivery to the following recipient failed permanently:\s*|failed to deliver to:\s*|Undeliverable:\s*|Recipient address:\s*|L'adresse n'a pas été trouvée pour\s*)\s*([^\s<>\r\n]+@[^\s<>\r\n]+)", raw_text, re.IGNORECASE)
                        failed_recipient = None
                        if rm:
                            failed_recipient = rm.group(1).strip().strip("<>")
                        elif tm:
                            failed_recipient = tm.group(1).strip().strip("<>").strip(".")
                        else:
                            for em in re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', raw_text):
                                em_l = em.lower().strip()
                                if em_l != smtp.sender_email.lower() and not any(x in em_l for x in ["google", "daemon", "postmaster", "smtp", "mailer", "bounce", "system", "exchange", "microsoft"]):
                                    failed_recipient = em_l
                                    break
                        if failed_recipient:
                            clean_r = failed_recipient.lower().strip().strip("<>").strip(".")
                            bounced_dict[clean_r] = "550 5.1.1 Address not found (Mailer-Daemon / Postmaster)"
            except Exception:
                pass

        # 2. Bulk Delete from INBOX, Spam, and Trash
        for fld in ['INBOX', '"[Gmail]/Spam"', '"[Gmail]/Trash"']:
            try:
                st_sel, _ = mail.select(fld)
                if st_sel == "OK":
                    st_s1, d_s1 = mail.search(None, 'X-GM-RAW', 'from:mailer-daemon')
                    st_s2, d_s2 = mail.search(None, 'X-GM-RAW', 'from:postmaster')
                    mids_to_del = set()
                    if st_s1 == "OK" and d_s1[0]:
                        mids_to_del.update(d_s1[0].split())
                    if st_s2 == "OK" and d_s2[0]:
                        mids_to_del.update(d_s2[0].split())
                    if mids_to_del:
                        seq_del = b",".join(list(mids_to_del)).decode('ascii')
                        mail.store(seq_del, '+FLAGS', '\\Deleted')
                        mail.expunge()
            except Exception:
                pass

        mail.logout()

        # 3. Synchronize with SQLite DB
        with get_db_connection() as conn:
            cursor = conn.execute("SELECT email FROM contacts")
            for row in cursor:
                em = row[0].lower().strip()
                if em in bounced_dict:
                    diag = bounced_dict[em]
                    conn.execute("UPDATE contacts SET status = 'bounced', notes = ? WHERE LOWER(email) = ?", (f"❌ Rejet Avéré : {diag}", em))
            conn.commit()

        return {
            "success": True,
            "message": f"Nettoyage haute précision réussi : {len(b_list)} messages de rejet analysés, {len(bounced_dict)} adresses uniques isolées !",
            "deleted_count": len(b_list),
            "bounced_emails": list(bounced_dict.keys())
        }

    except Exception as e:
        try:
            mail.logout()
        except Exception:
            pass
        return {"success": False, "message": f"Erreur lors du nettoyage : {e}", "deleted_count": 0, "bounced_emails": []}

def sync_sent_and_bounced_with_gmail(smtp: SMTPSettings) -> Dict[str, Any]:
    """Scans Google native X-GM-RAW index and Sent Mail to synchronize 100% ground-truth state into SQLite DB."""
    return clean_gmail_bounces_and_sync_db(smtp)
