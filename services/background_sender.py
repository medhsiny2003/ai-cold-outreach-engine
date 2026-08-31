import threading
import time
import random
import json
from pathlib import Path
from typing import Dict, Any, Optional, List
from config import BASE_DIR, DATA_DIR, UPLOADS_DIR, is_francophone
from services.storage_service import (
    get_all_contacts, load_smtp_settings, load_profile, log_sent_email,
    get_db_connection, save_or_update_contact
)
from services.prompt_builder import determine_language
from services.llm_service import generate_email_for_contact
from services.email_sender import send_single_email

STATE_FILE = DATA_DIR / "background_dispatch_state.json"

class BackgroundDispatcher:
    _thread: Optional[threading.Thread] = None
    _lock = threading.Lock()
    _should_stop = False
    
    @classmethod
    def _read_state(cls) -> Dict[str, Any]:
        if STATE_FILE.is_file():
            try:
                with open(STATE_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {
            "status": "IDLE",
            "sent_count": 0,
            "total_target": 0,
            "current_recipient": "",
            "last_log": "Aucun envoi actif",
            "started_at": 0,
            "last_update": 0
        }

    @classmethod
    def _write_state(cls, state: Dict[str, Any]):
        state["last_update"] = time.time()
        try:
            with open(STATE_FILE, "w", encoding="utf-8") as f:
                json.dump(state, f, ensure_ascii=False, indent=2)
        except Exception:
            pass

    @classmethod
    def get_status(cls) -> Dict[str, Any]:
        with cls._lock:
            state = cls._read_state()
            # Double check thread liveness
            if state.get("status") == "RUNNING":
                if cls._thread is None or not cls._thread.is_alive():
                    # Thread finished or died
                    state["status"] = "IDLE"
                    state["last_log"] = "Envoi en arrière-plan terminé."
                    cls._write_state(state)
            return state

    @classmethod
    def is_running(cls) -> bool:
        status = cls.get_status()
        return status.get("status") == "RUNNING"

    @classmethod
    def start(cls, batch_limit: int = 50, min_delay: int = 40, max_delay: int = 70) -> bool:
        with cls._lock:
            if cls._thread is not None and cls._thread.is_alive():
                return False  # Already running
            
            cls._should_stop = False
            cls._thread = threading.Thread(
                target=cls._worker_loop,
                args=(batch_limit, min_delay, max_delay),
                daemon=True
            )
            cls._thread.start()
            return True

    @classmethod
    def stop(cls):
        with cls._lock:
            cls._should_stop = True
            state = cls._read_state()
            state["status"] = "STOPPED"
            state["last_log"] = "⏹️ Envoi interrompu par l'utilisateur."
            cls._write_state(state)

    @classmethod
    def _worker_loop(cls, batch_limit: int, min_delay: int, max_delay: int):
        smtp = load_smtp_settings()
        profile = load_profile()
        
        all_contacts = get_all_contacts()
        approved = [c for c in all_contacts if c.get("status") == "approved"]
        
        to_send = approved[:batch_limit]
        total = len(to_send)
        
        if total == 0:
            cls._write_state({
                "status": "IDLE",
                "sent_count": 0,
                "total_target": 0,
                "current_recipient": "",
                "last_log": "Aucun contact en attente d'envoi.",
                "started_at": time.time()
            })
            return

        state = {
            "status": "RUNNING",
            "sent_count": 0,
            "total_target": total,
            "current_recipient": "",
            "last_log": f"Démarrage de l'envoi autonome en arrière-plan ({total} contacts)...",
            "started_at": time.time()
        }
        cls._write_state(state)

        # Asset Paths
        cv_fr = UPLOADS_DIR / "CV_Mohammed_HSINY_FR.pdf"
        cv_en = UPLOADS_DIR / "CV_Mohammed_HSINY_EN.pdf"
        portfolio_pdf = UPLOADS_DIR / "Portfolio_Mohammed_HSINY.pdf"

        sent_count = 0
        for idx, contact in enumerate(to_send, 1):
            if cls._should_stop:
                break
                
            recip_email = contact["email"].strip()
            lang = determine_language(contact)
            
            # Determine attachments
            attachments = []
            if lang == "fr" and cv_fr.is_file():
                attachments.append(str(cv_fr))
            elif lang == "en" and cv_en.is_file():
                attachments.append(str(cv_en))
            elif cv_fr.is_file():
                attachments.append(str(cv_fr))
                
            if portfolio_pdf.is_file():
                attachments.append(str(portfolio_pdf))

            # Subject & Body
            subject = contact.get("subject")
            body = contact.get("body")
            
            if not subject or not body or len(body.strip()) < 30:
                gen_email = generate_email_for_contact(contact, profile, language=lang)
                subject = gen_email.subject
                body = gen_email.body

            # Update State
            state["current_recipient"] = recip_email
            state["last_log"] = f"[{idx}/{total}] Envoi en cours à {recip_email} ({contact.get('company', 'N/A')})..."
            cls._write_state(state)

            # Send Email
            res = send_single_email(
                settings=smtp,
                recipient_email=recip_email,
                subject=subject,
                body_text=body,
                attachment_paths=attachments,
                profile=profile,
                language=lang
            )

            # Record in DB
            log_sent_email(
                recipient_email=recip_email,
                subject=subject,
                body=body,
                status="sent" if res.success else "failed",
                error_message=None if res.success else res.message
            )

            if res.success:
                contact["status"] = "sent"
                contact["notes"] = f"🟢 Envoyé en tâche de fond le {time.strftime('%d/%m/%Y %H:%M')}"
                save_or_update_contact(contact)
                sent_count += 1
                state["sent_count"] = sent_count
                state["last_log"] = f"✅ [{idx}/{total}] Succès pour {recip_email}"
            else:
                state["last_log"] = f"⚠️ [{idx}/{total}] Échec pour {recip_email} : {res.message}"
                
            cls._write_state(state)

            # Jitter Delay if more contacts remain
            if idx < total and not cls._should_stop:
                wait_s = random.randint(min_delay, max_delay)
                for _ in range(wait_s):
                    if cls._should_stop:
                        break
                    time.sleep(1)

        final_state = {
            "status": "COMPLETED" if not cls._should_stop else "STOPPED",
            "sent_count": sent_count,
            "total_target": total,
            "current_recipient": "",
            "last_log": f"Session terminée : {sent_count}/{total} emails expédiés avec succès.",
            "started_at": state.get("started_at", time.time())
        }
        cls._write_state(final_state)
