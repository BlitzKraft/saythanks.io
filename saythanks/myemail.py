# myemail.py

import os
import logging
import sendgrid
import sqlalchemy
from urllib.error import URLError
from sendgrid.helpers.mail import Email, To, Content, Mail
from flask import url_for, current_app

from . import storage

# -----------------------------
# Logging Configuration
# -----------------------------
logging.basicConfig(
    filename='Logfile.log',
    filemode='a',
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    datefmt='%d-%b-%y %H:%M:%S'
)
logger = logging.getLogger()

# -----------------------------
# SendGrid Setup
# -----------------------------
API_KEY = os.environ['SENDGRID_API_KEY']
sg = sendgrid.SendGridAPIClient(api_key=API_KEY)

# -----------------------------
# Email Template with Link
# -----------------------------
TEMPLATE = """<div>{}
<br><br>
--{}
<br><br>
Want to see it online? Just go ahead and click:<br>
<a href="{}">Read your note</a>
<br><br>
=========
<br><br>
This note of thanks was brought to you by SayThanks.io.
<br><br>
A KennethReitz project, now maintained by KGiSL Edu (info@kgisl.com).
</div>
"""

# -----------------------------
# Email Notification Function
# -----------------------------
def notify(note, email_address):
    """Build and send a formatted message with SendGrid."""

    try:
        # Step 1: Ensure note.uuid is populated
        if not getattr(note, 'uuid', None):
            q = sqlalchemy.text(
                "SELECT uuid FROM notes "
                "WHERE body = :body AND byline = :byline "
                "ORDER BY timestamp DESC LIMIT 1"
            )
            row = storage.conn.execute(
                q,
                body=note.body,
                byline=note.byline
            ).fetchone()
            note.uuid = row['uuid'] if row else None

        who = note.byline or 'someone'
        subject = f'saythanks.io: {who} sent a note!'

        if not note.uuid:
            logging.error("Could not find UUID for note — link will be blank.")
            note_url = ''
        else:
            with current_app.app_context():
                note_url = url_for('share_note', uuid=note.uuid, _external=True)

        message = TEMPLATE.format(note.body, note.byline, note_url)

        from_address = Email('no-reply@saythanks.io', name="SayThanks.io")
        to_address = To(email_address)
        content = Content('text/html', message)

        mail = Mail(from_address, to_address, subject, content)
        response = sg.client.mail.send.post(request_body=mail.get())

        logging.info(f"Email sent to {email_address} with status code {response.status_code}")

    except URLError as e:
        logging.error("URL Error occurred: " + str(e))
        print(e)
    except Exception as e:
        logging.error("General Error occurred: " + str(e))
        print(e)
