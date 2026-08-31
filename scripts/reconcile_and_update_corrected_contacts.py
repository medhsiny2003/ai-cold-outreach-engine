import sys
import pandas as pd
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from services.storage_service import get_all_contacts, get_db_connection, save_or_update_contact

sys.stdout.reconfigure(encoding='utf-8')

print("[*] ANALYSE DES CORRECTIONS DU FOURNISSEUR & MISES À JOUR SÉCURISÉES")
df = pd.read_excel("EMAILS_CORRIGES_ET_CERTIFIES_STAGE.xlsx")

# Map existing DB contacts by old_email and by (name_lower, company_lower)
db_contacts = get_all_contacts()
db_by_email = {c.get('email', '').lower().strip(): c for c in db_contacts}
db_by_name_comp = {}
for c in db_contacts:
    n = " ".join(c.get('name', '').lower().split())
    comp = c.get('company', '').lower().strip()
    db_by_name_comp[(n, comp)] = c

print(f"👥 Base SQLite actuelle : {len(db_contacts)} contacts")

sent_preserved = 0
bounced_updated = 0
not_found_in_db = 0

corrections_list = []

with get_db_connection() as conn:
    for idx, row in df.iterrows():
        comp = str(row.iloc[0]).strip()
        domain = str(row.iloc[1]).strip()
        first_name = str(row.iloc[2]).strip()
        last_name = str(row.iloc[3]).strip()
        full_name = f"{first_name} {last_name}".strip()
        job = str(row.iloc[4]).strip() if pd.notnull(row.iloc[4]) else ""
        new_email = str(row.iloc[6]).strip().lower()
        old_email = str(row.iloc[12]).strip().lower()
        status_prev = str(row.iloc[13]).strip()
        
        # Match with DB
        db_match = db_by_email.get(old_email) or db_by_name_comp.get((" ".join(full_name.lower().split()), comp.lower()))
        
        if db_match:
            current_status = db_match.get('status')
            
            # RULE 1: If ALREADY DELIVERED (sent) -> DO NOT TOUCH (0 doublon)
            if current_status == 'sent':
                sent_preserved += 1
                continue
                
            # RULE 2: If BOUNCED -> Update email to NEW corrected email and reset to 'approved'
            elif current_status == 'bounced' or "Bounced" in status_prev or "Rejeté" in status_prev:
                old_e_db = db_match.get('email')
                contact_id = db_match.get('id')
                
                # Update SQLite record
                conn.execute("""
                    UPDATE contacts 
                    SET email = ?, 
                        status = 'approved', 
                        notes = ?
                    WHERE id = ?
                """, (new_email, f"🔄 Email corrigé par le fournisseur (Ancien rejeté: {old_e_db})", contact_id))
                
                bounced_updated += 1
                corrections_list.append({
                    "Entreprise": comp,
                    "Nom": full_name,
                    "Ancien Email (Rejeté)": old_e_db,
                    "Nouvel Email Corrigé": new_email
                })
        else:
            not_found_in_db += 1

    conn.commit()

print("\n" + "="*80)
print("             BILAN DE LA SYNCHRONISATION DES NOUVELLES DONNÉES")
print("="*80)
print(f"🔒 CONTACTS DÉJÀ DÉLIVRÉS PROTÉGÉS (Zéro ré-envoi / Zéro doublon) : {sent_preserved}")
print(f"🔄 CONTACTS REJETÉS MIS À JOUR AVEC NOUVEL EMAIL (Prêts à envoyer)  : {bounced_updated}")
print(f"❓ Contacts non trouvés dans la base initiale                       : {not_found_in_db}")
print("="*80)

# Breakdown of updated companies
df_corr_summary = pd.DataFrame(corrections_list)
if not df_corr_summary.empty:
    print("\n🏢 DÉTAIL DES ENTREPRISES MISES À JOUR AVEC LE NOUVEAU DOMAINE :")
    for comp_name, grp in df_corr_summary.groupby("Entreprise"):
        print(f"\n- 🏢 {comp_name} ({len(grp)} contacts prêts)")
        for _, r in grp.head(3).iterrows():
            print(f"    👤 {r['Nom']:<22} | ❌ {r['Ancien Email (Rejeté)']:<32} ➔ 🟢 {r['Nouvel Email Corrigé']}")
        if len(grp) > 3:
            print(f"    ... et {len(grp)-3} autres")

