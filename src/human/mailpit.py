from datetime import datetime
import logging
import requests
import smtplib
import time
from email.message import EmailMessage
from email.utils import formataddr
import markdown

SMTP_HOST = 'localhost'
SMTP_PORT = 1025
MAILPIT_URL = 'http://localhost:8025'
SUBJECT_TAG = 'NEW PROJECT'
MANAGER_ADDRESS = 'manager@ai-team.local'
HUMAN_ADDRESS = 'cto@human.local'
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
                msg_detail = detail.json()
                logging.debug("Received message: %s", str(msg_detail))
                return msg_detail
        time.sleep(TIME_SLEEP)

def delete_message(message_id):
    """
    Remove the message from inbox
    """
    requests.delete(f"{MAILPIT_URL}/api/v1/messages", json={'ids': [message_id]})

def send_update(text, original_msg, *, receiver = HUMAN_ADDRESS, sender = MANAGER_ADDRESS):
    """
    Send a mail to a human
    """
    html_text = markdown.markdown(text, extensions=['fenced_code'])
    original_subject = original_msg['Subject']
    original_from = formataddr((original_msg['From']['Name'], original_msg['From']['Address']))
    original_to = formataddr((original_msg['To'][0]['Name'], original_msg['To'][0]['Address']))
    original_date = datetime.fromisoformat(original_msg['Date']).strftime('%c')
    original_html = markdown.markdown(original_msg['Text'], extensions=['fenced_code'])
    body = (
        f"{html_text}<br><hr>"
        f"<b>From:</b> {original_from}<br>"
        f"<b>Sent:</b> {original_date}<br>"
        f"<b>To:</b> {original_to}<br>"
        f"<b>Subject:</b> {original_subject}<br><br>"
        f"{original_html}"
    )
    msg = EmailMessage()
    msg.set_content(body, subtype='html')
    msg['Subject'] = f"Re: {original_subject}"
    msg['To'] = receiver
    msg['From'] = sender
    msg['In-Reply-To'] = original_msg['ID']
    msg['References'] = original_msg['ID']
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.send_message(msg)
