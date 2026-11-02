"""Email notification for newly queued review items — fired from
review_queue.add(), the one place every pending/merge_conflict item
already passes through, so every path that reaches the queue is covered
automatically.

Best-effort: if SMTP isn't configured, this prints a warning and lets
the run continue rather than failing it. A missed notification is
recoverable (run `pipeline.py review list`); a crashed pipeline run
isn't worth risking over an email.

Required env vars: SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD,
NOTIFY_FROM, NOTIFY_TO.
"""
import os
import smtplib
from email.mime.text import MIMEText


def notify_new_review_item(entry):
    host = os.environ.get("SMTP_HOST")
    user = os.environ.get("SMTP_USER")
    password = os.environ.get("SMTP_PASSWORD")
    sender = os.environ.get("NOTIFY_FROM")
    recipient = os.environ.get("NOTIFY_TO")

    if not all([host, user, password, sender, recipient]):
        print("    (email notification skipped — SMTP_HOST/SMTP_USER/SMTP_PASSWORD/NOTIFY_FROM/NOTIFY_TO not fully set in .env)")
        return

    port = int(os.environ.get("SMTP_PORT", "587"))

    subject = f"[Doc Sync] Review needed ({entry['status']}): {entry['article_id']}"
    body = (
        f"Article: {entry['article_id']}\n"
        f"Feature area: {entry['feature_area']}\n"
        f"Status: {entry['status']}\n"
        f"Confidence: {entry['confidence']}\n\n"
        f"{entry['rationale']}\n\n"
    )
    body += "\nReview: python3 doc_sync/pipeline.py review list\n"

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = recipient

    try:
        with smtplib.SMTP(host, port, timeout=15) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(sender, [recipient], msg.as_string())
        print(f"    (notified {recipient} by email)")
    except Exception as exc:
        print(f"    (email notification failed: {exc} — item is still queued, just not emailed)")
