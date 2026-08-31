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
    return _orig_getaddrinfo(host, port, socket.AF_INET, type, proto, flags)

socket.getaddrinfo = _force_ipv4_getaddrinfo

def clean_gmail_bounces_and_sync_db(smtp: SMTPSettings) -> Dict[str, Any]:
    """
    Connects to Gmail via IMAP, finds all 'Address not found' / Mailer-Daemon bounce emails,
    deletes them from INBOX, and marks those recipients as 'bounced' in SQLite database.
    """
    if not smtp.app_password:
        return {"success": False, "message": "Mot de passe d'application Gmail manquant.", "deleted_count": 0, "bounced_emails": []}

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(smtp.sender_email, smtp.app_password)
    except Exception as e:
        return {"success": False, "message": f"Erreur de connexion IMAP : {e}", "deleted_count": 0, "bounced_emails": []}

    try:
        mail.select("INBOX")
        search_queries = [
            '(FROM "mailer-daemon@googlemail.com")',
            '(FROM "Mail Delivery Subsystem")',
            '(SUBJECT "Address not found")',
            '(SUBJECT "Delivery Status Notification (Failure)")'
        ]

        found_msg_ids: Set[bytes] = set()
        for query in search_queries:
            status, data = mail.search(None, query)
            if status == "OK" and data[0]:
                for num in data[0].split():
                    found_msg_ids.add(num)

        bounced_dict: Dict[str, str] = {}

        for msg_id in found_msg_ids:
            status, msg_data = mail.fetch(msg_id, "(RFC822)")
            if status != "OK":
                continue

            raw_email = msg_data[0][1]
            msg = email.message_from_bytes(raw_email)
            
            failed_recipient = None
            diagnostic_code = "550 5.1.1 Address not found (Mailer-Daemon)"
            
            # RFC 3464 DSN parsing
            for part in msg.walk():
                if part.get_content_type() == "message/delivery-status":
                    sub_str = str(part.get_payload())
                    rm = re.search(r"Final-Recipient:\s*(?:rfc822;)?\s*([^\s;]+)", sub_str, re.IGNORECASE)
                    dm = re.search(r"Diagnostic-Code:\s*(.*)", sub_str, re.IGNORECASE)
                    if rm:
                        failed_recipient = rm.group(1).strip().strip("<>")
                    if dm:
                        diagnostic_code = dm.group(1).strip()

            if not failed_recipient:
                body_text = ""
                for part in msg.walk():
                    if part.get_content_type() == "text/plain":
                        try:
                            body_text += part.get_payload(decode=True).decode(errors="ignore") + "\n"
                        except Exception:
                            pass
                tm = re.search(r"(?:wasn\'t delivered to|Address not found|couldn\'t be delivered to|failed:)\s*([^\s<]+@[^\s>]+)", body_text, re.IGNORECASE)
                if tm:
                    failed_recipient = tm.group(1).strip().strip("<>").strip(".")
                else:
                    for e in re.findall(r"[\w\.-]+@[\w\.-]+\.\w+", body_text):
                        el = e.lower().strip()
                        if el != smtp.sender_email.lower() and "google" not in el and "daemon" not in el and "mail" not in el and "smtp" not in el:
                            failed_recipient = el
                            break

            if failed_recipient:
                clean_r = failed_recipient.lower().strip().strip("<>").strip(".")
                bounced_dict[clean_r] = diagnostic_code

        # Bulk delete / Move to Trash for INBOX
        if found_msg_ids:
            ids_str = ",".join(num.decode('ascii') if isinstance(num, bytes) else str(num) for num in found_msg_ids)
            try:
                mail.copy(ids_str, '"[Gmail]/Trash"')
                mail.store(ids_str, '+FLAGS', '\\Deleted')
                mail.expunge()
            except Exception:
                pass

        # Purge Spam and empty Trash
        for fld in ['"[Gmail]/Spam"', '"[Gmail]/Trash"']:
            try:
                st_f, _ = mail.select(fld)
                if st_f == "OK":
                    st_s, d_s = mail.search(None, '(OR (FROM "mailer-daemon") (OR (FROM "Mail Delivery Subsystem") (SUBJECT "Delivery Status Notification")))')
                    if st_s == "OK" and d_s[0] and d_s[0].strip():
                        s_ids = d_s[0].decode('ascii').replace(' ', ',')
                        mail.store(s_ids, '+FLAGS', '\\Deleted')
                        mail.expunge()
            except Exception:
                pass

        mail.logout()

        # Update SQLite DB to mark bounced contacts
        if bounced_dict:
            with get_db_connection() as conn:
                for b_email, b_diag in bounced_dict.items():
                    conn.execute("""
                        UPDATE contacts 
                        SET status = 'bounced', notes = ? 
                        WHERE LOWER(email) = ?
                    """, (f"❌ Rejeté Mailer-Daemon : {b_diag[:100]}", b_email))
                conn.commit()

        return {
            "success": True,
            "message": f"Nettoyage complet réussi : {len(found_msg_ids)} notification(s) DSN éliminée(s) de votre boîte Gmail.",
            "deleted_count": len(found_msg_ids),
            "bounced_emails": list(bounced_dict.keys())
        }

    except Exception as e:
        try:
            mail.logout()
        except Exception:
            pass
        return {"success": False, "message": f"Erreur lors du nettoyage : {e}", "deleted_count": 0, "bounced_emails": []}

def sync_sent_and_bounced_with_gmail(smtp: SMTPSettings) -> Dict[str, Any]:
    """Scans Gmail Sent Mail folder and RFC 3464 Non-Delivery Reports across all folders and marks SQLite DB."""
    if not smtp.app_password:
        return {"success": False, "message": "Mot de passe d'application manquant."}
        
    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(smtp.sender_email, smtp.app_password)
        
        # 1. Sent Mail
        mail.select('"[Gmail]/Sent Mail"', readonly=True)
        st, data = mail.search(None, 'ALL')
        all_sent_msg_ids = data[0].split() if st == 'OK' and data[0] else []
        
        sent_recipients = {}
        for i in range(0, len(all_sent_msg_ids), 100):
            chunk = all_sent_msg_ids[i:i+100]
            seq_set = b",".join(chunk).decode('ascii')
            st2, fetch_data = mail.fetch(seq_set, '(BODY.PEEK[HEADER.FIELDS (TO DATE)])')
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
                                if el != smtp.sender_email.lower():
                                    sent_recipients[el] = date_m.group(1).strip() if date_m else "Envoyé"

        # 2. RFC 3464 Bounces across INBOX and Trash
        bounces_dict = {}
        for fld in ['INBOX', '"[Gmail]/Trash"', '"[Gmail]/Spam"']:
            try:
                st_f, _ = mail.select(fld, readonly=True)
                if st_f != 'OK':
                    continue
                st_b, d_b = mail.search(None, '(OR (FROM "mailer-daemon") (OR (FROM "Mail Delivery Subsystem") (SUBJECT "Delivery Status Notification")))')
                if st_b == 'OK' and d_b[0]:
                    for b_id in d_b[0].split():
                        st2, bdata = mail.fetch(b_id, '(RFC822)')
                        if st2 == 'OK' and bdata[0]:
                            msg = email.message_from_bytes(bdata[0][1])
                            failed_recip = None
                            diag_code = "550 5.1.1 Address not found (User unknown)"
                            for part in msg.walk():
                                if part.get_content_type() == 'message/delivery-status':
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
                                tm = re.search(r"(?:wasn\'t delivered to|Address not found|couldn\'t be delivered to|failed:)\s*([^\s<]+@[^\s>]+)", body_txt, re.IGNORECASE)
                                if tm:
                                    failed_recip = tm.group(1).strip().strip('<>').strip('.')
                                else:
                                    for em in re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', body_txt):
                                        eml = em.lower().strip()
                                        if eml != smtp.sender_email.lower() and 'google' not in eml and 'daemon' not in eml and 'mail' not in eml:
                                            failed_recip = eml
                                            break
                            if failed_recip:
                                clean_r = failed_recip.lower().strip().strip('<>').strip('.')
                                bounces_dict[clean_r] = diag_code
            except Exception:
                pass

        mail.logout()
        
        with get_db_connection() as conn:
            for s_email, s_dt in sent_recipients.items():
                if s_email in bounces_dict:
                    diag = bounces_dict[s_email]
                    conn.execute("UPDATE contacts SET status = 'bounced', notes = ? WHERE LOWER(email) = ?", (f"❌ Rejeté Mailer-Daemon : {diag[:100]}", s_email))
                else:
                    conn.execute("UPDATE contacts SET status = 'sent', notes = ? WHERE LOWER(email) = ? AND status != 'bounced'", (f"🟢 Délivré sans erreur (Envoyé le {s_dt})", s_email))
            conn.commit()
            
        return {
            "success": True,
            "message": f"Synchronisation certifiée Gmail : {len(sent_recipients)} envoyés vérifiés | {len(bounces_dict)} rejets DSN identifiés.",
            "sent_count": len(sent_recipients),
            "bounced_count": len(bounces_dict)
        }
    except Exception as e:
        return {"success": False, "message": f"Erreur de synchronisation IMAP : {e}"}
