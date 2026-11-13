import sys
import os
sys.path.insert(0, os.path.abspath("."))
import traceback
from config import CandidateProfile, SMTPSettings, LLMSettings
import services.storage_service as ss
import services.email_validator as ev
import services.contact_manager as cm
import services.prompt_builder as pb
import services.llm_service as ls
import services.email_sender as es
import services.gmail_cleaner as gc

errors = []

def test_step(name, func):
    try:
        func()
        print(f"✅ {name}: SUCCESS")
    except Exception as e:
        print(f"❌ {name}: FAILED -> {e}")
        traceback.print_exc()
        errors.append((name, str(e)))

# Test 1: Storage DB
def t_db():
    ss.init_db()
    prof = ss.load_profile()
    smtp = ss.load_smtp_settings()
    llm = ss.load_llm_settings()
    cts = ss.get_all_contacts()
    logs = ss.get_all_sent_logs()
    resps = ss.get_all_recruiter_responses()
    ss.restore_documents_from_db()
test_step("Storage Service", t_db)

# Test 2: Contact Manager
def t_cm():
    sample = cm.generate_sample_csv()
    assert len(sample) > 0
test_step("Contact Manager Sample CSV", t_cm)

# Test 3: Email Validator
def t_ev():
    res = ev.validate_single_email("test@example.com", check_dns=False)
    assert res["is_valid"]
test_step("Email Validator", t_ev)

# Test 4: Prompt Builder
def t_pb():
    c = {"name": "Alexandre Dumas", "company": "Airbus", "role": "Directeur R&D"}
    p = CandidateProfile()
    sys_p = pb.build_system_prompt()
    usr_p = pb.build_user_prompt(c, p)
    assert "RoboThings" not in sys_p
    assert "https://portfolio-mohammed-hsiny" not in sys_p
test_step("Prompt Builder", t_pb)

# Test 5: Fallback LLM Templates
def t_ls():
    c = {"name": "Alexandre Dumas", "company": "Airbus", "role": "Directeur R&D"}
    p = CandidateProfile()
    res = ls.generate_fallback_template(c, p, language="fr")
    assert "http" not in res.body
    assert "RoboThings" not in res.body
test_step("LLM Fallback Template", t_ls)

# Test 6: Email Sender Message Creation
def t_es():
    p = CandidateProfile()
    msg = es.create_email_message(
        sender_name="Mohammed HSINY",
        sender_email="mohammedhsiny2@gmail.com",
        recipient_email="recruteur@airbus.com",
        subject="Candidature Stage PFE – Airbus – Mohammed HSINY",
        body_text="Bonjour,\nJe suis étudiant en dernière année.\nBien cordialement,\nMohammed",
        profile=p,
        language="fr"
    )
    assert msg["To"] == "recruteur@airbus.com"
test_step("Email Sender Message Creation", t_es)

if errors:
    print(f"\n🚨 FOUND {len(errors)} ERRORS:")
    for n, e in errors:
        print(f"  - {n}: {e}")
    sys.exit(1)
else:
    print("\n🎉 ALL SERVICES TESTED WITH ZERO ERRORS!")
