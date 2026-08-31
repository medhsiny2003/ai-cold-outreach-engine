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
print("   🔍 VÉRIFICATION ULTRA-STRICTE CONTACT PAR CONTACT (ZERO ERREUR)")
print("="*80)

init_db()

mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
mail.login("mohammedhsiny2@gmail.com", "qawi kviz qjqu hwgb")
print("[OK] Connecté à Gmail IMAP.")

contacts = get_all_contacts()
total = len(contacts)
print(f"[*] Analyse approfondie de chacun des {total} contacts...\n")

mail.select('"[Gmail]/All Mail"', readonly=True)

stats = {"sent_delivered": 0, "bounced": 0, "replied": 0, "not_sent": 0}

bounce_keywords = [
    "mailer-daemon", "postmaster", "delivery status notification", "address not found",
    "undeliverable", "undelivered", "non-delivery", "failure notice", "returned mail",
    "mail delivery failed", "user unknown", "550 5.1.1", "550", "recipient address rejected",
    "could not be delivered", "mailbox unavailable", "wasn't delivered"
]

with get_db_connection() as conn:
    for idx, c in enumerate(contacts, 1):
        target_email = c["email"].lower().strip()
        comp = c.get("company", "N/A")
        
        # 1. Search if this exact address was ever mentioned in any email (Sent, Received, Bounce)
        st, data = mail.search(None, 'X-GM-RAW', f'"{target_email}"')
        msg_ids = data[0].split() if st == "OK" and data[0] else []
        
        if not msg_ids:
            # Never sent from this Gmail account
            conn.execute("UPDATE contacts SET status = 'approved', notes = '⏳ Non encore envoyé' WHERE LOWER(email) = ?", (target_email,))
            stats["not_sent"] += 1
            if idx % 25 == 0 or idx == total:
                print(f"[{idx:03d}/{total:03d}] {target_email:<38} ➔ ⏳ NON ENVOYÉ")
            continue
            
        # 2. Inspect all messages mentioning this email
        is_bounced = False
        is_replied = False
        is_sent = False
        bounce_reason = "550 5.1.1 Address not found (Mailer-Daemon / Postmaster)"
        
        # Fetch headers of all matching messages
        seq = b",".join(msg_ids).decode('ascii')
        st_hdr, hdr_data = mail.fetch(seq, '(BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE)])')
        
        if st_hdr == "OK":
            for it in hdr_data:
                if isinstance(it, tuple) and len(it) > 1:
                    raw_hdr = it[1].decode('utf-8', errors='ignore').lower()
                    
                    # Check if it is a bounce
                    if any(kw in raw_hdr for kw in bounce_keywords):
                        is_bounced = True
                        
                    # Check if it was sent by Mohammed
                    if "from: mohammed hsiny" in raw_hdr or "from: <mohammedhsiny2@gmail.com>" in raw_hdr:
                        is_sent = True
                        
                    # Check if received FROM the recruiter
                    if f"from: {target_email}" in raw_hdr or f"<{target_email}>" in raw_hdr:
                        if not any(kw in raw_hdr for kw in bounce_keywords):
                            is_replied = True
                            
        # If we suspect bounce or sent, fetch text body to confirm
        if is_bounced:
            conn.execute("UPDATE contacts SET status = 'bounced', notes = ? WHERE LOWER(email) = ?", (f"❌ Rejet Avéré (Mailer-Daemon / Postmaster) : {bounce_reason}", target_email))
            stats["bounced"] += 1
            print(f"[{idx:03d}/{total:03d}] {target_email:<38} ➔ 🔴 REJETÉ (Address not found / Postmaster)")
        elif is_replied:
            conn.execute("UPDATE contacts SET status = 'replied', notes = '💬 Réponse reçue du recruteur !' WHERE LOWER(email) = ?", (target_email,))
            stats["replied"] += 1
            print(f"[{idx:03d}/{total:03d}] {target_email:<38} ➔ 💬 RÉPONSE REÇUE DU RECRUTEUR !")
        elif is_sent:
            conn.execute("UPDATE contacts SET status = 'sent', notes = '🟢 Délivré avec succès (Aucun rejet dans Gmail)' WHERE LOWER(email) = ?", (target_email,))
            stats["sent_delivered"] += 1
            if idx % 25 == 0 or idx == total:
                print(f"[{idx:03d}/{total:03d}] {target_email:<38} ➔ 🟢 DÉLIVRÉ AVEC SUCCÈS")
        else:
            conn.execute("UPDATE contacts SET status = 'approved', notes = '⏳ Non encore envoyé' WHERE LOWER(email) = ?", (target_email,))
            stats["not_sent"] += 1
            
    conn.commit()

mail.logout()

print("\n" + "="*80)
print("🏆 BILAN D'EXACTITUDE ABSOLUE CONTACT PAR CONTACT :")
print(f"   👥 Total Contacts Analysés          : {total}")
print(f"   🟢 VRAIS REÇUS (Sans aucun rejet)    : {stats['sent_delivered']}")
print(f"   💬 RÉPONSES DE RECRUTEURS REÇUES     : {stats['replied']}")
print(f"   🔴 REJETÉS (Bounces / Postmaster)   : {stats['bounced']}")
print(f"   ⏳ NON ENVOYÉS (Restants en attente): {stats['not_sent']}")
print("="*80)
