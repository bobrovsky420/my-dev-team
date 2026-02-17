from datetime import datetime
import logging
import re
import requests
import smtplib
import time
from email.message import EmailMessage
from email.utils import formataddr
import markdown
from project.project import Project

SMTP_HOST = 'localhost'
SMTP_PORT = 1025
MAILPIT_URL = 'http://localhost:8025'
SUBJECT_TAG = 'NEW PROJECT'
CLARIFICATION_TAG = 'CLARIFICATION REQUEST'
MANAGER_ADDRESS = 'manager@ai-team.local'
HUMAN_ADDRESS = 'cto@human.local'
TIME_SLEEP = 10

_thread_context = {
    'original_msg': None,
    'question_msg_id': None,
    'question_subject': None
}

def set_original_msg(original_msg: dict):
    _thread_context['original_msg'] = original_msg
    _thread_context['question_msg_id'] = None
    _thread_context['question_subject'] = None

def get_original_msg() -> dict:
    return _thread_context['original_msg']

def get_thread_context():
    return _thread_context

def update_original_msg(new_msg: dict):
    _thread_context['original_msg'] = new_msg

def set_question_context(msg_id: str, subject: str):
    """Store the clarification question message context for tracking responses."""
    _thread_context['question_msg_id'] = msg_id
    _thread_context['question_subject'] = subject

def check_new_project() -> Project:
    """
    Poll the local Mailpit inbox for new messages.
    If a message with "NEW PROJECT" in the subject is found, return its content.
    Original message is deleted after processing to prevent re-processing.
    """
    while True:
        response = requests.get(f"{MAILPIT_URL}/api/v1/messages?to={MANAGER_ADDRESS}")
        messages = response.json().get('messages', [])
        for msg in messages:
            if msg['Subject'].startswith(SUBJECT_TAG):
                detail = requests.get(f"{MAILPIT_URL}/api/v1/message/{msg['ID']}")
                msg_detail = detail.json()
                logging.debug("Received message: %s", str(msg_detail))
                set_original_msg(msg_detail)
                delete_message(msg_detail['ID'])
                project = Project(
                    original_mail=msg_detail,
                    title=msg_detail['Subject'][len(SUBJECT_TAG):].strip(),
                    description=msg_detail['Text']
                )
                return project
        time.sleep(TIME_SLEEP)

def delete_message(message_id):
    requests.delete(f"{MAILPIT_URL}/api/v1/messages", json={'ids': [message_id]})

def extract_body_from_html(html: str) -> str:
    """
    Extract body content from HTML if it's a full HTML document
    """
    if re.search(r'<html[^>]*>', html, re.IGNORECASE):
        if body_match := re.search(r'<body[^>]*>(.*?)</body>', html, re.IGNORECASE | re.DOTALL):
            return body_match.group(1)
    return html

def send_update(text, *, receiver = HUMAN_ADDRESS, sender = MANAGER_ADDRESS):
    """
    Compose and send an update mail
    """
    html_text = markdown.markdown(text, extensions=['fenced_code'])
    original_msg = get_original_msg()
    original_subject = original_msg['Subject']
    original_from = formataddr((original_msg['From']['Name'], original_msg['From']['Address']))
    original_to = formataddr((original_msg['To'][0]['Name'], original_msg['To'][0]['Address']))
    original_date = datetime.fromisoformat(original_msg['Date']).strftime('%c')
    original_html = extract_body_from_html(original_msg['HTML']) if 'HTML' in original_msg and original_msg['HTML'] else markdown.markdown(original_msg['Text'], extensions=['fenced_code'])
    body = (
        f"{html_text}"
        f"<br><hr>"
        f"<b>From:</b> {original_from}<br>"
        f"<b>Sent:</b> {original_date}<br>"
        f"<b>To:</b> {original_to}<br>"
        f"<b>Subject:</b> {original_subject}<br><br>"
        f"{original_html}"
    )
    msg = EmailMessage()
    msg.set_content(body, subtype='html')
    msg['Subject'] = original_subject if original_subject.startswith('Re:') else f"Re: {original_subject}"
    msg['To'] = receiver
    msg['From'] = sender
    msg['In-Reply-To'] = f"<{original_msg['MessageID']}>"
    msg['References'] = f"<{original_msg['MessageID']}>"
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.send_message(msg)

def send_question(question: str, role: str = 'Crew Manager', *, receiver = HUMAN_ADDRESS, sender = MANAGER_ADDRESS):
    """
    Send a clarification question to human and add it to the history
    """
    question_subject = f"{CLARIFICATION_TAG} [{role}]: {question[:50]}..."
    question_text = f"[{role}] {question}"
    msg = EmailMessage()
    msg.set_content(markdown.markdown(question_text, extensions=['fenced_code']), subtype='html')
    msg['Subject'] = question_subject
    msg['To'] = receiver
    msg['From'] = sender
    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.send_message(msg)
    set_question_context(question_subject, question_subject)
    logging.info(f"Clarification question sent from {role}: {question}")

def wait_for_clarification(max_wait_seconds: int = 300, receiver = MANAGER_ADDRESS, sender = HUMAN_ADDRESS):
    """
    Wait for a human response to a clarification question
    """
    wait_start = time.time()
    while True:
        if time.time() - wait_start > max_wait_seconds:
            logging.warning(f"No clarification received within {max_wait_seconds} seconds")
            return None
        response = requests.get(f"{MAILPIT_URL}/api/v1/messages?to={receiver}&from={sender}")
        messages = response.json().get('messages', [])
        for msg in messages:
            if msg['Subject'].startswith(f"Re: {CLARIFICATION_TAG}"):
                detail = requests.get(f"{MAILPIT_URL}/api/v1/message/{msg['ID']}")
                msg_detail = detail.json()
                response_text = msg_detail['Text']
                logging.info("Received clarification: %s", response_text)
                delete_message(msg_detail['ID'])
                return response_text
        time.sleep(TIME_SLEEP)
