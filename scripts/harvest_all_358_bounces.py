import imaplib
import email
import re
import sys
import time
from pathlib import Path

# Add project root to sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from services.storage_service import init_db, get_db_connection, get_all_contacts

sys.stdout.reconfigure(encoding='utf-8')

print("="*80)
print("   🚀 SCAN GLOBAL INTÉGRAL DE TOUS LES REJETS GMAIL (358+ MESSAGES)")
print("="*80)

init_db()

mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
mail.login("mohammedhsiny2@gmail.com", "qawi kviz qjqu hwgb")
print("[OK] Connecté à Gmail IMAP.")

all_bounced_recipients = {}
scanned_folders = ['"[Gmail]/All Mail"', '"[Gmail]/Trash"', '"[Gmail]/Spam"', 'INBOX']

# 1. Fetch Sent Mail first to get exact list of what was ever sent
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

# 2. Deep Harvest of all Mailer-Daemon & Postmaster messages
print("\n[*] Étape 2 : Récupération & Décorticage de TOUS les messages de Rejet...")

all_bounce_msg_ids = set()

for fld in scanned_folders:
    try:
        st_sel, _ = mail.select(fld, readonly=True)
        if st_sel != "OK":
            continue
            
        for q in ['from:mailer-daemon', 'from:postmaster']:
            st_q, d_q = mail.search(None, 'X-GM-RAW', q)
            if st_q == "OK" and d_q[0]:
                for mid in d_q[0].split():
                    all_bounce_msg_ids.add((fld, mid))
    except Exception as ex:
        print(f"    [!] Erreur sélection {fld}: {ex}")

print(f"    👉 Total messages de rejet identifiés à analyser : {len(all_bounce_msg_ids)}")

processed = 0
for fld, mid in all_bounce_msg_ids:
    try:
        mail.select(fld, readonly=True)
        st_msg, msg_res = mail.fetch(mid, '(RFC822)')
        if st_msg != 'OK' or not msg_res[0]:
            continue
            
        raw_msg = msg_res[0][1]
        msg = email.message_from_bytes(raw_msg)
        
        failed_recipient = None
        diag = "550 5.1.1 Address not found (Mailer-Daemon / Postmaster)"
        
        # 1. RFC 3464 delivery-status
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
                    
            # Check embedded original RFC 822 message
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
                
        processed += 1
        if processed % 50 == 0:
            print(f"    ... {processed}/{len(all_bounce_msg_ids)} messages décortiqués ({len(all_bounced_recipients)} adresses uniques rejetées trouvées)...")
    except Exception as ex:
        pass

mail.logout()

print("\n" + "="*80)
print(f"🏆 RÉSULTAT DU DÉCORTICAGE : {len(all_bounced_recipients)} ADRESSES REJETÉES UNIQUES DÉTECTÉES !")
print("="*80)

# 3. Synchronize with SQLite Database
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

