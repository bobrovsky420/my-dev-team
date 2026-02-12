import requests
import smtplib
import time

SMTP_HOST = "localhost"
SMTP_PORT = 1025
MAILPIT_URL = "http://localhost:8025"
SUBJECT_TAG = "NEW PROJECT"
MANAGER_ADDRESS = "manager@ai-team.local"
HUMAN_ADDRESS = "cto@human.local"

def check_inbox():
    """
    Poll the local Mailpit inbox for new messages.
    If a message with "NEW PROJECT" in the subject is found, return its content.
    """
    print("🕵️  Manager checking local inbox...")
    while True:
        response = requests.get(f"{MAILPIT_URL}/api/v1/messages?to={MANAGER_ADDRESS}")
        messages = response.json().get('messages', [])
        for msg in messages:
            if msg['Subject'].startswith(SUBJECT_TAG):
                detail = requests.get(f"{MAILPIT_URL}/api/v1/message/{msg['ID']}")
                project_desc = detail.json()['Text']
                print(f"🚀 Found project: {msg['Subject']}")
                return project_desc
        time.sleep(10)

def send_update(text, *, receiver: str = HUMAN_ADDRESS, sender: str = MANAGER_ADDRESS):
    """
    Send a mail to a human
    """
    message = f"Subject: Status Update\n\n{text}"
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.sendmail(sender, receiver, message)
