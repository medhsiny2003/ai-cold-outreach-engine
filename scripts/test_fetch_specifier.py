import imaplib
import time

mail = imaplib.IMAP4_SSL("imap.gmail.com", 993)
mail.login("mohammedhsiny2@gmail.com", "qawi kviz qjqu hwgb")
mail.select('"[Gmail]/All Mail"', readonly=True)

st, data = mail.search(None, 'X-GM-RAW', 'from:mailer-daemon')
ids = data[0].split()[:10]
seq = b",".join(ids).decode('ascii')

t0 = time.time()
st1, d1 = mail.fetch(seq, '(BODY.PEEK[1])')
print(f"BODY.PEEK[1] fetched in {time.time() - t0:.2f}s, count={len(d1)}")

t0 = time.time()
st2, d2 = mail.fetch(seq, '(RFC822.TEXT)')
print(f"RFC822.TEXT fetched in {time.time() - t0:.2f}s, count={len(d2)}")

mail.logout()
