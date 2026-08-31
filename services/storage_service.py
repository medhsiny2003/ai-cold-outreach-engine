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

def save_smtp_settings(settings: SMTPSettings):
    with get_db_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO smtp_settings (id, data_json, updated_at)
            VALUES (1, ?, ?)
        """, (settings.model_dump_json(), time.time()))
        conn.commit()

def load_smtp_settings() -> SMTPSettings:
    with get_db_connection() as conn:
        row = conn.execute("SELECT data_json FROM smtp_settings WHERE id = 1").fetchone()
        if row:
            try:
                settings = SMTPSettings.model_validate_json(row["data_json"])
                if settings.min_delay_seconds > 15:
                    settings.min_delay_seconds = 4
                    settings.max_delay_seconds = 8
                return settings
            except Exception:
                return SMTPSettings()
    return SMTPSettings()

def save_llm_settings(settings: LLMSettings):
    with get_db_connection() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO llm_settings (id, data_json, updated_at)
            VALUES (1, ?, ?)
        """, (settings.model_dump_json(), time.time()))
        conn.commit()

def load_llm_settings() -> LLMSettings:
    with get_db_connection() as conn:
        row = conn.execute("SELECT data_json FROM llm_settings WHERE id = 1").fetchone()
        if row:
            try:
                return LLMSettings.model_validate_json(row["data_json"])
            except Exception:
                return LLMSettings()
    return LLMSettings()

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
