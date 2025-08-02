import os

from mailersend import emails
from urllib.error import URLError
from flask import url_for, current_app

# importing module
import logging

# Create and configure logger
logging.basicConfig(filename='Logfile.log',
                    filemode='a',
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                    datefmt='%d-%b-%y %H:%M:%S')

# Creating an object
logger = logging.getLogger()

# Email Infrastructure
# --------------------

# Initialize MailerSend SDK
mailer = emails.NewEmail(os.getenv('MAILERSEND_API_KEY'))

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


def notify(note, email_address):
    """Use the note contents and a template, build a
    formatted message. Use MailerSend to deliver the formatted
    message as an email to the user.

    The email includes:
    - The note's body and byline.
    - A public URL for the note, allowing the user to share it with others.
        - If the note has a UUID, the URL is generated using Flask's `url_for`
        with the 'share_note' route.
        - If the note lacks a UUID, the URL field in the email will be left blank
        and an error is logged.

    Args:
        note: An object representing the note, expected to have 'body', 'byline',  
            and 'uuid' attributes.  
        email_address: The recipient's email address.  

    The function logs errors if the note's UUID is missing or if sending the email  
    fails.
    """
    try:
        if not note.uuid:
            logging.error("Could not find UUID for note — link will be blank.")
            note_url = ''
        else:
            with current_app.app_context():
                note_url = url_for('share_note', uuid=note.uuid, _external=True)

        # Say 'someone' if the byline is empty.
        who = note.byline or 'someone'

        subject = f'saythanks.io: {who} sent a note!'
        html_content = TEMPLATE.format(note.body, note.byline, note_url)
        plaintext_content = f"{note.body}\n\n--{note.byline or ''}\n\n{note_url}"

        mail_body = {}
        mailer.set_mail_from({"name": "SayThanks.io", "email": "no-reply@saythanks.io"}, mail_body)
        mailer.set_mail_to([{"email": email_address}], mail_body)
        mailer.set_subject(f"saythanks.io: {note.byline or 'someone'} sent a note!", mail_body)
        mailer.set_html_content(html_content, mail_body)
        mailer.set_plaintext_content(plaintext_content, mail_body)
        response = mailer.send(mail_body)

    except URLError as e:
        logging.error("URL Error occurred "+ str(e))
        print(e)
    except Exception as e:
        logging.error(f"MailerSend SDK send failed: {str(e)}")
        print(e)
