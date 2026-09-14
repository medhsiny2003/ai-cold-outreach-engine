import os
import sqlite3
import json
import time
from typing import List, Dict, Any, Optional
from config import DB_PATH, CandidateProfile, SMTPSettings, LLMSettings

def get_db_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH), timeout=60.0, isolation_level=None)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=60000;")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Initializes the database schema."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        
        # Profile table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS candidate_profile (
                id INTEGER PRIMARY KEY,
                data_json TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        
        # SMTP settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS smtp_settings (
                id INTEGER PRIMARY KEY,
                data_json TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        
        # LLM settings table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS llm_settings (
                id INTEGER PRIMARY KEY,
                data_json TEXT NOT NULL,
                updated_at REAL NOT NULL
            )
        """)
        
        # Contacts table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contacts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                email TEXT UNIQUE NOT NULL,
                name TEXT,
                company TEXT,
                role TEXT,
                location TEXT,
                industry TEXT,
                language TEXT,
                notes TEXT,
                alt_email_1 TEXT,
                alt_email_2 TEXT,
                status TEXT DEFAULT 'pending',
                subject TEXT,
                body TEXT,
                updated_at REAL NOT NULL
            )
        """)
        
        # Check and migrate columns if missing
        cursor.execute("PRAGMA table_info(contacts);")
        existing_cols = [r[1] for r in cursor.fetchall()]
        if "alt_email_1" not in existing_cols:
            cursor.execute("ALTER TABLE contacts ADD COLUMN alt_email_1 TEXT;")
        if "alt_email_2" not in existing_cols:
            cursor.execute("ALTER TABLE contacts ADD COLUMN alt_email_2 TEXT;")
        
        # Sent logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sent_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipient_email TEXT NOT NULL,
                subject TEXT NOT NULL,
                body TEXT NOT NULL,
                status TEXT NOT NULL,
                error_message TEXT,
                sent_at REAL NOT NULL
            )
        """)
        
        # Recruiter responses table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS recruiter_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                contact_id INTEGER,
                sender_email TEXT NOT NULL,
                sender_name TEXT,
                company TEXT,
                subject TEXT,
                body_text TEXT,
                received_at REAL NOT NULL,
                intent_category TEXT DEFAULT 'general',
                sentiment_label TEXT DEFAULT 'neutral',
                ai_summary TEXT,
                ai_suggested_reply TEXT,
                is_read INTEGER DEFAULT 0,
                FOREIGN KEY(contact_id) REFERENCES contacts(id)
            )
        """)
        
        # Ensure default profile, SMTP, and LLM rows exist on first run
        row_p = cursor.execute("SELECT id FROM candidate_profile WHERE id = 1").fetchone()
        if not row_p:
            cursor.execute("INSERT INTO candidate_profile (id, data_json, updated_at) VALUES (1, ?, ?)", (CandidateProfile().model_dump_json(), time.time()))

        row_s = cursor.execute("SELECT id FROM smtp_settings WHERE id = 1").fetchone()
        if not row_s:
            cursor.execute("INSERT INTO smtp_settings (id, data_json, updated_at) VALUES (1, ?, ?)", (SMTPSettings().model_dump_json(), time.time()))

        row_l = cursor.execute("SELECT id FROM llm_settings WHERE id = 1").fetchone()
        if not row_l:
            cursor.execute("INSERT INTO llm_settings (id, data_json, updated_at) VALUES (1, ?, ?)", (LLMSettings().model_dump_json(), time.time()))

        conn.commit()

def save_profile(profile: CandidateProfile):
    with get_db_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO candidate_profile (id, data_json, updated_at)
            VALUES (1, ?, ?)
        """, (profile.model_dump_json(), time.time()))
        conn.commit()

def load_profile() -> CandidateProfile:
    with get_db_connection() as conn:
        row = conn.execute("SELECT data_json FROM candidate_profile WHERE id = 1").fetchone()
        if row:
            try:
                return CandidateProfile.model_validate_json(row["data_json"])
            except Exception:
                return CandidateProfile()
    return CandidateProfile()

def update_env_file(key_values: Dict[str, str]):
    """Safely updates or appends key=value pairs in the local .env file."""
    try:
        env_path = BASE_DIR / ".env"
        lines = []
        if env_path.is_file():
            try:
                lines = env_path.read_text(encoding="utf-8").splitlines()
            except Exception:
                lines = []
                
        updated_keys = set()
        new_lines = []
        for line in lines:
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and "=" in stripped:
                k, _ = stripped.split("=", 1)
                k = k.strip()
                if k in key_values:
                    new_lines.append(f"{k}={key_values[k]}")
                    updated_keys.add(k)
                    continue
            new_lines.append(line)
            
        for k, v in key_values.items():
            if k not in updated_keys:
                new_lines.append(f"{k}={v}")
                
        env_path.write_text("\n".join(new_lines) + "\n", encoding="utf-8")
    except Exception:
        pass

def save_smtp_settings(settings: SMTPSettings):
    with get_db_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO smtp_settings (id, data_json, updated_at)
            VALUES (1, ?, ?)
        """, (settings.model_dump_json(), time.time()))
        conn.commit()
        
    # Keep os.environ & local .env in sync for background workers & multi-session persistence
    if settings.app_password:
        os.environ["GMAIL_APP_PASSWORD"] = settings.app_password
    if settings.sender_email:
        os.environ["GMAIL_SENDER_EMAIL"] = settings.sender_email
        
    update_env_file({
        "GMAIL_APP_PASSWORD": settings.app_password,
        "GMAIL_SENDER_EMAIL": settings.sender_email
    })

def load_smtp_settings() -> SMTPSettings:
    settings = None
    with get_db_connection() as conn:
        row = conn.execute("SELECT data_json FROM smtp_settings WHERE id = 1").fetchone()
        if row:
            try:
                settings = SMTPSettings.model_validate_json(row["data_json"])
                if settings.min_delay_seconds > 15:
                    settings.min_delay_seconds = 4
                    settings.max_delay_seconds = 8
            except Exception:
                settings = None
                
    if settings is None:
        settings = SMTPSettings()
        
    # Resolve app_password if empty in SQLite DB
    if not settings.app_password or not settings.app_password.strip():
        for env_k in ["GMAIL_APP_PASSWORD", "GMAIL_PASSWORD", "APP_PASSWORD", "EMAIL_PASSWORD"]:
            val = os.getenv(env_k, "").strip()
            if val:
                settings.app_password = val
                break
                
        if not settings.app_password:
            try:
                import streamlit as st
                for sec_k in ["GMAIL_APP_PASSWORD", "gmail_app_password", "GMAIL_PASSWORD", "gmail_password", "APP_PASSWORD", "app_password"]:
                    if sec_k in st.secrets:
                        val = str(st.secrets[sec_k]).strip()
                        if val:
                            settings.app_password = val
                            break
            except Exception:
                pass
                
        # If successfully retrieved from environment or secrets, persist back into DB
        if settings.app_password and settings.app_password.strip():
            try:
                with get_db_connection() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO smtp_settings (id, data_json, updated_at)
                        VALUES (1, ?, ?)
                    """, (settings.model_dump_json(), time.time()))
                    conn.commit()
            except Exception:
                pass

    if not settings.sender_email or not settings.sender_email.strip():
        settings.sender_email = os.getenv("GMAIL_SENDER_EMAIL", "mohammedhsiny2@gmail.com")
        try:
            import streamlit as st
            if "GMAIL_SENDER_EMAIL" in st.secrets:
                settings.sender_email = str(st.secrets["GMAIL_SENDER_EMAIL"]).strip()
        except Exception:
            pass
            
    return settings

def save_llm_settings(settings: LLMSettings):
    with get_db_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO llm_settings (id, data_json, updated_at)
            VALUES (1, ?, ?)
        """, (settings.model_dump_json(), time.time()))
        conn.commit()
        
    if settings.api_key:
        os.environ["GEMINI_API_KEY"] = settings.api_key
        update_env_file({
            "GEMINI_API_KEY": settings.api_key
        })

def load_llm_settings() -> LLMSettings:
    settings = None
    with get_db_connection() as conn:
        row = conn.execute("SELECT data_json FROM llm_settings WHERE id = 1").fetchone()
        if row:
            try:
                settings = LLMSettings.model_validate_json(row["data_json"])
            except Exception:
                settings = None
                
    if settings is None:
        settings = LLMSettings()
        
    if not settings.api_key or not settings.api_key.strip():
        for env_k in ["GEMINI_API_KEY", "OPENAI_API_KEY", "GROQ_API_KEY", "API_KEY"]:
            val = os.getenv(env_k, "").strip()
            if val:
                settings.api_key = val
                break
                
        if not settings.api_key:
            try:
                import streamlit as st
                for sec_k in ["GEMINI_API_KEY", "gemini_api_key", "API_KEY", "api_key"]:
                    if sec_k in st.secrets:
                        val = str(st.secrets[sec_k]).strip()
                        if val:
                            settings.api_key = val
                            break
            except Exception:
                pass
                
        if settings.api_key and settings.api_key.strip():
            try:
                with get_db_connection() as conn:
                    conn.execute("""
                        INSERT OR REPLACE INTO llm_settings (id, data_json, updated_at)
                        VALUES (1, ?, ?)
                    """, (settings.model_dump_json(), time.time()))
                    conn.commit()
            except Exception:
                pass
                
    return settings

def save_or_update_contact(contact: Dict[str, Any]):
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO contacts (email, name, company, role, location, industry, language, notes, status, subject, body, updated_at)
            VALUES (:email, :name, :company, :role, :location, :industry, :language, :notes, :status, :subject, :body, :updated_at)
            ON CONFLICT(email) DO UPDATE SET
                name = excluded.name,
                company = excluded.company,
                role = excluded.role,
                location = excluded.location,
                industry = excluded.industry,
                language = excluded.language,
                notes = excluded.notes,
                status = excluded.status,
                subject = excluded.subject,
                body = excluded.body,
                updated_at = excluded.updated_at
        """, {
            "email": contact["email"].lower().strip(),
            "name": contact.get("name", ""),
            "company": contact.get("company", ""),
            "role": contact.get("role", ""),
            "location": contact.get("location", ""),
            "industry": contact.get("industry", ""),
            "language": contact.get("language", ""),
            "notes": contact.get("notes", ""),
            "status": contact.get("status", "pending"),
            "subject": contact.get("subject", ""),
            "body": contact.get("body", ""),
            "updated_at": time.time()
        })
        conn.commit()

def get_all_contacts() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM contacts ORDER BY id ASC").fetchall()
        return [dict(row) for row in rows]

def save_contacts_bulk(contacts: List[Dict[str, Any]]):
    """Fast bulk insert or update for contacts."""
    now = time.time()
    payload = []
    for c in contacts:
        payload.append({
            "email": c["email"].lower().strip(),
            "name": c.get("name", ""),
            "company": c.get("company", ""),
            "role": c.get("role", ""),
            "location": c.get("location", ""),
            "industry": c.get("industry", ""),
            "language": c.get("language", ""),
            "notes": c.get("notes", ""),
            "status": c.get("status", "pending"),
            "subject": c.get("subject", ""),
            "body": c.get("body", ""),
            "updated_at": now
        })
        
    with get_db_connection() as conn:
        conn.executemany("""
            INSERT INTO contacts (email, name, company, role, location, industry, language, notes, status, subject, body, updated_at)
            VALUES (:email, :name, :company, :role, :location, :industry, :language, :notes, :status, :subject, :body, :updated_at)
            ON CONFLICT(email) DO UPDATE SET
                name = excluded.name,
                company = excluded.company,
                role = excluded.role,
                location = excluded.location,
                industry = excluded.industry,
                language = excluded.language,
                notes = excluded.notes,
                status = excluded.status,
                subject = excluded.subject,
                body = excluded.body,
                updated_at = excluded.updated_at
        """, payload)
        conn.commit()

def approve_all_contacts(only_generated: bool = False) -> int:
    """Instantly approves all contacts in a single fast atomic query."""
    now = time.time()
    with get_db_connection() as conn:
        if only_generated:
            cur = conn.execute("UPDATE contacts SET status = 'approved', updated_at = ? WHERE status = 'generated'", (now,))
        else:
            cur = conn.execute("UPDATE contacts SET status = 'approved', updated_at = ? WHERE status IN ('generated', 'pending')", (now,))
        conn.commit()
        return cur.rowcount

def clear_all_contacts():
    with get_db_connection() as conn:
        conn.execute("DELETE FROM contacts")
        conn.commit()

def log_sent_email(recipient_email: str, subject: str, body: str, status: str, error_message: Optional[str] = None):
    with get_db_connection() as conn:
        conn.execute("""
            INSERT INTO sent_logs (recipient_email, subject, body, status, error_message, sent_at)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (recipient_email, subject, body, status, error_message or "", time.time()))
        conn.commit()

def get_all_sent_logs() -> List[Dict[str, Any]]:
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM sent_logs ORDER BY sent_at DESC").fetchall()
        return [dict(row) for row in rows]

def trigger_waterfall_retry_bounced() -> Dict[str, Any]:
    """
    For contacts that bounced, checks if alt_email_1 or alt_email_2 exist,
    switches email to the secondary address and resets status to 'approved' for retry.
    """
    switched_count = 0
    switched_details = []
    with get_db_connection() as conn:
        bounced_rows = conn.execute("SELECT * FROM contacts WHERE status = 'bounced'").fetchall()
        for r in bounced_rows:
            c = dict(r)
            current_e = c.get("email", "").lower().strip()
            alt_1 = (c.get("alt_email_1") or "").lower().strip()
            alt_2 = (c.get("alt_email_2") or "").lower().strip()
            notes = c.get("notes") or ""
            
            target_next = None
            note_msg = ""
            if alt_1 and alt_1 != current_e and "alt1" not in notes.lower():
                target_next = alt_1
                note_msg = f"🔄 Waterfall : Essai Email Alternatif 1 ({alt_1})"
            elif alt_2 and alt_2 != current_e and "alt2" not in notes.lower():
                target_next = alt_2
                note_msg = f"🔄 Waterfall : Essai Email Alternatif 2 ({alt_2})"
                
            if target_next:
                conn.execute("""
                    UPDATE contacts 
                    SET email = ?, status = 'approved', notes = ?, updated_at = ?
                    WHERE id = ?
                """, (target_next, note_msg, time.time(), c["id"]))
                switched_count += 1
                switched_details.append({
                    "name": c.get("name"),
                    "company": c.get("company"),
                    "old_email": current_e,
                    "new_email": target_next
                })
        conn.commit()
    return {
        "success": True,
        "count": switched_count,
        "switched": switched_details
    }

def save_recruiter_response(data: Dict[str, Any]) -> int:
    """Inserts a new recruiter response into the database."""
    with get_db_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO recruiter_responses (
                contact_id, sender_email, sender_name, company, subject,
                body_text, received_at, intent_category, sentiment_label,
                ai_summary, ai_suggested_reply, is_read
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            data.get("contact_id"),
            data["sender_email"].lower().strip(),
            data.get("sender_name", ""),
            data.get("company", ""),
            data.get("subject", "Sans objet"),
            data.get("body_text", ""),
            data.get("received_at", time.time()),
            data.get("intent_category", "general"),
            data.get("sentiment_label", "neutral"),
            data.get("ai_summary", ""),
            data.get("ai_suggested_reply", ""),
            data.get("is_read", 0)
        ))
        conn.commit()
        return cursor.lastrowid

def get_all_recruiter_responses() -> List[Dict[str, Any]]:
    """Retrieves all recruiter responses ordered by date descending."""
    with get_db_connection() as conn:
        rows = conn.execute("SELECT * FROM recruiter_responses ORDER BY received_at DESC").fetchall()
        return [dict(r) for r in rows]

def mark_response_read(resp_id: int):
    """Marks a recruiter response as read."""
    with get_db_connection() as conn:
        conn.execute("UPDATE recruiter_responses SET is_read = 1 WHERE id = ?", (resp_id,))
        conn.commit()

def delete_contact_by_id(contact_id: int):
    """Deletes a single contact by its ID."""
    with get_db_connection() as conn:
        conn.execute("DELETE FROM contacts WHERE id = ?", (contact_id,))
        conn.commit()

def delete_contacts_bulk(contact_ids: List[int]) -> int:
    """Deletes multiple contacts by IDs."""
    if not contact_ids:
        return 0
    with get_db_connection() as conn:
        placeholders = ",".join("?" * len(contact_ids))
        cur = conn.execute(f"DELETE FROM contacts WHERE id IN ({placeholders})", contact_ids)
        conn.commit()
        return cur.rowcount

def update_contacts_status_bulk(contact_ids: List[int], new_status: str) -> int:
    """Updates status for a batch of contact IDs (e.g. 'excluded', 'pending', 'approved')."""
    if not contact_ids:
        return 0
    with get_db_connection() as conn:
        placeholders = ",".join("?" * len(contact_ids))
        params = [new_status, time.time()] + list(contact_ids)
        cur = conn.execute(f"UPDATE contacts SET status = ?, updated_at = ? WHERE id IN ({placeholders})", params)
        conn.commit()
        return cur.rowcount

def delete_contacts_by_status(status_list: List[str]) -> int:
    """Deletes contacts that match specific statuses (e.g. ['sent'], ['bounced'], ['excluded'])."""
    if not status_list:
        return 0
    with get_db_connection() as conn:
        placeholders = ",".join("?" * len(status_list))
        cur = conn.execute(f"DELETE FROM contacts WHERE status IN ({placeholders})", status_list)
        conn.commit()
        return cur.rowcount

def reset_all_contacts_to_pending() -> int:
    """Resets all contacts in the database to 'pending' to restart outreach cycles."""
    now = time.time()
    with get_db_connection() as conn:
        cur = conn.execute("UPDATE contacts SET status = 'pending', updated_at = ?", (now,))
        conn.commit()
        return cur.rowcount

def reset_sent_and_bounced_to_pending() -> int:
    """Resets only sent and bounced contacts back to 'pending' to retry campaigns."""
    now = time.time()
    with get_db_connection() as conn:
        cur = conn.execute("UPDATE contacts SET status = 'pending', updated_at = ? WHERE status IN ('sent', 'bounced')", (now,))
        conn.commit()
        return cur.rowcount

def clear_sent_logs_history():
    """Clears sent logs history."""
    with get_db_connection() as conn:
        conn.execute("DELETE FROM sent_logs")
        conn.commit()

def reset_all_data_and_contacts(clear_sent_logs: bool = False, clear_uploads: bool = False):
    """Resets the contacts table and optionally sent logs and uploads."""
    with get_db_connection() as conn:
        conn.execute("DELETE FROM contacts")
        if clear_sent_logs:
            conn.execute("DELETE FROM sent_logs")
            conn.execute("DELETE FROM recruiter_responses")
        conn.commit()
        
    if clear_uploads:
        from config import UPLOADS_DIR
        if UPLOADS_DIR.is_dir():
            for f in UPLOADS_DIR.iterdir():
                if f.is_file() and not f.name.startswith("CV_") and not f.name.startswith("Portfolio_"):
                    try:
                        f.unlink()
                    except Exception:
                        pass

