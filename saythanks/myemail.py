import os
import requests

from mailersend import emails
from urllib.error import URLError
from flask import url_for, current_app

# importing module
import logging

# Create and configure logger
logging.basicConfig(
    filename='Logfile.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S',
)

# Creating an object
logger = logging.getLogger()

# Email Infrastructure
# --------------------

# Initialize MailerSend SDK
mailersend_api_key = os.getenv('MAILERSEND_API_KEY')
if not mailersend_api_key:
    logger.error("MAILERSEND_API_KEY environment variable not set")
    mailer = None
else:
    mailer = emails.NewEmail(mailersend_api_key)

TEMPLATE = """<div>{}
<br>
<br>
--{}
<br>
<br>
The public URL for this note is <a clicktracking=off href="{}">here</a> <br>
<br>
<br>
=========
<br>
<br>
This note of gratitude was brought to you by SayThanks.io.
<br>
<br>
A KennethReitz project, now maintained by KGiSL Edu (https://edu.kgisl.com).
</div>
"""


def _get_note_url(note):
    """Generate the public URL for a note."""
    if not note.uuid:
        logging.error("Could not find UUID for note — link will be blank.")
        return ''
    with current_app.app_context():
        return url_for('share_note', uuid=note.uuid, _external=True)


def _get_audio_html(audio_path):
    """Generate HTML for audio attachment if present."""
    if audio_path is None:
        return ''
    with current_app.app_context():
        audio_url = url_for(
            "static",
            filename="recordings/" + audio_path,
            _external=True
        )
    return (
        f'<br><br><strong>🎧 Voice Note:</strong> '
        f'<a href="{audio_url}" target="_blank">Click to listen</a>'
    )


def _build_email_content(note, note_url, audio_html):
    """Build the email content in HTML and plaintext formats."""
    who = note.byline or 'someone'
    html_content = TEMPLATE.format(note.body + audio_html, note.byline, note_url)
    plaintext_content = f"{note.body}\n\n--{note.byline or ''}\n\n{note_url}"
    return who, html_content, plaintext_content


def _send_email(email_address, subject, html_content, plaintext_content):
    """Send email using MailerSend and handle the response."""
    mail_body = {}
    mailer.set_mail_from(
        {"name": "SayThanks.io", "email": "no-reply@saythanks.io"}, mail_body
    )
    mailer.set_mail_to([{"email": email_address}], mail_body)
    mailer.set_subject(subject, mail_body)
    mailer.set_html_content(html_content, mail_body)
    mailer.set_plaintext_content(plaintext_content, mail_body)

    response = mailer.send(mail_body)
    logger.info(f"MailerSend SDK send response: {response}")

    if not hasattr(response, 'status_code'):
        logger.info(f"Email request submitted successfully to {email_address}")
        return True

    if response.status_code == 202:
        logger.error(f"Email queued successfully for delivery to {email_address}")
        return True
    if response.status_code == 200:
        logger.info(f"Email sent successfully to {email_address}")
        return True
    if response.status_code >= 400:
        error_text = response.text if hasattr(response, 'text') else 'Unknown error'
        error_msg = f"MailerSend API error {response.status_code}: {error_text}"
        logger.error(error_msg)

    return True


def notify(note, email_address, topic=None, audio_path=None):
    """Send an email notification for a thank you note."""
    if mailer is None:
        logger.error("MailerSend not configured - email notification skipped")
        return False

    try:
        note_url = _get_note_url(note)
        audio_html = _get_audio_html(audio_path)
        who, html_content, plaintext_content = _build_email_content(
            note, note_url, audio_html
        )

        subject = (
            f'saythanks.io: {who} sent a note!'
            if not topic
            else f'saythanks.io: {who} sent a note about {topic}!'
        )

        return _send_email(
            email_address, subject, html_content, plaintext_content
        )

    except requests.exceptions.ConnectionError as e:
        logger.error(f"Network connection error when sending email: {str(e)}")
        logger.error(
            "Check your internet connection and MAILERSEND_API_KEY configuration"
        )
    except requests.exceptions.Timeout as e:
        logger.error(f"Timeout error when sending email: {str(e)}")
    except requests.exceptions.HTTPError as e:
        logger.error(f"HTTP error when sending email: {str(e)}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"Response status: {e.response.status_code}")
            logger.error(f"Response body: {e.response.text}")
    except URLError as e:
        logger.error(f"URL Error occurred: {str(e)}")
        print(e)
    except Exception as e:
        logger.error(f"Unexpected error when sending email: {str(e)}")
        logger.error(f"Error type: {type(e).__name__}")
        print(e)

    return False
