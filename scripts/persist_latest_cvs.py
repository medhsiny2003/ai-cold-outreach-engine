import shutil
from pathlib import Path
import sqlite3
import time

user_up = Path(r"C:\Users\medhs\.gemini\antigravity\brain\2fe0f6ab-01d7-4075-bf37-51a2c7de836e\.user_uploaded")
uploads_dir = Path("data/uploads")
uploads_dir.mkdir(parents=True, exist_ok=True)

# 1. Source files from latest uploaded media
src_fr_cv = user_up / "media_1788020252447.pdf"
src_en_cv = user_up / "media_1788020260053.pdf"
src_pf = user_up / "media_1788020300414.pdf"

dest_fr = uploads_dir / "CV_Mohammed_HSINY_FR.pdf"
dest_fr_alias = uploads_dir / "mohammed_hsiny_cv_fr.pdf"
dest_en = uploads_dir / "CV_Mohammed_HSINY_EN.pdf"
dest_pf = uploads_dir / "Portfolio_Mohammed_HSINY.pdf"

if src_fr_cv.is_file():
    shutil.copy2(src_fr_cv, dest_fr)
    shutil.copy2(src_fr_cv, dest_fr_alias)
    print(f"Copied {src_fr_cv.name} -> {dest_fr.name} ({dest_fr.stat().st_size} bytes)")

if src_en_cv.is_file():
    shutil.copy2(src_en_cv, dest_en)
    print(f"Copied {src_en_cv.name} -> {dest_en.name} ({dest_en.stat().st_size} bytes)")

if src_pf.is_file():
    shutil.copy2(src_pf, dest_pf)
    print(f"Copied {src_pf.name} -> {dest_pf.name} ({dest_pf.stat().st_size} bytes)")

# 2. Persist in SQLite outreach.db
db_path = Path("data/outreach.db")
conn = sqlite3.connect(db_path)
conn.execute("""
    CREATE TABLE IF NOT EXISTS app_documents (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        doc_name TEXT UNIQUE NOT NULL,
        file_bytes BLOB NOT NULL,
        updated_at REAL NOT NULL
    )
""")

for doc_file in [dest_fr, dest_fr_alias, dest_en, dest_pf]:
    if doc_file.is_file():
        b = doc_file.read_bytes()
        conn.execute("""
            INSERT INTO app_documents (doc_name, file_bytes, updated_at)
            VALUES (?, ?, ?)
            ON CONFLICT(doc_name) DO UPDATE SET
                file_bytes = excluded.file_bytes,
                updated_at = excluded.updated_at
        """, (doc_file.name, b, time.time()))
        print(f"Persisted {doc_file.name} ({len(b)} bytes) into SQLite app_documents")

conn.commit()
conn.close()
print("All latest documents copied and saved to SQLite successfully!")
