import requests
import smtplib
import time
from email.message import EmailMessage
from email.utils import formataddr

SMTP_HOST = "localhost"
SMTP_PORT = 1025
MAILPIT_URL = "http://localhost:8025"
SUBJECT_TAG = "NEW PROJECT"
MANAGER_ADDRESS = "manager@ai-team.local"
HUMAN_ADDRESS = "cto@human.local"
TIME_SLEEP = 10

def check_new_project():
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

def delete_message(message_id):
    """
    Remove the message from inbox
    """
    requests.delete(f"{MAILPIT_URL}/api/v1/messages", json={"ids": [message_id]})

def send_update(text, original_msg, *, receiver = HUMAN_ADDRESS, sender = MANAGER_ADDRESS):
    """
    Send a mail to a human
    """
    original_from = formataddr((original_msg['From']['Name'], original_msg['From']['Address']))
    body = (
        f"{text}\n\n"
        f"--- Original Message ---\n"
        f"From: {original_from}\n"
        f"Subject: {original_msg['Subject']}\n\n"
        f"{original_msg['Text']}"
    )
    msg = EmailMessage()
    msg.set_content(body)
    msg['Subject'] = f"Re: {original_msg['Subject']}"
    msg['To'] = receiver
    msg['From'] = sender
    msg['In-Reply-To'] = original_msg['ID']
    msg['References'] = original_msg['ID']

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.send_message(msg)
