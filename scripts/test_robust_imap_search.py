import imaplib
import email
import re
import sys
from pathlib import Path

mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
mail.login("mohammedhsiny2@gmail.com", "qawi kviz qjqu hwgb")

print("[*] Test des requêtes IMAP...")

# Test 1: X-GM-RAW syntax
mail.select('"[Gmail]/All Mail"', readonly=True)
st, data = mail.search(None, 'X-GM-RAW', 'from:mailer-daemon')
print(f"Test X-GM-RAW from:mailer-daemon : {st}, count={len(data[0].split()) if st=='OK' and data[0] else 0}")

st2, data2 = mail.search(None, 'X-GM-RAW', 'from:postmaster')
print(f"Test X-GM-RAW from:postmaster : {st2}, count={len(data2[0].split()) if st2=='OK' and data2[0] else 0}")

st3, data3 = mail.search(None, 'X-GM-RAW', 'subject:"Address not found"')
print(f"Test X-GM-RAW subject:Address not found : {st3}, count={len(data3[0].split()) if st3=='OK' and data3[0] else 0}")

st4, data4 = mail.search(None, 'X-GM-RAW', 'subject:Delivery')
print(f"Test X-GM-RAW subject:Delivery : {st4}, count={len(data4[0].split()) if st4=='OK' and data4[0] else 0}")

mail.logout()
