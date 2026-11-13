import re
from collections import Counter

with open('app.py', 'r', encoding='utf-8') as f:
    text = f.read()

keys = re.findall(r'key=["\']([^"\']+)["\']', text)
counts = Counter(keys)

duplicates = {k: v for k, v in counts.items() if v > 1}
if duplicates:
    print("Found duplicate keys:")
    for k, v in duplicates.items():
        print(f"  {k}: {v} times")
else:
    print("✅ No duplicate literal keys found!")
