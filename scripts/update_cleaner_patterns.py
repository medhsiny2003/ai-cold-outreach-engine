def update_cleaner():
    with open('services/gmail_cleaner.py', 'r', encoding='utf-8') as f:
        content = f.read().replace('\r\n', '\n')

    old_target = """                        rm = re.search(r"(?:Final-Recipient|Original-Recipient):\\s*(?:rfc822;)?\\s*([^\\s;\\r\\n]+)", raw_text, re.IGNORECASE)
                        tm = re.search(r"(?:wasn\\'t delivered to|Address not found|couldn\\'t be delivered to|failed:|Delivery to the following recipient failed permanently:\\s*|failed to deliver to:\\s*|Undeliverable:\\s*|Recipient address:\\s*|L'adresse n'a pas été trouvée pour\\s*)\\s*([^\\s<>\\r\\n]+@[^\\s<>\\r\\n]+)", raw_text, re.IGNORECASE)
                        failed_recipient = None
                        if rm:
                            failed_recipient = rm.group(1).strip().strip("<>")
                        elif tm:
                            failed_recipient = tm.group(1).strip().strip("<>").strip(".")
                        else:
                            for em in re.findall(r'[\\w\\.-]+@[\\w\\.-]+\\.\\w+', raw_text):
                                em_l = em.lower().strip()
                                if em_l != smtp.sender_email.lower() and not any(x in em_l for x in ["google", "daemon", "postmaster", "smtp", "mailer", "bounce", "system", "exchange", "microsoft"]):
                                    failed_recipient = em_l
                                    break
                        if failed_recipient:
                            clean_r = failed_recipient.lower().strip().strip("<>").strip(".")
                            bounced_dict[clean_r] = "550 5.1.1 Address not found (Mailer-Daemon / Postmaster)\""""

    new_replacement = """                        rm = re.search(r"(?:Final-Recipient|Original-Recipient):\\s*(?:rfc822;)?\\s*([^\\s;\\r\\n]+)", raw_text, re.IGNORECASE)
                        tm = re.search(r"(?:wasn\\'t delivered to|Address not found|couldn\\'t be delivered to|failed:|Delivery to the following recipient failed permanently:\\s*|failed to deliver to:\\s*|Undeliverable:\\s*|Recipient address:\\s*|L'adresse n'a pas été trouvée pour\\s*)\\s*([^\\s<>\\r\\n]+@[^\\s<>\\r\\n]+)", raw_text, re.IGNORECASE)
                        bm = re.search(r"(?:Your message to|Message blocked to)\\s+([^\\s<>\\r\\n]+@[^\\s<>\\r\\n]+)\\s+(?:has been blocked|couldn\\'t be delivered)", raw_text, re.IGNORECASE)
                        rl = re.search(r"Unable to relay for\\s+([^\\s<>\\r\\n]+@[^\\s<>\\r\\n]+)", raw_text, re.IGNORECASE)
                        
                        failed_recipient = None
                        if rm:
                            failed_recipient = rm.group(1).strip().strip("<>")
                        elif tm:
                            failed_recipient = tm.group(1).strip().strip("<>").strip(".")
                        elif bm:
                            failed_recipient = bm.group(1).strip().strip("<>").strip(".")
                        elif rl:
                            failed_recipient = rl.group(1).strip().strip("<>").strip(".")
                        else:
                            for em in re.findall(r'[\\w\\.-]+@[\\w\\.-]+\\.\\w+', raw_text):
                                em_l = em.lower().strip()
                                if em_l != smtp.sender_email.lower() and not any(x in em_l for x in ["google", "daemon", "postmaster", "smtp", "mailer", "bounce", "system", "exchange", "microsoft"]):
                                    failed_recipient = em_l
                                    break
                                    
                        if failed_recipient:
                            clean_r = failed_recipient.lower().strip().strip("<>").strip(".")
                            if "550 5.4.1" in raw_text or "Recipient address rejected" in raw_text:
                                bounced_dict[clean_r] = "550 5.4.1 Recipient address rejected (Adresse inexistante sur Exchange / Microsoft 365)"
                            elif "550 5.7.1" in raw_text or "Unable to relay" in raw_text or "policy" in raw_text.lower():
                                bounced_dict[clean_r] = "550 5.7.1 Unable to relay / Security Policy Rejection (Passerelle d'entreprise / Cloudflare)"
                            else:
                                bounced_dict[clean_r] = "550 5.1.1 Address not found (Mailer-Daemon / Postmaster)\""""

    if old_target in content:
        content = content.replace(old_target, new_replacement)
        with open('services/gmail_cleaner.py', 'w', encoding='utf-8') as f:
            f.write(content)
        print("Updated services/gmail_cleaner.py successfully!")
    else:
        print("Error: old_target still not found")

if __name__ == '__main__':
    update_cleaner()
