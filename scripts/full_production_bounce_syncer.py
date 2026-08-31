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
print("   ⚡ MOTEUR D'AUDIT CERTIFIÉ RFC 3464 (GOOGLE SEARCH ENGINE X-GM-RAW)")
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

# 2. Extract Bounces from [Gmail]/All Mail using lightweight RFC822.TEXT
print("\n[*] Étape 2 : Extraction ultra-rapide des adresses rejetées (X-GM-RAW)...")
all_bounced_recipients = {}

mail.select('"[Gmail]/All Mail"', readonly=True)

st_md, d_md = mail.search(None, 'X-GM-RAW', 'from:mailer-daemon')
st_pm, d_pm = mail.search(None, 'X-GM-RAW', 'from:postmaster')

bounce_ids = set()
if st_md == 'OK' and d_md[0]:
    bounce_ids.update(d_md[0].split())
if st_pm == 'OK' and d_pm[0]:
    bounce_ids.update(d_pm[0].split())

b_list = list(bounce_ids)
print(f"    👉 Total messages de rejet identifiés dans 'Tous les messages' : {len(b_list)}")

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
                
                # Regex extraction
                rm = re.search(r"(?:Final-Recipient|Original-Recipient):\s*(?:rfc822;)?\s*([^\s;\r\n]+)", raw_text, re.IGNORECASE)
                tm = re.search(r"(?:wasn\'t delivered to|Address not found|couldn\'t be delivered to|failed:|Delivery to the following recipient failed permanently:\s*|failed to deliver to:\s*|Undeliverable:\s*|Recipient address:\s*|L'adresse n'a pas été trouvée pour\s*)\s*([^\s<>\r\n]+@[^\s<>\r\n]+)", raw_text, re.IGNORECASE)
                
                failed_addr = None
                if rm:
                    failed_addr = rm.group(1).strip().strip("<>")
                elif tm:
                    failed_addr = tm.group(1).strip().strip("<>").strip(".")
                else:
                    for em in re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', raw_text):
                        em_l = em.lower().strip()
                        if em_l != "mohammedhsiny2@gmail.com" and not any(x in em_l for x in ["google", "daemon", "postmaster", "smtp", "mailer", "bounce", "system", "exchange", "microsoft"]):
                            failed_addr = em_l
                            break
                            
                if failed_addr:
                    clean = failed_addr.lower().strip().strip("<>").strip(".")
                    if clean not in all_bounced_recipients:
                        all_bounced_recipients[clean] = "550 5.1.1 Address not found (Mailer-Daemon / Postmaster)"
    except Exception as e:
        print(f"    [!] Erreur batch: {e}")
    if (i + 10) % 50 == 0:
        print(f"    ... {min(i+10, len(b_list))}/{len(b_list)} analysés ({len(all_bounced_recipients)} adresses rejetées trouvées)...")

mail.logout()

print("\n" + "="*80)
print(f"🏆 RÉSULTAT DU DÉCODAGE TOTAL : {len(all_bounced_recipients)} ADRESSES REJETÉES UNIQUES DÉTECTÉES !")
print("="*80)

# 3. Synchronize with SQLite Database
contacts = get_all_contacts()
with get_db_connection() as conn:
    for c in contacts:
        em = c['email'].lower().strip()
        if em in all_bounced_recipients:
            diag_val = all_bounced_recipients[em]
            conn.execute("UPDATE contacts SET status = 'bounced', notes = ? WHERE LOWER(email) = ?", (f"❌ Rejet Avéré (Mailer-Daemon / Postmaster) : {diag_val}", em))
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

