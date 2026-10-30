def fix():
    # 1. Add clear_sent_logs_history to services/storage_service.py
    with open('services/storage_service.py', 'r', encoding='utf-8') as f:
        ss = f.read()

    new_func = """def clear_sent_logs_history():
    \"\"\"Clears all records in sent_logs table.\"\"\"
    with get_db_connection() as conn:
        conn.execute("DELETE FROM sent_logs")
        conn.commit()

"""
    if "def clear_sent_logs_history" not in ss:
        # Insert before save_document_blob
        ss = ss.replace("def save_document_blob", new_func + "def save_document_blob")
        with open('services/storage_service.py', 'w', encoding='utf-8') as f:
            f.write(ss)
        print("Added clear_sent_logs_history to storage_service.py")

    # 2. Update app.py imports
    with open('app.py', 'r', encoding='utf-8') as f:
        app = f.read()

    old_import_block = """try:
    from services.storage_service import (
        init_db, load_profile, save_profile, load_smtp_settings, save_smtp_settings,
        load_llm_settings, save_llm_settings, get_all_contacts, save_or_update_contact,
        save_contacts_bulk, approve_all_contacts, clear_all_contacts, log_sent_email, get_all_sent_logs,
        get_all_recruiter_responses, mark_response_read, trigger_waterfall_retry_bounced,
        delete_contact_by_id, delete_contacts_bulk, update_contacts_status_bulk, reset_all_data_and_contacts,
        delete_contacts_by_status, reset_all_contacts_to_pending, reset_sent_and_bounced_to_pending, clear_sent_logs_history,
        get_unique_companies_summary, exclude_contacts_by_companies, reinclude_contacts_by_companies, delete_contacts_by_companies, save_document_blob, restore_documents_from_db
    )
except ImportError:
    from services.storage_service import (
        init_db, load_profile, save_profile, load_smtp_settings, save_smtp_settings,
        load_llm_settings, save_llm_settings, get_all_contacts, save_or_update_contact,
        save_contacts_bulk, approve_all_contacts, clear_all_contacts, log_sent_email, get_all_sent_logs
    )
    def get_all_recruiter_responses(): return []
    def mark_response_read(resp_id): pass
    def trigger_waterfall_retry_bounced(): return {"success": True, "count": 0, "message": "Aucun email alternatif."}
    def delete_contact_by_id(cid): pass
    def delete_contacts_bulk(cids): return 0
    def update_contacts_status_bulk(cids, st): return 0
    def reset_all_data_and_contacts(c_logs=False, c_up=False): pass
    def delete_contacts_by_status(st_list): return 0
    def reset_all_contacts_to_pending(): return 0
    def reset_sent_and_bounced_to_pending(): return 0
    def clear_sent_logs_history(): pass
    def get_unique_companies_summary(): return []
    def exclude_contacts_by_companies(c_names): return 0
    def reinclude_contacts_by_companies(c_names): return 0
    def delete_contacts_by_companies(c_names): return 0"""

    new_import_block = """try:
    from services.storage_service import (
        init_db, load_profile, save_profile, load_smtp_settings, save_smtp_settings,
        load_llm_settings, save_llm_settings, get_all_contacts, save_or_update_contact,
        save_contacts_bulk, approve_all_contacts, clear_all_contacts, log_sent_email, get_all_sent_logs,
        get_all_recruiter_responses, mark_response_read, trigger_waterfall_retry_bounced,
        delete_contact_by_id, delete_contacts_bulk, update_contacts_status_bulk, reset_all_data_and_contacts,
        delete_contacts_by_status, reset_all_contacts_to_pending, reset_sent_and_bounced_to_pending, clear_sent_logs_history,
        get_unique_companies_summary, exclude_contacts_by_companies, reinclude_contacts_by_companies, delete_contacts_by_companies,
        save_document_blob, restore_documents_from_db
    )
except ImportError:
    from services.storage_service import (
        init_db, load_profile, save_profile, load_smtp_settings, save_smtp_settings,
        load_llm_settings, save_llm_settings, get_all_contacts, save_or_update_contact,
        save_contacts_bulk, approve_all_contacts, clear_all_contacts, log_sent_email, get_all_sent_logs
    )
    def get_all_recruiter_responses(): return []
    def mark_response_read(resp_id): pass
    def trigger_waterfall_retry_bounced(): return {"success": True, "count": 0, "message": "Aucun email alternatif."}
    def delete_contact_by_id(cid): pass
    def delete_contacts_bulk(cids): return 0
    def update_contacts_status_bulk(cids, st): return 0
    def reset_all_data_and_contacts(c_logs=False, c_up=False): pass
    def delete_contacts_by_status(st_list): return 0
    def reset_all_contacts_to_pending(): return 0
    def reset_sent_and_bounced_to_pending(): return 0
    def clear_sent_logs_history(): pass
    def get_unique_companies_summary(): return []
    def exclude_contacts_by_companies(c_names): return 0
    def reinclude_contacts_by_companies(c_names): return 0
    def delete_contacts_by_companies(c_names): return 0
    def save_document_blob(doc_name, file_bytes): pass
    def restore_documents_from_db(): pass"""

    if old_import_block in app:
        app = app.replace(old_import_block, new_import_block)
        with open('app.py', 'w', encoding='utf-8') as f:
            f.write(app)
        print("Updated app.py imports and fallbacks!")
    else:
        print("Warning: old_import_block not found in app.py")

if __name__ == '__main__':
    fix()
