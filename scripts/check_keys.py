import re
from collections import Counter

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

keys = re.findall(r'key=["\']([^"\']+)["\']', text)
counts = Counter(keys)
dups = {k: v for k, v in counts.items() if v > 1}
if dups:
    print('Duplicate keys found:', dups)
else:
    print('SUCCESS: No duplicate keys found! All widget keys are 100% unique.')
