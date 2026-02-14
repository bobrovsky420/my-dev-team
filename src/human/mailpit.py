import requests
import smtplib
import time
from email.message import EmailMessage

SMTP_HOST = "localhost"
SMTP_PORT = 1025
MAILPIT_URL = "http://localhost:8025"
SUBJECT_TAG = "NEW PROJECT"
MANAGER_ADDRESS = "manager@ai-team.local"
HUMAN_ADDRESS = "cto@human.local"
TIME_SLEEP = 10

def check_inbox():
    """
    Poll the local Mailpit inbox for new messages.
    If a message with "NEW PROJECT" in the subject is found, return its content.
    """
    while True:
        response = requests.get(f"{MAILPIT_URL}/api/v1/messages?to={MANAGER_ADDRESS}")
        messages = response.json().get('messages', [])
        for msg in messages:
            if msg['Subject'].startswith(SUBJECT_TAG):
                detail = requests.get(f"{MAILPIT_URL}/api/v1/message/{msg['ID']}")
                return detail.json()
        time.sleep(TIME_SLEEP)

def send_update(text, original_msg, *, receiver = HUMAN_ADDRESS, sender = MANAGER_ADDRESS):
    """
    Send a mail to a human
    """
    msg = EmailMessage()
    msg.set_content(text)
    msg['Subject'] = f"Re: {original_msg['Subject']}"
    msg['To'] = receiver
    msg['From'] = sender
    msg['In-Reply-To'] = original_msg['ID']
    msg['References'] = original_msg['ID']

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.send_message(msg)
