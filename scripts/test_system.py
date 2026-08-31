import sys
import asyncio
from pathlib import Path

# Force UTF-8 on Windows stdout
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Add project root to sys.path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import CandidateProfile, SMTPSettings, LLMSettings
from services.storage_service import (
    init_db, save_profile, load_profile, save_or_update_contact,
    get_all_contacts, log_sent_email, get_all_sent_logs
)
from services.contact_manager import parse_contacts_file, generate_sample_csv
from services.prompt_builder import determine_language, build_user_prompt
from services.llm_service import generate_email_for_contact
from services.email_sender import create_email_message

def run_tests():
    print("========================================")
    print("[*] RUNNING AUTOMATED SYSTEM INTEGRATION TESTS")
    print("========================================")

    # 1. Test Database Initialization & Profile
    print("\n[Test 1/5] Initializing Database & Candidate Profile...")
    init_db()
    profile = CandidateProfile()
    save_profile(profile)
    loaded_p = load_profile()
    assert loaded_p.name == "Mohammed HSINY"
    print(f"[OK] Profile loaded: {loaded_p.name} ({loaded_p.school})")

    # 2. Test Contact Manager & Parsing
    print("\n[Test 2/5] Testing CSV Contact Parser...")
    sample_csv = generate_sample_csv().encode("utf-8")
    contacts, errors = parse_contacts_file(sample_csv, "test_contacts.csv")
    assert len(errors) == 0, f"Errors: {errors}"
    assert len(contacts) == 6, f"Expected 6 contacts, got {len(contacts)}"
    print(f"[OK] Parsed {len(contacts)} contacts successfully.")

    for c in contacts:
        save_or_update_contact(c)
    saved_contacts = get_all_contacts()
    assert len(saved_contacts) >= 6
    print(f"[OK] Saved contacts to SQLite successfully.")

    # 3. Test Language Auto-Detection
    print("\n[Test 3/5] Testing Language Auto-Detection...")
    fr_contact = {"name": "Julien Moreau", "location": "Paris, France", "company": "Parrot"}
    en_contact = {"name": "Sarah Jenkins", "location": "San Mateo, CA, USA", "company": "Skydio"}
    be_contact = {"name": "Marc", "location": "Gosselies, Belgique", "company": "Sonaca"}
    de_contact = {"name": "Michael", "location": "Bruchsal, Germany", "company": "Volocopter"}

    assert determine_language(fr_contact) == "fr"
    assert determine_language(en_contact) == "en"
    assert determine_language(be_contact) == "fr"
    assert determine_language(de_contact) == "en"
    print("[OK] Language detection passed (FR for France/Belgium, EN for USA/Germany).")

    # 4. Test Email Generation (Offline Fallback & Structured Output)
    print("\n[Test 4/5] Testing Email Generation Engine...")
    llm_settings = LLMSettings(provider="gemini", api_key="") # Test fallback
    
    async def test_gen():
        email_fr = await generate_email_for_contact(fr_contact, profile, llm_settings)
        print(f"\n--- Generated French Email (Subject) ---\n{email_fr.subject}")
        print(f"--- Generated French Email (Preview) ---\n{email_fr.body[:180]}...\n")
        assert "Mohammed HSINY" in email_fr.body
        assert "portfolio-mohammed-hsiny" in email_fr.body

        email_en = await generate_email_for_contact(en_contact, profile, llm_settings)
        print(f"\n--- Generated English Email (Subject) ---\n{email_en.subject}")
        print(f"--- Generated English Email (Preview) ---\n{email_en.body[:180]}...\n")
        assert "Mohammed HSINY" in email_en.body
        assert "portfolio-mohammed-hsiny" in email_en.body

    asyncio.run(test_gen())
    print("[OK] Email generation pipeline validated.")

    # 5. Test MIME Email Construction
    print("\n[Test 5/5] Testing MIME Email Builder...")
    msg = create_email_message(
        sender_name="Mohammed HSINY",
        sender_email="mohammedhsiny2@gmail.com",
        recipient_email="test@example.com",
        subject="Test Stage PFE",
        body_text="Test Body"
    )
    assert msg["From"] == "Mohammed HSINY <mohammedhsiny2@gmail.com>"
    assert msg["To"] == "test@example.com"
    print("[OK] MIME email structure verified.")

    print("\n========================================")
    print("[SUCCESS] ALL TESTS COMPLETED SUCCESSFULLY !")
    print("========================================")

if __name__ == "__main__":
    run_tests()
