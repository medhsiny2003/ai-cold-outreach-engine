# services/email_validator.py
import re
import socket
from typing import Dict, Any, List, Optional, Tuple

__all__ = [
    'check_email_syntax',
    'check_domain_dns',
    'validate_single_email',
    'validate_contacts_list',
    'DISPOSABLE_DOMAINS',
    'COMMON_TYPOS'
]

# Comprehensive Disposable / Temp Mail Domains
DISPOSABLE_DOMAINS = {
    'mailinator.com', '10minutemail.com', 'tempmail.com', 'guerrillamail.com',
    'throwawaymail.com', 'yopmail.com', 'trashmail.com', 'sharklasers.com',
    'getairmail.com', 'dispostable.com', 'crazymailing.com', 'fakeinbox.com',
    'mytemp.email', 'temp-mail.org', 'tempail.com', 'burnermail.io'
}

# Common domain typos -> suggestions
COMMON_TYPOS = {
    'gmial.com': 'gmail.com',
    'gmai.com': 'gmail.com',
    'gamil.com': 'gmail.com',
    'gmaill.com': 'gmail.com',
    'hotmial.com': 'hotmail.com',
    'hotmai.com': 'hotmail.com',
    'yaho.com': 'yahoo.com',
    'yahooo.fr': 'yahoo.fr',
    'wanado.fr': 'wanadoo.fr',
    'outlok.com': 'outlook.com',
}

# Domain DNS resolution cache
_DNS_CACHE: Dict[str, bool] = {}

# RFC 5322 Compliant Email Regex
EMAIL_REGEX = re.compile(
    r'^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?(?:\.[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?)+$'
)

def check_email_syntax(email: str) -> Tuple[bool, str]:
    if not email or not isinstance(email, str):
        return False, 'Adresse email vide ou format invalide'
    
    clean_email = email.strip().lower()
    
    if len(clean_email) > 254:
        return False, 'Adresse email trop longue (> 254 caractères)'
        
    if ' ' in clean_email:
        return False, 'Contient des espaces'
        
    if clean_email.count('@') != 1:
        return False, 'Doit contenir exactement un seul arobase (@)'
        
    local_part, domain_part = clean_email.split('@', 1)
    
    if not local_part or not domain_part:
        return False, 'Partie locale ou domaine manquant'
        
    if len(local_part) > 64:
        return False, 'Identifiant avant @ trop long (> 64 caractères)'
        
    if '..' in clean_email:
        return False, 'Contient des points consécutifs (..)'
        
    if local_part.startswith('.') or local_part.endswith('.'):
        return False, 'Ne peut pas commencer ou finir par un point'
        
    if '.' not in domain_part:
        return False, 'Extension de domaine manquante (ex: .com, .fr)'
        
    tld = domain_part.split('.')[-1]
    if len(tld) < 2:
        return False, 'Extension de domaine invalide (< 2 caractères)'
        
    if not EMAIL_REGEX.match(clean_email):
        return False, 'Caractères non conformes RFC 5322'
        
    return True, 'Syntaxe valide'

def check_domain_dns(domain: str) -> bool:
    domain_clean = domain.strip().lower()
    
    if domain_clean in _DNS_CACHE:
        return _DNS_CACHE[domain_clean]
        
    try:
        socket.setdefaulttimeout(3.0)
        socket.gethostbyname(domain_clean)
        _DNS_CACHE[domain_clean] = True
        return True
    except Exception:
        _DNS_CACHE[domain_clean] = False
        return False

def validate_single_email(email: str, check_dns: bool = True) -> Dict[str, Any]:
    clean_e = (email or '').strip().lower()
    
    if not clean_e:
        return {
            'email': email,
            'is_valid': False,
            'status': 'invalid_syntax',
            'reason': 'Adresse email vide',
            'suggested_fix': None
        }
        
    syntax_ok, syntax_reason = check_email_syntax(clean_e)
    if not syntax_ok:
        return {
            'email': clean_e,
            'is_valid': False,
            'status': 'invalid_syntax',
            'reason': syntax_reason,
            'suggested_fix': None
        }
        
    local, domain = clean_e.split('@', 1)
    
    if domain in DISPOSABLE_DOMAINS:
        return {
            'email': clean_e,
            'is_valid': False,
            'status': 'disposable',
            'reason': 'Adresse email temporaire / jetable détectée',
            'suggested_fix': None
        }
        
    suggested = None
    if domain in COMMON_TYPOS:
        suggested = f'{local}@{COMMON_TYPOS[domain]}'
        
    if check_dns:
        dns_ok = check_domain_dns(domain)
        if not dns_ok:
            return {
                'email': clean_e,
                'is_valid': False,
                'status': 'invalid_domain',
                'reason': f'Domaine @{domain} introuvable ou inactif sur le réseau',
                'suggested_fix': suggested
            }
            
    return {
        'email': clean_e,
        'is_valid': True,
        'status': 'valid',
        'reason': 'Adresse email valide et domaine actif',
        'suggested_fix': suggested
    }

def validate_contacts_list(contacts: List[Dict[str, Any]], check_dns: bool = True) -> Dict[str, Any]:
    valid_list = []
    invalid_list = []
    details = []
    
    for c in contacts:
        email = c.get('email', '')
        res = validate_single_email(email, check_dns=check_dns)
        res['contact_id'] = c.get('id')
        res['name'] = c.get('name', '')
        res['company'] = c.get('company', '')
        res['role'] = c.get('role', '')
        details.append(res)
        
        if res['is_valid']:
            valid_list.append(c)
        else:
            invalid_list.append({**c, 'validation_reason': res['reason'], 'validation_status': res['status']})
            
    return {
        'total': len(contacts),
        'valid_count': len(valid_list),
        'invalid_count': len(invalid_list),
        'valid_contacts': valid_list,
        'invalid_contacts': invalid_list,
        'details': details
    }
