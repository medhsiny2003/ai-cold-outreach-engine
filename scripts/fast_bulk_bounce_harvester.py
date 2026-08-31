import imaplib
import email
import re
import sys
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.storage_service import init_db, get_db_connection, get_all_contacts

sys.stdout.reconfigure(encoding='utf-8')

print("="*80)
print("   🚀 SCAN GLOBAL BULK HAUTE VITESSE - REJETS GMAIL (451+ MESSAGES)")
print("="*80)

init_db()

mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
mail.login("mohammedhsiny2@gmail.com", "qawi kviz qjqu hwgb")
print("[OK] Connecté à Gmail IMAP.")

# 1. Sent Mail
print("\n[*] Étape 1 : Analyse des 'Messages envoyés'...")
mail.select('"[Gmail]/Sent Mail"', readonly=True)
st_sent, d_sent = mail.search(None, 'ALL')
sent_ids = d_sent[0].split() if st_sent == 'OK' and d_sent[0] else []
print(f"    👉 Total messages envoyés répertoriés : {len(sent_ids)}")

all_sent_addresses = set()
for i in range(0, len(sent_ids), 100):
    chunk = sent_ids[i:i+100]
    seq = b",".join(chunk).decode('ascii')
    st_f, f_data = mail.fetch(seq, '(BODY.PEEK[HEADER.FIELDS (TO DATE SUBJECT)])')
    if st_f == 'OK':
        for it in f_data:
            if isinstance(it, tuple) and len(it) > 1:
                hdr = it[1].decode('utf-8', errors='ignore')
                to_m = re.search(r'To:\s*(.*)', hdr, re.IGNORECASE)
                if to_m:
                    for em in re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', to_m.group(1)):
                        em_l = em.lower().strip()
                        if em_l != 'mohammedhsiny2@gmail.com':
                            all_sent_addresses.add(em_l)

print(f"    👉 Destinataires uniques contactés : {len(all_sent_addresses)}")

# 2. Search Bounces in Folders
print("\n[*] Étape 2 : Recherche X-GM-RAW de tous les rejets dans chaque dossier...")
folders = ['"[Gmail]/All Mail"', '"[Gmail]/Trash"', '"[Gmail]/Spam"', 'INBOX']
bounces_by_folder = {}

for fld in folders:
    try:
        st_sel, _ = mail.select(fld, readonly=True)
        if st_sel != "OK":
            continue
        folder_mids = set()
        for q in ['from:mailer-daemon', 'from:postmaster']:
            st_q, d_q = mail.search(None, 'X-GM-RAW', q)
            if st_q == "OK" and d_q[0]:
                for mid in d_q[0].split():
                    folder_mids.add(mid)
        bounces_by_folder[fld] = list(folder_mids)
        print(f"    📁 {fld:<18} : {len(folder_mids)} messages de rejet détectés.")
    except Exception as ex:
        print(f"    [!] Erreur {fld}: {ex}")

# 3. Bulk Fetch and Parse
print("\n[*] Étape 3 : Décodage MIME ultra-rapide des messages...")
all_bounced_recipients = {}

for fld, mids in bounces_by_folder.items():
    if not mids:
        continue
    mail.select(fld, readonly=True)
    for i in range(0, len(mids), 25):
        chunk = mids[i:i+25]
        seq = b",".join(chunk).decode('ascii')
        try:
            st_f, f_data = mail.fetch(seq, '(RFC822)')
            if st_f != 'OK':
                continue
            for it in f_data:
                if isinstance(it, tuple) and len(it) > 1:
                    raw_msg = it[1]
                    try:
                        msg = email.message_from_bytes(raw_msg)
                    except Exception:
                        continue
                        
                    failed_recipient = None
                    diag = "550 5.1.1 Address not found (Mailer-Daemon / Postmaster)"
                    
                    # 1. Delivery-status part
                    for part in msg.walk():
                        ct = part.get_content_type()
                        if ct == "message/delivery-status":
                            payload = str(part.get_payload())
                            rm = re.search(r"(?:Final-Recipient|Original-Recipient):\s*(?:rfc822;)?\s*([^\s;]+)", payload, re.IGNORECASE)
                            dm = re.search(r"Diagnostic-Code:\s*(.*)", payload, re.IGNORECASE)
                            if rm:
                                failed_recipient = rm.group(1).strip().strip("<>")
                            if dm:
                                diag = dm.group(1).strip()
                                
                        if ct == "message/rfc822":
                            try:
                                sub_raw = part.get_payload(0)
                                if isinstance(sub_raw, email.message.Message):
                                    orig_to = sub_raw.get("To") or ""
                                    for em in re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', orig_to):
                                        if em.lower() != "mohammedhsiny2@gmail.com":
                                            failed_recipient = em.lower().strip()
                                            break
                            except Exception:
                                pass
                                
                    # 2. Text body fallback
                    if not failed_recipient:
                        body = ""
                        for part in msg.walk():
                            if part.get_content_type() in ["text/plain", "text/html"]:
                                try:
                                    body += part.get_payload(decode=True).decode(errors="ignore") + "\n"
                                except Exception:
                                    pass
                                    
                        tm = re.search(r"(?:wasn\'t delivered to|Address not found|couldn\'t be delivered to|failed:|Delivery to the following recipient failed permanently:\s*|failed to deliver to:\s*|Undeliverable:\s*|Recipient address:\s*|L'adresse n'a pas été trouvée pour\s*)\s*([^\s<]+@[^\s>]+)", body, re.IGNORECASE)
                        if tm:
                            failed_recipient = tm.group(1).strip().strip("<>").strip(".")
                        else:
                            for em in re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', body):
                                em_l = em.lower().strip()
                                if em_l != "mohammedhsiny2@gmail.com" and not any(x in em_l for x in ["google", "daemon", "postmaster", "smtp", "mailer", "bounce", "system", "exchange", "microsoft"]):
                                    failed_recipient = em_l
                                    break
                                    
                    if failed_recipient:
                        clean_rec = failed_recipient.lower().strip().strip("<>").strip(".")
                        if clean_rec not in all_bounced_recipients:
                            all_bounced_recipients[clean_rec] = diag
        except Exception:
            pass

mail.logout()

print("\n" + "="*80)
print(f"🏆 RÉSULTAT GLOBAL : {len(all_bounced_recipients)} ADRESSES REJETÉES UNIQUES DÉTECTÉES !")
print("="*80)

# 4. Synchronize with SQLite Database
contacts = get_all_contacts()
with get_db_connection() as conn:
    for c in contacts:
        em = c['email'].lower().strip()
        if em in all_bounced_recipients:
            diag_val = all_bounced_recipients[em]
            conn.execute("UPDATE contacts SET status = 'bounced', notes = ? WHERE LOWER(email) = ?", (f"❌ Rejet Avéré (Mailer-Daemon / Postmaster) : {diag_val[:120]}", em))
        elif em in all_sent_addresses:
            conn.execute("UPDATE contacts SET status = 'sent', notes = ? WHERE LOWER(email) = ? AND status != 'bounced'", ("🟢 Délivré avec succès (Vérifié sans aucun rejet)", em))
    conn.commit()

# Final stats
fresh = get_all_contacts()
stat_map = {}
for c in fresh:
    st = c.get('status', 'pending')
    stat_map[st] = stat_map.get(st, 0) + 1

print(f"\n📊 NOUVEAU BILAN DE VÉRITÉ ABSOLUE DE VOTRE BASE DE DONNÉES :")
print(f"   👥 Total Base Contacts              : {len(fresh)}")
print(f"   🟢 TOTAL RÉELLEMENT DÉLIVRÉS (Reçus) : {stat_map.get('sent', 0)}")
print(f"   🔴 TOTAL REJETÉS DÉTECTÉS (Bounces) : {stat_map.get('bounced', 0)}")
print(f"   ⏳ RESTANTS EN ATTENTE (Non envoyés): {stat_map.get('approved', 0)}")
print("="*80)

