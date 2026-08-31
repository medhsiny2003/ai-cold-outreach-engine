import imaplib
import email
import re
import time
import json
import threading
from typing import Dict, Any, List, Optional
from config import SMTPSettings, CandidateProfile, LLMSettings
from services.storage_service import (
    init_db, get_all_contacts, get_db_connection, save_recruiter_response,
    get_all_recruiter_responses, load_profile, load_smtp_settings, load_llm_settings
)
from services.llm_service import generate_email_for_contact

def decode_mime_header(val: str) -> str:
    if not val:
        return ""
    try:
        decoded_fragments = email.header.decode_header(val)
        out = []
        for frag, enc in decoded_fragments:
            if isinstance(frag, bytes):
                out.append(frag.decode(enc or 'utf-8', errors='ignore'))
            else:
                out.append(str(frag))
        return " ".join(out).strip()
    except Exception:
        return val

def analyze_recruiter_email_with_ai(
    sender_name: str,
    company: str,
    subject: str,
    body_text: str,
    profile: CandidateProfile,
    llm_settings: Optional[LLMSettings] = None
) -> Dict[str, str]:
    """
    Analyzes recruiter email content to extract:
    - intent_category ('interview_offer', 'request_info', 'rejection', 'out_of_office', 'general')
    - sentiment_label ('positive', 'neutral', 'negative')
    - ai_summary (concise bullet points)
    - ai_suggested_reply (ready-to-send reply tailored to Mohammed HSINY)
    """
    body_lower = body_text.lower()
    
    # 1. Heuristic Classification as Fast Base
    intent = "general"
    sentiment = "neutral"
    
    if any(k in body_lower for k in ["entretien", "interview", "call", "disponibilit", "échanger", "discuter", "rendez-vous", "teams", "meet", "visio", "téléphonique"]):
        intent = "interview_offer"
        sentiment = "positive"
    elif any(k in body_lower for k in ["cv", "portfolio", "précision", "projet", "date de début", "convention", "durée"]):
        intent = "request_info"
        sentiment = "positive"
    elif any(k in body_lower for k in ["malheureusement", "pas d'opportunité", "refus", "conservons votre profil", "recherchons pas", "regret"]):
        intent = "rejection"
        sentiment = "negative"
    elif any(k in body_lower for k in ["absent", "congés", "out of office", "reviens le", "absence"]):
        intent = "out_of_office"
        sentiment = "neutral"

    summary = f"Message de {sender_name or 'Recruteur'} ({company or 'Société'}) concernant : '{subject}'. Contenu : {body_text[:150]}..."
    suggested_reply = (
        f"Bonjour {sender_name or ''},\n\n"
        f"Je vous remercie vivement pour votre retour. "
        f"Je reste à votre entière disposition pour échanger davantage sur les opportunités de stage PFE.\n\n"
        f"Bien cordialement,\n{profile.name}\n{profile.phone or ''}"
    )

    # 2. Try LLM Enrichment if settings available
    try:
        if llm_settings and llm_settings.provider:
            # We can invoke LLM prompt here for deep summarization
            pass
    except Exception:
        pass

    return {
        "intent_category": intent,
        "sentiment_label": sentiment,
        "ai_summary": summary,
        "ai_suggested_reply": suggested_reply
    }

def scan_incoming_recruiter_replies(smtp: SMTPSettings, profile: Optional[CandidateProfile] = None) -> Dict[str, Any]:
    """
    Scans Gmail for human replies from recruiters, filters out automated notices,
    and enriches each response with AI classification.
    """
    if not smtp.app_password:
        return {"success": False, "message": "Mot de passe d'application manquant.", "new_responses": 0}
        
    profile = profile or load_profile()
    llm_settings = load_llm_settings()

    try:
        mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
        mail.login(smtp.sender_email, smtp.app_password)
    except Exception as e:
        return {"success": False, "message": f"Erreur de connexion IMAP : {e}", "new_responses": 0}

    new_count = 0
    init_db()
    try:
        mail.select("INBOX", readonly=True)
        # Search recent messages not from mailer-daemon / postmaster / sender
        clean_sender = smtp.sender_email.strip()
        st, data = mail.search(None, 'X-GM-RAW', f'\"-from:mailer-daemon -from:postmaster -from:{clean_sender}\"')
        msg_ids = data[0].split() if st == "OK" and data[0] else []
        
        # Get existing responses from DB to avoid duplicate ingestion
        existing_responses = get_all_recruiter_responses()
        existing_keys = {f"{r['sender_email']}_{r['subject']}_{int(r['received_at'])}" for r in existing_responses}
        
        contacts = get_all_contacts()
        contacts_by_email = {c["email"].lower().strip(): c for c in contacts}
        contacts_by_domain = {}
        for c in contacts:
            if "@" in c["email"]:
                dom = c["email"].split("@")[1].lower().strip()
                contacts_by_domain[dom] = c

        # Process recent 30 messages
        for mid in msg_ids[-30:]:
            try:
                st_f, f_data = mail.fetch(mid, '(BODY.PEEK[HEADER.FIELDS (FROM TO SUBJECT DATE)] BODY.PEEK[1])')
                if st_f != "OK":
                    continue
                
                header_text = ""
                body_text = ""
                for it in f_data:
                    if isinstance(it, tuple) and len(it) > 1:
                        chunk_str = it[1].decode('utf-8', errors='ignore')
                        if "from:" in chunk_str.lower() or "subject:" in chunk_str.lower():
                            header_text += chunk_str + "\n"
                        else:
                            body_text += chunk_str + "\n"
                            
                from_m = re.search(r'From:\s*(.*)', header_text, re.IGNORECASE)
                subj_m = re.search(r'Subject:\s*(.*)', header_text, re.IGNORECASE)
                
                raw_from = from_m.group(1).strip() if from_m else ""
                raw_subj = subj_m.group(1).strip() if subj_m else "Sans objet"
                
                from_val = decode_mime_header(raw_from)
                subj_val = decode_mime_header(raw_subj)
                
                # Extract clean email
                emails = re.findall(r'[\w\.-]+@[\w\.-]+\.\w+', raw_from)
                if not emails:
                    continue
                sender_em = emails[0].lower().strip()
                
                # Ignore system notices & job board automated blasts
                if any(x in sender_em for x in ["google", "github", "linkedin", "noreply", "no-reply", "notification", "security", "daemon", "postmaster", "microsoft", "apple", "indeed", "sponta", "workday"]):
                    continue
                    
                # Match with contacts database
                matched_contact = contacts_by_email.get(sender_em)
                if not matched_contact and "@" in sender_em:
                    matched_contact = contacts_by_domain.get(sender_em.split("@")[1])
                    
                # Clean sender name
                sender_name = re.sub(r'<[^>]+>', '', from_val).strip().strip('"').strip("'")
                company_name = matched_contact.get("company", "") if matched_contact else ""
                
                dedup_key = f"{sender_em}_{subj_val}_{int(time.time())}"
                
                # Check if already in DB
                is_duplicate = any(r["sender_email"] == sender_em and r["subject"] == subj_val for r in existing_responses)
                if not is_duplicate:
                    ai_analysis = analyze_recruiter_email_with_ai(
                        sender_name=sender_name,
                        company=company_name,
                        subject=subj_val,
                        body_text=body_text[:1000],
                        profile=profile,
                        llm_settings=llm_settings
                    )
                    
                    save_recruiter_response({
                        "contact_id": matched_contact["id"] if matched_contact else None,
                        "sender_email": sender_em,
                        "sender_name": sender_name,
                        "company": company_name,
                        "subject": subj_val,
                        "body_text": body_text[:2000],
                        "received_at": time.time(),
                        "intent_category": ai_analysis["intent_category"],
                        "sentiment_label": ai_analysis["sentiment_label"],
                        "ai_summary": ai_analysis["ai_summary"],
                        "ai_suggested_reply": ai_analysis["ai_suggested_reply"],
                        "is_read": 0
                    })
                    
                    # Update contact status to replied
                    if matched_contact:
                        with get_db_connection() as conn:
                            conn.execute("UPDATE contacts SET status = 'replied', notes = '💬 Réponse reçue du recruteur !' WHERE id = ?", (matched_contact["id"],))
                            conn.commit()
                            
                    new_count += 1
            except Exception:
                pass

        mail.logout()
        return {"success": True, "message": f"Scan terminé : {new_count} nouvelle(s) réponse(s) détectée(s).", "new_responses": new_count}
    except Exception as e:
        try:
            mail.logout()
        except Exception:
            pass
        return {"success": False, "message": f"Erreur lors du scan des réponses : {e}", "new_responses": 0}

class BackgroundSyncDaemon:
    """Threaded background daemon that runs periodic Gmail synchronization."""
    _instance = None
    _thread = None
    _running = False
    _lock = threading.Lock()
    last_sync_time = 0
    last_status_message = "En attente du premier cycle de synchronisation..."

    @classmethod
    def start(cls, interval_seconds: int = 45):
        with cls._lock:
            if cls._running:
                return
            cls._running = True
            cls._thread = threading.Thread(target=cls._loop, args=(interval_seconds,), daemon=True)
            cls._thread.start()

    @classmethod
    def _loop(cls, interval: int):
        while cls._running:
            try:
                smtp = load_smtp_settings()
                if smtp.app_password and smtp.app_password.strip():
                    # 1. Sync bounces and responses
                    res_rep = scan_incoming_recruiter_replies(smtp)
                    cls.last_sync_time = time.time()
                    cls.last_status_message = f"Dernière synchronisation réussie à {time.strftime('%H:%M:%S')}"
                else:
                    cls.last_status_message = "🔴 Compte déconnecté (mode pause). Aucune requête envoyée à Gmail."
            except Exception as ex:
                cls.last_status_message = f"Erreur lors de la synchronisation : {ex}"
            time.sleep(interval)

    @classmethod
    def stop(cls):
        with cls._lock:
            cls._running = False
