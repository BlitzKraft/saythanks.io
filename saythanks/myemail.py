import html
import os
import re
from string import Template
from urllib.error import URLError

import requests
from flask import url_for, current_app
from mailersend import emails

# importing module
import logging
from .logging_config import configure_logging

# Configure logging once for the application.
configure_logging()
logger = logging.getLogger(__name__)

# Email Infrastructure
# --------------------

# Initialize MailerSend SDK
mailersend_api_key = os.getenv('MAILERSEND_API_KEY')
if not mailersend_api_key:
    logger.error("MAILERSEND_API_KEY environment variable not set")
    mailer = None
else:
    mailer = emails.NewEmail(mailersend_api_key)

DEFAULT_TEMPLATE = 'classic'

_CLASSIC = """<div>$topic_block$body
<br>
<br>
$audio_block--$byline
<br>
<br>
The public URL for this note is <a clicktracking=off href="$note_url">here</a> <br>
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

_COMPACT = """<div style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;font-size:15px;line-height:1.5;color:#222;max-width:600px">
$topic_block
<div style="margin:0 0 12px">$body</div>
$audio_block
<div style="margin:0 0 12px;color:#555">--$byline</div>
<div style="margin:0 0 16px">The public URL for this note is <a clicktracking=off href="$note_url">here</a></div>
<hr style="border:0;border-top:1px solid #ddd;margin:16px 0">
<div style="font-size:13px;color:#777;line-height:1.4">
This note of gratitude was brought to you by SayThanks.io.<br>
A KennethReitz project, now maintained by KGiSL Edu (<a clicktracking=off href="https://edu.kgisl.com">https://edu.kgisl.com</a>).
</div>
</div>
"""

_LETTER = """<div style="font-family:-apple-system,Segoe UI,Roboto,Helvetica,Arial,sans-serif;font-size:15px;line-height:1.5;color:#222;max-width:600px">
<div style="border:1px solid #e5e5e5;border-left:4px solid #1EAEDB;padding:16px 20px;background:#fff">
<div style="font-size:12px;letter-spacing:0.04em;text-transform:uppercase;color:#1EAEDB;margin:0 0 12px">A note of gratitude</div>
$topic_block
<div style="margin:0 0 12px">$body</div>
$audio_block
<div style="margin:0 0 12px;color:#555">--$byline</div>
<div>The public URL for this note is <a clicktracking=off href="$note_url">here</a></div>
</div>
<div style="font-size:12px;color:#888;line-height:1.4;margin:12px 4px 0">
This note of gratitude was brought to you by SayThanks.io.<br>
A KennethReitz project, now maintained by KGiSL Edu (<a clicktracking=off href="https://edu.kgisl.com">https://edu.kgisl.com</a>).
</div>
</div>
"""

TEMPLATES = {
    'classic': Template(_CLASSIC),
    'compact': Template(_COMPACT),
    'letter': Template(_LETTER),
}
TEMPLATE_IDS = tuple(TEMPLATES)


def resolve_template_id(template_id):
    """Return a known template id, or Classic when the value is not allowed."""
    if template_id in TEMPLATE_IDS:
        return template_id
    return DEFAULT_TEMPLATE


def _topic_block(topic):
    """Return a Ref: HTML fragment, or '' when topic is missing."""
    if topic is None:
        return ''
    topic_text = str(topic).strip()
    if not topic_text:
        return ''
    escaped = html.escape(topic_text, quote=True)
    return (
        '<div style="margin:0 0 12px"><strong>Ref:</strong> about '
        f'{escaped}</div>'
    )


def render_email_html(
    template_id,
    *,
    body,
    byline,
    note_url,
    topic=None,
    audio_html='',
):
    """Render one predefined notification-email layout.

    `body` and `audio_html` are inserted as HTML. `byline`, `note_url`,
    and `topic` are escaped.
    """
    chosen = resolve_template_id(template_id)
    return TEMPLATES[chosen].safe_substitute(
        body='' if body is None else str(body),
        byline=html.escape('' if byline is None else str(byline), quote=True),
        note_url=html.escape(
            '' if note_url is None else str(note_url), quote=True
        ),
        topic_block=_topic_block(topic),
        audio_block='' if not audio_html else str(audio_html),
    )


def _get_note_url(note):
    """Generate the public URL for a note.

    Uses Flask's url_for with _external=True to produce an absolute URL
    for the 'share_note' endpoint using note.uuid.

    Parameters
    - note: object with attribute `uuid`.

    Returns
    - str: Absolute URL for the note if uuid is present,
      otherwise an empty string.

    Side effects
    - Logs an error if note.uuid is missing.
    """
    if not note.uuid:
        logging.error("Could not find UUID for note — link will be blank.")
        return ''
    with current_app.app_context():
        return url_for('share_note', uuid=note.uuid, _external=True)


def _plaintext_audio(audio_html):
    """Extract a voice-note URL from the HTML snippet for the plaintext part."""
    if not audio_html:
        return ''
    match = re.search(r'href="([^"]+)"', audio_html)
    if not match:
        return ''
    return f"\n\nVoice Note: {match.group(1)}"


def _build_email_content(
    note,
    note_url,
    audio_html='',
    template_id=None,
    body=None,
    topic=None,
):
    """Assemble HTML and plaintext email bodies.

    Parameters
    - note: object with attributes `body` and `byline`.
    - note_url: public URL for the note (string).
    - audio_html: optional HTML snippet for audio (string).
    - template_id: predefined layout id (unknown values fall back to classic).
    - body: optional pre-audio HTML body; defaults to note.body.
    - topic: optional topic string for a Ref: line in the HTML layout.

    Returns
    - tuple: (who, html_content, plaintext_content)
      - who: display name for the sender (note.byline or 'someone')
      - html_content: full HTML email body
      - plaintext_content: plain text representation for fallback
    """
    who = note.byline or 'someone'
    email_body = note.body if body is None else body
    html_content = render_email_html(
        template_id,
        body=email_body,
        byline=note.byline or '',
        note_url=note_url,
        topic=topic,
        audio_html=audio_html or '',
    )
    plaintext_content = (
        f"{email_body}\n\n--{note.byline or ''}"
        f"{_plaintext_audio(audio_html)}\n\n{note_url}"
    )
    return who, html_content, plaintext_content


def _send_email(email_address, subject, html_content, plaintext_content):
    """Send an email via the MailerSend SDK.

    Builds the mail payload, issues the send call and logs the response.

    Parameters
    - email_address: recipient email address (string or list accepted by SDK)
    - subject: email subject (string)
    - html_content: HTML body (string)
    - plaintext_content: plaintext body (string)

    Returns
    - bool: True when the send routine reports success or is queued.
      Logs errors for response codes >= 400.

    Notes
    - This function relies on the module-level `mailer` object initialized
      from the MAILERSEND_API_KEY environment variable.
    """
    mail_body = {}
    mailer.set_mail_from(
        {"name": "SayThanks.io", "email": "no-reply@saythanks.io"}, mail_body
    )
    mailer.set_mail_to([{"email": email_address}], mail_body)
    mailer.set_subject(subject, mail_body)
    mailer.set_html_content(html_content, mail_body)
    mailer.set_plaintext_content(plaintext_content, mail_body)

    response = mailer.send(mail_body)
    logger.info(f"MailerSend SDK send response: {response.strip()}")

    if not hasattr(response, 'status_code'):
        logger.info(f"Email request submitted successfully to {email_address}")
        return True

    if response.status_code == 202:
        logger.error(
            f"Email queued successfully for delivery to {email_address}"
        )
        return True
    if response.status_code == 200:
        logger.info(f"Email sent successfully to {email_address}")
        return True
    if response.status_code >= 400:
        error_text = (
            response.text if hasattr(response, 'text') else 'Unknown error'
        )
        error_msg = f"MailerSend API error {response.status_code}: {error_text}"
        logger.error(error_msg)

    return True


def notify(
    note,
    email_address,
    topic=None,
    audio_path=None,
    template_id=None,
    audio_html=None,
    body=None,
):
    """Send an email notification for a thank-you note.

    Orchestrates URL generation, optional audio handling, content assembly,
    subject formatting and the final send attempt. Catches and logs common
    network and HTTP-related exceptions.

    Parameters
    - note: note object (expects attributes `uuid`, `body`, `byline`)
    - email_address: recipient email address (string)
    - topic: optional topic string used in the email subject and Ref: line
    - audio_path: optional filename for an attached voice note (unused; kept
      for callers that still pass it)
    - template_id: predefined layout id (classic, compact, letter)
    - audio_html: optional voice-note HTML for a separate email slot
    - body: optional pre-audio HTML body; defaults to note.body

    Returns
    - bool: True if the email was submitted/queued, False on failure
      or when MailerSend is not configured.

    Error handling
    - Logs and returns False when mailer is not configured.
    - Catches requests and urllib errors and logs details for diagnosis.
    """
    if mailer is None:
        logger.error("MailerSend not configured - email notification skipped")
        return False

    try:
        note_url = _get_note_url(note)
        who, html_content, plaintext_content = _build_email_content(
            note,
            note_url,
            audio_html=audio_html or '',
            template_id=template_id,
            body=body,
            topic=topic,
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
            "Check your internet connection and "
            "MAILERSEND_API_KEY configuration"
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
