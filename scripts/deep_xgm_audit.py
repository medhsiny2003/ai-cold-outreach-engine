import imaplib
import email
import re
import sys
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

sys.stdout.reconfigure(encoding='utf-8')

print("="*80)
print("   🔍 MOTEUR D'AUDIT HAUTE PRÉCISION (X-GM-RAW & GOOGLE SEARCH ENGINE)")
print("="*80)

mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
mail.login("mohammedhsiny2@gmail.com", "qawi kviz qjqu hwgb")

# Search in [Gmail]/All Mail, [Gmail]/Trash, [Gmail]/Spam using pure ASCII Google syntax
raw_query = 'from:mailer-daemon OR from:postmaster OR subject:"Address not found" OR subject:"Delivery Status Notification" OR subject:"Undeliverable" OR subject:"Non remis" OR subject:"Echec" OR "550 5.1.1" OR "User unknown" OR "Mail delivery failed"'

total_bounces_found = {}

for fld in ['"[Gmail]/All Mail"', '"[Gmail]/Trash"', '"[Gmail]/Spam"', 'INBOX']:
    try:
        st, _ = mail.select(fld, readonly=True)
        if st != "OK":
            continue
        print(f"\n[*] Scan approfondi du dossier : {fld}...")
        st, data = mail.search(None, 'X-GM-RAW', f'"{raw_query}"')
        if st == "OK" and data[0]:
            msg_ids = data[0].split()
            print(f"    👉 {len(msg_ids)} messages de rejet détectés !")
            
            for idx, msg_id in enumerate(msg_ids, 1):
                st_fetch, msg_data = mail.fetch(msg_id, "(RFC822)")
                if st_fetch != "OK" or not msg_data[0]:
                    continue
                
                raw_bytes = msg_data[0][1]
                msg = email.message_from_bytes(raw_bytes)
                
                failed_addr = None
                diag_info = ""
                
                # 1. Check RFC 3464 delivery-status
                for part in msg.walk():
                    if part.get_content_type() == "message/delivery-status":
                        payload = str(part.get_payload())
                        rm = re.search(r"(?:Final-Recipient|Original-Recipient):\s*(?:rfc822;)?\s*([^\s;]+)", payload, re.IGNORECASE)
                        dm = re.search(r"Diagnostic-Code:\s*(.*)", payload, re.IGNORECASE)
                        if rm:
                            failed_addr = rm.group(1).strip().strip("<>")
                        if dm:
                            diag_info = dm.group(1).strip()
                            
                    # Check attached original message headers
                    if part.get_content_type() == "message/rfc822":
                        try:
                            orig_msg = email.message_from_bytes(part.get_payload(decode=True) or b"")
                            orig_to = orig_msg.get("To") or ""
                            if orig_to:
                                ems = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', orig_to)
                                for em in ems:
                                    if em.lower() != "mohammedhsiny2@gmail.com":
                                        failed_addr = em.lower().strip()
                                        break
                        except Exception:
                            pass
                
                # 2. Check body text
                if not failed_addr:
                    body = ""
                    for part in msg.walk():
                        if part.get_content_type() in ["text/plain", "text/html"]:
                            try:
                                body += part.get_payload(decode=True).decode(errors="ignore") + "\n"
                            except Exception:
                                pass
                                
                    tm = re.search(r"(?:wasn\'t delivered to|Address not found|couldn\'t be delivered to|failed:|Delivery to the following recipient failed permanently:\s*|failed to deliver to:\s*|Undeliverable:\s*|Recipient address:\s*|L'adresse n'a pas été trouvée pour\s*)\s*([^\s<]+@[^\s>]+)", body, re.IGNORECASE)
                    if tm:
                        failed_addr = tm.group(1).strip().strip("<>").strip(".")
                    else:
                        all_found = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', body)
                        for em in all_found:
                            em_l = em.lower().strip()
                            if em_l != "mohammedhsiny2@gmail.com" and not any(x in em_l for x in ["google", "daemon", "postmaster", "smtp", "mailer", "bounce", "system", "exchange", "microsoft"]):
                                failed_addr = em_l
                                break
                                
                if failed_addr:
                    clean_addr = failed_addr.lower().strip().strip("<>").strip(".")
                    if clean_addr not in total_bounces_found:
                        total_bounces_found[clean_addr] = diag_info or "Address not found / Postmaster rejection"
    except Exception as ex:
        print(f"    [!] Erreur sur {fld}: {ex}")

mail.logout()

print("\n" + "="*80)
print(f"🏆 RÉSULTAT GLOBAL : {len(total_bounces_found)} ADRESSES REJETÉES UNIQUES DÉTECTÉES AU TOTAL !")
print("="*80)

for idx, (b_email, b_diag) in enumerate(sorted(total_bounces_found.items()), 1):
    print(f"  {idx:03d}. {b_email:<45} | {b_diag[:50]}")

